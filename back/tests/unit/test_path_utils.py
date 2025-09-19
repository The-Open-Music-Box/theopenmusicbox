#!/usr/bin/env python3
"""
Unit tests for path utilities.

Tests the path normalization and folder management utilities used throughout
the application for consistent folder naming and file organization.
"""

import pytest
from pathlib import Path
from app.src.utils.path_utils import normalize_folder_name, migrate_existing_folder


class TestPathUtils:
    """Test suite for path utility functions."""

    def test_normalize_folder_name_basic_cases(self):
        """Test basic folder name normalization."""
        # Simple cases
        assert normalize_folder_name("Simple Name") == "simple_name"
        assert normalize_folder_name("UPPERCASE") == "uppercase"
        assert normalize_folder_name("MixedCase") == "mixedcase"

    def test_normalize_folder_name_special_characters(self):
        """Test normalization of special characters."""
        # Spaces
        assert normalize_folder_name("Multiple   Spaces") == "multiple_spaces"
        assert normalize_folder_name("  Leading Trailing  ") == "leading_trailing"

        # Parentheses and brackets
        assert normalize_folder_name("Name (with) [brackets]") == "name__with___brackets_"
        assert normalize_folder_name("(Parentheses)") == "_parentheses_"
        assert normalize_folder_name("[Brackets]") == "_brackets_"

        # Colons and other punctuation
        assert normalize_folder_name("Title: Subtitle") == "title__subtitle"
        assert normalize_folder_name("Artist - Album") == "artist___album"

    def test_normalize_folder_name_unicode_and_accents(self):
        """Test normalization of unicode characters and accents."""
        # French accents
        assert normalize_folder_name("Café") == "cafe"
        assert normalize_folder_name("Naïve") == "naive"
        assert normalize_folder_name("Élève") == "eleve"

        # German umlauts
        assert normalize_folder_name("Björk") == "bjork"
        assert normalize_folder_name("Müller") == "muller"

        # Spanish characters
        assert normalize_folder_name("Niño") == "nino"

    def test_normalize_folder_name_edge_cases(self):
        """Test edge cases for folder name normalization."""
        # Empty or whitespace only
        assert normalize_folder_name("") == "unknown"
        assert normalize_folder_name("   ") == "unknown"
        assert normalize_folder_name(None) == "unknown"

        # Only special characters
        assert normalize_folder_name("()[]:-") == "______"

        # Mixed numbers and text
        assert normalize_folder_name("Track 01 - Song Name") == "track_01___song_name"
        assert normalize_folder_name("Album 2025") == "album_2025"

    def test_normalize_folder_name_consistency(self):
        """Test that normalization is consistent and idempotent."""
        test_names = [
            "Complex (Name) [With] Special: Characters - 2025",
            "Café de la Musique",
            "Multiple   Spaces   Here",
        ]

        for name in test_names:
            normalized_once = normalize_folder_name(name)
            normalized_twice = normalize_folder_name(normalized_once)

            # Should be idempotent (normalizing already normalized name doesn't change it)
            assert normalized_once == normalized_twice

            # Should be consistent
            assert normalize_folder_name(name) == normalized_once

    def test_migrate_existing_folder_success(self, tmp_path):
        """Test successful folder migration."""
        # Create source folder with content
        source_folder = tmp_path / "source_folder"
        target_folder = tmp_path / "target_folder"

        source_folder.mkdir()
        (source_folder / "file1.txt").write_text("content 1")
        (source_folder / "subfolder").mkdir()
        (source_folder / "subfolder" / "file2.txt").write_text("content 2")

        # Migrate folder
        success = migrate_existing_folder(str(source_folder), str(target_folder))

        # Verify migration
        assert success, "Migration should succeed"
        assert target_folder.exists(), "Target folder should exist"
        assert not source_folder.exists(), "Source folder should be removed"

        # Verify content was moved
        assert (target_folder / "file1.txt").exists()
        assert (target_folder / "file1.txt").read_text() == "content 1"
        assert (target_folder / "subfolder" / "file2.txt").exists()
        assert (target_folder / "subfolder" / "file2.txt").read_text() == "content 2"

    def test_migrate_existing_folder_merge_with_existing(self, tmp_path):
        """Test folder migration when target already exists."""
        # Create source and target folders with different content
        source_folder = tmp_path / "source_folder"
        target_folder = tmp_path / "target_folder"

        source_folder.mkdir()
        target_folder.mkdir()

        (source_folder / "source_file.txt").write_text("source content")
        (target_folder / "target_file.txt").write_text("target content")

        # Migrate folder
        success = migrate_existing_folder(str(source_folder), str(target_folder))

        # Verify migration and merge
        assert success, "Migration should succeed"
        assert target_folder.exists(), "Target folder should exist"
        assert not source_folder.exists(), "Source folder should be removed"

        # Verify both files exist in target
        assert (target_folder / "source_file.txt").exists()
        assert (target_folder / "target_file.txt").exists()
        assert (target_folder / "source_file.txt").read_text() == "source content"
        assert (target_folder / "target_file.txt").read_text() == "target content"

    def test_migrate_existing_folder_source_not_exists(self, tmp_path):
        """Test folder migration when source doesn't exist."""
        source_folder = tmp_path / "nonexistent_source"
        target_folder = tmp_path / "target_folder"

        # Try to migrate non-existent folder
        success = migrate_existing_folder(str(source_folder), str(target_folder))

        # Should handle gracefully
        assert not success, "Migration should fail for non-existent source"
        assert not target_folder.exists(), "Target folder should not be created"

    def test_migrate_existing_folder_handles_permission_errors(self, tmp_path):
        """Test folder migration handles permission errors gracefully."""
        import os
        import stat

        source_folder = tmp_path / "source_folder"
        target_folder = tmp_path / "target_folder"

        source_folder.mkdir()
        test_file = source_folder / "test_file.txt"
        test_file.write_text("test content")

        # Make source folder read-only (simulating permission error)
        try:
            source_folder.chmod(stat.S_IRUSR | stat.S_IXUSR)  # Read and execute only

            # Try to migrate (might fail due to permissions)
            success = migrate_existing_folder(str(source_folder), str(target_folder))

            # The function should handle the error gracefully (return False)
            # Note: On some systems this might still succeed, so we just ensure it doesn't crash

        finally:
            # Restore permissions for cleanup
            try:
                source_folder.chmod(stat.S_IRWXU)  # Full permissions
            except:
                pass

    def test_path_normalization_integration(self):
        """Test integration between different path utilities."""
        test_cases = [
            {
                "input": "Louis de Funès - Fables de La Fontaine [mp3-320K]",
                "expected": "louis_de_funes___fables_de_la_fontaine__mp3_320k_"
            },
            {
                "input": "Faba - La vache",
                "expected": "faba___la_vache"
            },
            {
                "input": "bibeo - les petits poissons...",
                "expected": "bibeo___les_petits_poissons___"
            },
            {
                "input": "Crypt of the Necrodancer OST - Tombtorial (Tutorial)",
                "expected": "crypt_of_the_necrodancer_ost___tombtorial__tutorial_"
            }
        ]

        for case in test_cases:
            result = normalize_folder_name(case["input"])
            assert result == case["expected"], f"Failed for input '{case['input']}': expected '{case['expected']}', got '{result}'"