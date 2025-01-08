import os
import pytest
from PIL import Image

# Import your ImageProcessor class
# If the module is named image_processor.py, adjust the import accordingly:
# from your_module import ImageProcessor

from image_processor import ImageProcessor

TEST_FILES_DIR = "test_files"
OUTPUT_DIR = "./image_output"

@pytest.fixture(scope="module")
def processor():
    """
    A fixture that creates a single ImageProcessor instance to be used
    for all tests in this module.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    return ImageProcessor(output_dir=OUTPUT_DIR)

def test_rotate_image_clockwise(processor):
    """
    Test rotating the 'car.jpg' by 90 degrees clockwise.
    """
    input_path = os.path.join(TEST_FILES_DIR, "car.jpg")
    output_path = processor.rotate_image(
        input_path=input_path,
        degree=90,
        direction='clockwise'
    )

    assert os.path.exists(output_path), "Rotated image file was not created."
    # Additional check: open the image to ensure it is valid
    with Image.open(output_path) as img:
        assert img is not None, "Rotated image is not a valid image file."
    print(f"Clockwise rotated image saved at: {output_path}")

def test_rotate_image_counterclockwise(processor):
    """
    Test rotating the 'car.jpg' by 45 degrees counter-clockwise.
    """
    input_path = os.path.join(TEST_FILES_DIR, "car.jpg")
    output_path = processor.rotate_image(
        input_path=input_path,
        degree=45,
        direction='counter_clockwise'
    )

    assert os.path.exists(output_path), "Rotated image file was not created."
    with Image.open(output_path) as img:
        assert img is not None, "Rotated image is not a valid image file."
    print(f"Counter-clockwise rotated image saved at: {output_path}")

def test_stack_images_vertical(processor):
    """
    Test stacking 'car.jpg', 'person.jpg', and 'landscape.png' vertically.
    """
    input_paths = [
        os.path.join(TEST_FILES_DIR, "car.jpg"),
        os.path.join(TEST_FILES_DIR, "person.jpg"),
        os.path.join(TEST_FILES_DIR, "landscape.png")
    ]
    output_path = processor.stack_images(input_paths, direction='vertical')
    assert os.path.exists(output_path), "Stacked image file was not created."
    with Image.open(output_path) as img:
        assert img is not None, "Stacked image is not a valid image file."
    print(f"Vertically stacked image saved at: {output_path}")

def test_stack_images_horizontal(processor):
    """
    Test stacking 'car.jpg', 'person.jpg', and 'landscape.png' horizontally.
    """
    input_paths = [
        os.path.join(TEST_FILES_DIR, "car.jpg"),
        os.path.join(TEST_FILES_DIR, "person.jpg"),
        os.path.join(TEST_FILES_DIR, "landscape.png")
    ]
    output_path = processor.stack_images(input_paths, direction='horizontal')
    assert os.path.exists(output_path), "Stacked image file was not created."
    with Image.open(output_path) as img:
        assert img is not None, "Stacked image is not a valid image file."
    print(f"Horizontally stacked image saved at: {output_path}")

def test_remove_background(processor):
    """
    Test removing background from 'person.jpg'.
    """
    input_path = os.path.join(TEST_FILES_DIR, "car.jpg")
    output_path = processor.remove_background(input_path)
    assert os.path.exists(output_path), "Background-removed image file was not created."
    with Image.open(output_path) as img:
        assert img is not None, "Background-removed image is not a valid image file."
    print(f"Background-removed image saved at: {output_path}")



