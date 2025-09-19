# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""NFC Domain Module.

Contains all domain entities, value objects, services and interfaces
for NFC tag management according to Domain-Driven Design principles.
"""

from .entities.nfc_tag import NfcTag
from .entities.association_session import AssociationSession, SessionState
from .value_objects.tag_identifier import TagIdentifier
from .services.nfc_association_service import NfcAssociationService
from .protocols.nfc_hardware_protocol import NfcHardwareProtocol, NfcRepositoryProtocol

__all__ = [
    "NfcTag",
    "AssociationSession",
    "SessionState",
    "TagIdentifier",
    "NfcAssociationService",
    "NfcHardwareProtocol",
    "NfcRepositoryProtocol",
]
