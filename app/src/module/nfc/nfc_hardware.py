from typing import Optional, Protocol


class NFCHardware(Protocol):
    """Interface définissant les opérations NFC standard.

    Toutes les implémentations matérielles doivent respecter cette
    interface.
    """

    async def initialize(self) -> None: ...

    async def read_nfc(self) -> Optional[bytes]: ...

    async def start_nfc_reader(self) -> None: ...

    async def stop_nfc_reader(self) -> None: ...

    async def cleanup(self) -> None: ...
