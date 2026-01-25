#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract text from DOCX files"""

import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

def extract_text_from_docx(docx_path):
    """Extract text from a DOCX file"""
    text_content = []

    with zipfile.ZipFile(docx_path, 'r') as zip_ref:
        # Read the main document
        xml_content = zip_ref.read('word/document.xml')

        # Parse XML
        root = ET.fromstring(xml_content)

        # Define namespace
        ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

        # Extract all paragraphs
        paragraphs = root.findall('.//w:p', ns)

        for para in paragraphs:
            # Extract all text runs in this paragraph
            texts = para.findall('.//w:t', ns)
            para_text = ''.join([t.text for t in texts if t.text])

            if para_text.strip():
                text_content.append(para_text)

    return '\n\n'.join(text_content)

if __name__ == '__main__':
    import sys

    if len(sys.argv) != 3:
        print("Usage: python extract_docx.py <input.docx> <output.txt>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    text = extract_text_from_docx(input_file)

    Path(output_file).write_text(text, encoding='utf-8')
    print(f"Extracted text to {output_file}")
