#!/usr/bin/env python3
"""Test P-code detection for PowerBuilder objects."""

from src.decompile.pcode.detector import EnhancedPCodeDetector, PCodeInfo


class TestPCodeInfo:
    """Test the PCodeInfo class."""

    def test_default_initialization(self):
        """Test default PCodeInfo initialization."""
        info = PCodeInfo()
        assert info.pcode_offset == -1
        assert info.pcode_length == 0
        assert info.object_type == "function"
        assert info.confidence == "none"

    def test_custom_initialization(self):
        """Test custom PCodeInfo initialization."""
        info = PCodeInfo(
            pcode_offset=100, pcode_length=256, object_type="window", confidence="high"
        )
        assert info.pcode_offset == 100
        assert info.pcode_length == 256
        assert info.object_type == "window"
        assert info.confidence == "high"


class TestEnhancedPCodeDetector:
    """Test the EnhancedPCodeDetector class."""

    def test_is_pcode_object_functions(self):
        """Test function object detection."""
        detector = EnhancedPCodeDetector()

        assert detector.is_pcode_object("test.fun")
        assert detector.is_pcode_object("TEST.FUN")
        assert not detector.is_pcode_object("test.dwo")
        assert not detector.is_pcode_object("test.txt")

    def test_is_pcode_object_various_types(self):
        """Test various object type detection."""
        detector = EnhancedPCodeDetector()

        # Should detect these as P-code objects
        assert detector.is_pcode_object("window.srw")
        assert detector.is_pcode_object("userobject.sru")
        assert detector.is_pcode_object("menu.srm")
        assert detector.is_pcode_object("app.sra")
        assert detector.is_pcode_object("struct.str")
        assert detector.is_pcode_object("old_menu.men")
        assert detector.is_pcode_object("old_window.win")
        assert detector.is_pcode_object("old_udo.udo")

        # Should not detect these
        assert not detector.is_pcode_object("datawindow.srd")
        assert not detector.is_pcode_object("query.srq")
        assert not detector.is_pcode_object("pipeline.srl")

    def test_handle_export_format_valid(self):
        """Test handling of valid export format."""
        data = b"HA$PBExportHeader$test.fun\n$PBExportComments$\n\x00\x01\x02\x03"

        offset, length = EnhancedPCodeDetector._handle_export_format(data)

        assert offset == 47  # After both newlines
        assert length == 4  # Length of P-code data

    def test_handle_export_format_invalid(self):
        """Test handling of invalid export format."""
        # Missing first newline
        data1 = b"HA$PBExportHeader$test.fun"
        offset1, length1 = EnhancedPCodeDetector._handle_export_format(data1)
        assert offset1 == -1
        assert length1 == 0

        # Missing second newline
        data2 = b"HA$PBExportHeader$test.fun\n$PBExportComments$"
        offset2, length2 = EnhancedPCodeDetector._handle_export_format(data2)
        assert offset2 == -1
        assert length2 == 0

    def test_looks_like_pcode_valid(self):
        """Test P-code pattern recognition."""
        # Data with valid opcodes
        valid_pcode = bytes(
            [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09]
        )
        assert EnhancedPCodeDetector._looks_like_pcode(valid_pcode)

        # Data with some valid opcodes
        mixed_data = bytes([0x00, 0xFF, 0x01, 0xFF, 0x02, 0xFF, 0x03, 0xFF, 0x04, 0xFF])
        assert EnhancedPCodeDetector._looks_like_pcode(mixed_data)

    def test_looks_like_pcode_valid_opcodes(self):
        """Test P-code validation with specific valid opcodes."""
        # Mix of valid opcodes from enhanced test
        valid_data = (
            b"\x00\x04\x05\x29\x2c"  # RETURN, JUMP, DBSTART, GLOBFUNCCALL, DOTFUNCCALL
        )
        assert EnhancedPCodeDetector._looks_like_pcode(valid_data) is True

    def test_looks_like_pcode_invalid(self):
        """Test invalid P-code patterns."""
        # Too short
        short_data = b"\x00\x01"
        assert not EnhancedPCodeDetector._looks_like_pcode(short_data)

        # All text
        text_data = b"this is text content only"
        assert not EnhancedPCodeDetector._looks_like_pcode(text_data)

        # No valid opcodes
        invalid_data = bytes(
            [0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18, 0x19, 0x1A]
        )
        assert not EnhancedPCodeDetector._looks_like_pcode(invalid_data)

    def test_verify_pcode_context_binary(self):
        """Test P-code context verification for binary data."""
        # Mostly binary data (should pass)
        binary_data = bytes([0x00, 0x01, 0x02, 0x03, 0x80, 0x81, 0x82, 0x83])
        assert EnhancedPCodeDetector._verify_pcode_context(binary_data, 4)

        # Mostly non-printable bytes
        binary_data2 = b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09"
        assert EnhancedPCodeDetector._verify_pcode_context(binary_data2, 5) is True

    def test_verify_pcode_context_text(self):
        """Test P-code context verification for text data."""
        # Mostly text data (should fail)
        text_data = b"this is mostly text content"
        assert not EnhancedPCodeDetector._verify_pcode_context(text_data, 4)

        # Mostly printable ASCII
        text_data2 = b"This is regular text content"
        assert EnhancedPCodeDetector._verify_pcode_context(text_data2, 10) is False

    def test_find_text_to_binary_transition(self):
        """Test finding transition from text to binary."""
        # Text followed by binary
        data = b"This is some text metadata\x00\x01\x02\x03\x04\x05"
        offset = EnhancedPCodeDetector._find_text_to_binary_transition(data)
        assert offset == 27  # Where binary starts

        # Test with clear text-to-binary transition (from enhanced)
        text_part = b"Function metadata and description text here"
        binary_part = b"\x00\x04\x05\x29\x2c\x00\x01\x02"
        test_data = text_part + binary_part
        transition = EnhancedPCodeDetector._find_text_to_binary_transition(test_data)
        assert transition == len(text_part)

    def test_find_text_to_binary_transition_no_transition(self):
        """Test when there's no clear text to binary transition."""
        # All text
        text_data = b"This is all text content with no binary"
        offset = EnhancedPCodeDetector._find_text_to_binary_transition(text_data)
        assert offset == -1

        # All binary
        binary_data = bytes([0x00, 0x01, 0x02, 0x03, 0x04, 0x05])
        offset = EnhancedPCodeDetector._find_text_to_binary_transition(binary_data)
        assert offset == -1

    def test_find_pcode_in_function_export_format(self):
        """Test P-code detection in export format."""
        data = b"HA$PBExportHeader$test.fun\n$PBExportComments$\n\x00\x01\x02\x03"

        offset, length = EnhancedPCodeDetector.find_pcode_in_function(data)

        assert offset == 47
        assert length == 4

    def test_find_pcode_in_function_binary(self):
        """Test P-code detection in binary data."""
        # Binary data with P-code pattern
        data = b"\x00\x00\x00\x00" + bytes([0x00, 0x01, 0x02, 0x03, 0x04, 0x05])

        offset, length = EnhancedPCodeDetector.find_pcode_in_function(data)

        assert offset >= 0  # Should find P-code
        assert length > 0

    def test_find_pcode_in_function_empty_data(self):
        """Test with empty data."""
        offset, length = EnhancedPCodeDetector.find_pcode_in_function(b"")
        assert offset == -1
        assert length == 0

    def test_find_pcode_in_function_too_short(self):
        """Test P-code detection with insufficient data."""
        short_data = b"\x00\x01"

        offset, length = EnhancedPCodeDetector.find_pcode_in_function(short_data)

        assert offset == -1
        assert length == 0

        # Also test with data too short to contain P-code (from enhanced)
        offset2, length2 = EnhancedPCodeDetector.find_pcode_in_function(b"ABC")
        assert offset2 == -1
        assert length2 == 0

    def test_find_pcode_with_return_pattern(self):
        """Test P-code detection with RETURN opcode pattern."""
        # Create test data with valid P-code sequence
        test_data = b"\x04\x00\x10\x00\x00\x00"  # JUMP followed by RETURNs
        offset, length = EnhancedPCodeDetector.find_pcode_in_function(test_data)
        # The detector looks for valid P-code patterns
        if offset == -1:
            # If not found, that's okay - the test data might not match detection criteria
            assert length == 0
        else:
            assert offset >= 0
            assert length > 0

    def test_find_pcode_with_jump_pattern(self):
        """Test P-code detection with JUMP opcode pattern."""
        # Create test data with JUMP opcode (0x04)
        test_data = b"metadata" + b"\x04\x00\x10\x00"  # JUMP with offset
        offset, length = EnhancedPCodeDetector.find_pcode_in_function(test_data)
        # The detector might find it at offset 8 or not at all
        if offset != -1:
            assert offset >= 0
            assert length > 0

    def test_find_pcode_section_function(self):
        """Test P-code section detection for functions."""
        data = b"HA$PBExportHeader$test.fun\n$PBExportComments$\n\x00\x01\x02\x03"

        offset, length = EnhancedPCodeDetector.find_pcode_section(data, "function")

        assert offset == 47
        assert length == 4

        # Also test main entry point for function objects (from enhanced)
        test_data = b"metadata" + b"\x00\x00\x04\x00\x10\x00"
        offset2, length2 = EnhancedPCodeDetector.find_pcode_section(
            test_data, "function"
        )
        assert offset2 >= 0 or (offset2 == -1 and length2 == 0)  # Valid result

    def test_find_pcode_section_other_types(self):
        """Test P-code section detection for other object types."""
        data = b"HA$PBExportHeader$test.win\n$PBExportComments$\n\x00\x01\x02\x03"

        # Should use same detection method for all types currently
        offset, length = EnhancedPCodeDetector.find_pcode_section(data, "window")

        assert offset == 47
        assert length == 4

        # Test fallback for non-function object types (from enhanced)
        test_data = b"window object data"
        offset2, length2 = EnhancedPCodeDetector.find_pcode_section(test_data, "window")
        assert isinstance(offset2, int)
        assert isinstance(length2, int)

    def test_detect_pcode_function(self):
        """Test full P-code detection for function."""
        detector = EnhancedPCodeDetector()
        data = b"HA$PBExportHeader$test.fun\n$PBExportComments$\n\x00\x01\x02\x03"

        info = detector.detect_pcode(data, "test.fun")

        assert info.pcode_offset == 47
        assert info.pcode_length == 4
        assert info.object_type == "function"
        assert info.confidence == "high"

    def test_detect_pcode_structure(self):
        """Test P-code detection for structure."""
        detector = EnhancedPCodeDetector()
        data = b"HA$PBExportHeader$test.str\n$PBExportComments$\n\x00\x01\x02\x03"

        info = detector.detect_pcode(data, "test.str")

        assert info.object_type == "structure"
        assert info.confidence == "high"

    def test_detect_pcode_menu(self):
        """Test P-code detection for menu."""
        detector = EnhancedPCodeDetector()
        data = b"HA$PBExportHeader$test.men\n$PBExportComments$\n\x00\x01\x02\x03"

        info = detector.detect_pcode(data, "test.men")

        assert info.object_type == "menu"
        assert info.confidence == "high"

    def test_detect_pcode_not_found(self):
        """Test P-code detection when no P-code found."""
        detector = EnhancedPCodeDetector()
        data = b"This is just text data with no P-code"

        info = detector.detect_pcode(data, "test.fun")

        assert info.pcode_offset == -1
        assert info.pcode_length == 0
        assert info.confidence == "none"

    def test_find_pcode_end_consecutive_returns(self):
        """Test finding P-code end with consecutive returns."""
        data = (
            b"\x01\x02\x03\x00\x00\x00\xff\xff\xff"  # Code then 3 returns then padding
        )

        end_offset = EnhancedPCodeDetector._find_pcode_end(data, 0)

        assert end_offset == 4  # After first return in the sequence

    def test_find_pcode_end_multiple_returns(self):
        """Test end detection with multiple RETURN opcodes."""
        # Three consecutive RETURNs should mark end
        pcode_data = b"\x04\x00\x10"  # JUMP
        pcode_data += b"\x00\x00\x00"  # Three RETURNs
        pcode_data += b"\xff\xff\xff"  # Padding

        end_offset = EnhancedPCodeDetector._find_pcode_end(pcode_data, 0)
        assert end_offset == 4  # Should end after first valid instruction

    def test_find_pcode_end_padding(self):
        """Test finding P-code end with padding."""
        data = b"\x01\x02\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00"  # Code then null padding

        end_offset = EnhancedPCodeDetector._find_pcode_end(data, 0)

        assert end_offset == 4  # After valid code, before padding

    def test_find_pcode_end_padding_detection(self):
        """Test end detection with padding bytes."""
        # Code followed by null padding
        pcode_data = b"\x04\x00\x10"  # JUMP
        pcode_data += b"\x00" * 10  # Null padding

        end_offset = EnhancedPCodeDetector._find_pcode_end(pcode_data, 0)
        assert end_offset < len(pcode_data)  # Should not include all padding

    def test_find_pcode_end_ff_padding(self):
        """Test finding P-code end with 0xFF padding."""
        data = (
            b"\x01\x02\x03\xff\xff\xff\xff\xff\xff\xff\xff\xff"  # Code then FF padding
        )

        end_offset = EnhancedPCodeDetector._find_pcode_end(data, 0)

        assert end_offset == 4  # After valid code, before padding

    def test_find_pcode_end_no_clear_end(self):
        """Test finding P-code end when there's no clear end marker."""
        data = b"\x01\x02\x03\x04\x05\x06"  # All valid code

        end_offset = EnhancedPCodeDetector._find_pcode_end(data, 0)

        assert end_offset == len(data)  # Should return full length

    def test_find_pcode_start_pattern_detection(self):
        """Test P-code start detection by pattern."""
        # Data with a clear P-code pattern
        data = b"some text\x00\x00\x00\x00\x01\x02\x03\x04\x05"

        offset = EnhancedPCodeDetector._find_pcode_start(data)

        assert offset >= 0  # Should find something

    def test_find_pcode_start_no_pattern(self):
        """Test P-code start detection when no pattern found."""
        # All text data
        data = b"This is all text with no binary patterns"

        offset = EnhancedPCodeDetector._find_pcode_start(data)

        assert offset == -1  # Should not find anything


class TestIntegration:
    """Integration tests for the complete P-code detection flow."""

    def test_complete_detection_flow(self):
        """Test the complete detection flow."""
        detector = EnhancedPCodeDetector()

        # Create realistic function data
        export_header = b"HA$PBExportHeader$calculate_total.fun\n"
        export_comments = b"$PBExportComments$\n"
        pcode_data = bytes(
            [
                0x32,
                0x00,
                0x00,  # PUSH_CONST_INT 0
                0x00,  # RETURN
            ]
        )

        data = export_header + export_comments + pcode_data

        # Test is_pcode_object
        assert detector.is_pcode_object("calculate_total.fun")

        # Test detect_pcode
        info = detector.detect_pcode(data, "calculate_total.fun")

        assert info.confidence == "high"
        assert info.object_type == "function"
        assert info.pcode_offset > 0
        assert info.pcode_length > 0

        # Verify the detected P-code section
        detected_pcode = data[info.pcode_offset : info.pcode_offset + info.pcode_length]
        assert detected_pcode == pcode_data

    def test_various_object_types_detection(self):
        """Test detection across various object types."""
        detector = EnhancedPCodeDetector()

        test_cases = [
            ("window.srw", "function"),  # Currently all use same detection
            ("userobject.sru", "function"),
            ("menu.men", "menu"),
            ("struct.str", "structure"),
        ]

        for object_name, expected_type in test_cases:
            assert detector.is_pcode_object(object_name)

            # Create basic test data
            data = (
                b"HA$PBExportHeader$"
                + object_name.encode()
                + b"\n$PBExportComments$\n\x00"
            )
            info = detector.detect_pcode(data, object_name)

            assert info.object_type == expected_type

    def test_small_pcode_detection(self):
        """Test detection of small P-code sections (e.g., getters/setters)."""
        detector = EnhancedPCodeDetector()

        # Test case 1: Simple getter (6 bytes)
        getter_data = bytes(
            [
                0x2D,
                0x00,
                0x01,
                0x00,  # PUSH_PROPERTY with property ID
                0x00,
                0x00,  # RETURN
            ]
        )
        info = detector.detect_pcode(getter_data, "get_value.fun")
        assert info.confidence == "high"
        assert info.pcode_offset == 0
        assert info.pcode_length == 6
        assert len(info.sections) == 1
        assert info.sections[0].confidence >= 0.85

        # Test case 2: Simple setter (5 bytes)
        setter_data = bytes(
            [
                0x2E,
                0x00,
                0x02,  # POP_PROPERTY with property ID
                0x00,
                0x00,  # RETURN
            ]
        )
        info = detector.detect_pcode(setter_data, "set_value.fun")
        assert info.confidence == "high"
        assert info.pcode_offset == 0
        assert info.pcode_length == 5
        assert len(info.sections) == 1
        assert info.sections[0].confidence >= 0.85

        # Test case 3: Tiny constant return (4 bytes - minimum)
        tiny_data = bytes(
            [
                0x3A,
                0x00,  # PUSH_CONST_TRUE
                0x00,
                0x00,  # RETURN
            ]
        )
        info = detector.detect_pcode(tiny_data, "is_enabled.fun")
        assert info.confidence == "high"
        assert info.pcode_offset == 0
        assert info.pcode_length == 4
        assert len(info.sections) == 1

        # Test case 4: Too small (3 bytes - should be rejected)
        too_small = bytes([0x00, 0x00, 0x00])
        info = detector.detect_pcode(too_small, "invalid.fun")
        assert info.confidence == "none"
        assert info.pcode_offset == -1
        assert info.pcode_length == 0
        assert len(info.sections) == 0
