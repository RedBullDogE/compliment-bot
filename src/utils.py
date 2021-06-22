from dataclasses import dataclass
import re


def check_mark(state: bool):
    """
    Returns emoji with a check mark if state is True, otherwise - a cross
    """
    return "✅" if state else "❌"


def validate_time(time: str):
    """
    Helper function for validating string time. Specified string
    should match the following format: 
        hh:mm
    or
        h:mm
    """
    if not re.match(r"^\d{1,2}:\d{2}$", time):
        return False

    h, m = map(int, time.split(":"))

    if h < 0 or h > 23:
        return False

    if m < 0 or m > 59:
        return False

    return True


@dataclass
class Messages:
    """
    Dataclass with bot messages

    TODO: move all bot messages to this class
    """
    start: str = "From now on I stop making compliments! I hope see you soon ^^"
    day_setup: str = "Day Setup (default: everyday)"
    time_setup: str = ""


msg = Messages()
