from typing import Optional, Protocol


class NFCHardware(Protocol):
    """Interface définissant les opérations NFC standard.

    Toutes les implémentations matérielles doivent respecter cette
    interface.
    """

    async def initialize(self) -> None:
        """Initialise le matériel NFC.

        Returns:
            None
        """
        pass

    async def read_nfc(self) -> Optional[bytes]:
        """Lit les données NFC et retourne les octets lus, ou None."""
        pass

    async def start_nfc_reader(self) -> None:
        """Démarre le lecteur NFC."""
        pass

    async def stop_nfc_reader(self) -> None:
        """Arrête le lecteur NFC."""
        pass

    async def cleanup(self) -> None:
        """Nettoie et libère les ressources du matériel NFC."""
        pass
