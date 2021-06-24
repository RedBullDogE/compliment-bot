import re
from dataclasses import dataclass

from emoji import emojize


def check_mark(state: bool):
    """
    Returns emoji with a check mark if state is True, otherwise - a cross
    """
    return emojize(":check_mark_button:") if state else emojize(":cross_mark:")


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


def format_schedule(days: list, time: str):
    """
    Helper function for transforming day and time data into string.
    """

    weekday_list = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]

    weekdays = ", ".join(
        [
            emojize(f"\n:check_mark_button: {wd}")
            if d
            else emojize(f"\n:cross_mark: {wd}")
            for wd, d in zip(weekday_list, days)
        ]
    )

    if weekdays == "":
        return msg.emtry_list_message2

    return msg.success_message.format(weekdays=weekdays, time=time)


def wrap_class_methods(function_decorator):
    """
    Decorator-function for classes. Wraps all methods of a class
    except those that start with double-score (__)
    """

    def decorator(cls):
        for name, obj in vars(cls).items():
            if callable(obj) and not name.startswith("__"):
                setattr(cls, name, function_decorator(obj))
        return cls

    return decorator


@dataclass(frozen=True)
class Messages:
    """
    Dataclass with bot messages
    """

    # Main Menu button text
    sch_setup: str = emojize("Schedule setup :calendar:")
    sch_list: str = emojize("List :notebook:")
    sch_clear: str = emojize("Clear schedule :broom:")
    help_str: str = emojize("Help :folded_hands:")
    contacts: str = emojize("Contacts :notebook:")

    # Messages
    menu_message: str = "Choose your option from bot menu or type /help"
    days_message: str = emojize(
        "Firstly, choose any compliment days you want and click on 'Next:right_arrow:':"
    )
    time_message: str = "Now, click on the time when you want to receive compliments:"
    success_message: str = emojize(
        "Well! You'll receive compliments on: {weekdays}\nat exactly {time} :relieved_face:"
    )
    list_message: str = emojize(
        "Scheduled compliments:\n{weekdays}\nAt {time} :alarm_clock:"
    )
    stop_message: str = emojize(
        "From now on I stop making compliments!\n\nI hope to see you soon :kissing_cat:"
    )
    empty_list_message: str = emojize(
        "You still don't have scheduled compliments!\n"
        + "Let's change it with /set_days :face_savoring_food:"
    )
    emtry_list_message2: str = emojize(
        "Oh, you won't receive compliments :pensive_face:"
    )
    help_message: str = (
        "To use this bot, you only need to set up the days of compliments "
        + "and the time of sending. Scheduling is available using the command /set_days\n\n"
        + "/list - get all compliment days and time\n"
        + "/stop - stop complimenting\n"
        + "/contacts - get author's contacts\n\n"
        + "Also you can use all these features with menu buttons!"
    )

    contacts_message: str = emojize(
        "This bot was developed with love by @redbulldog :face_blowing_a_kiss:"
    )

    # Daytime greetings
    morning_greeting: str = emojize("Goooooood morning! :smiling_face_with_halo:")
    day_greeting: str = emojize("Hey, cutie! :smiling_face_with_heart-eyes:")
    evening_greeting: str = emojize("Good evening, honey! :smiling_face_with_hearts:")
    night_greeting: str = emojize(
        "Are you sleeping? :sleeping_face: "
        + "Goodnight, sweety :kissing_face_with_closed_eyes:"
    )

    compliment_message: str = emojize(
        ":glowing_star::glowing_star::glowing_star:\n\n"
        + "{greeting}\n\nOn this beautiful day I want to tell you:\n\n{compliment}\n\n"
        + ":red_heart:"
    )


@dataclass(frozen=True)
class ButtonsCaptions:
    """ """

    mon_on: str = emojize("Mon - :check_mark_button:")
    tue_on: str = emojize("Tue - :check_mark_button:")
    wed_on: str = emojize("Wed - :check_mark_button:")
    thu_on: str = emojize("Thu - :check_mark_button:")
    fri_on: str = emojize("Fri - :check_mark_button:")
    sat_on: str = emojize("Sat - :check_mark_button:")
    sun_on: str = emojize("Sun - :check_mark_button:")

    next: str = emojize("Next:right_arrow:")


btn_captions = ButtonsCaptions()
msg = Messages()
