import ast
import os
import sys

import lib


# ==============================================================================
class UI(object):
    """
    Base UI class. Intended to be subclassed.
    """

    def __init__(self, resources_obj, section, step_no, total_steps,
                 default_value=None):
        """
        Init.
        """

        # Store the passed values.
        self.resources_obj = resources_obj
        self.section = section
        self.step_no = step_no
        self.total_steps = total_steps
        self.default_value = default_value

        # Extract and format the data from the language resources file.
        self.title = self.get_title()
        self.desc = self.get_description()
        self.query = self.get_instruction()
        self.prompt = self.get_prompt()
        self.legal_quit_chars = self.get_legal_quit_chars()

        # Some basic flags that will have to be overridden in subclasses.
        self.multi_item = False

        self.values = list()

    # --------------------------------------------------------------------------
    @staticmethod
    def wrap_text(msg, max_width=80):
        """
        Wraps text to match the maxWidth (i.e. it will split on a space, but be
        no longer than max_width)

        :param msg: The message to split
        :param max_width: The maximum number of characters. Defaults to 80
               characters.

        :return: The message with newlines inserted.
        """

        lines = list()

        # First split on newlines
        sections = msg.replace(r"\n", "\n").split("\n")

        # Process each section independently
        for section in sections:

            # Split the section on spaces
            section_lines = list()
            line = ""
            words = section.split(" ")

            # Process each word
            for word in words:
                if len(line + " " + word) > max_width:
                    section_lines.append(line)
                    line = word
                else:
                    line += " " + word

            # Append the last bit and create a string out of it
            section_lines.append(line)
            section_string = "\n".join(section_lines).lstrip("\n").lstrip(" ")

            # Append this string to the lines list
            lines.append(section_string)

        # Return a final, formatted string
        return "\n".join(lines).lstrip(" ")

    # --------------------------------------------------------------------------
    def get_title(self):
        """
        Returns the title_string of an interactive session.

        :return: The title_string as a string.
        """

        step_string = self.resources_obj.get("messages", "step")
        step_string = step_string.format(step_no=self.step_no,
                                         steps=self.total_steps)
        title_string = self.resources_obj.get(self.section, "title")

        title = step_string + title_string + "\n"
        title += "-" * 90 + "\n"

        return self.wrap_text(lib.format_string(title))

    # --------------------------------------------------------------------------
    def get_description(self):
        """
        Returns the description of an interactive session.

        :return: The description as a string.
        """

        desc = self.resources_obj.get(self.section, "description")
        desc = self.wrap_text(desc, 90) + "\n"

        return self.wrap_text(lib.format_string(desc))

    # --------------------------------------------------------------------------
    def get_instruction(self):
        """
        Returns the instruction portion of an interactive session.

        :return: The instruction as a string.
        """

        # prefix = lib.BRIGHT_CYAN + "Please do the following:\n" + lib.ENDC
        instruction = self.resources_obj.get(self.section, "instruction")
        instruction = self.wrap_text(instruction, 90)
        instruction += "\n"

        return self.wrap_text(lib.format_string(instruction))

    # --------------------------------------------------------------------------
    def get_prompt(self):
        """
        Returns the title of an interactive session.

        :return: The title as a string.
        """

        msg = self.resources_obj.get(self.section, "prompt") + "\n"
        if self.default_value is not None:
            msg += lib.ENDC + "-> " + lib.BRIGHT_YELLOW
            msg += str(self.format_default(self.default_value))
            msg += "\n"
        msg += lib.ENDC

        return self.wrap_text(lib.format_string(msg), 100)

    # --------------------------------------------------------------------------
    def get_legal_quit_chars(self):
        """
        Returns a list of legal quit characters.

        :return: The legal quit characters in the form of a list.
        """

        legal_quit_chars = self.resources_obj.get("legal_chars",
                                                  "legal_quit_characters")
        legal_quit_chars = ast.literal_eval(legal_quit_chars)

        return legal_quit_chars

    # --------------------------------------------------------------------------
    def format_default(self, default):
        """
        Formats the default before displaying it. This is intended to be
        optionally overridden in subclasses.

        :param default: The default value to be formatted.

        :return: The formatted default.
        """

        return default

    # --------------------------------------------------------------------------
    def format_response(self, response):

        """
        Formats the user's response, based on type. This is intended to be
        overridden in subclasses.

        :param response: The user's input.

        :return: The formatted input. In this parent class just return the
                 response unchanged.
        """

        return response

    # --------------------------------------------------------------------------
    def validate_response(self, response):
        """
        Validates the user's response, based on type. This is intended to be
        overridden in subclasses.

        :param response: The user's input.

        :return: True if it passes validation, False otherwise. In this parent
                 class, just return True.
        """

        return True

    # --------------------------------------------------------------------------
    def echo_back(self, values):
        """
        Displays an confirmation message of what the user entered. This is
        intended to be overridden in subclasses.

        :param values: The value to be echoed back to the user. If value is a
               list type, then it will be displayed a multi-line result.

        :return: Nothing.
        """

        msg = self.resources_obj.get("messages", "you_selected") + " "
        padding = len(msg)
        msg += lib.BRIGHT_BLUE

        if values:
            msg += values[0] + "\n"
            for item in values[1:]:
                msg += " " * padding
                msg += item
                msg += "\n"
            msg += lib.ENDC

        lib.display_message(msg)

    # --------------------------------------------------------------------------
    def get_input(self):
        """
        Displays the instructional text and gets the response from the user.

        :return: Nothing
        """

        response = None

        added_string = self.resources_obj.get("words", "added")

        # Display the title
        lib.display_message(self.title)

        # Display the description
        lib.display_message(self.desc)

        # Display the query
        lib.display_message(self.query)

        # Display the prompt and get the user input
        while response is None:

            # Get the user input
            response = input(self.prompt)

            # Check to see if they chose to quit
            if response.upper() in self.legal_quit_chars:
                sys.exit()

            # If they just hit enter without typing any text, one of two things
            # can happen
            if response == "":

                # If this is a multi-item then stop gathering inputs
                if self.multi_item:
                    continue

                # If this is a single-item then set the response to be the
                # default value
                else:
                    response = self.default_value

            # Format the response
            response = self.format_response(response)

            # Validate the response
            if not self.validate_response(response):
                response = None
                continue

            # If the response is validated, store it in the list
            self.values.append(response)

            # If this is a multi-step, let the user know what was added and then
            # reset response to None so that it will gather another round.
            if self.multi_item:
                lib.display_message(lib.BRIGHT_YELLOW + added_string + ": " +
                                    response + lib.ENDC + "\n")
                response = None

        # Echo back their response
        self.echo_back(self.values)


# ==============================================================================
class DirUI(UI):
    """
    UI to get a single directory.
    """

    def __init__(self, resources_obj, section, step_no, total_steps,
                 default_value=None):
        """
        Init.
        """

        super(DirUI, self).__init__(resources_obj, section, step_no,
                                    total_steps, default_value)

    # --------------------------------------------------------------------------
    def format_response(self, response):
        """
        Formats the user's response, based on type.

        :param response: The user's input.

        :return: The formatted input.
        """
        # Reformat the response into a full, absolute path
        output = response.strip()
        output = output.replace("//", "/")
        output = os.path.abspath(os.path.expanduser(output))

        return output

    # --------------------------------------------------------------------------
    def validate_response(self, response):
        """
        Validates the user's response, based on type.

        :param response: The user's input.

        :return: True if it passes validation, False otherwise.
        """

        does_not_exist = self.resources_obj.get("errors", "does_not_exist")
        does_not_exist = does_not_exist.format(file_name=response)
        does_not_exist = lib.format_string(does_not_exist)
        dir_is_file = self.resources_obj.get("errors", "dir_is_file")
        dir_is_file = dir_is_file.format(file_name=response)
        dir_is_file = lib.format_string(dir_is_file)

        # Check to see if the path exists
        if not os.path.exists(response):
            lib.display_error(does_not_exist)
            return False

        if not os.path.isdir(response):
            lib.display_error(dir_is_file)
            return False

        return True

    # --------------------------------------------------------------------------
    def echo_back(self, values):
        """
        Displays an confirmation message of what the user entered.

        :param values: The value to be echoed back to the user. If value is a
               list type, then it will be displayed a multi-line result.

        :return: Nothing.
        """

        msg = self.resources_obj.get(self.section, "echo_back") + " --> "
        padding = len(msg)
        msg += lib.BRIGHT_BLUE

        if values:
            msg += values[0] + "\n"
            for item in values[1:]:
                msg += " " * padding
                msg += item
                msg += "\n"
            msg += lib.ENDC

        lib.display_message(self.wrap_text(msg, 90))


# ==============================================================================
class MultiDirUI(DirUI):
    """
    UI to get a multiple directories.
    """

    def __init__(self, resources_obj, section, step_no, total_steps,
                 default_value=None):
        """
        Init.
        """

        super(MultiDirUI, self).__init__(resources_obj, section, step_no,
                                         total_steps, default_value)

        self.multi_item = True


# ==============================================================================
class FileInUI(UI):
    """
    UI to get a single file in.
    """

    def __init__(self, resources_obj, section, step_no, total_steps,
                 default_value=None):
        """
        Init.
        """

        super(FileInUI, self).__init__(resources_obj, section, step_no,
                                       total_steps, default_value)

    # --------------------------------------------------------------------------
    def format_response(self, response):
        """
        Formats the user's response, based on type.

        :param response: The user's input.

        :return: The formatted input.
        """

        # Reformat the response into a full, absolute path
        output = response.strip()
        if output == "":
            return output
        output = output.replace("//", "/")
        output = os.path.abspath(os.path.expanduser(output))

        return output

    # --------------------------------------------------------------------------
    def validate_response(self, response):
        """
        Validates the user's response, based on type.

        :param response: The user's input.

        :return: True if it passes validation, False otherwise.
        """

        error_prefix = self.resources_obj.get("errors", "prefix")
        file_does_not_exist = self.resources_obj.get("errors",
                                                     "file_does_not_exist")
        file_is_dir = self.resources_obj.get("errors", "file_is_dir")
        not_sub_dir = self.resources_obj.get("errors", "not_sub_dir")

        # Check to see if the path exists
        if not os.path.exists(response) or response == "":
            error_msg = "\n" + error_prefix + " " + file_does_not_exist + "\n"
            lib.display_error(error_msg)
            return False

        # # If parent_dir is not None then the user expects this path to be a
        # # child of another, specified dir. Check that this is the case.
        # if self.parent_dir is not None
        #     if not response.startswith(self.parent_dir):
        #     error_msg = ["\n", error_prefix, response, not_sub_dir, "\n"]
        #     lib.display_error(error_msg)
        #     return False

        if os.path.isdir(response):
            error_msg = "\n" + error_prefix + " " + file_is_dir + "\n"
            lib.display_error(error_msg)
            return False

        return True


# ==============================================================================
class MultiFileInUI(FileInUI):
    """
    UI to get a single file in.
    """

    def __init__(self, resources_obj, section, step_no, total_steps,
                 default_value=None):
        """
        Init.
        """

        super(MultiFileInUI, self).__init__(resources_obj, section, step_no,
                                            total_steps, default_value)

        self.multi_item = True


# ==============================================================================
class FileOutUI(UI):
    """
    UI to get a file out.
    """

    def __init__(self, resources_obj, section, step_no, total_steps,
                 default_value=None):
        """
        Init.
        """

        super(FileOutUI, self).__init__(resources_obj, section, step_no,
                                        total_steps, default_value)

    # --------------------------------------------------------------------------
    def format_response(self, response):
        """
        Formats the user's response, based on type.

        :param response: The user's input.

        :return: The formatted input.
        """

        # Call the super class method
        response = super(FileOutUI, self).format_response(response)

        # Reformat the response into a full, absolute path
        output = response.strip()
        output = output.replace("\\", "")
        output = os.path.abspath(os.path.expanduser(output))

        return output

    # --------------------------------------------------------------------------
    def validate_response(self, response):
        """
        Validates the user's response, based on type.

        :param response: The user's input.

        :return: True if it passes validation, False otherwise.
        """

        error_prefix = self.resources_obj.get("errors", "prefix")
        dir_does_not_exist = self.resources_obj.get("errors",
                                                    "dir_does_not_exist")
        confirm_overwrite = self.resources_obj.get("messages",
                                                   "confirm_overwrite")
        legal_affirmatives = self.resources_obj.get("legal_chars",
                                                    "legal_affirmatives")

        # Check to see if we are going to overwrite
        if os.path.exists(response):
            overwrite = input(confirm_overwrite)
            if overwrite.upper() in legal_affirmatives and overwrite != "":
                return True
            else:
                if overwrite.upper() in self.legal_quit_chars:
                    sys.exit(0)
                else:
                    return False

        # Make sure the parent path exists
        base_name = os.path.split(response)[0]
        if not os.path.exists(os.path.join(base_name, os.pardir)):
            msg = "\n" + error_prefix + response + dir_does_not_exist + "\n"
            lib.display_error(msg)
            return False

        return True


# ==============================================================================
class MultiFileOutUI(FileOutUI):
    """
    UI to get a file out.
    """

    def __init__(self, resources_obj, section, step_no, total_steps,
                 default_value=None):
        """
        Init.
        """

        super(MultiFileOutUI, self).__init__(resources_obj, section, step_no,
                                             total_steps, default_value)

        self.multi_item = True


# ==============================================================================
class TrueFalseUI(UI):
    """
    Get a True or False from the user.
    """

    def __init__(self, resources_obj, section, step_no, total_steps,
                 default_value=True):
        """
        Init.
        """

        super(TrueFalseUI, self).__init__(resources_obj, section, step_no,
                                          total_steps, default_value)

    # --------------------------------------------------------------------------
    def format_default(self, default):
        """
        Override the base class.

        :param default: The default value to be formatted. Should be a boolean.

        :return: The boolean formatted into either a "yes" or "no" (adjusted
                 for the local language).
        """

        # Convert the default value into a string.
        if default:
            return self.resources_obj.get("words", "yes")
        else:
            return self.resources_obj.get("words", "no")

    # --------------------------------------------------------------------------
    def format_response(self, response):
        """
        Formats the user's response into True or False if it isn't already.

        :param response: The user's input.

        :return: The formatted input as either a True or a False.
        """

        # Process booleans
        if type(response) == bool:
            return response

        # Process strings
        legal_affirmatives = self.resources_obj.get("legal_chars",
                                                    "legal_affirmatives")
        legal_affirmatives = ast.literal_eval(legal_affirmatives)
        if response.upper() in legal_affirmatives:
            return True
        return False

    # --------------------------------------------------------------------------
    def validate_response(self, response):
        """
        Validates the user's response, based on type. This is intended to be
        overridden in subclasses.

        :param response: The user's input.

        :return: True if it passes validation, False otherwise. In this parent
                 class, just return True.
        """

        if response in [True, False]:
            return True
        return False

    # --------------------------------------------------------------------------
    def echo_back(self, value):
        """
        Displays an confirmation message of what the user entered.

        :param value: The boolean value to be echoed back to the user.

        :return: Nothing.
        """

        value = value[0]

        msg = lib.BRIGHT_BLUE
        if value:
            msg += self.resources_obj.get(self.section, "echo_back_true")
        else:
            msg += self.resources_obj.get(self.section, "echo_back_false")
        msg += lib.ENDC

        lib.display_message(self.wrap_text(msg, 90))


# ==============================================================================
class FileType(UI):
    """
    Get a file type from the user.
    """

    def __init__(self, resources_obj, section, step_no, total_steps,
                 default_value=None):
        """
        Init.
        """

        super(FileType, self).__init__(resources_obj, section, step_no,
                                       total_steps, default_value)

    # --------------------------------------------------------------------------
    def validate_response(self, response):
        """
        Validates the user's response, based on type. This is intended to be
        overridden in subclasses.

        :param response: The user's input.

        :return: True if it passes validation, False otherwise. In this parent
                 class, just return True.
        """

        # Call the super class method
        response = super(FileType, self).validate_response(response)

        legal_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ."
        for char in str(response):
            if char not in legal_chars:
                return False

        return True


# ==============================================================================
class MultipleFileTypes(FileType):
    """
    Get a multiple file types from the user.
    """

    def __init__(self, resources_obj, section, step_no, total_steps,
                 default_value=None):
        """
        Init.
        """

        super(MultipleFileTypes, self).__init__(resources_obj, section,
                                                step_no, total_steps,
                                                default_value)

        self.multi_item = True


# ==============================================================================
class IntUI(UI):
    """
    UI to get an integer.
    """

    def __init__(self, resources_obj, section, step_no, total_steps,
                 default_value=None):
        """
        Init.
        """

        super(IntUI, self).__init__(resources_obj, section, step_no,
                                    total_steps, default_value)

    # --------------------------------------------------------------------------
    def format_response(self, response):
        """
        Formats the user's response, based on type.

        :param response: The user's input.

        :return: The formatted input.
        """

        try:
            return int(response)
        except ValueError:
            return None

    # --------------------------------------------------------------------------
    def validate_response(self, response):
        """
        Validates the user's response, based on type.

        :param response: The user's input.

        :return: True if it passes validation, False otherwise.
        """

        try:
            return int(response) == int(response)
        except ValueError:
            return False

    # --------------------------------------------------------------------------
    def echo_back(self, values):
        """
        Displays an confirmation message of what the user entered.

        :param values: The value to be echoed back to the user. If value is a
               list type, then it will be displayed a multi-line result.

        :return: Nothing.
        """

        msg = self.resources_obj.get(self.section, "echo_back") + " --> "
        padding = len(msg)
        msg += lib.BRIGHT_BLUE

        if values:
            msg += values[0] + "\n"
            for item in values[1:]:
                msg += " " * padding
                msg += item
                msg += "\n"
            msg += lib.ENDC

        lib.display_message(self.wrap_text(msg, 90))
