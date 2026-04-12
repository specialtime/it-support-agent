import pytest
from bs4 import BeautifulSoup

from etl.pipeline_sharepoint import extract_html_text

class TestSharepointETL:
    def test_html_parsing_logic(self):
        # Arrange
        dummy_html = """
        <html>
            <head><title>Runbook P1</title></head>
            <body>
                <h1>Error 403 ERP</h1>
                <p>Para resolver el error, verifique los permisos de rol.</p>
            </body>
        </html>
        """
        
        # Act
        extracted = extract_html_text(dummy_html)
        
        # Assert
        assert "Runbook P1" in extracted
        assert "Error 403 ERP" in extracted
        assert "verifique los permisos" in extracted
        assert "<html>" not in extracted # Ensure HTML tags are stripped
