# app/src/module/nfc/nfc_interface.py

from abc import ABC, abstractmethod
from rx.subject import Subject

class NFCInterface(ABC):
    @abstractmethod
    def read_nfc(self):
        """Read NFC tag data."""

    @abstractmethod
    def start_nfc_reader(self):
        """Start the NFC reader thread."""

    @abstractmethod
    def stop_nfc_reader(self):
        """Stop the NFC reader thread."""

    @abstractmethod
    def cleanup(self):
        """Clean up resources."""

    @property
    @abstractmethod
    def tag_subject(self) -> Subject:
        """
        Get the subject that emits tag updates.

        Returns:
            Subject: The subject used to emit tag events.
        """
