# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

from colorama import Back, Fore


class ColorScheme:
    """Defines color and symbol schemes for log levels."""
    COLORS = {
        "DEBUG": Fore.CYAN,
        "INFO": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Fore.RED + Back.WHITE,
    }

    SYMBOLS = {"DEBUG": "→", "INFO": "✓", "WARNING": "⚠", "ERROR": "✗", "CRITICAL": "‼"}
