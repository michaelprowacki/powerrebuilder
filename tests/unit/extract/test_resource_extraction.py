"""Tests for enhanced resource extraction functionality."""

import tempfile
from pathlib import Path

from src.extract.pbd.catalog import ResourceCatalog
from src.extract.pbd.extractor_binary import (
    EnhancedImageExtractor,
    StringResourceExtractor,
)


class TestStringResourceExtractor:
    """Test string resource extraction."""

    def test_extract_ascii_strings(self):
        """Test extraction of ASCII strings."""
        extractor = StringResourceExtractor()

        # Create test data with embedded strings
        data = b"\x00\x00Hello World\x00\x00This is a test\x00\x00"

        strings = extractor.extract_strings_from_data(data)

        assert "Hello World" in strings
        assert "This is a test" in strings

    def test_extract_unicode_strings(self):
        """Test extraction of Unicode strings."""
        extractor = StringResourceExtractor()

        # Create test data with Unicode strings (UTF-16LE)
        data = b"H\x00e\x00l\x00l\x00o\x00 \x00W\x00o\x00r\x00l\x00d\x00\x00\x00"

        strings = extractor.extract_strings_from_data(data)

        assert "Hello World" in strings

    def test_filter_invalid_strings(self):
        """Test that invalid strings are filtered out."""
        extractor = StringResourceExtractor()

        # Create test data with noise
        data = b"aa\x00\x00\xff\xff\xff\x00\x00Valid String Here\x00\x001234567890\x00"

        strings = extractor.extract_strings_from_data(data)

        # Should filter out 'aa' (too short) and hex strings
        assert "Valid String Here" in strings
        assert "aa" not in strings
        assert "1234567890" not in strings  # All digits

    def test_extract_properties(self):
        """Test property extraction."""
        extractor = StringResourceExtractor()

        # Create test data with properties
        data = b'width=100\nheight=200\ntitle="My Window"\nvisible=true\n'

        properties = extractor.extract_property_strings(data)

        assert properties["width"] == "100"
        assert properties["height"] == "200"
        assert properties["title"] == "My Window"
        assert properties["visible"] == "true"

    def test_extract_string_table(self):
        """Test string table extraction."""
        extractor = StringResourceExtractor()

        # Create test data with string table (2-byte length prefix)
        data = b"\x05\x00Hello\x05\x00World\x04\x00Test"

        table = extractor.extract_string_table(data)

        assert len(table) == 3
        assert table[0] == (0, "Hello")
        assert table[1] == (1, "World")
        assert table[2] == (2, "Test")


class TestEnhancedImageExtractor:
    """Test enhanced image extraction."""

    def test_find_bmp_image(self):
        """Test BMP image detection and extraction."""
        extractor = EnhancedImageExtractor()

        # Create minimal BMP header
        bmp_data = b"BM"  # Signature
        bmp_data += b"\x46\x00\x00\x00"  # File size (70 bytes)
        bmp_data += b"\x00\x00\x00\x00"  # Reserved
        bmp_data += b"\x36\x00\x00\x00"  # Data offset
        bmp_data += b"\x28\x00\x00\x00"  # Header size
        bmp_data += b"\x02\x00\x00\x00"  # Width (2)
        bmp_data += b"\x02\x00\x00\x00"  # Height (2)
        bmp_data += b"\x01\x00"  # Planes
        bmp_data += b"\x18\x00"  # Bits per pixel (24)
        bmp_data += b"\x00" * 24  # Rest of header
        bmp_data += b"\xff" * 16  # Pixel data

        # Embed in larger data
        test_data = b"\x00" * 100 + bmp_data + b"\x00" * 100

        images = extractor.find_images_in_data(test_data, "test.srm")

        assert len(images) == 1
        assert images[0]["format"] == "bmp"
        assert images[0]["offset"] == 100
        assert images[0]["metadata"]["width"] == 2
        assert images[0]["metadata"]["height"] == 2

    def test_find_png_image(self):
        """Test PNG image detection."""
        extractor = EnhancedImageExtractor()

        # Create minimal PNG
        png_data = b"\x89PNG\r\n\x1a\n"  # PNG signature
        png_data += b"\x00\x00\x00\x0d"  # IHDR length
        png_data += b"IHDR"  # IHDR chunk
        png_data += b"\x00\x00\x00\x10"  # Width (16)
        png_data += b"\x00\x00\x00\x10"  # Height (16)
        png_data += b"\x08\x02\x00\x00\x00"  # Bit depth, color type, etc
        png_data += b"\x90\x91\x68\x36"  # CRC
        png_data += b"\x00\x00\x00\x00IEND\xae\x42\x60\x82"  # IEND chunk

        images = extractor.find_images_in_data(png_data, "test.sru")

        assert len(images) == 1
        assert images[0]["format"] == "png"
        assert images[0]["metadata"]["width"] == 16
        assert images[0]["metadata"]["height"] == 16

    def test_multiple_images(self):
        """Test extraction of multiple images."""
        extractor = EnhancedImageExtractor()

        # Create data with multiple images
        gif_data = b"GIF89a\x01\x00\x01\x00\x00\x00\x00;"  # Minimal GIF
        bmp_data = b"BM\x46\x00\x00\x00" + b"\x00" * 66  # Minimal BMP

        test_data = gif_data + b"\x00" * 50 + bmp_data

        images = extractor.find_images_in_data(test_data, "test.srw")

        assert len(images) == 2
        assert images[0]["format"] == "gif"
        assert images[1]["format"] == "bmp"

    def test_save_extracted_images(self):
        """Test saving extracted images."""
        extractor = EnhancedImageExtractor()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            # Create test file with image
            test_file = output_dir / "test.srm"
            bmp_data = b"BM\x46\x00\x00\x00" + b"\x00" * 66
            test_file.write_bytes(bmp_data)

            # Extract with saving
            images = extractor.extract_images_from_file(test_file, output_dir)

            assert len(images) == 1
            assert "saved_path" in images[0]

            # Check saved file exists
            saved_path = Path(images[0]["saved_path"])
            assert saved_path.exists()
            assert saved_path.read_bytes()[:2] == b"BM"


class TestResourceCatalog:
    """Test resource catalog functionality."""

    def test_add_string_resource(self):
        """Test adding string resources."""
        catalog = ResourceCatalog()

        # Add a string
        resource_id = catalog.add_string_resource("test.pbl", "Hello World")

        assert resource_id in catalog.resources["strings"]
        assert catalog.resources["strings"][resource_id]["value"] == "Hello World"

        # Add same string from different source
        resource_id2 = catalog.add_string_resource("test2.pbl", "Hello World")

        assert resource_id == resource_id2  # Same ID for same string
        assert len(catalog.resources["strings"][resource_id]["sources"]) == 2

    def test_add_image_resource(self):
        """Test adding image resources."""
        catalog = ResourceCatalog()

        image_data = {
            "format": "png",
            "size": 1024,
            "offset": 100,
            "metadata": {"width": 32, "height": 32},
        }

        resource_id = catalog.add_image_resource("test.pbl", image_data)

        assert resource_id in catalog.resources["images"]
        assert catalog.resources["images"][resource_id]["format"] == "png"

    def test_cross_references(self):
        """Test resource cross-referencing."""
        catalog = ResourceCatalog()

        # Add resources
        string_id = catalog.add_string_resource("window.srw", "Window Title")
        image_id = catalog.add_image_resource(
            "window.srw", {"format": "ico", "size": 256}
        )

        # Check cross-references
        assert "window.srw" in catalog.find_resource_usage(string_id)
        assert "window.srw" in catalog.find_resource_usage(image_id)

        resources = catalog.find_object_resources("window.srw")
        assert string_id in resources["strings"]
        assert image_id in resources["images"]

    def test_find_common_resources(self):
        """Test finding common resources."""
        catalog = ResourceCatalog()

        # Add shared string
        catalog.add_string_resource("file1.pbl", "Common String")
        catalog.add_string_resource("file2.pbl", "Common String")
        catalog.add_string_resource("file3.pbl", "Common String")

        # Add unique string
        catalog.add_string_resource("file1.pbl", "Unique String")

        common = catalog.find_common_resources(min_usage=2)

        assert len(common) == 1
        # The resource ID is a hash, not the actual string
        resource_id = list(common.keys())[0]
        # Verify it's the common string by checking the resource
        resource = catalog._find_resource(resource_id)
        assert resource["value"] == "Common String"

    def test_catalog_persistence(self):
        """Test saving and loading catalog."""
        with tempfile.TemporaryDirectory() as tmpdir:
            catalog_path = Path(tmpdir) / "catalog.json"

            # Create catalog with data
            catalog1 = ResourceCatalog(catalog_path)
            catalog1.add_string_resource("test.pbl", "Test String")
            catalog1.add_image_resource("test.pbl", {"format": "png", "size": 100})
            catalog1.save_catalog()

            # Load catalog
            catalog2 = ResourceCatalog(catalog_path)
            catalog2.load_catalog()

            # Verify data
            assert len(catalog2.resources["strings"]) == 1
            assert len(catalog2.resources["images"]) == 1
            assert catalog2.find_object_resources("test.pbl")

    def test_generate_statistics(self):
        """Test statistics generation."""
        catalog = ResourceCatalog()

        # Add various resources
        catalog.add_string_resource("file1.pbl", "Short")
        catalog.add_string_resource("file2.pbl", "A longer string here")
        catalog.add_image_resource("file1.pbl", {"format": "png", "size": 1024})
        catalog.add_image_resource("file2.pbl", {"format": "bmp", "size": 2048})

        stats = catalog.generate_statistics()

        assert stats["total_resources"] == 4
        assert stats["resource_counts"]["strings"] == 2
        assert stats["resource_counts"]["images"] == 2
        assert stats["total_size"] == 3072
        assert "string_statistics" in stats
        assert stats["image_formats"]["png"] == 1
        assert stats["image_formats"]["bmp"] == 1
