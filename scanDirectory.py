import os
import sys
import time

import lib


class ScanDirectory(object):
    """
    A class responsible for scanning and storing the data from a single
    directory.
    """

    # --------------------------------------------------------------------------
    def __init__(self, scan_dir, resources_obj, skip_hidden=True,
                 skip_dsstore=True, limit_to_patterns=False, patterns=None,
                 skip_zero_len=True, type_is_source=True, debug_obj=None):
        """
        Initializes the object.

        :param scan_dir: The directory to scan.
        :param resources_obj: The resources object.
        :param skip_hidden: If True, skip hidden files. Defaults to True.
        :param skip_dsstore: If True, skip .DSStore files. Defaults to True.
        :param limit_to_patterns: If True, limit to files in param: patterns
               list. Defaults to False.
        :param patterns: A list of patterns to limit the scan to. If None, then
               no patterns will be included, and all files will match.
        :param skip_zero_len: If True, skip zero length files. Defaults to True.
        :param type_is_source: If True, then we are scanning a source directory.
               If False, then we are scanning a target directory. Defaults to
               True.
        :param debug_obj: An optional debug object to write out debug info.
               Defaults to None.

        :return: Nothing.
        """

        self.scan_dir = scan_dir
        self.resources_obj = resources_obj
        self.skip_hidden = skip_hidden
        self.skip_dsstore = skip_dsstore
        self.limit_to_patterns = limit_to_patterns
        self.patterns = patterns
        self.skip_zero_len = skip_zero_len
        self.type_is_source = type_is_source
        if type_is_source:
            self.type = resources_obj.get("words", "source").capitalize()
        else:
            self.type = resources_obj.get("words", "target").capitalize()
        self.debug_obj = debug_obj

        self.file_count = 0
        self.items = dict()

    # --------------------------------------------------------------------------
    def scan(self):
        """
        Actually perform the scan.

        :return: Nothing.
        """

        # Build the resource strings
        scanning = self.resources_obj.get("messages", "scanning")
        scanning = scanning.format(type=self.type,
                                   time_now=time.strftime("%I:%M:%S"))
        scanning = lib.format_string(scanning)
        scanned_so_far = self.resources_obj.get("messages", "scanned_so_far")
        scan_summary = self.resources_obj.get("messages", "scan_summary")

        # initialize counters
        checked_counter = 0
        actual_counter = 0

        # Print status
        lib.display_message(scanning)
        lib.display_message("-" * 80)

        # Step through each of the files in the source
        for root, sub_folders, files in os.walk(self.scan_dir):

            for file_name in files:

                # DEBUG
                if self.debug_obj is not None:
                    self.debug_obj.debug("\nscanning: ", file_name)

                # Increment the number of files checked
                checked_counter += 1

                # Update the status every 1000 files
                if checked_counter % 1000 == 0:

                    # Print the status, flush buffer, and move back to the
                    # beginning of the line.
                    message = scanned_so_far.format(count=checked_counter)
                    sys.stdout.write(message)
                    sys.stdout.flush()
                    sys.stdout.write("\b" * (len(message)))

                # Skip any files that are hidden if so directed.
                if self.skip_hidden and file_name[0] == ".":
                    # DEBUG
                    if self.debug_obj is not None:
                        self.debug_obj.debug("file is hidden. skipping.")
                    continue

                # Skip .DSStore files if so directed.
                if self.skip_dsstore and file_name == ".DS_Store":
                    # DEBUG
                    if self.debug_obj is not None:
                        self.debug_obj.debug("file is .DSStore. skipping.")
                    continue

                # Skip files if they are not specific file types if so directed.
                if self.limit_to_patterns and self.patterns is not None:
                    ext = os.path.splitext(file_name)[1]
                    ext = ext.upper().lstrip(".")
                    if self.limit_to_patterns and ext not in self.patterns:
                        # DEBUG
                        if self.debug_obj is not None:
                            self.debug_obj.debug("ext is wrong type. skipping.")
                        continue

                # Get the path and file size of the current file.
                file_path = os.path.join(root, file_name)

                try:
                    file_size = os.path.getsize(file_path)
                except FileNotFoundError:
                    # TODO: Log this in the errors log (Needs to be passed
                    # TODO: to this object first
                    # DEBUG
                    if self.debug_obj is not None:
                        self.debug_obj.debug("Cannot read size. skipping.")
                    continue

                # If we are to skip zero files and the file size is less than 0,
                # then continue
                if self.skip_zero_len and file_size < 1:
                    # DEBUG
                    if self.debug_obj is not None:
                        self.debug_obj.debug("file is zero length. skipping.")
                    continue

                # Increment the counter of added files
                actual_counter += 1

                # If this is a source directory, add to the dict keyed on path,
                if self.type_is_source:

                    # DEBUG
                    if self.debug_obj is not None:
                        self.debug_obj.debug("adding file by name.")

                    self.items[file_path] = [file_name, file_size]

                # otherwise add to the dict, keyed on size.
                else:

                    # If this the first time we see a file of this size, add
                    # it to the dictionary keyed on size.
                    if file_size not in self.items.keys():

                        # DEBUG
                        if self.debug_obj is not None:
                            self.debug_obj.debug("adding file by size.")
                        self.items[file_size] = [[file_path, file_size]]

                    # Otherwise we have seen this file size before, so append
                    # the full path and size to the existing item in the
                    # dictionary
                    else:

                        # DEBUG
                        if self.debug_obj is not None:
                            self.debug_obj.debug("APPENDING file by size.")
                        # self.items[file_size] = [[file_path, file_size]]
                        temp_data = self.items[file_size]
                        temp_data.append([file_path, file_size])
                        self.items[file_size] = temp_data

        self.file_count = actual_counter
        lib.display_message(scan_summary.format(
            count_added=actual_counter,
            count_scanned=checked_counter,
            time_now=time.strftime("%I:%M:%S")
        ))

    # --------------------------------------------------------------------------
    def get_count(self):
        """
        Returns a count of the scanned files.

        :return: An integer containing the number of scanned files.
        """

        return self.file_count
