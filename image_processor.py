import os

from PIL import Image, ImageDraw, ImageFont
from rembg import new_session, remove

class ImageProcessor:
    def __init__(self, output_dir=''):
        self.output_dir = output_dir
        # Define available fonts
        self.fonts = {
            "XB Roya": os.path.join(os.path.dirname(__file__), 'resources', 'fonts', 'XB ROYA.ttf'),
            "Consolas": os.path.join(os.path.dirname(__file__), 'resources', 'fonts', 'consola.ttf'),
            "Linux Libertine": os.path.join(os.path.dirname(__file__), 'resources', 'fonts', 'LinLibertine_R.ttf')
        }

        self.rembg_session = new_session('isnet-general-use')

    def _get_image_format(self, input_path, needs_transparency):
        """
        Determines the appropriate image format and mode based on the original image and transparency requirement.

        :param input_path: Path to the input image.
        :param needs_transparency: Boolean indicating if transparency is required.
        :return: Tuple (mode, format)
        """
        _, ext = os.path.splitext(input_path.lower())
        is_png = ext == '.png'

        if needs_transparency:
            return ('RGBA', 'PNG')
        else:
            return ('RGBA' if is_png else 'RGB', 'PNG' if is_png else 'JPEG')

    def rotate_image(self, input_path, degree, direction='clockwise', output_path=None):
        """
        Rotates an image by the specified degree and direction.

        :param input_path: Path to the input image.
        :param degree: Degree to rotate.
        :param direction: 'clockwise' or 'counter_clockwise'.
        :param output_path: Path to save the rotated image. If None, saves in output_dir.
        :return: Path to the rotated image.
        """
        image = Image.open(input_path).convert("RGBA")
        if direction == 'clockwise':
            degree = -degree
        rotated_image = image.rotate(degree, expand=True)
        if not output_path:
            base, ext = os.path.splitext(os.path.basename(input_path))
            output_ext = '.png'  # Save as PNG to preserve any transparency
            output_path = os.path.join(self.output_dir, f"{base}_rotated{output_ext}")
        rotated_image.save(output_path)
        return output_path
    
    def crop_image(self, input_path, crop_top=0, crop_bottom=0, crop_left=0, crop_right=0, output_path=None):
        """
        Crops an image based on the percentage values from each edge.

        :param input_path: Path to the input image.
        :param crop_top: Percentage to crop from the top (0-100).
        :param crop_bottom: Percentage to crop from the bottom (0-100).
        :param crop_left: Percentage to crop from the left (0-100).
        :param crop_right: Percentage to crop from the right (0-100).
        :param output_path: Path to save the cropped image. If None, saves in output_dir.
        :return: Path to the cropped image.
        """
        image = Image.open(input_path)
        width, height = image.size

        # Calculate crop boundaries in pixels
        left = int(width * (crop_left / 100))
        right = int(width * (1 - crop_right / 100))
        top = int(height * (crop_top / 100))
        bottom = int(height * (1 - crop_bottom / 100))

        # Ensure cropping dimensions are valid
        if left >= right or top >= bottom:
            raise ValueError("Invalid crop dimensions. Ensure the percentages result in a valid cropped area.")

        cropped_image = image.crop((left, top, right, bottom))

        if not output_path:
            base, ext = os.path.splitext(os.path.basename(input_path))
            output_ext = ext or '.png'
            output_path = os.path.join(self.output_dir, f"{base}_cropped{output_ext}")

        cropped_image.save(output_path)
        return output_path


    def stack_images(self, input_paths, direction='vertical', padding=10, padding_color=(255, 255, 255, 255), output_path=None):
        """
        Stacks multiple images vertically or horizontally with specified padding.
        All images are converted to RGBA and handled in memory.

        :param input_paths: List of image file paths to stack.
        :param direction: 'vertical' or 'horizontal'.
        :param padding: Thickness of padding in pixels.
        :param padding_color: Color of padding as an RGBA tuple.
        :param output_path: Path to save the stacked image. If None, saves in output_dir.
        :return: Path to the stacked image.
        """
        try:
            # Convert all images to RGBA and keep them in memory
            images = []
            for path in input_paths:
                with Image.open(path).convert("RGBA") as img:
                    images.append(img.copy())  # Make a copy to keep the image in memory

            # Calculate the size of the new image
            if direction == 'vertical':
                width = max(img.width for img in images)
                height = sum(img.height for img in images) + padding * (len(images) - 1)
                new_image = Image.new('RGBA', (width, height), padding_color)
                y_offset = 0
                for img in images:
                    new_image.paste(img, ((width - img.width) // 2, y_offset), img)
                    y_offset += img.height + padding
            else:  # horizontal
                width = sum(img.width for img in images) + padding * (len(images) - 1)
                height = max(img.height for img in images)
                new_image = Image.new('RGBA', (width, height), padding_color)
                x_offset = 0
                for img in images:
                    new_image.paste(img, (x_offset, (height - img.height) // 2), img)
                    x_offset += img.width + padding

            if not output_path:
                output_path = os.path.join(self.output_dir, "stacked_image.png")

            new_image.save(output_path, format='PNG')
            return output_path
        except Exception as e:
            raise e
        
    def remove_background(self, input_path, output_path=None):
        """
        Removes the background of an image using rembg with the 'isnet-general-use' model.

        :param input_path: Path to the input image.
        :param output_path: Path to save the image with removed background. If None, saves in output_dir.
        :return: Path to the image with removed background.
        """
        with open(input_path, 'rb') as i:
            input_data = i.read()
        output_data = remove(input_data, session=self.rembg_session)

        if not output_path:
            base, _ = os.path.splitext(os.path.basename(input_path))
            output_path = os.path.join(self.output_dir, f"{base}_no_bg.png")
        with open(output_path, 'wb') as o:
            o.write(output_data)
        return output_path
    
    def change_format(self, input_path, new_format, output_path=None, **kwargs):
        """
        Changes the format of an image file and saves it to the specified output path.

        Args:
            input_path (str): The file path to the input image.
            new_format (str): The new format for the image (e.g., "jpeg", "png").
            output_path (str, optional): The file path to save the converted image. 
                                        If not provided, it will be generated automatically.
            **kwargs: Additional parameters, e.g., "compression" for JPEG quality.

        Returns:
            str: The file path of the saved image in the new format.
        """
        image = Image.open(input_path)
    
        if not output_path:
            base, ext = os.path.splitext(os.path.basename(input_path))
            output_path = os.path.join(self.output_dir, base)
            output_path = output_path.rsplit('.', 1)[0] + f".{new_format.lower()}"
        if new_format.lower() == "jpeg" and "compression" in kwargs:
            image.quality = kwargs["compression"]
        image.save(output_path)
        return output_path
        
        

    def add_caption(
        self,
        input_path,
        text,
        box_vertices,
        box_color=(0, 0, 0, 128),
        padding=10,
        font_name="Consolas",
        font_size=20,
        font_color=(255, 255, 255, 255),
        output_path=None,
        text_position="center"
    ):
        """
        Adds a caption in a box on an image, with the following rules:
        1. box_color is an RGBA tuple, and padding is applied around the text.
        2. If the box is not fully opaque (alpha < 255), the output format is forced to PNG.
           Otherwise, the original format (JPEG/PNG) is preserved.
        3. The text is placed according to 'text_position':
             - "up":    near the top of the box (with padding)
             - "down":  near the bottom of the box (with padding)
             - "center": vertically centered within the box (default)
             - integer between 0 and 100: a relative vertical position
               (0 = topmost, 100 = bottommost)
        4. If text plus padding is larger than the original box, the box expands.
        5. font_name can be one of: "XB Roya", "Consolas", or "Linux Libertine".
        :param input_path: Path to the input image.
        :param text: Text to be placed inside the box.
        :param box_vertices: List of four tuples for box corners as relative coords [(x1, y1), (x2, y2), ...].
        :param box_color: RGBA tuple for box color.
        :param padding: Integer padding (in pixels) around text within the box.
        :param font_name: One of "XB Roya", "Consolas", or "Linux Libertine".
        :param font_size: Font size in points.
        :param font_color: RGBA color for the text.
        :param output_path: Path to save the output image.
        :param text_position: "up", "down", "center" or integer [0..100].
        :return: Path to the saved image.
        """

        # --- Step 1: Determine the input image mode and format ---
        # Check if box_color is fully opaque
        alpha = box_color[3]
        # Decide on output format based on alpha
        if alpha < 255:
            # Force PNG (transparency required)
            out_format = "PNG"
        else:
            # Keep the original extension
            _, ext = os.path.splitext(input_path.lower())
            if ext in [".jpg", ".jpeg"]:
                out_format = "JPEG"
            elif ext == ".png":
                out_format = "PNG"
            else:
                # Default to PNG if unknown extension
                out_format = "PNG"

        # Open the image
        image = Image.open(input_path)
        # If transparency is needed, ensure we use RGBA
        if out_format == "PNG":
            image = image.convert("RGBA")
        else:
            image = image.convert("RGB")

        draw = ImageDraw.Draw(image)
        width, height = image.size

        # --- Step 2: Convert relative box coordinates to absolute ---
        # box_vertices: [(x1, y1), (x2, y2), (x3, y3), (x4, y4)]
        abs_coords = [(int(x * width), int(y * height)) for x, y in box_vertices]
        xs = [pt[0] for pt in abs_coords]
        ys = [pt[1] for pt in abs_coords]

        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        box_width = max_x - min_x
        box_height = max_y - min_y

        # --- Step 3: Prepare the font ---
        font_path = self.fonts.get(font_name)
        if font_path and os.path.exists(font_path):
            try:
                font = ImageFont.truetype(font_path, font_size)
            except IOError:
                font = ImageFont.load_default()
        else:
            font = ImageFont.load_default()

        # --- Step 4: Measure the text using textbbox() if available, otherwise fallback ---
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
        except AttributeError:
            # Older Pillow fallback
            text_w, text_h = font.getsize(text)

        # --- Step 5: Potentially expand box dimensions based on text size + padding ---
        needed_width = text_w + 2 * padding
        needed_height = text_h + 2 * padding

        final_box_width = max(box_width, needed_width)
        final_box_height = max(box_height, needed_height)



        box_center_x = width / 2
        final_min_x = box_center_x - final_box_width/2 
        final_max_x = final_min_x + final_box_width 
        # Decide vertical position
        if text_position == "center":
            # Center the final box around the original box center
            box_center_y = (min_y + max_y) // 2

            final_min_y = box_center_y - final_box_height // 2
            final_max_y = final_min_y + final_box_height
        elif text_position == "top":
         
            final_min_y =  final_box_height // 2
            final_max_y =  final_box_height *1.5
        elif text_position == "bottom":
            
            final_min_y = height-final_box_height * 1.5 
            final_max_y = height - final_box_height // 2

        elif isinstance(text_position, int) and 0 <= text_position <= 100:
            vertical_span = height-final_box_height 
            final_min_y = int(vertical_span * (text_position / 100.0)) 
            final_max_y = int(vertical_span * (text_position / 100.0))+ final_box_height  
        else:
            raise ValueError(
                "Invalid value for text_position. "
                "Must be one of 'up', 'down', 'center' or an integer in [0..100]."
            )
        
        
        # --- Step 6: Draw the box ---
        draw.rectangle(
            [final_min_x, final_min_y, final_max_x, final_max_y],
            fill=box_color
        )

        # --- Step 7: Center the text within the final box ---
        text_x = final_min_x + (final_box_width - text_w) // 2
        text_y = final_min_y + (final_box_height - text_h) // 2

        draw.text(
            (text_x, text_y),
            text,
            font=font,
            fill=font_color
        )

        # --- Step 8: Prepare final output path ---
        if not output_path:
            base_name, _ = os.path.splitext(os.path.basename(input_path))
            if out_format == "PNG":
                output_ext = ".png"
            else:
                output_ext = ".jpg"
            output_path = os.path.join(self.output_dir, f"{base_name}_caption{output_ext}")

        # --- Step 9: Save the result ---
        image.save(output_path, format=out_format)
        return output_path

