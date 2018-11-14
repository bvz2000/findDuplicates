import os
import sys

import lib


class Debug(object):
    """
    A Debug class responsible for printing to stdOut or stdErr.
    """

    # ----------------------------------------------------------------------------------------------
    def __init__(self, do_debug, resources_obj, max_count=1000,
                 exit_on_max_count=False, write_to_file=True, debug_file=None,
                 write_to_stdout=False, write_to_stderr=True):
        """
        Set up the basic settings.

        :param max_count: The maximum number of lines to write to the log before
               no longer writing any more messages. If None, then do not limit
               the number of lines written. Defaults to 1000. This will not
               prevent messages past this number to write to stdOut or stdErr.
        :param exit_on_max_count: Whether to terminate the entire app upon
               reaching the maximum number of lines. Defaults to False.
        :param write_to_file: If true, writes the debug messages to the file
               given by debug_file. Defaults to False.
        :param debug_file: The full path to the debug file where the messages
               will be written to if write_to_file is True. This file will be
               overwritten without warning. If None, the file will be written to
               a file called findDuplicates.debug the user's home directory.
        :param write_to_stdout: Also write log messages to stdOut. Defaults to
               False.
        :param write_to_stderr: Also write log messages to stdErr. Defaults to
               True.
        """

        self.do_debug = do_debug
        self.resources_obj = resources_obj
        self.max_count = max_count
        self.exit_on_max_count = exit_on_max_count
        self.write_to_file = write_to_file
        self.write_to_stdout = write_to_stdout
        self.write_to_stderr = write_to_stderr

        if debug_file is None:
            self.debug_file = os.path.expanduser("~/findDuplicates.debug")
        else:
            self.debug_file = debug_file

        # If they want to write to a file, open it now
        if self.write_to_file and self.do_debug:
            f = open(self.debug_file, "w")
            f.close()

        self.count = 0

    # ----------------------------------------------------------------------------------------------
    def debug(self, *msgs):
        """
        Takes any number of message arguments, converts them to strings,
        concatenates them, and then outputs them to the appropriate locations.

        :param msgs: Any number of arguments that will be written out

        :return: Nothing.
        """

        if not self.do_debug:
            return

        output = ""
        for msg in msgs:
            output += " " + str(msg)
        output.strip(" ")

        if self.write_to_file:
            if self.max_count is None or self.count < self.max_count:
                f = open(self.debug_file, "a")
                f.write(output + "\n")
                f.close()

        if self.write_to_stderr:
            print(output, file=sys.stderr)

        if self.write_to_stdout:
            print(output)

        self.count += 1

        if self.exit_on_max_count:
            if self.max_count is not None:
                if self.count >= self.max_count:
                    lib.display_error(
                        self.resources_obj.get("messages", "debug_count_limit"))
                    sys.exit(0)