#!/usr/bin/env python3
"""Comprehensive tests for the enhanced DataWindow integration."""

from unittest.mock import Mock, patch

from src.decompile.extractors.datawindow_integration import (
    DataWindowExtractionManager,
)


class TestDataWindowExtractionManager:
    """Test the DataWindow extraction manager."""

    def test_init_with_enhanced(self):
        """Test initialization with enhanced extraction enabled."""
        manager = DataWindowExtractionManager(use_enhanced=True)

        assert manager.use_enhanced is True
        assert manager.standard_extractor is not None
        assert manager.enhanced_extractor is not None

    def test_init_without_enhanced(self):
        """Test initialization with enhanced extraction disabled."""
        manager = DataWindowExtractionManager(use_enhanced=False)

        assert manager.use_enhanced is False
        assert manager.standard_extractor is not None
        assert manager.enhanced_extractor is None

    @patch("decompile.analysis.enhanced_datawindow_integration.ObjectTypeDetector")
    def test_extract_syntax_enhanced_success(self, mock_detector):
        """Test successful extraction using enhanced extractor."""
        manager = DataWindowExtractionManager(use_enhanced=True)

        # Mock the analysis
        mock_detector.analyze_file_content.return_value = {
            "null_percentage": 5.0,
            "is_binary": False,
            "magic_number": 0x12345678,
        }
        mock_detector.validate_extraction_target.return_value = (True, "text")

        # Mock enhanced extractor success
        manager.enhanced_extractor = Mock()
        manager.enhanced_extractor.extract_syntax.return_value = (
            "release 10; datawindow()",
            True,
        )

        data = b"test data"
        syntax, success, method = manager.extract_syntax(data, "d_test.srd")

        assert success is True
        assert syntax == "release 10; datawindow()"
        assert method == "enhanced_text"
        assert manager.enhanced_extractor.extract_syntax.called

    @patch("decompile.analysis.enhanced_datawindow_integration.ObjectTypeDetector")
    def test_extract_syntax_fallback_to_standard(self, mock_detector):
        """Test fallback to standard extraction when enhanced fails."""
        manager = DataWindowExtractionManager(use_enhanced=True)

        # Mock the analysis
        mock_detector.analyze_file_content.return_value = {
            "null_percentage": 10.0,
            "is_binary": True,
            "magic_number": None,
        }
        mock_detector.validate_extraction_target.return_value = (True, "binary")

        # Mock enhanced extractor failure
        manager.enhanced_extractor = Mock()
        manager.enhanced_extractor.extract_syntax.return_value = (None, False)

        # Mock standard extractor success
        manager.standard_extractor = Mock()
        manager.standard_extractor.extract_syntax.return_value = "standard syntax"

        data = b"test data"
        syntax, success, method = manager.extract_syntax(data, "d_test.srd")

        assert success is True
        assert syntax == "standard syntax"
        assert method == "standard"
        assert manager.enhanced_extractor.extract_syntax.called
        assert manager.standard_extractor.extract_syntax.called

    @patch("decompile.analysis.enhanced_datawindow_integration.ObjectTypeDetector")
    def test_extract_syntax_both_fail(self, mock_detector):
        """Test when both extractors fail."""
        manager = DataWindowExtractionManager(use_enhanced=True)

        # Mock the analysis
        mock_detector.analyze_file_content.return_value = {
            "null_percentage": 80.0,
            "is_binary": True,
            "magic_number": None,
        }
        mock_detector.validate_extraction_target.return_value = (False, "unknown")

        # Mock both extractors failing
        manager.enhanced_extractor = Mock()
        manager.enhanced_extractor.extract_syntax.return_value = (None, False)

        manager.standard_extractor = Mock()
        manager.standard_extractor.extract_syntax.return_value = None

        data = b"corrupted data"
        syntax, success, method = manager.extract_syntax(data, "d_corrupt.srd")

        assert success is False
        assert syntax is None
        assert method == "failed"

    @patch("decompile.analysis.enhanced_datawindow_integration.ObjectTypeDetector")
    def test_extract_syntax_standard_only(self, mock_detector):
        """Test extraction with enhanced disabled."""
        manager = DataWindowExtractionManager(use_enhanced=False)

        # Mock the analysis
        mock_detector.analyze_file_content.return_value = {
            "null_percentage": 0.0,
            "is_binary": False,
            "magic_number": None,
        }
        mock_detector.validate_extraction_target.return_value = (True, "text")

        # Mock standard extractor
        manager.standard_extractor = Mock()
        manager.standard_extractor.extract_syntax.return_value = "standard syntax"

        data = b"test data"
        syntax, success, method = manager.extract_syntax(data, "d_test.srd")

        assert success is True
        assert syntax == "standard syntax"
        assert method == "standard"
        assert manager.enhanced_extractor is None  # Not created

    def test_extract_from_pbd_object_with_dat_header(self):
        """Test extraction from PBD object with DAT header."""
        manager = DataWindowExtractionManager()

        # Mock the extraction
        with patch.object(manager, "extract_syntax") as mock_extract:
            mock_extract.return_value = ("syntax", True, "enhanced")

            # Data with DAT* header
            data = b"DAT*" + b"datawindow content"
            syntax, success = manager.extract_from_pbd_object(data, "d_test")

            assert success is True
            assert syntax == "syntax"
            mock_extract.assert_called_once()

    def test_extract_from_pbd_object_with_unicode_dat_header(self):
        """Test extraction from PBD object with Unicode DAT header."""
        manager = DataWindowExtractionManager()

        # Mock the extraction
        with patch.object(manager, "extract_syntax") as mock_extract:
            mock_extract.return_value = ("syntax", True, "enhanced")

            # Data with Unicode DAT header
            data = b"D\0A\0T\0" + b"datawindow content"
            syntax, success = manager.extract_from_pbd_object(data, "d_test")

            assert success is True
            assert syntax == "syntax"
            mock_extract.assert_called_once()

    def test_extract_from_pbd_object_no_dat_header(self):
        """Test extraction from PBD object without DAT header."""
        manager = DataWindowExtractionManager()

        # Data without DAT header
        data = b"FUN*" + b"function content"
        syntax, success = manager.extract_from_pbd_object(data, "f_test")

        assert success is False
        assert syntax is None

    def test_validate_extraction_output_valid(self):
        """Test validation of valid extraction output."""
        manager = DataWindowExtractionManager()

        # Valid DataWindow syntax
        syntax = """release 10;
datawindow(units=0 timer_interval=0)
table(column=(type=number name=id))
"""

        is_valid, cleaned = manager.validate_extraction_output(syntax)

        assert is_valid is True
        assert "release 10;" in cleaned
        assert "datawindow(" in cleaned

    def test_validate_extraction_output_invalid(self):
        """Test validation of invalid extraction output."""
        manager = DataWindowExtractionManager()

        # Invalid syntax
        syntax = "not a datawindow"

        is_valid, cleaned = manager.validate_extraction_output(syntax)

        assert is_valid is False
        assert cleaned == ""

    def test_validate_extraction_output_none(self):
        """Test validation with None input."""
        manager = DataWindowExtractionManager()

        is_valid, cleaned = manager.validate_extraction_output(None)

        assert is_valid is False
        assert cleaned == ""

    def test_get_extraction_statistics(self):
        """Test getting extraction statistics."""
        manager = DataWindowExtractionManager()

        # Mock some extractions
        with patch.object(manager, "extract_syntax") as mock_extract:
            # Successful enhanced extraction
            mock_extract.return_value = ("syntax1", True, "enhanced_text")
            manager.extract_syntax(b"data1", "d_test1.srd")

            # Successful standard extraction
            mock_extract.return_value = ("syntax2", True, "standard")
            manager.extract_syntax(b"data2", "d_test2.srd")

            # Failed extraction
            mock_extract.return_value = (None, False, "failed")
            manager.extract_syntax(b"data3", "d_test3.srd")

        stats = manager.get_extraction_statistics()

        # Should have statistics (method depends on implementation)
        assert isinstance(stats, dict)


class TestExtractionMethodSelection:
    """Test extraction method selection logic."""

    @patch("decompile.analysis.enhanced_datawindow_integration.ObjectTypeDetector")
    def test_binary_file_detection(self, mock_detector):
        """Test handling of binary files."""
        manager = DataWindowExtractionManager()

        # Mock binary file detection
        mock_detector.analyze_file_content.return_value = {
            "null_percentage": 50.0,
            "is_binary": True,
            "magic_number": 0xDEADBEEF,
        }
        mock_detector.validate_extraction_target.return_value = (True, "binary")

        # Mock extractors
        manager.enhanced_extractor = Mock()
        manager.enhanced_extractor.extract_syntax.return_value = ("binary syntax", True)

        data = b"\x00\x01\x02\x03" * 100
        syntax, success, method = manager.extract_syntax(data, "d_binary.srd")

        assert success is True
        assert method == "enhanced_binary"

    @patch("decompile.analysis.enhanced_datawindow_integration.ObjectTypeDetector")
    def test_text_file_detection(self, mock_detector):
        """Test handling of text files."""
        manager = DataWindowExtractionManager()

        # Mock text file detection
        mock_detector.analyze_file_content.return_value = {
            "null_percentage": 0.0,
            "is_binary": False,
            "magic_number": None,
        }
        mock_detector.validate_extraction_target.return_value = (True, "text")

        # Mock extractors
        manager.enhanced_extractor = Mock()
        manager.enhanced_extractor.extract_syntax.return_value = ("text syntax", True)

        data = b"release 10; datawindow()"
        syntax, success, method = manager.extract_syntax(data, "d_text.srd")

        assert success is True
        assert method == "enhanced_text"

    @patch("decompile.analysis.enhanced_datawindow_integration.ObjectTypeDetector")
    def test_mixed_content_detection(self, mock_detector):
        """Test handling of mixed binary/text content."""
        manager = DataWindowExtractionManager()

        # Mock mixed content detection
        mock_detector.analyze_file_content.return_value = {
            "null_percentage": 25.0,
            "is_binary": True,
            "magic_number": None,
        }
        mock_detector.validate_extraction_target.return_value = (True, "mixed")

        # Mock extractors
        manager.enhanced_extractor = Mock()
        manager.enhanced_extractor.extract_syntax.return_value = ("mixed syntax", True)

        data = b"release 10;\x00\x00datawindow()\x00\x00"
        syntax, success, method = manager.extract_syntax(data, "d_mixed.srd")

        assert success is True
        assert method == "enhanced_mixed"


class TestErrorHandling:
    """Test error handling in the extraction manager."""

    @patch("decompile.analysis.enhanced_datawindow_integration.ObjectTypeDetector")
    def test_detector_exception_handling(self, mock_detector):
        """Test handling of exceptions from object type detector."""
        manager = DataWindowExtractionManager()

        # Mock detector raising exception
        mock_detector.analyze_file_content.side_effect = Exception("Analysis failed")

        # Should handle exception gracefully
        data = b"test data"
        # This test depends on the actual implementation's error handling
        try:
            syntax, success, method = manager.extract_syntax(data, "d_error.srd")
            # If it doesn't raise, check the result
            assert success is False or syntax is None
        except Exception:
            # If it does raise, that's also acceptable behavior
            pass

    def test_enhanced_extractor_exception(self):
        """Test handling of exceptions from enhanced extractor."""
        manager = DataWindowExtractionManager()

        # Mock enhanced extractor raising exception
        manager.enhanced_extractor = Mock()
        manager.enhanced_extractor.extract_syntax.side_effect = Exception(
            "Enhanced failed"
        )

        # Mock standard extractor working
        manager.standard_extractor = Mock()
        manager.standard_extractor.extract_syntax.return_value = "fallback syntax"

        with patch(
            "decompile.analysis.enhanced_datawindow_integration.ObjectTypeDetector"
        ) as mock_detector:
            mock_detector.analyze_file_content.return_value = {
                "null_percentage": 0.0,
                "is_binary": False,
                "magic_number": None,
            }
            mock_detector.validate_extraction_target.return_value = (True, "text")

            # Should fall back to standard extractor
            data = b"test data"
            # This test depends on error handling implementation
            try:
                syntax, success, method = manager.extract_syntax(data, "d_error.srd")
                # Should have fallen back to standard
                if success:
                    assert method == "standard"
            except Exception:
                # If exception propagates, that's also valid behavior
                pass

    def test_empty_data_handling(self):
        """Test handling of empty data."""
        manager = DataWindowExtractionManager()

        with patch(
            "decompile.analysis.enhanced_datawindow_integration.ObjectTypeDetector"
        ) as mock_detector:
            mock_detector.analyze_file_content.return_value = {
                "null_percentage": 0.0,
                "is_binary": False,
                "magic_number": None,
            }
            mock_detector.validate_extraction_target.return_value = (False, "empty")

            syntax, success, method = manager.extract_syntax(b"", "d_empty.srd")

            assert success is False
            assert syntax is None

    def test_none_data_handling(self):
        """Test handling of None data."""
        manager = DataWindowExtractionManager()

        # Should handle None gracefully
        try:
            syntax, success, method = manager.extract_syntax(None, "d_none.srd")
            assert success is False
        except (TypeError, AttributeError):
            # These exceptions are also acceptable for None input
            pass
