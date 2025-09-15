#!/usr/bin/env python3
"""Test complete blob/binary data type support integration."""

import pytest

from src.generate.converters.data.blobs import BlobConverter
from src.generate.converters.flutter.datawindows import (
    DataWindowColumn,
    DataWindowConverter,
)
from src.generate.converters.flutter.models import TypeConverter
from src.generate.converters.utils.expressions import ExpressionConverter


class TestBlobIntegration:
    """Test blob support across all converters."""

    @pytest.fixture
    def converters(self):
        """Create converter instances."""
        type_converter = TypeConverter()
        expr_converter = ExpressionConverter(type_converter)
        blob_converter = BlobConverter()
        dw_converter = DataWindowConverter(
            type_converter, expr_converter, blob_converter
        )

        return {
            "type": type_converter,
            "expr": expr_converter,
            "blob": blob_converter,
            "dw": dw_converter,
        }

    def test_datawindow_blob_column_metadata(self, converters):
        """Test DataWindow blob column gets proper metadata."""
        dw_syntax = """
        datawindow(
            processing=0
        )
        table(
            column=(type=char(50) name=employee_name)
            column=(type=blob name=employee_photo)
            column=(type=blob name=resume_document)
        )
        """

        dw_def = converters["dw"].convert_datawindow(dw_syntax, "d_employee")

        # Check columns
        assert len(dw_def.columns) == 3

        # Check photo column
        photo_col = next(col for col in dw_def.columns if col.name == "employee_photo")
        assert photo_col.blob_metadata is not None
        assert photo_col.blob_metadata["usage"] == "image"
        assert photo_col.blob_metadata["display_widget"] == "EmployeePhotoBlobDisplay"

        # Check document column
        doc_col = next(col for col in dw_def.columns if col.name == "resume_document")
        assert doc_col.blob_metadata is not None
        assert doc_col.blob_metadata["usage"] == "document"
        assert doc_col.blob_metadata["display_widget"] == "ResumeDocumentBlobDisplay"

        # Check blob columns method
        blob_cols = dw_def.get_blob_columns()
        assert len(blob_cols) == 2

    def test_datawindow_blob_imports(self, converters):
        """Test DataWindow with blob columns generates correct imports."""
        # Create a DataWindow definition with blob column
        photo_col = DataWindowColumn(
            name="profile_pic",
            label="Profile Picture",
            data_type="Uint8List",
            blob_metadata={"usage": "image", "display_widget": "ProfilePicBlobDisplay"},
        )

        dw_def = converters["dw"].convert_datawindow("", "d_test")
        dw_def.columns = [photo_col]

        imports = dw_def._get_imports()

        assert "import 'dart:typed_data';" in imports
        assert "import 'dart:convert';" in imports
        assert "import 'dart:io';" in imports
        assert "import 'package:path_provider/path_provider.dart';" in imports
        assert "import '../widgets/profile_pic_blob_display.dart';" in imports

    def test_blob_handling_code_generation(self, converters):
        """Test blob handling code generation."""
        # Create columns with blob metadata
        photo_col = DataWindowColumn(
            name="photo",
            label="Photo",
            data_type="Uint8List",
            blob_metadata={"usage": "image", "display_widget": "PhotoBlobDisplay"},
        )

        doc_col = DataWindowColumn(
            name="attachment",
            label="Attachment",
            data_type="Uint8List",
            blob_metadata={
                "usage": "document",
                "display_widget": "AttachmentBlobDisplay",
            },
        )

        dw_def = converters["dw"].convert_datawindow("", "d_test")
        dw_def.columns = [photo_col, doc_col]

        # Generate blob handling code
        blob_code = dw_def.generate_blob_handling_code(converters["blob"])

        # Check repository methods
        assert "Future<Uint8List> getPhoto()" in blob_code["repository_methods"]
        assert "Stream<Uint8List> getPhotoStream()" in blob_code["repository_methods"]
        assert "Future<Uint8List> getAttachment()" in blob_code["repository_methods"]

        # Check display widgets
        assert len(blob_code["display_widgets"]) == 2

        photo_widget = blob_code["display_widgets"][0]
        assert "PhotoDisplay extends StatelessWidget" in photo_widget["code"]
        assert "Image.memory" in photo_widget["code"]

        attach_widget = blob_code["display_widgets"][1]
        assert "AttachmentDisplay extends StatelessWidget" in attach_widget["code"]
        assert "ListTile" in attach_widget["code"]

    def test_expression_converter_blob_functions(self, converters):
        """Test expression converter handles blob functions."""
        expr_conv = converters["expr"]

        # Test Blob() function
        result = expr_conv.convert_blob_expression("Blob('Hello World')")
        assert result == "Uint8List.fromList('Hello World'.codeUnits)"

        # Test BlobMid() function
        result = expr_conv.convert_blob_expression("BlobMid(myBlob, 5, 10)")
        assert result == "myBlob.sublist(5 - 1, (5 - 1) + 10)"

        # Test BlobMid() without length
        result = expr_conv.convert_blob_expression("BlobMid(data, 10)")
        assert result == "data.sublist(10 - 1)"

        # Test BlobEdit() function
        result = expr_conv.convert_blob_expression("BlobEdit(buffer, 1, 255)")
        assert result == "_editBlob(buffer, 1, 255)"

        # Test Len() with blob
        result = expr_conv.convert_blob_expression("Len(myUint8List)")
        assert result == "myUint8List.length"

    def test_expression_converter_blob_imports(self, converters):
        """Test expression converter generates blob imports."""
        expr_conv = converters["expr"]

        # Check Uint8List import
        imports = expr_conv.get_required_imports("Uint8List data = Uint8List(0);")
        assert "import 'dart:typed_data';" in imports

        # Check base64 import
        imports = expr_conv.get_required_imports("base64Encode(data)")
        assert "import 'dart:convert';" in imports

        # Check blob function import
        imports = expr_conv.get_required_imports("_blob(someString)")
        assert "import 'dart:typed_data';" in imports

    def test_type_converter_blob_arrays(self, converters):
        """Test type converter handles blob arrays."""
        type_conv = converters["type"]

        # Test blob array
        dart_type = type_conv.convert_type("blob[]")
        assert dart_type == "List<Uint8List>"

        # Test nullable blob array
        dart_type = type_conv.convert_type("blob[]", nullable=True)
        assert dart_type == "List<Uint8List>?"

    def test_column_to_dict_with_blob(self, converters):
        """Test DataWindowColumn.to_dict includes blob metadata."""
        col = DataWindowColumn(
            name="signature",
            label="Signature",
            data_type="Uint8List",
            blob_metadata={"usage": "image", "display_widget": "SignatureDisplay"},
        )

        col_dict = col.to_dict()

        assert col_dict["is_blob"] is True
        assert col_dict["blob_metadata"]["usage"] == "image"
        assert col_dict["blob_metadata"]["display_widget"] == "SignatureDisplay"

    def test_blob_usage_detection(self, converters):
        """Test blob usage type detection from column names."""
        dw_conv = converters["dw"]

        # Test image detection
        assert dw_conv._determine_blob_usage("employee_photo", "") == "image"
        assert dw_conv._determine_blob_usage("profile_picture", "") == "image"
        assert dw_conv._determine_blob_usage("avatar_image", "") == "image"
        assert dw_conv._determine_blob_usage("screenshot_png", "") == "image"

        # Test document detection
        assert dw_conv._determine_blob_usage("resume_pdf", "") == "document"
        assert dw_conv._determine_blob_usage("contract_document", "") == "document"
        assert dw_conv._determine_blob_usage("excel_file", "") == "document"
        assert dw_conv._determine_blob_usage("report_attachment", "") == "document"

        # Test generic data
        assert dw_conv._determine_blob_usage("binary_data", "") == "data"
        assert dw_conv._determine_blob_usage("blob_field", "") == "data"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
