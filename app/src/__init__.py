"""
Core package for the music box application.
"""

__version__ = "0.1.0"
__app_name__ = "TheOpenMusicBox"
__author__ = "Jonathan Piette"


from .helpers.exceptions import AppError

__all__ = [

    'AppError',
    '__version__',
    '__app_name__',
    '__author__'
]

