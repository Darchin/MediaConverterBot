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

    def _deskew_with_tesseract_osd(self, pil_image):
        """
        Performs deskewing using Tesseract's OSD (Orientation and Script Detection).
        :param pil_image: A PIL Image object.
        :return: A new PIL Image, rotated to correct orientation.
        """
        # Get OSD data from Tesseract
        osd_data = pytesseract.image_to_osd(pil_image)
        # Example OSD output snippet:
        #   Page number: 0
        #   Orientation in degrees: 270
        #   Rotate: 90
        #   Orientation confidence: 10.00
        #   Script: Latin
        #   Script confidence: 7.96

        # Parse out the orientation in degrees
        angle_search = re.search(r"Orientation in degrees: (\d+)", osd_data)
        if angle_search:
            orientation = int(angle_search.group(1))
        else:
            orientation = 0

        # Convert Tesseract orientation to a rotation angle
        # If orientation is 270°, we want to rotate by +90° to correct it
        # Typically: corrected rotation = 360 - orientation
        rot_angle = (360 - orientation) % 360
        if rot_angle != 0:
            pil_image = pil_image.rotate(rot_angle, expand=True)

        return pil_image

    def _save_ocr_to_docx(self, text_lines, output_path):
        """
        Saves OCR text lines to a docx file, attempting to preserve some structure.
        :param text_lines: List of text lines (strings).
        :param output_path: Full path to output docx file.
        """
        doc = Document()
        for line in text_lines:
            doc.add_paragraph(line)
        doc.save(output_path)

    def _save_ocr_to_markdown(self, text_lines, output_path):
        """
        Saves OCR text lines to a markdown file.
        :param text_lines: List of text lines (strings).
        :param output_path: Full path to output md file.
        """
        with open(output_path, "w", encoding="utf-8") as f:
            for line in text_lines:
                f.write(line + "\n")

    def ocr_document(
        self,
        input_path,
        output_format="pdf",
        language=None,
        output_filename=None
    ):
        """
        Performs deskewing and OCR on the given input, which can be a PDF or an image.
        If it's a PDF, each page is converted to an image, deskewed, and then OCR is performed.
        If it's an image, it is processed as a single page.

        :param input_path: Path to the input file (PDF or image).
        :param output_format: 'pdf' (searchable PDF), 'md' (markdown), or 'docx'.
        :param language: Language for OCR. If None, uses Tesseract default or OSD for script detection.
        :param output_filename: Optional name for the output file.
        :return: Path to the output (PDF, MD, or DOCX) file.
        """
        base_name = os.path.splitext(os.path.basename(input_path))[0]

        # Set Tesseract language
        config = ""
        if language:
            config = f"-l {language}"

        # Determine if input is PDF or image
        file_ext = os.path.splitext(input_path)[1].lower()
        image_extensions = [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]
        is_image = file_ext in image_extensions

        if output_filename is None:
            output_filename = f"{base_name}_ocr.{output_format}"

        output_path = os.path.join(self.output_dir, output_filename)

        if is_image:
            # 1) Open image with PIL
            pil_img = Image.open(input_path).convert("RGB")
            # 2) Deskew using Tesseract OSD
            deskewed_img = self._deskew_with_tesseract_osd(pil_img)
            # 3) Perform OCR
            ocr_text = pytesseract.image_to_string(deskewed_img, config=config)

            if output_format == "pdf":
                # Make a single-page searchable PDF
                pdf_bytes = pytesseract.image_to_pdf_or_hocr(deskewed_img, extension='pdf', config=config)
                with open(output_path, "wb") as f:
                    f.write(pdf_bytes)

            elif output_format == "docx":
                self._save_ocr_to_docx(ocr_text.splitlines(), output_path)

            elif output_format == "md":
                self._save_ocr_to_markdown(ocr_text.splitlines(), output_path)

            else:
                raise ValueError("Unsupported output format.")
        else:
            # It's a PDF
            # Convert PDF pages to images => deskew => OCR => combine
            pdf_pages = convert_from_path(input_path, dpi=300)

            if output_format == "pdf":
                # Build a new PDF with a text layer on each page
                writer = PdfWriter()
                for page_img in pdf_pages:
                    # 1) Deskew the PIL image
                    deskewed_img = self._deskew_with_tesseract_osd(page_img)
                    # 2) Convert to OCR'ed PDF bytes
                    pdf_bytes = pytesseract.image_to_pdf_or_hocr(deskewed_img, extension='pdf', config=config)
                    # 3) Read the PDF bytes back into a PdfReader, then add page(s) to the writer
                    page_reader = PdfReader(BytesIO(pdf_bytes))
                    for p in page_reader.pages:
                        writer.add_page(p)

                with open(output_path, "wb") as out_file:
                    writer.write(out_file)

            elif output_format in ["docx", "md"]:
                # Extract text from each page via OCR and output as docx or md
                all_text_lines = []
                for page_img in pdf_pages:
                    deskewed_img = self._deskew_with_tesseract_osd(page_img)
                    text = pytesseract.image_to_string(deskewed_img, config=config)
                    if text:
                        all_text_lines.extend(text.splitlines())

                if output_format == "docx":
                    self._save_ocr_to_docx(all_text_lines, output_path)
                else:
                    self._save_ocr_to_markdown(all_text_lines, output_path)
            else:
                raise ValueError("Unsupported output format.")

        return output_path
