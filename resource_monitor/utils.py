from .ascii_escape import *


def format_bytes_compact(num_bytes, target_unit=None):
    units = ["B", "K", "M", "G", "T"]
    value = float(num_bytes)

    for unit in units:
        if value < 1024 or unit == units[-1] or unit == target_unit:
            break
        value /= 1024

    # Adjust precision to keep numeric part <= 3 chars
    if value >= 100:
        formatted = f"{int(round(value))}"
    elif value >= 10:
        formatted = f"{value:.0f}".rstrip(".")
    else:
        formatted = f"{value:.1f}".rstrip("0").rstrip(".")

    return f"{formatted}{unit}"


def progress_bar(percent=None, used=None, total=None, width=50, unit=None, color_percents=(70, 90)):
    percent = percent if percent is not None else 100*used/total

    progress_width = width-2
    filled = int(progress_width * percent / 100)
    empty = progress_width - filled
    bar = "|" * filled + " " * empty

    if percent < color_percents[0]:
        color = GREEN
    elif percent < color_percents[1]:
        color = YELLOW
    else:
        color = RED

    if (used is None or total is None):
        value = f'{percent:.1f}%'
    else:
        used = format_bytes_compact(used, target_unit=unit)
        total = format_bytes_compact(total, target_unit=unit)
        value = f'{used}/{total}'
    
    str = f"{BOLD}[{RESET}{color}{bar[:-len(value)]}{value}{RESET}{BOLD}]{RESET}"

    return str
