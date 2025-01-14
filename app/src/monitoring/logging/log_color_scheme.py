# app/src/monitoring/logging/log_color_scheme.py

from colorama import Fore, Back

class ColorScheme:
    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Back.WHITE,
    }

    SYMBOLS = {
        'DEBUG': "→",
        'INFO': "✓",
        'WARNING': "⚠",
        'ERROR': "✗",
        'CRITICAL': "‼"
    }
