import os
import pytest
from document_processor import DocumentProcessor

OUTPUT_DIR = "./document_output"

@pytest.fixture
def doc_processor():
    """
    Pytest fixture that initializes the DocumentProcessor,
    pointing output_dir to a temporary directory for test isolation.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    return DocumentProcessor(output_dir=OUTPUT_DIR)

def test_merge_pdfs(doc_processor):
    test_dir = "test_files"
    pdf1 = os.path.join(test_dir, "sample_document1.pdf")
    pdf2 = os.path.join(test_dir, "sample_document2.pdf")

    merged_path = doc_processor.merge_pdfs([pdf1, pdf2], output_filename="merged_test.pdf")
    assert os.path.exists(merged_path), "Merged PDF should exist"
    assert merged_path.endswith("merged_test.pdf")

def test_split_pdf(doc_processor):
    test_dir = "test_files"
    pdf_path = os.path.join(test_dir, "sample_document1.pdf")
    
    intervals = [(1, 1), (2, 3)]  # Example intervals
    output_paths = doc_processor.split_pdf(pdf_path, intervals, output_prefix="split_test")
    assert len(output_paths) == 2, "Should produce two fragments"
    for path in output_paths:
        assert os.path.exists(path), f"Output fragment {path} should exist"

def test_compress_pdf(doc_processor):
    test_dir = "test_files"
    pdf_path = os.path.join(test_dir, "sample_document1.pdf")

    # Test low-quality compression
    compressed_path = doc_processor.compress_pdf(pdf_path, quality="low", output_filename="compressed_low.pdf")
    assert os.path.exists(compressed_path), "Compressed PDF (low) should exist"

    # Test medium-quality compression
    compressed_path = doc_processor.compress_pdf(pdf_path, quality="medium", output_filename="compressed_medium.pdf")
    assert os.path.exists(compressed_path), "Compressed PDF (medium) should exist"

def test_ocr_pdf_to_searchable_pdf(doc_processor):
    test_dir = "test_files"
    pdf_path = os.path.join(test_dir, "sample_ocr_pdf.pdf")
    
    ocr_pdf_path = doc_processor.ocr_document(
        pdf_path,
        output_format="pdf",
        language=None,
        output_filename="ocr_result_searchable.pdf"
    )
    assert os.path.exists(ocr_pdf_path), "OCR-generated searchable PDF should exist"

def test_ocr_pdf_to_docx(doc_processor):
    test_dir = "test_files"
    pdf_path = os.path.join(test_dir, "sample_ocr_pdf.pdf")
    
    ocr_docx_path = doc_processor.ocr_document(
        pdf_path,
        output_format="docx",
        language="eng",  # Example language
        output_filename="ocr_result.docx"
    )
    assert os.path.exists(ocr_docx_path), "OCR-generated docx should exist"

def test_ocr_pdf_to_md(doc_processor):
    test_dir = "test_files"
    pdf_path = os.path.join(test_dir, "sample_ocr_pdf.pdf")
    
    ocr_md_path = doc_processor.ocr_document(
        pdf_path,
        output_format="md",
        output_filename="ocr_result.md"
    )
    assert os.path.exists(ocr_md_path), "OCR-generated markdown should exist"

def test_ocr_image_to_docx(doc_processor):
    test_dir = "test_files"
    img_path = os.path.join(test_dir, "sample_ocr_img.png")

    ocr_docx_path = doc_processor.ocr_document(
        img_path,
        output_format="docx",
        language="eng",
        output_filename="ocr_img_result.docx"
    )
    assert os.path.exists(ocr_docx_path), "OCR-generated docx from image should exist"

def test_ocr_image_to_md(doc_processor):
    test_dir = "test_files"
    img_path = os.path.join(test_dir, "sample_ocr_img.png")

    ocr_md_path = doc_processor.ocr_document(
        img_path,
        output_format="md",
        output_filename="ocr_img_result.md"
    )
    assert os.path.exists(ocr_md_path), "OCR-generated markdown from image should exist"
