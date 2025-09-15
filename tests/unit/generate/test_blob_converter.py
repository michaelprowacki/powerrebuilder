#!/usr/bin/env python3
"""Test suite for blob/binary data type conversion."""

import base64

import pytest

from src.generate.converters.data.blobs import BlobConverter
from src.generate.converters.flutter.models import TypeConverter


class TestBlobConverter:
    """Test blob data conversion functionality."""

    def test_empty_blob_handling(self):
        """Test handling of empty blob data."""
        converter = BlobConverter()

        result = converter.convert_blob(b"", "profile_pic")

        assert result["dart_type"] == "Uint8List?"
        assert result["implementation"] == "null"
        assert "import 'dart:typed_data';" in result["imports"]

    def test_small_blob_inline(self):
        """Test small blob converted to inline base64."""
        converter = BlobConverter()

        # Small data (< 10KB)
        small_data = b"Hello, World!" * 100  # ~1.3KB
        result = converter.convert_blob(small_data, "small_data")

        assert result["dart_type"] == "Uint8List"
        assert "base64Decode(" in result["implementation"]
        assert "import 'dart:convert';" in result["imports"]

        # Verify base64 encoding
        expected_base64 = base64.b64encode(small_data).decode("utf-8")
        assert expected_base64 in result["implementation"]

    def test_image_blob_detection(self):
        """Test image blob detection and conversion."""
        converter = BlobConverter()

        # JPEG magic bytes
        jpeg_data = b"\xff\xd8\xff\xe0" + b"JFIF" + b"\x00" * 100
        result = converter.convert_blob(jpeg_data, "photo", None)

        assert result["dart_type"] == "Widget"
        assert "Image.memory(" in result["implementation"]
        assert "import 'package:flutter/material.dart';" in result["imports"]

    def test_large_image_blob(self):
        """Test large image blob handling."""
        converter = BlobConverter()

        # Large PNG data (> 10KB)
        png_header = b"\x89PNG\r\n\x1a\n"
        large_png = png_header + b"\x00" * 20000  # ~20KB

        result = converter.convert_blob(large_png, "large_image")

        assert result["dart_type"] == "ImageProvider"
        assert "MemoryImage(" in result["implementation"]
        assert "_large_imageData" in result["implementation"]
        assert "Future<void> _loadLargeImage()" in result["helper_code"]

    def test_pdf_blob_handling(self):
        """Test PDF blob detection and handling."""
        converter = BlobConverter()

        # PDF magic bytes
        pdf_data = b"%PDF-1.4" + b"\x00" * 5000
        result = converter.convert_blob(pdf_data, "document")

        assert result["dart_type"] == "Uint8List"
        assert "_documentData" in result["implementation"]
        assert "application/pdf" in result["helper_code"]

    def test_large_file_blob(self):
        """Test large blob requiring file storage."""
        converter = BlobConverter()

        # Large blob (> 1MB)
        large_data = b"X" * (2 * 1024 * 1024)  # 2MB
        result = converter.convert_blob(large_data, "large_file")

        assert result["dart_type"] == "File?"
        assert "_large_fileFile" in result["implementation"]
        assert "import 'dart:io';" in result["imports"]
        assert "getTemporaryDirectory()" in result["helper_code"]
        assert "_cleanupLargeFile()" in result["helper_code"]

    def test_mime_type_detection(self):
        """Test MIME type detection for various formats."""
        converter = BlobConverter()

        test_cases = [
            (b"\xff\xd8\xff", "image/jpeg"),
            (b"\x89PNG\r\n\x1a\n", "image/png"),
            (b"GIF89a", "image/gif"),
            (b"BM", "image/bmp"),
            (b"%PDF", "application/pdf"),
            (b"PK\x03\x04", "application/zip"),
            (b"\x1f\x8b", "application/gzip"),
            (b"unknown", "application/octet-stream"),
        ]

        for data, expected_mime in test_cases:
            mime_type = converter._detect_mime_type(data + b"\x00" * 100)
            assert mime_type == expected_mime

    def test_blob_repository_methods(self):
        """Test generation of repository methods for blob handling."""
        converter = BlobConverter()

        blob_fields = [
            {"name": "profile_image", "type": "blob"},
            {"name": "document_data", "type": "blob"},
        ]

        code = converter.generate_blob_repository_methods(blob_fields)

        assert "Future<Uint8List> getProfileImage()" in code
        assert "Stream<Uint8List> getProfileImageStream()" in code
        assert "Future<Uint8List> getDocumentData()" in code
        assert "const chunkSize = 1024 * 1024;" in code

    def test_blob_display_widget_image(self):
        """Test generation of image blob display widget."""
        converter = BlobConverter()

        widget_code = converter.generate_blob_widget("profile_pic", "image/jpeg")

        assert "class ProfilePicDisplay extends StatelessWidget" in widget_code
        assert "Image.memory(" in widget_code
        assert "BoxFit fit" in widget_code
        assert "Icons.image_not_supported" in widget_code
        assert "errorBuilder:" in widget_code

    def test_blob_display_widget_generic(self):
        """Test generation of generic blob display widget."""
        converter = BlobConverter()

        widget_code = converter.generate_blob_widget("attachment", "application/pdf")

        assert "class AttachmentDisplay extends StatelessWidget" in widget_code
        assert "ListTile(" in widget_code
        assert "Icons.download" in widget_code
        assert "Size: $sizeInKB KB" in widget_code
        assert "_getIconForMimeType" in widget_code


class TestTypeConverterBlobIntegration:
    """Test blob handling integration in TypeConverter."""

    def test_blob_type_conversion(self):
        """Test basic blob type conversion."""
        converter = TypeConverter()

        dart_type = converter.convert_type("blob")
        assert dart_type == "Uint8List"

        nullable_type = converter.convert_type("blob", nullable=True)
        assert nullable_type == "Uint8List?"

    def test_blob_imports(self):
        """Test import generation for blob types."""
        converter = TypeConverter()

        imports = converter.get_imports_for_type("blob")
        assert "import 'dart:typed_data';" in imports
        assert "import 'dart:convert';" in imports

    def test_blob_default_value(self):
        """Test default value for blob type."""
        converter = TypeConverter()

        default = converter.get_default_value("blob")
        assert default == "Uint8List(0)"

    def test_context_aware_blob_conversion(self):
        """Test context-aware blob type conversion."""
        converter = TypeConverter()

        # Small data blob
        small_context = {"expected_size": 5000, "usage": "data"}
        result = converter.convert_blob_type("blob", small_context)
        assert result["dart_type"] == "String"
        assert result["strategy"] == "base64"

        # Image blob
        image_context = {"expected_size": 50000, "usage": "image"}
        result = converter.convert_blob_type("blob", image_context)
        assert result["dart_type"] == "ImageProvider"
        assert result["strategy"] == "image"

        # Large file blob
        file_context = {"expected_size": 5000000, "usage": "document"}
        result = converter.convert_blob_type("blob", file_context)
        assert result["dart_type"] == "File"
        assert result["strategy"] == "file"

    def test_blob_array_type(self):
        """Test blob array type conversion."""
        converter = TypeConverter()

        dart_type = converter.convert_type("blob[]")
        assert dart_type == "List<Uint8List>"

        nullable_array = converter.convert_type("blob[]", nullable=True)
        assert nullable_array == "List<Uint8List>?"


class TestBlobHandlingEndToEnd:
    """Test end-to-end blob handling scenarios."""

    def test_datawindow_with_blob_column(self):
        """Test handling DataWindow with blob columns."""
        type_converter = TypeConverter()
        blob_converter = BlobConverter()

        # Simulate DataWindow column with blob
        column = {
            "name": "employee_photo",
            "type": "blob",
            "usage": "image",
        }

        # Convert type
        dart_type = type_converter.convert_type(column["type"])
        assert dart_type == "Uint8List"

        # Generate display widget
        widget = blob_converter.generate_blob_widget(
            column["name"],
            "image/jpeg",
        )
        assert "EmployeePhotoDisplay" in widget

    def test_blob_in_structure(self):
        """Test blob field in PowerBuilder structure."""
        type_converter = TypeConverter()

        # Structure with blob field
        structure_fields = [
            {"name": "id", "type": "integer"},
            {"name": "name", "type": "string"},
            {"name": "data", "type": "blob"},
            {"name": "thumbnail", "type": "blob"},
        ]

        # Convert each field
        dart_fields = []
        for field in structure_fields:
            dart_type = type_converter.convert_type(field["type"])
            dart_fields.append(f"final {dart_type} {field['name']};")

        assert "final int id;" in dart_fields
        assert "final String name;" in dart_fields
        assert "final Uint8List data;" in dart_fields
        assert "final Uint8List thumbnail;" in dart_fields


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
