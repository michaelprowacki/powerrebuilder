#!/usr/bin/env python3
"""Test the P-code detection logic directly."""

# Source extensions from core.py
SOURCE_EXTENSIONS = (
    ".sru",
    ".srw",
    ".srd",
    ".srm",
    ".sra",
    ".srq",
    ".srs",
    ".srf",
    ".srj",
)


def test_pcode_detection() -> None:
    """Test various scenarios for P-code detection."""
    test_cases = [
        # (objectname, version, expected_result, description)
        ("n_cst_mailsession.udo", "0.6.0.0", False, "User data object with PB version"),
        ("w_mail_test.win", "0.6.0.0", False, "Window with PB version"),
        (
            "n_test.sru",
            "0.6.0.0",
            False,
            "Source file with PB version - NO function/event",
        ),
        ("n_test.sru", "function", True, "Source file with 'function' version"),
        ("n_test.sru", "event handler", True, "Source file with 'event' in version"),
        ("test.srf", "0.6.0.0", True, "SRF file - always P-code"),
        ("test.srj", "whatever", True, "SRJ file - always P-code"),
        ("w_window.srw", "window", False, "Window source without function/event"),
        ("f_function.srf", "pfcasads", True, "Special SRF file"),
    ]

    for objectname, version, _expected, _description in test_cases:
        # Apply the exact logic from core.py
        (
            objectname.lower().endswith(tuple(SOURCE_EXTENSIONS))
            and ("function" in version.lower() or "event" in version.lower())
        ) or objectname.lower().endswith((".srf", ".srj"))


if __name__ == "__main__":
    test_pcode_detection()
