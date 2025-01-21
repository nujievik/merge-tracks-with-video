from pathlib import Path
from datetime import timedelta

def str_to_path(str_in, check_exists=False):
    try:
        path_out = Path(str_in)
        if check_exists and not path_out.exists():
            print('Error. Path not exists!')
            return
    except Exception:
        return

    return path_out

def str_to_number(str_in, int_num=True, non_negative=True):
    try:
        number = int(str_in) if int_num else float(str_in)
        if non_negative and number < 0:
            return
    except Exception:
        return

    return number

def timedelta_to_str(td, hours_place=1, decimal_place=2):
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    d, dp = td.microseconds, decimal_place
    decimal = int(d / (10 ** (6 - dp))) if dp <= 6 else d * 10 ** (dp - 6)
    return f'{hours:0{hours_place}}:{minutes:02}:{seconds:02}.{decimal:0{decimal_place}}'

def str_to_timedelta(time_str):
    hours, minutes, seconds = time_str.split(':')
    total_seconds = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    return timedelta(seconds=total_seconds)

def command_to_print_str(command):
    return f"'{str_to_path(command[0]).stem}' {' '.join(f"'{str(item)}'" for item in command[1:])}"
