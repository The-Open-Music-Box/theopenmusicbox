from typing import Generic, TypeVar
from .nfc_hardware import NFCHardware

T = TypeVar('T', bound=NFCHardware)

class NFCHandler(Generic[T]):
    """Gestionnaire NFC qui abstrait le matériel sous-jacent (MockNFC ou PN532I2CNFC).
    Cette classe s'assure que tous les accès au matériel passent par les bonnes interfaces.
    """
    def __init__(self, hardware: T):
        """Initialise le handler avec le matériel spécifié.
        
        Args:
            hardware: Instance du matériel NFC (mock ou réel)
        """
        self._hardware = hardware

    @property
    def tag_subject(self):
        """Accède au subject RxPy qui émet les événements de détection de tag."""
        if hasattr(self._hardware, "tag_subject"):
            return self._hardware.tag_subject
        raise AttributeError("Underlying hardware does not have a tag_subject property.")

    async def start_nfc_reader(self) -> None:
        """Démarre le lecteur NFC de manière asynchrone."""
        if hasattr(self._hardware, "start_nfc_reader"):
            await self._hardware.start_nfc_reader()
        else:
            raise NotImplementedError("Underlying hardware does not support start_nfc_reader().")

    async def stop_nfc_reader(self) -> None:
        """Arrête le lecteur NFC de manière asynchrone."""
        if hasattr(self._hardware, "stop_nfc_reader"):
            await self._hardware.stop_nfc_reader()
        else:
            raise NotImplementedError("Underlying hardware does not support stop_nfc_reader().")

    async def read_tag(self) -> str:
        """Lit un tag NFC de manière asynchrone."""
        if hasattr(self._hardware, "read_nfc"):
            return await self._hardware.read_nfc()
        raise NotImplementedError("Underlying hardware does not support read_nfc().")

    async def write_tag(self, data: str) -> None:
        """Écrit des données sur un tag NFC de manière asynchrone."""
        if hasattr(self._hardware, "write_tag"):
            await self._hardware.write_tag(data)
        else:
            raise NotImplementedError("Underlying hardware does not support write_tag().")

    async def cleanup(self) -> None:
        """Nettoie les ressources du matériel de manière asynchrone."""
        if hasattr(self._hardware, "cleanup"):
            await self._hardware.cleanup()
        else:
            raise NotImplementedError("Underlying hardware does not support cleanup().")
