import os
import re
import uuid
import subprocess
from io import BytesIO

import pytesseract
from PyPDF2 import PdfReader, PdfWriter
from docx import Document
from pdf2image import convert_from_path
from PIL import Image

class DocumentProcessor :
    def __init__(self, output_dir="document_output"):
        """
        :param output_dir: Directory where all output files will be stored.
        """
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def merge_pdfs(self, input_paths, output_filename=None):
        """
        Merges multiple PDF files into a single PDF in the specified order.

        :param input_paths: List of PDF paths to merge in the given order.
        :param output_filename: Name of the merged output file (optional).
        :return: Path to the merged PDF file.
        """
        if output_filename is None:
            output_filename = f"merged_{uuid.uuid4().hex}.pdf"

        output_path = os.path.join(self.output_dir, output_filename)

        writer = PdfWriter()
        for path in input_paths:
            reader = PdfReader(path)
            for page in reader.pages:
                writer.add_page(page)

        with open(output_path, "wb") as f:
            writer.write(f)

        return output_path

    def split_pdf(self, pdf_path, intervals, output_prefix=None):
        """
        Splits a PDF into fragments specified by intervals (page ranges).
        Intervals is a list of (start, end) 1-based page indices.

        :param pdf_path: Path to the PDF to be split.
        :param intervals: List of tuples representing (start_page, end_page).
        :param output_prefix: Optional prefix for the output file names.
        :return: List of output fragment file paths.
        """
        if output_prefix is None:
            base_name = os.path.splitext(os.path.basename(pdf_path))[0]
            output_prefix = f"{base_name}_frag"

        reader = PdfReader(pdf_path)
        output_paths = []

        for i, (start, end) in enumerate(intervals, start=1):
            writer = PdfWriter()
            # Ensure pages exist within range
            start_index = max(0, start - 1)
            end_index = min(len(reader.pages), end)
            for page_idx in range(start_index, end_index):
                writer.add_page(reader.pages[page_idx])

            fragment_filename = f"{output_prefix}_{i}.pdf"
            output_path = os.path.join(self.output_dir, fragment_filename)
            with open(output_path, "wb") as f:
                writer.write(f)
            output_paths.append(output_path)

        return output_paths

    def compress_pdf(self, pdf_path, quality="medium", output_filename=None):
        """
        Compress a PDF using Ghostscript with three preset options: low, medium, high.

        :param pdf_path: Path to the PDF to be compressed.
        :param quality: One of ['low', 'medium', 'high'].
        :param output_filename: Name of the compressed output file (optional).
        :return: Path to the compressed PDF file.
        """
        settings_map = {
            "low": "/screen",    # smaller size, lower quality
            "medium": "/ebook",  # better quality
            "high": "/prepress"  # best quality, larger size
        }

        if quality not in settings_map:
            raise ValueError(f"Quality must be one of {list(settings_map.keys())}")

        if output_filename is None:
            base_name = os.path.splitext(os.path.basename(pdf_path))[0]
            output_filename = f"{base_name}_compressed_{quality}.pdf"

        output_path = os.path.join(self.output_dir, output_filename)

        # Example Ghostscript command
        gs_command = [
            "gs",
            "-sDEVICE=pdfwrite",
            f"-dPDFSETTINGS={settings_map[quality]}",
            "-dCompatibilityLevel=1.4",
            "-dNOPAUSE",
            "-dQUIET",
            "-dBATCH",
            f"-sOutputFile={output_path}",
            pdf_path
        ]

        subprocess.run(gs_command, check=True)

        return output_path
