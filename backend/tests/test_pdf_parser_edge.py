import pytest
from app.services.pdf_parser import parse_pdf_bytes

def test_parse_pdf_bytes_magic_bytes_failure():
    # Provide data that doesn't start with %PDF
    invalid_bytes = b"This is not a PDF file"
    with pytest.raises(ValueError) as exc_info:
        parse_pdf_bytes(invalid_bytes, "invalid.pdf")
    assert "valid PDF" in str(exc_info.value)

def test_parse_pdf_bytes_oversize():
    # Provide data larger than 10MB
    # Let's mock the 10MB check by just faking the length
    # Wait, simple way is to pass a 10MB + 1 byte file
    # Creating a 10MB byte string in memory is quick (10 * 1024 * 1024 + 1 bytes)
    big_bytes = b"%PDF-1.4\n" + (b"0" * 10485760)
    with pytest.raises(ValueError) as exc_info:
        parse_pdf_bytes(big_bytes, "big.pdf")
    assert "exceeds" in str(exc_info.value)

def test_base_parser_unknown_type():
    with pytest.raises(ValueError) as exc_info:
        # Mocking fitz so we don't actually need a valid PDF structure inside
        import fitz
        from unittest.mock import patch
        with patch('fitz.open') as mock_fitz:
            mock_doc = mock_fitz.return_value
            mock_doc.__iter__.return_value = [type('obj', (object,), {'get_text': lambda self: "Unknown text"})()]
            parse_pdf_bytes(b"%PDF-1.4\n", "raw test")
    assert "Unknown report type" in str(exc_info.value)
