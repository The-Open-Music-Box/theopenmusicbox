# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Upload Factory for creating configured upload services."""

from typing import Optional

from app.src.domain.upload.services.upload_validation_service import UploadValidationService
from app.src.application.services.upload_application_service import UploadApplicationService
from .adapters.file_storage_adapter import LocalFileStorageAdapter
from .adapters.metadata_extractor import MutagenMetadataExtractor, MockMetadataExtractor


class UploadFactory:
    """Factory for creating upload services with proper dependency injection."""

    @staticmethod
    def create_upload_application_service(
        upload_folder: str = "uploads",
        temp_folder: str = "temp_uploads",
        max_file_size: int = 100 * 1024 * 1024,  # 100MB
        use_mock_metadata: bool = False,
    ) -> UploadApplicationService:
        """Create a fully configured upload application service.

        Args:
            upload_folder: Folder for final uploaded files
            temp_folder: Folder for temporary upload chunks
            max_file_size: Maximum file size in bytes
            use_mock_metadata: Use mock metadata extractor for testing

        Returns:
            Configured upload application service
        """
        # Create file storage adapter
        file_storage = LocalFileStorageAdapter(temp_folder)

        # Create metadata extractor
        if use_mock_metadata:
            metadata_extractor = MockMetadataExtractor()
        else:
            metadata_extractor = MutagenMetadataExtractor()

        # Create validation service
        validation_service = UploadValidationService(
            max_file_size=max_file_size,
            allowed_extensions=set(metadata_extractor.get_supported_formats()),
        )

        # Create application service
        return UploadApplicationService(
            file_storage=file_storage,
            metadata_extractor=metadata_extractor,
            validation_service=validation_service,
            upload_folder=upload_folder,
        )

    @staticmethod
    def create_mock_upload_service() -> UploadApplicationService:
        """Create upload service with mock implementations for testing.

        Returns:
            Upload application service with mock implementations
        """
        return UploadFactory.create_upload_application_service(
            upload_folder="test_uploads", temp_folder="test_temp", use_mock_metadata=True
        )
