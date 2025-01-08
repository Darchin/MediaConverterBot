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
