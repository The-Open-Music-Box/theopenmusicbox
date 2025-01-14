# app/src/monitoring/logging/log_colored_formatter.py

import logging

from colorama import Fore, Style
from log_base_formatter import BaseLogFormatter
from log_filter import LogFilter
from log_color_scheme import ColorScheme

class ColoredLogFormatter(BaseLogFormatter, logging.Formatter):
    def __init__(self, fmt=None, datefmt=None):
        BaseLogFormatter.__init__(self)
        logging.Formatter.__init__(self, fmt, datefmt)

    def format(self, record):
        if not LogFilter.should_log(record.msg):
            return ""
        record.msg = LogFilter.clean_message(record.msg)
        if not record.msg.strip():
            return ""

        color = ColorScheme.COLORS.get(record.levelname, Fore.WHITE)
        symbol = ColorScheme.SYMBOLS.get(record.levelname, "•")
        record.name = self._simplify_component_name(record.name)
        if "Initializing" in str(record.msg):
            self._startup_phase = self._extract_component(record.msg)
            return f"{Fore.CYAN}◉ Initializing {self._startup_phase}...{Style.RESET_ALL}"

        elif "ready" in str(record.msg) and self._startup_phase:
            result = f"{Fore.GREEN}  ↳ {self._startup_phase} ready{Style.RESET_ALL}"
            self._startup_phase = None
            return result

        record.levelname = f"{color}{record.levelname:<8}{Style.RESET_ALL}"
        record.name = f"{Fore.BLUE}{record.name:<20}{Style.RESET_ALL}"
        record.msg = f"{color}{symbol} {record.msg}{Style.RESET_ALL}"

        return super().format(record)
