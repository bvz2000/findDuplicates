import math
import sys

# define some colors
# ------------------------------------------------------------------------------
BLACK = '\033[30m'
RED = '\033[31m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
BLUE = '\033[34m'
MAGENTA = '\033[35m'
CYAN = '\033[36m'
WHITE = '\033[37m'
BRIGHT_RED = '\033[91m'
BRIGHT_GREEN = '\033[92m'
BRIGHT_YELLOW = '\033[93m'
BRIGHT_BLUE = '\033[94m'
BRIGHT_MAGENTA = '\033[95m'
BRIGHT_CYAN = '\033[96m'
BRIGHT_WHITE = '\033[97m'
ENDC = '\033[0m'


# ------------------------------------------------------------------------------
def display_progress(count, total, old_percent, width=50, completed_char="#",
                     empty_char="."):
    """
    Draws and updates ASCII progress bar on the stdout.

    :param count: The current count for our progress bar.
    :param total: The count at 100%.
    :param old_percent: The previous percent. Necessary to prevent updates if
           the percentage has not changed since the last call.
    :param width: How wide to draw the progress bar in characters. If given an
           odd number, it will be rounded down to the nearest even value.
    :param completed_char: The character to display for a completed chunk.
    :param empty_char: The character to display for an as-yet uncompleted chunk.

    :return: The percent value for the current state.
    """

    # only allow even numbered widths
    if width % 2 != 0:
        width -= 1

    # calculate the percent
    percent = round((count * 1.0) / total * 100, 1)

    # only update the display if the percentage has changed
    if percent == old_percent:
        return percent

    # build the completed and uncompleted portions of the progress bar
    done_str = "{0}".format(completed_char * (int(round(percent / (100 / width), 0))))
    empty_str = "{0}".format(empty_char * (width - (int(round(percent / (100 / width))))))

    # build the X out of Y text
    count_str = " (" + str(count) + " of " + str(total) + ")"

    # build the percent string
    percent_str = "{0}".format(" " * (3 - len(str(int(math.floor(percent)))))) + str(percent) + "%"

    # build the complete string, and insert the percent
    progress_bar_str = "[" + done_str + empty_str + "]"
    progress_left = progress_bar_str[
                    :int((len(progress_bar_str) / 2) - math.floor(len(percent_str) / 2))]
    progress_right = progress_bar_str[
                     int((len(progress_bar_str) / 2) + math.ceil(len(percent_str) / 2)):]
    progress_bar_str = progress_left + percent_str + progress_right

    # append the count string
    progress_bar_str += count_str

    # show it
    sys.stdout.write(progress_bar_str)
    sys.stdout.flush()
    sys.stdout.write("\b" * (len(progress_bar_str)))  # return to start of line

    # return the percent (so that we only update the percentage when it changes)
    return percent


# ------------------------------------------------------------------------------
def display_error(*msgs):
    """
    Given any number of args, converts those args to strings, concatenates them,
    and prints to stdErr.

    :return: Nothing.
    """

    output = ""
    for msg in msgs:
        output += " " + str(msg)
    print(output.lstrip(" "), file=sys.stderr)


# ------------------------------------------------------------------------------
def format_string(msg):
    """
    Given a string (msg) this will format it with colors based on the {{COLOR}}
    tags. (example {{COLOR_RED}}). It will also convert literal \n character
    string into a proper newline.

    :param msg: The string to format.

    :return: The formatted string.
    """

    output = msg.replace(r"\n", "\n")
    output = output.replace("{{", "{")
    output = output.replace("}}", "}")

    output = output.format(
        COLOR_BLACK=BLACK,
        COLOR_RED=RED,
        COLOR_GREEN=GREEN,
        COLOR_YELLOW=YELLOW,
        COLOR_BLUE=BLUE,
        COLOR_MAGENTA=MAGENTA,
        COLOR_CYAN=CYAN,
        COLOR_WHITE=WHITE,
        COLOR_BRIGHT_RED=BRIGHT_RED,
        COLOR_BRIGHT_GREEN=BRIGHT_GREEN,
        COLOR_BRIGHT_YELLOW=BRIGHT_YELLOW,
        COLOR_BRIGHT_BLUE=BRIGHT_BLUE,
        COLOR_BRIGHT_MAGENTA=BRIGHT_MAGENTA,
        COLOR_BRIGHT_CYAN=BRIGHT_CYAN,
        COLOR_BRIGHT_WHITE=BRIGHT_WHITE,
        COLOR_NONE=ENDC,
    )

    return output


# ------------------------------------------------------------------------------
def display_message(*msgs):
    """
    Given any number of args, converts those args to strings, concatenates them,
    and prints to stdOut.

    :return: Nothing.
    """

    print(" ".join([str(item) for item in msgs]))
