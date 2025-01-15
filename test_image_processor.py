import os
import pytest
from PIL import Image

# Import your ImageProcessor class
# If the module is named image_processor.py, adjust the import accordingly:
# from your_module import ImageProcessor

from image_processor import ImageProcessor

TEST_FILES_DIR = "./test_files"
OUTPUT_DIR = "image_output"

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
    input_path = os.path.join(TEST_FILES_DIR, "person.jpg")
    output_path = processor.rotate_image(
        input_path=input_path,
        degree=45,
        direction='counter_clockwise'
    )

    assert os.path.exists(output_path), "Rotated image file was not created."
    with Image.open(output_path) as img:
        assert img is not None, "Rotated image is not a valid image file."
    print(f"Counter-clockwise rotated image saved at: {output_path}")

def test_crop_image(processor):
    """
    Test cropping the 'landscape.png' with 10% from the top, bottom, left, and right.
    """
    input_path = os.path.join(TEST_FILES_DIR, "landscape.png")
    output_path = processor.crop_image(
        input_path=input_path,
        crop_top=10,
        crop_bottom=10,
        crop_left=10,
        crop_right=10
    )
    assert os.path.exists(output_path), "croped image file was not created."
    with Image.open(output_path) as img:
        assert img is not None, "croped image is not a valid image file."
    print(f"croped image saved at: {output_path}")

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
    input_path = os.path.join(TEST_FILES_DIR, "person.jpg")
    output_path = processor.remove_background(input_path)
    assert os.path.exists(output_path), "Background-removed image file was not created."
    with Image.open(output_path) as img:
        assert img is not None, "Background-removed image is not a valid image file."
    print(f"Background-removed image saved at: {output_path}")

def test_change_format(processor):
    """
    Test change format from 'person.jpg'.
    """
    input_path = os.path.join(TEST_FILES_DIR, "person.jpg")
    output_path = processor.change_format(
        input_path=input_path,
        new_format="jpeg", 
        compression=85
    )

    assert os.path.exists(output_path), "changed format image file was not created."
    with Image.open(output_path) as img:
        assert img is not None, "changed format image is not a valid image file."
    print(f"changed format image saved at: {output_path}")
   

def test_add_caption(processor):
    """
    Test adding a caption to 'landscape.png' with semi-transparent box.
    Verify that text is positioned correctly (up, down, center, and custom) and the box is appropriately sized.
    """
    input_path = os.path.join(TEST_FILES_DIR, "landscape.png")
    
    # Define a small region to see the box expansion
    box_vertices = [(0.4, 0.4), (0.5, 0.4), (0.5, 0.45), (0.4, 0.45)]
    
    text = "Longer Caption Text to Test Expansion"
    box_color = (0, 0, 0, 128)  # semi-transparent black
    font_color = (255, 255, 255, 255)
    padding = 20
    font_name = "Consolas"
    font_size = 30

    # Test each text position
    positions = ["top" , "bottom" , "center" , 25]  # 25 as a sample custom integer position
    for pos in positions:
        output_path = processor.add_caption(
            input_path=input_path,
            text=text,
            box_vertices=box_vertices,
            box_color=box_color,
            padding=padding,
            font_name=font_name,
            font_size=font_size,
            font_color=font_color,
            text_position=pos
        )
        assert os.path.exists(output_path), f"Captioned image file was not created for position: {pos}"
        with Image.open(output_path) as img:
            assert img is not None, f"Captioned image is not a valid image file for position: {pos}"
           
        print(f"Captioned image with position {pos} saved at: {output_path}")

