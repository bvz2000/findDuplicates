import ast
import configparser
import os.path

import lib

from ui import DirUI
from ui import FileOutUI
from ui import IntUI
from ui import MultiDirUI
from ui import MultipleFileTypes
from ui import TrueFalseUI


# ------------------------------------------------------------------------------
class Settings(object):
    """
    Queries the user to get the info needed to run the compare.
    """

    # --------------------------------------------------------------------------
    def __init__(self, resources_obj, defaults, advanced=False):
        """
        Set up the basic wizard.

        :param resources_obj: The language resources object.
        :param defaults: A dictionary containing the defaults.

        :return: Nothing.
        """

        # Store the resources object
        self.resources_obj = resources_obj
        self.advanced = advanced

        # Store the number of steps
        if advanced:
            self.step_count = 17
        else:
            self.step_count = 4

        # Establish the legal set of affirmative responses
        self.legal_affirmatives = self.resources_obj.get("legal_chars",
                                                         "legal_affirmatives")
        self.legal_affirmatives = ast.literal_eval(self.legal_affirmatives)

        # Store the defaults
        self.defaults = defaults

        # Set the attributes of this object to the default values
        self.source_dir = defaults["source_dir"]
        self.skip_source = defaults["skip_source_sub_dirs"]
        self.source_dirs_to_skip = defaults["source_dirs_to_skip"]
        self.target_dir = defaults["target_dir"]
        self.skip_target_sub_dirs = defaults["skip_target_sub_dirs"]
        self.target_dirs_to_skip = defaults["target_dirs_to_skip"]
        self.log_file = defaults["log_file"]
        self.limit_to_patterns = defaults["limit_to_patterns"]
        self.pattern_list = defaults["pattern_list"]
        self.skip_zero_len = defaults["skip_zero_len"]
        self.skip_hidden = defaults["skip_hidden"]
        self.skip_dsstore = defaults["skip_dsstore"]
        self.skip_links = defaults["skip_links"]
        self.follow_links = defaults["follow_links"]
        self.many_dupes = defaults["many_dupes"]
        self.do_debug = defaults["do_debug"]
        self.debug_limit = defaults["debug_limit"]

    # --------------------------------------------------------------------------
    def run_wizard(self):
        """
        Runs the wizard.

        :return: Nothing.
        """

        current_step = 0
        skip_msg = self.resources_obj.get("messages", "skip")

        # Source Dir
        current_step += 1
        self.source_dir = self.get_source_dir(
            current_step,
            self.step_count,
            self.defaults["source_dir"])

        # The following question will only be asked if advanced is true
        if self.advanced:

            # Skip Source Dirs
            current_step += 1
            skip = self.get_skip_source_sub_dirs(
                current_step,
                self.step_count,
                self.defaults["skip_source_sub_dirs"])
            if skip:
                current_step += 1
                self.source_dirs_to_skip = self.get_source_sub_dirs_to_skip(
                    current_step,
                    self.step_count,
                    self.defaults["source_dirs_to_skip"])
            else:
                current_step += 1
                lib.display_message(
                    lib.format_string(
                        skip_msg.format(step_no=current_step)))

        # Target Dir
        current_step += 1
        self.target_dir = self.get_target_dir(
            current_step,
            self.step_count,
            self.defaults["target_dir"])

        # The following question will only be asked if advanced is true
        if self.advanced:

            # Skip Target Dirs
            current_step += 1
            skip = self.get_skip_target_sub_dirs(
                current_step,
                self.step_count,
                self.defaults["skip_target_sub_dirs"])
            if skip:
                current_step += 1
                self.target_dirs_to_skip = self.get_target_sub_dirs_to_skip(
                    current_step,
                    self.step_count,
                    self.defaults["target_dirs_to_skip"])
            else:
                current_step += 1
                lib.display_message(
                    lib.format_string(
                        skip_msg.format(step_no=current_step)))

        # Log file
        current_step += 1
        self.log_file = self.get_log_file(
            current_step,
            self.step_count,
            self.defaults["log_file"])

        # The following question will only be asked if advanced is true
        if self.advanced:

            # Limit to file types
            current_step += 1
            limit = self.get_limit_to_file_patterns(
                current_step,
                self.step_count,
                self.defaults["limit_to_patterns"])
            if limit:
                current_step += 1
                self.pattern_list = self.get_file_patterns(
                    current_step,
                    self.step_count,
                    self.defaults["pattern_list"])
            else:
                current_step += 1
                lib.display_message(
                    lib.format_string(
                        skip_msg.format(step_no=current_step)))

            # Skip files of zero length
            current_step += 1
            self.skip_zero_len = self.get_skip_zero_len(
                current_step,
                self.step_count,
                self.defaults["skip_zero_len"])

            # skip hidden files
            current_step += 1
            self.skip_hidden = self.get_skip_hidden(
                current_step,
                self.step_count,
                self.defaults["skip_hidden"])

            # Skip .DSStore files
            current_step += 1
            self.skip_dsstore = self.get_skip_ds_store(
                current_step,
                self.step_count,
                self.defaults["skip_dsstore"])

            # Skip symlinks
            current_step += 1
            self.skip_links = self.get_skip_symlinks(
                current_step,
                self.step_count,
                self.defaults["skip_links"])

            # Follow symlinks
            current_step += 1
            self.follow_links = self.get_follow_symlinks(
                current_step,
                self.step_count,
                self.defaults["follow_links"])

        # Will there likely be many duplicate files
        current_step += 1
        self.many_dupes = self.get_many_dupes(
            current_step,
            self.step_count,
            self.defaults["many_dupes"])

        # The following question will only be asked if advanced is true
        if self.advanced:

            # Debug
            current_step += 1
            self.do_debug = self.get_do_debug(
                current_step,
                self.step_count,
                self.defaults["do_debug"])
            if self.do_debug:
                current_step += 1
                self.debug_limit = self.get_debug_limit(
                    current_step,
                    self.step_count,
                    self.defaults["debug_limit"])
            else:
                current_step += 1
                lib.display_message(
                    lib.format_string(
                        skip_msg.format(step_no=current_step)))

    # --------------------------------------------------------------------------
    def get_source_dir(self, step, step_count, default="~"):
        """
        Get the source directory from the user.

        :return: A list of length one containing the source directory.
        """

        default = os.path.expanduser(default)
        ui_obj = DirUI(
            self.resources_obj,
            "source_dir",
            step,
            step_count,
            default)
        ui_obj.get_input()
        return ui_obj.values[0]

    # --------------------------------------------------------------------------
    def get_skip_source_sub_dirs(self, step, step_count, default=False):
        """
        Ask whether to skip any sub-directories of the source directory.

        :return: A list of length one with a True or False.
        """

        ui_obj = TrueFalseUI(
            self.resources_obj,
            "skip_source_sub_dirs",
            step,
            step_count,
            default)
        ui_obj.get_input()
        return ui_obj.values[0]

    # --------------------------------------------------------------------------
    def get_source_sub_dirs_to_skip(self, step, step_count, default=""):
        """
        Get a list of source sub dirs to skip.

        :return: A list containing the source sub directories to skip.
        """

        ui_obj = MultiDirUI(
            self.resources_obj,
            "source_dirs_to_skip",
            step,
            step_count,
            default)
        ui_obj.get_input()
        return ui_obj.values

    # --------------------------------------------------------------------------
    def get_target_dir(self, step, step_count, default="~"):
        """
        Get the target directory from the user.

        :return: A list of length one containing the target directory.
        """

        default = os.path.expanduser(default)
        ui_obj = DirUI(
            self.resources_obj,
            "target_dir",
            step,
            step_count,
            default)
        ui_obj.get_input()
        return ui_obj.values[0]

    # --------------------------------------------------------------------------
    def get_skip_target_sub_dirs(self, step, step_count, default=False):
        """
        Ask whether to skip any sub-directories of the target directory.

        :return: A list of length one with a True or False.
        """

        ui_obj = TrueFalseUI(
            self.resources_obj,
            "skip_target_sub_dirs",
            step,
            step_count,
            default)
        ui_obj.get_input()
        return ui_obj.values[0]

    # --------------------------------------------------------------------------
    def get_target_sub_dirs_to_skip(self, step, step_count, default=""):
        """
        Get a list of target sub dirs to skip.

        :return: A list containing the target sub directories to skip.
        """

        ui_obj = MultiDirUI(
            self.resources_obj,
            "target_dirs_to_skip",
            step,
            step_count,
            default)
        ui_obj.get_input()
        return ui_obj.values

    # --------------------------------------------------------------------------
    def get_log_file(self, step, step_count, default="~/duplicates.log"):
        """
        Get a path to where the log will be written.

        :return: A list of length one containing the path to the log file.
        """

        default = os.path.expanduser(default)
        ui_obj = FileOutUI(
            self.resources_obj,
            "log_file",
            step,
            step_count,
            default)
        ui_obj.get_input()
        return ui_obj.values[0]

    # --------------------------------------------------------------------------
    def get_limit_to_file_patterns(self, step, step_count, default=False):
        """
        Ask whether to limit the compares to specific file types.

        :return: A list of length one with a True or False.
        """

        ui_obj = TrueFalseUI(
            self.resources_obj,
            "limit_to_patterns",
            step,
            step_count,
            default)
        ui_obj.get_input()
        return ui_obj.values[0]

    # --------------------------------------------------------------------------
    def get_file_patterns(self, step, step_count, default=""):
        """
        Get a list of file types to limit the compare to.

        :return: A list of file types.
        """

        ui_obj = MultipleFileTypes(
            self.resources_obj,
            "pattern_list",
            step,
            step_count,
            default)
        ui_obj.get_input()
        return ui_obj.values

    # --------------------------------------------------------------------------
    def get_skip_zero_len(self, step, step_count, default=True):
        """
        Ask whether to limit the compares to specific file types.

        :return: A list of length one with a True or False.
        """

        ui_obj = TrueFalseUI(
            self.resources_obj,
            "skip_zero_len",
            step,
            step_count,
            default)
        ui_obj.get_input()
        return ui_obj.values[0]

    # --------------------------------------------------------------------------
    def get_skip_hidden(self, step, step_count, default=False):
        """
        Ask whether to limit the compares to specific file types.

        :return: A list of length one with a True or False.
        """

        ui_obj = TrueFalseUI(
            self.resources_obj,
            "skip_hidden",
            step,
            step_count,
            default)
        ui_obj.get_input()
        return ui_obj.values[0]

    # --------------------------------------------------------------------------
    def get_skip_ds_store(self, step, step_count, default=True):
        """
        Ask whether to limit the compares to specific file types.

        :return: A list of length one with a True or False.
        """

        ui_obj = TrueFalseUI(
            self.resources_obj,
            "skip_dsstore",
            step,
            step_count,
            default)
        ui_obj.get_input()
        return ui_obj.values[0]

    # --------------------------------------------------------------------------
    def get_skip_symlinks(self, step, step_count, default=True):
        """
        Ask whether to limit the compares to specific file types.

        :return: A list of length one with a True or False.
        """

        ui_obj = TrueFalseUI(
            self.resources_obj,
            "skip_links",
            step,
            step_count,
            default)
        ui_obj.get_input()
        return ui_obj.values[0]

    # --------------------------------------------------------------------------
    def get_follow_symlinks(self, step, step_count, default=False):
        """
        Ask whether to limit the compares to specific file types.

        :return: A list of length one with a True or False.
        """

        ui_obj = TrueFalseUI(
            self.resources_obj,
            "follow_links",
            step,
            step_count,
            default)
        ui_obj.get_input()
        return ui_obj.values[0]

    # --------------------------------------------------------------------------
    def get_many_dupes(self, step, step_count, default=False):
        """
        Ask whether to limit the compares to specific file types.

        :return: A list of length one with a True or False.
        """

        ui_obj = TrueFalseUI(
            self.resources_obj,
            "many_dupes",
            step,
            step_count,
            default)
        ui_obj.get_input()
        return ui_obj.values[0]

    # --------------------------------------------------------------------------
    def get_do_debug(self, step, step_count, default=False):
        """
        Ask whether to enable debugging.

        :return: A list of length one with a True or False.
        """

        ui_obj = TrueFalseUI(
            self.resources_obj,
            "do_debug",
            step,
            step_count,
            default)
        ui_obj.get_input()
        return ui_obj.values[0]

    # --------------------------------------------------------------------------
    def get_debug_limit(self, step, step_count, default=1000):
        """
        Get the number of lines in the debug log.

        :return: An integer.
        """

        ui_obj = IntUI(
            self.resources_obj,
            "debug_limit",
            step,
            step_count,
            default)
        ui_obj.get_input()
        return ui_obj.values[0]

    # --------------------------------------------------------------------------
    def write_preset(self, file_name):
        """
        Writes the current settings out to a preset file.

        :param file_name: The name of the preset file to write to.

        :return: Nothing.
        """

        preset = configparser.ConfigParser()

        preset.add_section("presets")
        preset.set("presets", "source_dir", str(self.source_dir))
        preset.set("presets", "skip_source_sub_dirs", str(self.skip_source))
        preset.set("presets", "source_dirs_to_skip", str(self.source_dirs_to_skip))
        preset.set("presets", "target_dir", str(self.target_dir))
        preset.set("presets", "skip_target_sub_dirs", str(self.skip_target_sub_dirs))
        preset.set("presets", "target_dirs_to_skip", str(self.target_dirs_to_skip))
        preset.set("presets", "log_file", str(self.log_file))
        preset.set("presets", "limit_to_patterns", str(self.limit_to_patterns))
        preset.set("presets", "pattern_list", str(self.pattern_list))
        preset.set("presets", "skip_zero_len", str(self.skip_zero_len))
        preset.set("presets", "skip_hidden", str(self.skip_hidden))
        preset.set("presets", "skip_dsstore", str(self.skip_dsstore))
        preset.set("presets", "skip_links", str(self.skip_links))
        preset.set("presets", "follow_links", str(self.follow_links))
        preset.set("presets", "many_dupes", str(self.many_dupes))
        preset.set("presets", "do_debug", str(self.do_debug))
        preset.set("presets", "debug_limit", str(self.debug_limit))

        if not os.path.exists(os.path.split(file_name)[0]):
            os.makedirs(os.path.split(file_name)[0])

        with open(file_name, "w") as f:
            preset.write(f)
