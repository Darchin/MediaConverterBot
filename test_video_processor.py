import os
import pytest
from video_processor import VideoProcessor

# Example input files:
SAMPLE_VIDEO_1 = "./test_files/sample_960x400_ocean_with_audio.mpeg"
SAMPLE_VIDEO_2 = "./test_files/sample_1280x720_surfing_with_audio.mpeg"

OUTPUT_DIR = "video_output"
RESIZED_VIDEO = os.path.join(OUTPUT_DIR, "resized_video.mpeg")
FRAMERATE_VIDEO = os.path.join(OUTPUT_DIR, "framerate_video.mpeg")
MERGED_VIDEO = os.path.join(OUTPUT_DIR, "merged_video.mpeg")
TRIM_DIR = os.path.join(OUTPUT_DIR, "trimmed")

@pytest.fixture(scope="module")
def video_processor():
    return VideoProcessor()

def test_change_resolution(video_processor):
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    out_file = video_processor.change_resolution(
        input_path=SAMPLE_VIDEO_1,
        output_path=RESIZED_VIDEO,
        resolution=(640, 360)
    )
    assert os.path.isfile(out_file), "Resized video was not created."

def test_change_framerate(video_processor):
    out_file = video_processor.change_framerate(
        input_path=SAMPLE_VIDEO_1,
        output_path=FRAMERATE_VIDEO,
        framerate=24
    )
    assert os.path.isfile(out_file), "Framerate-changed video was not created."

def test_merge_videos(video_processor):
    out_file = video_processor.merge_videos(
        [SAMPLE_VIDEO_1, SAMPLE_VIDEO_2],
        MERGED_VIDEO,
        unify_format=None,
        resolution=None,
        framerate=None
    )
    assert os.path.isfile(out_file), "Merged video was not created."

def test_trim_video(video_processor):
    if not os.path.exists(TRIM_DIR):
        os.makedirs(TRIM_DIR)

    intervals = [(0, 3), (3, 6)]
    output_files = video_processor.trim_video(
        input_path=SAMPLE_VIDEO_1,
        intervals=intervals,
        output_directory=TRIM_DIR
    )
    for f in output_files:
        assert os.path.isfile(f), f"Trimmed video file {f} not created."