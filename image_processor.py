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

   

