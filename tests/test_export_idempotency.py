"""Tests for export idempotency."""

import pytest
import tempfile
from pathlib import Path
from src.export.obsidian import check_manual_edit, write_note


@pytest.fixture
def temp_note_dir():
    """Create temporary directory for notes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_check_manual_edit_empty_rating(temp_note_dir):
    """Test that empty rating is not considered manual edit."""
    note_path = temp_note_dir / "test.md"
    content = """---
title: Test
rating:
---

# Test Note
"""
    note_path.write_text(content)

    assert not check_manual_edit(note_path)


def test_check_manual_edit_filled_rating(temp_note_dir):
    """Test that filled rating is considered manual edit."""
    note_path = temp_note_dir / "test.md"
    content = """---
title: Test
rating: 5
---

# Test Note
"""
    note_path.write_text(content)

    assert check_manual_edit(note_path)


def test_check_manual_edit_nonexistent(temp_note_dir):
    """Test checking non-existent file."""
    note_path = temp_note_dir / "nonexistent.md"
    assert not check_manual_edit(note_path)


def test_write_note_creates_file(temp_note_dir):
    """Test that write_note creates file."""
    note_path = temp_note_dir / "new_note.md"
    content = "# Test Content"

    result = write_note(note_path, content, check_edit=False)

    assert result is True
    assert note_path.exists()
    assert note_path.read_text() == content


def test_write_note_skips_manual_edit(temp_note_dir):
    """Test that write_note skips manually edited files."""
    note_path = temp_note_dir / "edited.md"

    # Create note with filled rating (manual edit)
    original_content = """---
rating: 5
---

# Original
"""
    note_path.write_text(original_content)

    # Try to overwrite
    new_content = "# New Content"
    result = write_note(note_path, new_content, check_edit=True)

    # Should be skipped
    assert result is False
    assert note_path.read_text() == original_content


def test_write_note_overwrites_non_edited(temp_note_dir):
    """Test that write_note overwrites non-edited files."""
    note_path = temp_note_dir / "auto.md"

    # Create note without rating (auto-generated)
    original_content = """---
rating:
---

# Original
"""
    note_path.write_text(original_content)

    # Overwrite should succeed
    new_content = """---
rating:
---

# Updated
"""
    result = write_note(note_path, new_content, check_edit=True)

    assert result is True
    assert note_path.read_text() == new_content
