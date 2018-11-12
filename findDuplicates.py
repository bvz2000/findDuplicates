#! /usr/bin/env python3

import configparser
import hashlib
import os
import os.path
import sys
import time
from optparse import OptionParser

import lib
from scanDirectory import ScanDirectory
from settings import Settings
from ui import TrueFalseUI


OPTIONS_SETTINGS = {
    "interactive":
        ("-i", "--interactive", "store_true", False, None),
    "language":
        ("", "--language", "store", "english", "string"),
    "use_preset":
        ("-P", "--use-preset", "store_true", False, None),
    "save_preset":
        ("-w", "--save-preset", "store_true", False, None),
    "compare_two_files":
        ("-c", "--compare-two", "store_true", False, None),
    "source_dir":
        ("-s", "--source-dir", "store", os.path.expanduser("~"), "string"),
    "skip_source_sub_dirs":
        ("-k", "--skip-source", "store_false", False, None),
    "source_dirs_to_skip":
        ("", "--source-dirs-to-skip", "store", None, "string"),
    "target_dir":
        ("-t", "--target-dir", "store", os.path.expanduser("~"), "string"),
    "skip_target_sub_dirs":
        ("-K", "--skip-target", "store_false", False, None),
    "target_dirs_to_skip":
        ("", "--target-dirs-to-skip", "store", None, "string"),
    "log_file":
        ("-g", "--log-file", "store",
         os.path.expanduser("~/compareFiles.duplicates"), "string"),
    "overwrite_log":
        ("-o", "--overwrite-log", "store_false", True, None),
    "limit_to_patterns":
        ("-p", "--limit-to-patterns", "store_false", False, None),
    "pattern_list":
        ("", "--pattern-list", "store", None, "string"),
    "skip_zero_len":
        ("-e", "--ignore-zero-length", "store_true", True, None),
    "skip_hidden":
        ("-H", "--ignore-hidden", "store_true", False, None),
    "skip_dsstore":
        ("-d", "--ignore-dsstore", "store_true", True, None),
    "skip_links":
        ("-l", "--ignore-links", "store_true", True, None),
    "follow_links":
        ("-f", "--follow-links", "store_false", False, None),
    "many_dupes":
        ("-m", "--many-dupes-expected", "store_false", False, None),
    "do_debug":
        ("", "--do-debug", "store_true", False, None),
    "debug_limit":
        ("", "--debug-limit", "store", 1000, "int"),
}


# ------------------------------------------------------------------------------
def read_resources():
    """
    Opens up the appropriate resource file and returns a ConfigParser object
    with the contents of this file.

    :return: A ConfigParser object.
    """

    # Start off with a tiny hack to see if they have included a language via the
    # -l or --language options. This needs to be done before we actually load
    # the options using optparse because that operation depends on the resource
    # file.

    language = "english"

    # Get the language (if supplied on the command line)
    if "--language" in sys.argv:
        index = sys.argv.index("--language")
        try:
            language = str.lower(sys.argv[index + 1])
        except IndexError:
            # just stick with english since they supplied the flag but not the
            # actual language
            pass

    # Build a path to the correct language resources file
    resources_path = os.path.realpath(sys.path[0])
    resources_file = os.path.join(resources_path, "resources",
                                  "resources_" + language + ".ini")

    # If this file does not exist, warn the user and bail
    if not os.path.exists(resources_file):
        msg = "Cannot locate resource file:"
        lib.display_error(msg, resources_file)
        sys.exit(1)

    # Open and populate the resources object
    resource_obj = configparser.ConfigParser(allow_no_value=True)
    resource_obj.read(resources_file)

    return resource_obj


# ------------------------------------------------------------------------------
def overwrite_file_ui():
    """
    Checks to see if the user wants to overwrite the file.

    :return: True if the file should be overwritten, False otherwise.
    """

    overwrite_ui = TrueFalseUI(resources_obj, "overwrite_file", 1, 1, False)
    overwrite_ui.get_input()

    return overwrite_ui.values[0]


# ------------------------------------------------------------------------------
def create_error_log(file_name):
    """
    Create the error log file.

    :param file_name: The name of the error log file.

    :return: The error log file object.
    """

    creating_log = resources_obj.get("messages", "creating_err_log")
    cannot_create_log = resources_obj.get("errors", "cannot_create_log")
    source = resources_obj.get("words", "source")
    target = resources_obj.get("words", "target")

    lib.display_message(creating_log.format(log_file=file_name,
                                            time_now=time.strftime("%I:%M:%S")))
    lib.display_message("-" * 80)

    try:
        errors_file = open(file_name + ".errors", "w")
    except (OSError, IOError):
        lib.display_error(cannot_create_log.format(log_file=file_name))
        sys.exit(1)

    errors_file.write(resources_obj.get("log_errors", "description"))

    errors_file.write(source + "\t" + options.sourceDir + "\n")
    errors_file.write(target + "\t" + options.targetDir + "\n")

    return errors_file


# ------------------------------------------------------------------------------
def create_duplicates_log(file_name):
    """
    Create the log file.

    :param file_name: The name of the log file.

    :return: The duplicates log.
    """

    creating_log = resources_obj.get("messages", "creating_dup_log")
    error = resources_obj.get("errors", "cannot_create_log")

    lib.display_message(creating_log.format(log_file=file_name,
                                            time_now=time.strftime("%I:%M:%S")))
    lib.display_message("-" * 80)

    try:
        results_file = open(file_name, "w")
    except (OSError, IOError):
        lib.display_error(error)
        sys.exit(1)

    results_file.write(resources_obj.get("headers", "log_file"))

    return results_file


# ------------------------------------------------------------------------------
def reformat_undelimited_items(items):
    """
    Given a list of tuples, extracts the first element of each into a list.

    :param items: A list of two item tuples.

    :return: A list where only the first item of each tuple is present.
    """

    output = list()
    for item in items:
        output.append(item[0])
    return output


# ------------------------------------------------------------------------------
def define_options():
    """
    Sets up the option parser.

    :return: A tuple where the first item is a fully populated option parser
             object, and the second is a list of the remaining arguments.
    """

    # Add in any missing items to this resources object
    for item in [setting[0] for setting in OPTIONS_SETTINGS]:

        # Create a default title if it is missing
        try:
            resources_obj.get(item, "title")
        except configparser.NoSectionError:
            resources_obj.add_section(item)
            resources_obj.set(item, "title", "No title available")
        except configparser.NoOptionError:
            resources_obj.set(item, "title", "No title available")

        # Do the same for the short description
        try:
            resources_obj.get(item, "short_desc")
        except configparser.NoSectionError:
            resources_obj.add_section(item)
            resources_obj.set(item, "short_desc", "No description available")
        except configparser.NoOptionError:
            resources_obj.set(item, "short_desc", "No description available")

        # Do the same for the full description
        try:
            resources_obj.get(item, "description")
        except configparser.NoSectionError:
            resources_obj.add_section(item)
            resources_obj.set(item, "short_desc", "No description available")
        except configparser.NoOptionError:
            resources_obj.set(item, "short_desc", "No description available")

        # set up the parser
        usage = reformat_undelimited_items(resources_obj.items("usage"))
        usage = "\n".join(usage)
        parser = OptionParser(usage=usage)

        # Set up each option
        for setting in OPTIONS_SETTINGS.keys():
            parser.add_option(
                OPTIONS_SETTINGS[setting][0],
                OPTIONS_SETTINGS[setting][1],
                action=OPTIONS_SETTINGS[setting][2],
                type=OPTIONS_SETTINGS[setting][4],
                dest=setting,
                metavar=resources_obj.get(setting, "short_desc"),
                default=OPTIONS_SETTINGS[setting][3],
                help=resources_obj.get(setting, "description_cl"),
                )

        # actually parse the command my_line
        opts, args = parser.parse_args()

        return opts, args


# ------------------------------------------------------------------------------
def load_defaults_from_preset(preset_file):
    """
    Loads presets from a file.

    :return: A dictionary of defaults.
    """

    # If the file does not exist
    if not os.path.exists(preset_file):
        lib.display_error(resources_obj.get("errors",
                                            "file_does_not_exist"))
        sys.exit(1)

    # If the file is a directory
    if os.path.isdir(preset_file):
        lib.display_error(resources_obj.get("errors",
                                            "file_is_dir"))
        sys.exit(1)

    # Create a new config parser object
    preset_obj = configparser.ConfigParser()
    preset_obj.read(preset_file)

    output = dict()
    preset_items = preset_obj.items("presets")
    for item in preset_items:
        output[item[0]] = item[1]
    return output


# ------------------------------------------------------------------------------
def load_defaults_from_options():
    """
    Returns a dictionary from the options passed via the opt parse module.

    :return: A dictionary of defaults.
    """

    output = dict()

    output["source_dir"] = options.source_dir
    output["skip_source_sub_dirs"] = options.skip_source_sub_dirs
    output["source_dirs_to_skip"] = options.source_dirs_to_skip
    output["target_dir"] = options.target_dir
    output["skip_target_sub_dirs"] = options.skip_target_sub_dirs
    output["target_dirs_to_skip"] = options.target_dirs_to_skip
    output["log_file"] = options.log_file
    output["overwrite_log"] = options.overwrite_log
    output["limit_to_patterns"] = options.limit_to_patterns
    output["pattern_list"] = options.pattern_list
    output["skip_zero_len"] = options.skip_zero_len
    output["skip_hidden"] = options.skip_hidden
    output["skip_dsstore"] = options.skip_dsstore
    output["skip_links"] = options.skip_links
    output["follow_links"] = options.follow_links
    output["many_dupes"] = options.many_dupes
    output["do_debug"] = options.do_debug
    output["debug_limit"] = options.debug_limit

    return output
#
#
# # ------------------------------------------------------------------------------
# def build_source_list():
#     """
#     Reads in all the files and builds a list of the source directory.
#
#     :return: A list of the source files.
#     """
#
#     # Build the resource strings
#     building_src_list = resources_obj.get("messages", "building_src_list")
#     scanned_so_far = resources_obj.get("messages", "scanned_so_far")
#     unable_to_get_size = resources_obj.get("errors", "unable_to_get_size")
#     added = resources_obj.get("words", "added")
#     files = resources_obj.get("words", "files")
#     scanned = resources_obj.get("words", "scanned")
#     of = resources_obj.get("words", "of")
#     at = resources_obj.get("words", "at")
#
#     # initialize counters and list
#     checked_counter = 0
#     actual_counter = 0
#     output = list()
#
#     # Print status
#     time_now = time.strftime("%I:%M:%S")
#     lib.display_message("\n\n" + building_src_list + " " + time_now + ".")
#     lib.display_message("-" * 80)
#
#     # Step through each of the files in the source
#     for root, sub_folders, files in os.walk(settings.source_dir):
#
#         for file_name in files:
#
#             # Increment the number of files checked
#             checked_counter += 1
#
#             # Update the status every 1000 files
#             if checked_counter % 1000 == 0:
#
#                 # Print the status, flush the buffer, and rest to the beginning
#                 message = str(checked_counter) + scanned_so_far
#                 sys.stdout.write(message)
#                 sys.stdout.flush()
#                 sys.stdout.write("\b" * (len(message)))
#
#             # Skip any files that are hidden if so directed.
#             if settings.skip_hidden and file_name[0] == ".":
#                 continue
#
#             # Skip .DSStore files if so directed.
#             if settings.skip_dsstore and file_name == ".DS_Store":
#                 continue
#
#             # Skip files if they are not specific file types if so directed.
#             ext = os.path.splitext(file_name)[1].upper().replace(".", "")
#             if settings.limit_to_patterns and ext not in settings.pattern_list:
#                 continue
#
#             # Get the path and file size of the current file.
#             file_path = os.path.join(root, file_name)
#             try:
#                 file_size = os.path.getsize(file_path)
#             except Exception:
#                 file_size = -1
#                 errors_log.write(unable_to_get_size + " " + file_path + "\n")
#
#             # If we are to skip zero files and the file size is less than 0,
#             # then continue
#             if settings.skip_zero_len and file_size < 1:
#                 continue
#
#             # Increment the counter of added files
#             actual_counter += 1
#
#             # Append the file
#             output.append([file_name, file_path, file_size])
#
#     source_file_count = actual_counter
#     msg = added + " " + str(actual_counter) + " " + files + " " + of + " "
#     msg += str(checked_counter) + " " + scanned + " " + at + " "
#     msg += time.strftime("%I:%M:%S") + "."
#     lib.display_message(msg)
#
#     return output
#
#
# # ------------------------------------------------------------------------------
# def build_target_dict():
#     """
#     Reads all of the files in the target directory and builds a list
#
#     :return: A dictionary of the files in the target directory.
#     """
#
#     # Build the resource strings
#     building_tgt_list = resources_obj.get("messages", "building_tgt_list")
#     scanned_so_far = resources_obj.get("messages", "scanned_so_far")
#     unable_to_get_size = resources_obj.get("errors", "unable_to_get_size")
#     added = resources_obj.get("words", "added")
#     files = resources_obj.get("words", "files")
#     scanned = resources_obj.get("words", "scanned")
#     of = resources_obj.get("words", "of")
#     at = resources_obj.get("words", "at")
#
#     # Initialize counters and dict
#     checked_counter = 0
#     actual_counter = 0
#     target_dirs = dict()
#
#     # Print status
#     time_now = time.strftime("%I:%M:%S")
#     lib.display_message("\n\n" + building_tgt_list + " " + time_now + ".")
#     lib.display_message("-" * 80)
#
#     # Step through each of the files in the target
#     for root, sub_folders, files in os.walk(settings.target_dir):
#
#         for file_name in files:
#
#             # Increment the number of files checked
#             checked_counter += 1
#
#             # Update the status every 1000 files
#             if checked_counter % 1000 == 0:
#
#                 # Print the status, flush the buffer, and rest to the beginning
#                 message = str(checked_counter) + scanned_so_far
#                 sys.stdout.write(message)
#                 sys.stdout.flush()
#                 sys.stdout.write("\b" * (len(message)))
#
#             # Skip any files that are hidden if so directed.
#             if settings.skip_hidden and file_name[0] == ".":
#                 continue
#
#             # Skip .DSStore files if so directed.
#             if settings.skip_dsstore and file_name == ".DS_Store":
#                 continue
#
#             # Skip files if they are not specific file types if so directed.
#             ext = os.path.splitext(file_name)[1].upper().replace(".", "")
#             if settings.limit_to_patterns and ext not in settings.pattern_list:
#                 continue
#
#             # Get the path and file size of the current file.
#             file_path = os.path.join(root, file_name)
#             try:
#                 file_size = os.path.getsize(file_path)
#             except Exception:
#                 file_size = -1
#                 errors_log.write(unable_to_get_size + " " + file_path + "\n")
#
#             # If we are to skip zero files and the file size is less than 0,
#             # then continue
#             if settings.skip_zero_len and file_size < 1:
#                 continue
#
#             # Increment the counter of added files and append this file
#             actual_counter += 1
#
#             # Is this the first time we see a file of this size?
#             if not(target_dirs.has_key(file_size)):
#                 # if so, create a new list of the full path and checksum value
#                 target_dirs[file_size] = [[file_path, file_size]]
#
#             # Otherwise we have seen this file size before, so append the full
#             # path and checksum to the existing size item in the dictionary
#             else:
#                 temp_data = target_dirs[file_size]
#                 temp_data.append([file_path, file_size])
#                 target_dirs[file_size] = temp_data
#
#     targetFileCount = actual_counter
#     msg = added + " " + str(actual_counter) + " " + files + " " + of + " "
#     msg += str(checked_counter) + " " + scanned + " " + at + " "
#     msg += time.strftime("%I:%M:%S") + "."
#     lib.display_message(msg)
#
#     return target_dirs


# ------------------------------------------------------------------------------
def md5_partial_match(file_path_a, file_path_b, num_bytes=1024):
    """
    Takes two files and compares the hash of the first num_bytes of these files
    to see if they are the same. This is primarily used to do a quick compare of
    two files. If these bytes match, it still does not necessarily mean that the
    files are identical, just that they have a decent probability of being the
    same.

    :param file_path_a: The first file to compare
    :param file_path_b: The second file to compare
    :param num_bytes: The number of bytes to hash. Defaults to 1K (1024)

    :return: True if the first N bytes of the two files match (via a hash)
    """

    # file A first 'bytes' checksum
    f = open(file_path_a, 'rb')
    chunk = f.read(num_bytes)
    f.close()
    md5 = hashlib.md5()
    md5.update(chunk)
    checksum_a = md5.hexdigest()

    # file B first 'bytes' checksum
    f = open(file_path_b, 'rb')
    chunk = f.read(num_bytes)
    f.close()
    md5 = hashlib.md5()
    md5.update(chunk)
    checksum_b = md5.hexdigest()

    # return whether they match
    return checksum_a == checksum_b


# ------------------------------------------------------------------------------
def md5_full_match(file_path_a, file_path_b):
    """
    Performs a full md5 checksum compare between two files. If they files match,
    the md5 hash is returned. If they do not match, None is returned.

    :param file_path_a: The first file to compare
    :param file_path_b: The second file to compare

    :return: The checksum of the files if they match, False otherwise.
    """

    # file A full checksum
    md5 = hashlib.md5()
    with open(file_path_a, 'rb') as f:
        for chunk in iter(lambda: f.read(128 * md5.block_size), b''):
            md5.update(chunk)
    checksum_a = md5.hexdigest()

    # file B full checksum
    md5 = hashlib.md5()
    with open(file_path_b, 'rb') as f:
        for chunk in iter(lambda: f.read(128 * md5.block_size), b''):
            md5.update(chunk)
    checksum_b = md5.hexdigest()

    # return their shared checksum if they match, False otherwise.
    if checksum_a == checksum_b:
        return checksum_b
    else:
        return False


# ------------------------------------------------------------------------------
def do_compare(source, target):
    """
    Actually run the compare.

    :param source: The source scan object. The target scan object.

    :return: Nothing.
    """

    is_symlink = False
    #
    # # preset some counters and flags
    # counter = 0
    # old_percent = 0
    # num_duplicates = 0
    # num_total_duplicates = 0
    # num_unique = 0
    # num_symlinks = 0
    # num_errors = 0
    #
    # # make a list that will store each matched file so that it is not visited
    # # twice. i.e. if we find that A=B, we do not later want to record that B=A
    # # this is really only an issue if the source and target directory are the
    # # same.
    # visited_files = list()
    #
    # # test each source file
    # for source_file_path in source.items.keys():
    #
    #     # print the progress bar
    #     counter += 1
    #     old_percent = lib.display_progress(counter, len(source.items),
    #                                        old_percent, 50, "#", "-")
    #
    #     source_file_name = source.items[source_file_path][0]
    #     source_file_size = source.items[source_file_path][1]
    #
    #     # do not test files that have already been identified as matches for
    #     # other files (only happens if both source and target dirs are the same)
    #     if source.scan_dir == target.scan_dir:
    #         if source_file_path in visited_files:
    #             continue
    #
    #     # preset the log file lists and the unique flag
    #     duplicate_list = list()
    #     error_list = list()
    #     # unique = False
    #
    #     # check to see if any files in the target dir have the same size as the
    #     # file we are testing.
    #     try:
    #         possible_matches_list = target.items[source_file_size]
    #         # matched_size = True
    #     except KeyError:
    #         possible_matches_list = list()
    #         # matched_size = False
    #
    #     # Check each possible match
    #     for possibleMatch in possible_matches_list:
    #
    #         match_file_path = possibleMatch[0]
    #         match_file_size = possibleMatch[1]
    #
    #         # Don't match against yourself
    #         if source_file_path == match_file_path:
    #             continue
    #
    #         # Since the file sizes match, compare the two files
    #         match = compare_two_files(source_file_path, match_file_path,
    #                                   settings.many_dupes)
    #
    #         # If a match, store this file in the duplicate_list
    #         if match:
    #             duplicate_list.append([match_file_path,
    #                                   str(match_file_size),
    #                                   str(is_symlink)])
    #         #
    #         # # if nothing matches, this is a unique file
    #         # if not(match) and not(matched_size):# and not(nameMatch):
    #         #     unique = True
    #
    #         # If we are listing A=B, don't also later list B=A if we already
    #         # found a match.
    #         if options.sourceDir == options.targetDir and match:
    #             visited_files.append(match_file_path)
    #
    #
    #
    #     # update the counts
    #     if duplicate_list:
    #         num_duplicates += 1
    #         num_total_duplicates = num_total_duplicates + len(duplicate_list)
    #     # if unique or not possible_matches_list: num_unique = num_unique + 1
    #     # if error_list: num_errors = num_errors + 1
    #
    #
    #
    #     # write the resutls to the log file (regardless of match outcome)
    #     resultsLog.write("RESULT\t")
    #     resultsLog.write("\t")
    #     if len(duplicate_list) > 0:
    #         resultsLog.write("DUPLICATE\t")
    #     else:
    #         resultsLog.write("UNIQUE\t")
    #     # sourceFullPath = os.path.join(options.sourceDir, source_file_name)
    #     resultsLog.write(sourceFilePath + "\t")
    #     # resultsLog.write(sourceFilePath.replace(options.sourceDir,"").lstrip("/") + "\t")
    #     resultsLog.write(str(source_file_size) + "\t")
    #     resultsLog.write(str(is_symlink) + "\t")
    #     for my_item in duplicate_list:
    #         resultsLog.write(my_item[0] + "\t")
    #         resultsLog.write(my_item[1] + "\t")
    #         resultsLog.write(my_item[2] + "\t")
    #     resultsLog.write("\n")
    #
    #
    #
    #     # write the errors to the errors log file (if there are any)
    #     if error_list:
    #         errorsLog.write("Error comparing\t")
    #         errorsLog.write(source_file_name + "\t")
    #         errorsLog.write(sourceFilePath.replace(options.sourceDir,"").lstrip("/") + "\t")
    #         errorsLog.write(str(source_file_size) + "\t")
    #         for my_item in error_list:
    #             errorsLog.write(my_item[0] + "\t")
    #             errorsLog.write(my_item[1] + "\t")
    #             errorsLog.write(my_item[2] + "\t")
    #         errorsLog.write("\n")


# ------------------------------------------------------------------------------
def compare_two_files(file_a, file_b, single_pass=False):
    """
    Compares two files passed on the command line. Displays the results directly
    on stdOut.

    :param file_a: The first file to be compared.
    :param file_b: The second file to be compared.
    :param single_pass: If True, then the two files will be compared using a
           full checksum of each file. If False, then only the first 1K bytes
           of each file will be checksummed. Only if these bytes match will a
           second, full checksum of both files be done.

    :return: True the files are identical, False otherwise.
    """

    # Some basic error checking.
    if not os.path.exists(file_a):
        msg = resources_obj.get("errors", "file_does_not_exist")
        lib.display_error(msg.format(file_name=file_a))
        sys.exit(1)

    if os.path.isdir(file_a):
        msg = resources_obj.get("errors", "file_is_dir")
        lib.display_error(msg.format(file_name=file_a))
        sys.exit(1)

    if not os.path.exists(file_b):
        msg = resources_obj.get("errors", "file_does_not_exist")
        lib.display_error(msg.format(file_name=file_b))
        sys.exit(1)

    if os.path.isdir(file_b):
        msg = resources_obj.get("errors", "file_is_dir")
        lib.display_error(msg.format(file_name=file_b))
        sys.exit(1)

    # Compare the files.
    if single_pass:
        if md5_full_match(file_a, file_b):
            return True
    else:
        if md5_partial_match(file_a, file_b):
            if md5_full_match(file_a, file_b):
                return True

    return False


# ------------------------------------------------------------------------------
def verify_preset():
    """
    Check to see if a preset is to be saved, and verify overwrite if it already
    exists.

    :return: A preset object if it is verfied, or None otherwise.
    """

    # If they want to write out the settings to a preset file, verify that now
    if options.save_preset:

        # There should be exactly 2 items left in the args
        if len(sys.argv) != 2:
            msg = resources_obj.get("errors", "incorrect_num_args")
            lib.display_error(msg.format(expected=2,
                                         actual=len(sys.argv)))
            sys.exit(1)

        # If the preset already exists, ask to overwrite
        if os.path.exists(sys.argv[1]):

            if not overwrite_file_ui():
                sys.exit(0)

        # Create the preset config parser object
        return configparser.ConfigParser()

    return None


# ------------------------------------------------------------------------------
def verify_compare():
    """
    Check to see if the user wants to compare two files on the command line.

    :return: Nothing.
    """

    # If they want to compare two files to see if they match.
    if options.compare_two_files:

        # There should be exactly 3 items left in the args
        if len(sys.argv) != 3:
            msg = resources_obj.get("errors", "incorrect_num_comp_args")
            lib.display_error(msg)
            sys.exit(1)

        # Compare the two files
        result = compare_two_files(sys.argv[1], sys.argv[2])
        if result:
            msg = resources_obj.get("messages", "files_match")
            lib.display_message(msg)
        else:
            msg = resources_obj.get("messages", "files_do_not_match")
            lib.display_message(msg)

        # Regardless of the result, quit.
        sys.exit(0)


# ==============================================================================
if __name__ == "__main__":

    # Read the resources file.
    resources_obj = read_resources()

    # Set up the option parser and process the command line options.
    options, sys.argv[1:] = define_options()
    #
    # # Initialize the debug object
    # debug_obj = Debug(max_count=options.debug_limit, exit_on_max_count=True,
    #                   write_to_file=True, write_to_stderr=True)

    # If they want to write out the settings to a preset file, verify that now
    preset_out_obj = verify_preset()

    # If they want to compare two files to see if they match.
    verify_compare()

    # If they want to load from a preset, load the preset into the defaults.
    # Otherwise: If we are running interactively, load the actual, built-in
    # defaults. If we are NOT running interactively, load the options passed
    # on the command line.
    if options.use_preset:

        # There should be exactly 2 items left in the args
        if len(sys.argv) != 2:
            lib.display_error(resources_obj.get("errors",
                                                "incorrect_num_args"))
            sys.exit(1)

        defaults = load_defaults_from_preset(sys.argv[1])

    else:

        if options.interactive:

            # There should be exactly 1 item left in the args
            if len(sys.argv) != 1:
                lib.display_error(resources_obj.get("errors",
                                                    "incorrect_num_args"))
                sys.exit(1)

            defaults = dict()
            for key in OPTIONS_SETTINGS:
                defaults[key] = OPTIONS_SETTINGS[key][3]
        else:
            defaults = load_defaults_from_options()

    # Create a new settings object
    settings = Settings(resources_obj, defaults)

    # If options interactive is true, fill the settings object interactively.
    if options.interactive:
        settings.run_wizard()

    # Create the log files
    results_log, errors_log = create_duplicates_log(settings.log_file)

    # Build the source list
    source_obj = ScanDirectory(
        settings.source_dir,
        settings.skip_hidden,
        settings.skip_dsstore,
        settings.limit_to_patterns,
        settings.pattern_list,
        settings.skip_zero_len,
        resources_obj,
        True,
    )

    # Build the target list
    target_obj = ScanDirectory(
        settings.target_dir,
        settings.skip_hidden,
        settings.skip_dsstore,
        settings.limit_to_patterns,
        settings.pattern_list,
        settings.skip_zero_len,
        resources_obj,
        True,
    )

    # Display a status to the user
    status_msg = resources_obj.get("messages", "start_comparing")
    lib.display_message(status_msg).format(
        source_count=source_obj.get_count(),
        source_dir=source_obj.scan_dir,
        target_count=target_obj.get_count(),
        target_dir=target_obj.scan_dir,
        start_time=time.strftime("%I:%M:%S"),
    )
    lib.display_message("-" * 80)

    # Do the actual comparison
    #do_compare(source_obj, target_obj)



    #
    # # Compare each of the Source Dir files to the Target Dir files
    # # --------------------------------------------------------------------------------------------------
    # print("\n\nComparing " + str(sourceFileCount) + " source files (in: " + options.sourceDir + ")")
    # print("       to " +  str(targetFileCount) + " target files (in: " + options.targetDir + ")")
    # print("       at " + time.strftime("%I:%M:%S") + ".")
    # print("------------------------------------------------------------------------------------------")
    #
    # # Do the compare
    # do_compare()
    #
    # # clean up
    # # --------------------------------------------------------------------------------------------------
    # resultsLog.close()
    # errorsLog.close()
    #
    # # Print a summary
    # # --------------------------------------------------------------------------------------------------
    # print("\n")
    # print("Operation Completed at " + time.strftime("%I:%M:%S") + ".")
    # print()
    # print("Comparing source directory: " + options.sourceDir)
    # print("       to target directory: " + options.targetDir)
    # print()
    # print(str(sourceFileCount) + " source files were checked against " + str(targetFileCount),
    #       " files in the target dir.")
    # print(str(numDuplicates) + " source files had duplicates in the target dir (",
    #       "these " + str(numDuplicates) + " files have " + str(numTotalDuplicates) + " matching files).")
    # if options.sourceDir == options.targetDir:
    #     print("Listing unique files disabled because source and target directories are the same.")
    # else:
    #     print(str(numUnique) + " source files were unique.")
    # print(str(numSymlinks) + " source files were symbolic links.")
    # print(str(numErrors) + " errors encountered.")
    # print()
    # print("For a detailed list of results, see the file: " + options.logFile)
    # print("For a list of any error encounterd, see the file: " + options.logFile + ".errors")
    #


