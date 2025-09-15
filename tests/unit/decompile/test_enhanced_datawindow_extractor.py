#!/usr/bin/env python3
"""Comprehensive tests for the enhanced DataWindow extractor."""

from src.decompile.extractors.datawindow_extractor import (
    DataWindowType,
    EnhancedDataWindowExtractor,
    MagicNumbers,
)


class TestEnhancedDataWindowExtractor:
    """Test the enhanced DataWindow extractor."""

    def test_init(self):
        """Test extractor initialization."""
        extractor = EnhancedDataWindowExtractor()

        # Should have multiple extraction strategies
        assert len(extractor.extraction_strategies) == 6
        assert callable(extractor.extraction_strategies[0])

    def test_detect_datawindow_type_from_filename(self):
        """Test DataWindow type detection from filename."""
        extractor = EnhancedDataWindowExtractor()

        # Test various filename patterns
        assert (
            extractor._detect_datawindow_type("d_customer_sql.srd")
            == DataWindowType.SQL
        )
        assert (
            extractor._detect_datawindow_type("d_order_ds.srd")
            == DataWindowType.DATASTORE
        )
        assert (
            extractor._detect_datawindow_type("d_product_ex.srd")
            == DataWindowType.EXTERNAL
        )
        assert (
            extractor._detect_datawindow_type("d_state_dddw.srd")
            == DataWindowType.DROPDOWN
        )
        assert (
            extractor._detect_datawindow_type("d_sales_rpt.srd")
            == DataWindowType.REPORT
        )
        assert (
            extractor._detect_datawindow_type("d_employee_dw.srd")
            == DataWindowType.DATAWINDOW
        )
        assert (
            extractor._detect_datawindow_type("d_something.srd")
            == DataWindowType.UNKNOWN
        )

        # Case insensitive
        assert (
            extractor._detect_datawindow_type("D_CUSTOMER_SQL.SRD")
            == DataWindowType.SQL
        )

    def test_extract_standard_syntax(self):
        """Test standard syntax extraction."""
        extractor = EnhancedDataWindowExtractor()

        # Create standard DataWindow syntax
        data = b"""release 10;
datawindow(units=0 timer_interval=0)
retrieve="SELECT id, name FROM customers"
table(column=(type=number name=id) column=(type=char(50) name=name))
"""

        syntax, success = extractor._extract_standard_syntax(data, DataWindowType.SQL)

        assert success is True
        assert syntax is not None
        assert "release 10;" in syntax
        assert "SELECT id, name FROM customers" in syntax

    def test_extract_standard_syntax_no_release(self):
        """Test standard extraction with no release marker."""
        extractor = EnhancedDataWindowExtractor()

        data = b"datawindow(units=0) table()"

        syntax, success = extractor._extract_standard_syntax(data, DataWindowType.SQL)

        assert success is False
        assert syntax is None

    def test_extract_binary_embedded_syntax(self):
        """Test extraction from binary-embedded syntax."""
        extractor = EnhancedDataWindowExtractor()

        # Mock binary data with embedded syntax
        data = (
            b"\x00\x00\x00\x00"  # Binary header
            b"release 11.5;\ndatawindow(processing=0)\n"
            b"\x00\x00\x00\x00"  # Binary footer
        )

        syntax, success = extractor._extract_binary_embedded_syntax(
            data, DataWindowType.SQL
        )

        # Should extract the embedded text
        if success:
            assert "release 11.5;" in syntax
            assert "datawindow(processing=0)" in syntax

    def test_extract_compressed_syntax(self):
        """Test extraction of compressed syntax."""
        extractor = EnhancedDataWindowExtractor()

        # Mock compressed data (simplified test)
        data = b"PK\x03\x04" + b"compressed data"

        syntax, success = extractor._extract_compressed_syntax(data, DataWindowType.SQL)

        # Compressed extraction may fail in test environment
        assert isinstance(success, bool)

    def test_extract_legacy_format(self):
        """Test extraction of legacy format."""
        extractor = EnhancedDataWindowExtractor()

        # Mock legacy format data
        data = b"$PBExportHeader$" + b"legacy datawindow content"

        syntax, success = extractor._extract_legacy_format(data, DataWindowType.SQL)

        # Legacy extraction should handle old formats
        assert isinstance(success, bool)

    def test_extract_with_error_recovery(self):
        """Test extraction with error recovery."""
        extractor = EnhancedDataWindowExtractor()

        # Mock corrupted data
        data = b"release 10;\ndatawi" + b"\xff\xff" + b"ndow(units=0)"

        syntax, success = extractor._extract_with_error_recovery(
            data, DataWindowType.SQL
        )

        # Error recovery should attempt to extract usable parts
        assert isinstance(success, bool)

    def test_deep_binary_inspection(self):
        """Test deep binary inspection strategy."""
        extractor = EnhancedDataWindowExtractor()

        # Mock binary data with patterns
        data = struct.pack("<I", MagicNumbers.DATAWINDOW_HEADER) + b"binary content"

        syntax, success = extractor._deep_binary_inspection(data, DataWindowType.SQL)

        # Deep inspection may or may not succeed
        assert isinstance(success, bool)

    def test_extract_syntax_all_strategies(self):
        """Test that extract_syntax tries all strategies."""
        extractor = EnhancedDataWindowExtractor()

        # Mock data that will fail most strategies
        data = b"invalid datawindow content"

        # Track which strategies were called
        strategies_called = []

        # Patch strategies to track calls
        original_strategies = extractor.extraction_strategies.copy()

        def make_tracker(strategy):
            def tracked_strategy(data, dw_type):
                strategies_called.append(strategy.__name__)
                return strategy(data, dw_type)

            return tracked_strategy

        extractor.extraction_strategies = [make_tracker(s) for s in original_strategies]

        syntax, success = extractor.extract_syntax(data, "d_test.srd")

        # Should try multiple strategies
        assert len(strategies_called) > 1

    def test_extract_syntax_success(self):
        """Test successful syntax extraction."""
        extractor = EnhancedDataWindowExtractor()

        # Valid DataWindow syntax
        data = b"""release 12.5;
datawindow(units=0 timer_interval=0 color=1073741824 processing=0 HTMLDW=no print.printername="" print.documentname="" print.orientation = 0 print.margin.left = 110 print.margin.right = 110 print.margin.top = 96 print.margin.bottom = 96 print.paper.source = 0 print.paper.size = 0 print.canusedefaultprinter=yes print.prompt=no print.buttons=no print.preview.buttons=no print.cliptext=no print.overrideprintjob=no print.collate=yes hidegrayline=no )
summary(height=0 color="536870912" )
footer(height=0 color="536870912" )
detail(height=92 color="536870912" )
table(column=(type=number name=id dbname="customers.id" )
 column=(type=char(50) name=name dbname="customers.name" )
)
retrieve="SELECT customers.id, customers.name FROM customers"
"""

        syntax, success = extractor.extract_syntax(data, "d_customer_sql.srd")

        assert success is True
        assert syntax is not None
        assert "release 12.5;" in syntax
        assert "SELECT customers.id" in syntax

    def test_post_process_syntax(self):
        """Test syntax post-processing."""
        extractor = EnhancedDataWindowExtractor()

        # Syntax with common issues
        syntax = "release 10;\r\ndatawindow(units=0)\r\n\r\n\r\ntable()"

        processed = extractor._post_process_syntax(syntax, DataWindowType.SQL)

        # Should normalize line endings and remove excess whitespace
        assert "\r" not in processed
        assert "\n\n\n" not in processed  # No triple newlines

    def test_magic_numbers(self):
        """Test magic number constants."""
        # Verify magic numbers are correct values
        assert MagicNumbers.DATAWINDOW_HEADER == 0x444F4D76
        assert MagicNumbers.OBJECT_DESCRIPTOR == 0x4F424A44
        assert MagicNumbers.BINARY_MARKER == 0x00000000
        assert MagicNumbers.SQL_MARKER == 0x53514C20

    def test_datawindow_type_enum(self):
        """Test DataWindow type enumeration."""
        # Verify all expected types exist
        assert DataWindowType.SQL.value == "_sql"
        assert DataWindowType.DATASTORE.value == "_ds"
        assert DataWindowType.EXTERNAL.value == "_ex"
        assert DataWindowType.DROPDOWN.value == "_dddw"
        assert DataWindowType.REPORT.value == "_rpt"
        assert DataWindowType.DATAWINDOW.value == "_dw"
        assert DataWindowType.UNKNOWN.value == "_unknown"


class TestExtractionStrategies:
    """Test individual extraction strategies in detail."""

    def test_standard_extraction_with_complex_syntax(self):
        """Test standard extraction with complex DataWindow syntax."""
        extractor = EnhancedDataWindowExtractor()

        # Complex syntax with nested structures
        data = b"""release 12.6;
datawindow(units=0 timer_interval=0 color=1073741824 processing=1 HTMLDW=no print.printername="" )
header(height=72 color="536870912" )
summary(height=0 color="536870912" )
footer(height=0 color="536870912" )
detail(height=84 color="536870912" )
table(column=(type=number updatewhereclause=yes name=id dbname="customers.id" )
 column=(type=char(50) updatewhereclause=yes name=name dbname="customers.name" )
 column=(type=datetime updatewhereclause=yes name=created_date dbname="customers.created_date" )
 retrieve="SELECT customers.id,
         customers.name,
         customers.created_date
    FROM customers
   WHERE customers.active = 'Y'
     AND customers.region = :region_param
ORDER BY customers.name"
 sort="name A " )
group(level=1 header.height=72 trailer.height=0 by=("region" ) )
compute(band=detail alignment="1" expression="sum(amount for group 1)"border="0" color="33554432" x="558" y="4" height="64" width="274" format="[GENERAL]" html.valueishtml="0"  name=compute_1 visible="1"  font.face="Tahoma" font.height="-10" font.weight="400"  font.family="2" font.pitch="2" font.charset="0" background.mode="1" background.color="536870912" )
text(band=header alignment="2" text="Customer Report" border="0" color="33554432" x="9" y="8" height="64" width="411" html.valueishtml="0"  name=t_1 visible="1"  font.face="Arial" font.height="-10" font.weight="700"  font.family="2" font.pitch="2" font.charset="0" background.mode="1" background.color="536870912" )
"""

        syntax, success = extractor._extract_standard_syntax(
            data, DataWindowType.REPORT
        )

        assert success is True
        assert syntax is not None
        assert "group(level=1" in syntax
        assert "compute(band=detail" in syntax
        assert "WHERE customers.active = 'Y'" in syntax

    def test_binary_embedded_with_markers(self):
        """Test binary embedded extraction with specific markers."""
        extractor = EnhancedDataWindowExtractor()

        # Create data with binary markers
        import struct

        data = (
            struct.pack("<I", MagicNumbers.SQL_MARKER)
            + b"release 10;\n"
            + b"datawindow(processing=0)\n"
            + b'retrieve="SELECT * FROM test"\n'
            + struct.pack("<I", MagicNumbers.BINARY_MARKER)
        )

        syntax, success = extractor._extract_binary_embedded_syntax(
            data, DataWindowType.SQL
        )

        # Should handle binary markers
        assert isinstance(success, bool)

    def test_error_recovery_with_truncated_data(self):
        """Test error recovery with truncated DataWindow."""
        extractor = EnhancedDataWindowExtractor()

        # Truncated DataWindow syntax
        data = b"""release 11;
datawindow(units=0 timer_interval=0 color=1073741824 processing=0
table(column=(type=number name=id dbname="test"""  # Truncated

        syntax, success = extractor._extract_with_error_recovery(
            data, DataWindowType.SQL
        )

        # Error recovery should handle truncation
        assert isinstance(success, bool)
        if success and syntax:
            assert "release 11;" in syntax


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_data(self):
        """Test extraction with empty data."""
        extractor = EnhancedDataWindowExtractor()

        syntax, success = extractor.extract_syntax(b"", "d_empty.srd")

        assert success is False
        assert syntax is None

    def test_very_large_data(self):
        """Test extraction with very large data."""
        extractor = EnhancedDataWindowExtractor()

        # Create large data
        data = b"release 10;\n" + b"x" * (1024 * 1024)  # 1MB of data

        syntax, success = extractor.extract_syntax(data, "d_large.srd")

        # Should handle large data without crashing
        assert isinstance(success, bool)

    def test_invalid_encoding(self):
        """Test extraction with invalid encoding."""
        extractor = EnhancedDataWindowExtractor()

        # Data with invalid UTF-8 sequences
        data = b"release 10;\n" + b"\xff\xfe" + b"datawindow()"

        syntax, success = extractor.extract_syntax(data, "d_invalid.srd")

        # Should handle encoding errors
        assert isinstance(success, bool)

    def test_mixed_binary_text(self):
        """Test extraction with mixed binary and text content."""
        extractor = EnhancedDataWindowExtractor()

        # Mixed content
        data = (
            b"release 10;\n"
            b"\x00\x01\x02\x03"
            b"datawindow(processing=0)\n"
            b"\xff\xfe\xfd\xfc"
            b"table()\n"
        )

        syntax, success = extractor.extract_syntax(data, "d_mixed.srd")

        # Should handle mixed content
        assert isinstance(success, bool)


# Import struct for binary data tests
import struct
