"""Tests for file I/O operations."""

from src.model.ast import (
    CloseFile,
    FileManager,
    FileMode,
    FileOperation,
    OpenFile,
    ReadFile,
    WriteFile,
)


def test_file_mode_values():
    """Test file mode enumeration values."""
    assert FileMode.READ.value == "r"
    assert FileMode.WRITE.value == "w"
    assert FileMode.APPEND.value == "a"
    assert FileMode.READ_WRITE.value == "r+"
    assert FileMode.WRITE_READ.value == "w+"
    assert FileMode.APPEND_READ.value == "a+"
    assert FileMode.BINARY_READ.value == "rb"
    assert FileMode.BINARY_WRITE.value == "wb"
    assert FileMode.BINARY_APPEND.value == "ab"


def test_file_operation_validation():
    """Test base file operation validation."""
    # Valid operation
    op = FileOperation(file_path="test.txt")
    assert op.validate()

    # Invalid operation (empty path)
    op = FileOperation(file_path="")
    assert not op.validate()


def test_open_file_validation():
    """Test open file operation validation."""
    # Valid open operation
    op = OpenFile(file_path="test.txt", mode=FileMode.READ)
    assert op.validate()

    # Invalid open operation (no mode)
    op = OpenFile(file_path="test.txt")
    assert not op.validate()

    # Invalid open operation (empty path)
    op = OpenFile(file_path="", mode=FileMode.READ)
    assert not op.validate()


def test_read_file_validation():
    """Test read file operation validation."""
    # Valid read operation
    op = ReadFile(file_path="test.txt")
    assert op.validate()

    # Valid read operation with max bytes
    op = ReadFile(file_path="test.txt", max_bytes=100)
    assert op.validate()

    # Invalid read operation (empty path)
    op = ReadFile(file_path="")
    assert not op.validate()

    # Invalid read operation (negative max bytes)
    op = ReadFile(file_path="test.txt", max_bytes=-1)
    assert not op.validate()


def test_write_file_validation():
    """Test write file operation validation."""
    # Valid write operation
    op = WriteFile(file_path="test.txt", content="Hello")
    assert op.validate()

    # Invalid write operation (empty path)
    op = WriteFile(file_path="", content="Hello")
    assert not op.validate()

    # Invalid write operation (no content)
    op = WriteFile(file_path="test.txt", content=None)
    assert not op.validate()


def test_file_manager():
    """Test file manager functionality."""
    manager = FileManager(open_files={})

    # Test opening a file
    assert manager.open_file("test.txt", FileMode.READ)
    assert manager.is_file_open("test.txt")
    assert manager.get_file_mode("test.txt") == FileMode.READ

    # Test opening already open file
    assert not manager.open_file("test.txt", FileMode.WRITE)

    # Test closing a file
    assert manager.close_file("test.txt")
    assert not manager.is_file_open("test.txt")

    # Test closing non-existent file
    assert not manager.close_file("nonexistent.txt")


def test_file_manager_operation_validation():
    """Test file manager operation validation."""
    manager = FileManager(open_files={})

    # Test open operation validation
    open_op = OpenFile(file_path="test.txt", mode=FileMode.READ)
    assert manager.validate_operation(open_op)  # File not open yet
    manager.open_file("test.txt", FileMode.READ)
    assert not manager.validate_operation(open_op)  # File already open

    # Test read operation validation
    read_op = ReadFile(file_path="test.txt")
    assert manager.validate_operation(read_op)  # File open in read mode
    manager.close_file("test.txt")
    assert not manager.validate_operation(read_op)  # File closed

    # Test write operation validation
    manager.open_file("test.txt", FileMode.WRITE)
    write_op = WriteFile(file_path="test.txt", content="Hello")
    assert manager.validate_operation(write_op)  # File open in write mode

    # Test close operation validation
    close_op = CloseFile(file_path="test.txt")
    assert manager.validate_operation(close_op)  # File is open
    manager.close_file("test.txt")
    assert not manager.validate_operation(close_op)  # File already closed


def test_file_mode_compatibility():
    """Test file mode compatibility for operations."""
    manager = FileManager(open_files={})

    # Test read compatibility
    manager.open_file("test.txt", FileMode.READ)
    read_op = ReadFile(file_path="test.txt")
    assert manager.validate_operation(read_op)  # Can read in READ mode
    write_op = WriteFile(file_path="test.txt", content="Hello")
    assert not manager.validate_operation(write_op)  # Cannot write in READ mode
    manager.close_file("test.txt")

    # Test write compatibility
    manager.open_file("test.txt", FileMode.WRITE)
    assert not manager.validate_operation(read_op)  # Cannot read in WRITE mode
    assert manager.validate_operation(write_op)  # Can write in WRITE mode
    manager.close_file("test.txt")

    # Test read-write compatibility
    manager.open_file("test.txt", FileMode.READ_WRITE)
    assert manager.validate_operation(read_op)  # Can read in READ_WRITE mode
    assert manager.validate_operation(write_op)  # Can write in READ_WRITE mode
