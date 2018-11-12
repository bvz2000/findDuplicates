import ast
import os.path

import lib

from ui import DirUI
from ui import TrueFalseUI
from ui import MultiDirUI
from ui import FileInUI
from ui import FileOutUI
from ui import MultipleFileTypes


# ------------------------------------------------------------------------------
class Settings(object):
    """
    Queries the user to get the info needed to run the compare.
    """

    # --------------------------------------------------------------------------
    def __init__(self, resources_obj, defaults):
        """
        Set up the basic wizard.

        :param resources_obj: The language resources object.
        :param defaults: A dictionary containing the defaults.

        :return: Nothing.
        """

        # Store the resources object
        self.resources_obj = resources_obj

        # Establish the legal set of affirmative responses
        self.legal_affirmatives = self.resources_obj.get("legal_chars",
                                                         "legal_affirmatives")
        self.legal_affirmatives = ast.literal_eval(self.legal_affirmatives)

        # Store the defaults
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

        skip_msg = self.resources_obj.get("messages", "skip")

        # Source Dir
        self.source_dir = self.get_source_dir(self.source_dir)

        # Skip Source Dirs
        if self.get_skip_source_sub_dirs(self.skip_source):
            temp = self.get_source_sub_dirs_to_skip(self.source_dirs_to_skip)
            self.source_dirs_to_skip = temp
        else:
            lib.display_message(lib.format_string(skip_msg.format(step_no=3)))

        # Target Dir
        self.target_dir = self.get_target_dir(self.target_dir)

        # Skip Target Dirs
        if self.get_skip_target_sub_dirs(self.skip_target_sub_dirs):
            temp = self.get_target_sub_dirs_to_skip(self.target_dirs_to_skip)
            self.target_dirs_to_skip = temp
        else:
            lib.display_message(lib.format_string(skip_msg.format(step_no=6)))

        # Log file
        self.log_file = self.get_log_file(self.log_file)

        # Limit to file types
        if self.get_limit_to_file_patterns(self.limit_to_patterns):
            self.pattern_list = self.get_file_patterns(self.pattern_list)
        else:
            lib.display_message(lib.format_string(skip_msg.format(step_no=9)))

        self.skip_zero_len = self.get_skip_zero_len(self.skip_zero_len)
        self.skip_hidden = self.get_skip_hidden(self.skip_hidden)
        self.skip_dsstore = self.get_skip_ds_store(self.skip_dsstore)
        self.skip_links = self.get_skip_symlinks(self.skip_links)
        self.follow_links = self.get_follow_symlinks(self.follow_links)
        self.many_dupes = self.get_many_dupes(self.many_dupes)

        # Debug
        if self.get_do_debug(self.do_debug):
            self.debug_limit = self.get_debug_limit(self.debug_limit)
        else:
            lib.display_message(lib.format_string(skip_msg.format(step_no=17)))

    # --------------------------------------------------------------------------
    def get_source_dir(self, default="~"):
        """
        Get the source directory from the user.

        :return: A list of length one containing the source directory.
        """

        default = os.path.expanduser(default)
        ui_obj = DirUI(self.resources_obj, "source_dir", 1, 17, default)
        ui_obj.get_input()
        return ui_obj.values[0]

    # --------------------------------------------------------------------------
    def get_skip_source_sub_dirs(self, default=False):
        """
        Ask whether to skip any sub-directories of the source directory.

        :return: A list of length one with a True or False.
        """

        ui_obj = TrueFalseUI(self.resources_obj, "skip_source_sub_dirs", 2, 17,
                             default)
        ui_obj.get_input()
        return ui_obj.values[0]

    # --------------------------------------------------------------------------
    def get_source_sub_dirs_to_skip(self, default=""):
        """
        Get a list of source sub dirs to skip.

        :return: A list containing the source sub directories to skip.
        """

        ui_obj = MultiDirUI(self.resources_obj, "source_dirs_to_skip", 3, 17,
                            default)
        ui_obj.get_input()
        return ui_obj.values

    # --------------------------------------------------------------------------
    def get_target_dir(self, default="~"):
        """
        Get the target directory from the user.

        :return: A list of length one containing the target directory.
        """

        default = os.path.expanduser(default)
        ui_obj = DirUI(self.resources_obj, "target_dir", 4, 17,
                       default)
        ui_obj.get_input()
        return ui_obj.values[0]

    # --------------------------------------------------------------------------
    def get_skip_target_sub_dirs(self, default=False):
        """
        Ask whether to skip any sub-directories of the target directory.

        :return: A list of length one with a True or False.
        """

        ui_obj = TrueFalseUI(self.resources_obj, "skip_target_sub_dirs", 5, 17,
                             default)
        ui_obj.get_input()
        return ui_obj.values[0]

    # --------------------------------------------------------------------------
    def get_target_sub_dirs_to_skip(self, default=""):
        """
        Get a list of target sub dirs to skip.

        :return: A list containing the target sub directories to skip.
        """

        ui_obj = MultiDirUI(self.resources_obj, "target_dirs_to_skip", 6, 17,
                            default)
        ui_obj.get_input()
        return ui_obj.values

    # --------------------------------------------------------------------------
    def get_log_file(self, default="~/duplicates.log"):
        """
        Get a path to where the log will be written.

        :return: A list of length one containing the path to the log file.
        """

        default = os.path.expanduser(default)
        ui_obj = FileOutUI(self.resources_obj, "log_file", 7, 17,
                           default)
        ui_obj.get_input()
        return ui_obj.values[0]

    # --------------------------------------------------------------------------
    def get_limit_to_file_patterns(self, default=False):
        """
        Ask whether to limit the compares to specific file types.

        :return: A list of length one with a True or False.
        """

        ui_obj = TrueFalseUI(self.resources_obj, "limit_to_patterns", 8, 17,
                             default)
        ui_obj.get_input()
        return ui_obj.values[0]

    # --------------------------------------------------------------------------
    def get_file_patterns(self, default=""):
        """
        Get a list of file types to limit the compare to.

        :return: A list of file types.
        """

        ui_obj = MultipleFileTypes(self.resources_obj, "pattern_list", 9, 17,
                                   default)
        ui_obj.get_input()
        return ui_obj.values

    # --------------------------------------------------------------------------
    def get_skip_zero_len(self, default=True):
        """
        Ask whether to limit the compares to specific file types.

        :return: A list of length one with a True or False.
        """

        ui_obj = TrueFalseUI(self.resources_obj, "skip_zero_len", 10, 17,
                             default)
        ui_obj.get_input()
        return ui_obj.values[0]

    # --------------------------------------------------------------------------
    def get_skip_hidden(self, default=False):
        """
        Ask whether to limit the compares to specific file types.

        :return: A list of length one with a True or False.
        """

        ui_obj = TrueFalseUI(self.resources_obj, "skip_hidden", 11, 17,
                             default)
        ui_obj.get_input()
        return ui_obj.values[0]

    # --------------------------------------------------------------------------
    def get_skip_ds_store(self, default=True):
        """
        Ask whether to limit the compares to specific file types.

        :return: A list of length one with a True or False.
        """

        ui_obj = TrueFalseUI(self.resources_obj, "skip_dsstore", 12, 17,
                             default)
        ui_obj.get_input()
        return ui_obj.values[0]

    # --------------------------------------------------------------------------
    def get_skip_symlinks(self, default=True):
        """
        Ask whether to limit the compares to specific file types.

        :return: A list of length one with a True or False.
        """

        ui_obj = TrueFalseUI(self.resources_obj, "skip_links", 13, 17,
                             default)
        ui_obj.get_input()
        return ui_obj.values[0]

    # --------------------------------------------------------------------------
    def get_follow_symlinks(self, default=False):
        """
        Ask whether to limit the compares to specific file types.

        :return: A list of length one with a True or False.
        """

        ui_obj = TrueFalseUI(self.resources_obj, "follow_links", 14, 17,
                             default)
        ui_obj.get_input()
        return ui_obj.values[0]

    # --------------------------------------------------------------------------
    def get_many_dupes(self, default=False):
        """
        Ask whether to limit the compares to specific file types.

        :return: A list of length one with a True or False.
        """

        ui_obj = TrueFalseUI(self.resources_obj, "many_dupes", 15, 17,
                             default)
        ui_obj.get_input()
        return ui_obj.values[0]

    # --------------------------------------------------------------------------
    def get_do_debug(self, default=False):
        """
        Ask whether to enable debugging.

        :return: A list of length one with a True or False.
        """

        ui_obj = TrueFalseUI(self.resources_obj, "do_debug", 16, 17,
                             default)
        ui_obj.get_input()
        return ui_obj.values[0]

    # --------------------------------------------------------------------------
    def get_debug_limit(self, default=1000):
        """
        Get the number of lines in the debug log.

        :return: An integer.
        """

        ui_obj = TrueFalseUI(self.resources_obj, "debug_limit", 17, 17,
                             default)
        ui_obj.get_input()
        return ui_obj.values[0]
