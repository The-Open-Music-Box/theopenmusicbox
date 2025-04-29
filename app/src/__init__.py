# app/src/__init__.py

"""
Core package for the music box application.
"""

__version__ = "0.1.0"
__app_name__ = "TheMusicBox"
__author__ = "Jonathan Piette"


from .helpers.exceptions import AppError

__all__ = [
    
    'AppError',
    '__version__',
    '__app_name__',
    '__author__'
]

