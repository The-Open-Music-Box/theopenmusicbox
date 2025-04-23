# app/tests/api/models/menu_item.py

from dataclasses import dataclass
from typing import Optional, Callable

@dataclass
class MenuItem:
    """Represents a menu item in the API tester."""
    title: str
    action: Callable
    description: Optional[str] = None
    shortcut: Optional[str] = None

    def __str__(self) -> str:
        return f"{self.title} ({self.shortcut})" if self.shortcut else self.title