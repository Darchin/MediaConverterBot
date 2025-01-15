# Media Manipulation Telegram Bot
This Telegram-hosted bot written in Python provides an easy and user-friendly interface to applying some relatively simple but useful media file (document, video, image) manipulations on any device that runs Telegram.
Albeit the main interface of the bot is via Telegram, you can use the components on their own by importing them as modules within a Python script and passing the appropriate arguments to them. 
To facilitate user experience, a brief introduction to every supported functionality is given below. 

Note that all implemented methods expect the input files to be given as string file paths, and they save the output and return the file path(s) of the processed files.
Also, the functionality described below serves to explain the various methods as available in the respective modules, and the actually implemented and available functionality within the Telegram bot may be more limited in order not to clog up the user interface and confuse the user with a large number of adjustable parameters.

## VideoProcessor
This module is effectively a down-sized wrapper around the `ffmpeg-python` package which itself is a wrapper around FFmpeg. The implemented functionality is the following:
* You can **change the resolution** of an input video to any specified resolution. This is done using *bicubic up- or down-sampling.
* You can **change the framerate** of an input video to any specified frame rate. This is achieved using frame dropping or duplication.
* You can **merge multiple videos** into one video, using a variety of options for resolution and framerate matching, as well as format unification.
* You can **split a video** into multiple shorter videos by designating a list of intervals.
* You can **extract the pure audio or video stream** from a video file.
* You can **add a caption** to a video file, with control over appearance interval, various text attributes and background box positioning and color (in RGBA format).

## ImageProcessor
This module streamlines some common image manipulations through the use of `PIL` (Pillow). It also allows accurate background removal from images using pre-trained deep learning models available via the `rembg` package.
The implemented functionality is the following:
* You can **rotate an input image** by specifying rotation direction and angle.
* You can **crop an input image** by specifying the rectangular region to keep as a 4-tuple of points (as percentages of the total image size).
* You can **stack images vertically or horizontally** along with adjustable padding between each image.
* You can **remove the background** of images using `rembg` to obtain RGBA images retaining only the object of interest within each image.
* You can **convert an image from one format to another**.
* You can **add a caption** to an image with control over text attributes and text placement.

## DocumentProcessor
This module makes use of a couple of binaries along with their Python bindings/wrappers, with the main ones being OCR Tesserect (by Google) + PyTesseract, Poppler utils + `pdf2image` and Ghostscript. It also makes use of `PyPDF2` (not the newer but perhaps confusingly named `PyPDF`) for some general PDF manipulations and `PIL` (Pillow) for image-level manipulations (useful during OCR).
The implemented functionality is the following:
* You can **merge multiple PDFs** into one PDF file.
* You can also **split one PDF** into multiple PDF files.
* You can **compress** an input PDF file based on three presets (as provided by Ghostscript), giving you access to a variety of quality/file-size trade-offs.
* You can perform **OCR** on an input PDF or image. The language can both be specified or left unspecified for automatic detection by `pytesseract`. The function will also manage the de-skewing of the content prior to performing OCR.
