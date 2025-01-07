import math
import os
from typing import List, Tuple, Union

import ffmpeg


def _guess_container_and_codecs(path: str):
    """
    Given a file path, guess the container format from its extension
    and return (container, vcodec, acodec) for video files.

    For non-video audio extensions, see _guess_audio_container_and_codec instead.
    """
    ext = os.path.splitext(path.lower())[1]
    if ext in ('.mpeg', '.mpg'):
        return ('mpeg', 'mpeg2video', 'mp2')
    elif ext == '.mp4':
        return ('mp4', 'libx264', 'aac')
    elif ext == '.mkv':
        return ('matroska', 'libx264', 'aac')
    else:
        # Fallback to MP4 if unrecognized
        return ('mp4', 'libx264', 'aac')

def _guess_audio_container_and_codec(path: str):
    """
    For pure audio output (extract_audio), figure out container & codec from extension.
    Examples:
      .m4a -> (container='ipod', acodec='aac')
      .mp3 -> (container='mp3',  acodec='libmp3lame')
      .wav -> (container='wav',  acodec='pcm_s16le')
      Otherwise fallback to .m4a
    """
    ext = os.path.splitext(path.lower())[1]
    if ext == '.m4a':
        return ('ipod', 'aac')
    elif ext == '.mp3':
        return ('mp3', 'libmp3lame')
    elif ext == '.wav':
        return ('wav', 'pcm_s16le')
    else:
        # Fallback to M4A
        return ('ipod', 'aac')

class VideoProcessor:
    """
    Handles:
      1) Change resolution
      2) Change frame rate
      3) Merge multiple videos
      4) Trim/split video
      5) Extract audio / video
      6) Add caption with auto bounding box
    """

    def __init__(self):
        # Map logical font name to TTF file in ./resources/fonts
        self.font_map = {
            "XB Roya": "./resources/fonts/XB ROYA.ttf",
            "Consolas": "./resources/fonts/consola.ttf",
            "Linux Libertine": "./resources/fonts/LinLibertine_R.ttf"
        }

    # ----------------------------------------------------
    # 1) Change resolution
    # ----------------------------------------------------
    def change_resolution(
        self,
        input_path: str,
        output_path: str,
        resolution: Tuple[int, int] = (1280, 720),
    ) -> str:
        """
        Upscale or downscale to a specified resolution.
        Keep audio by passing both video and audio streams to ffmpeg's output.
        Attempt to preserve container/codec if extension matches.
        """
        in_probe = ffmpeg.probe(input_path)
        in_format = in_probe['format']['format_name'].split(',')[0]
        streams = in_probe['streams']
        audio_stream = next((s for s in streams if s['codec_type'] == 'audio'), None)

        container, vcodec, acodec = _guess_container_and_codecs(output_path)
        input_stream = ffmpeg.input(input_path)

        # We must filter the video for scaling:
        video = input_stream.video.filter('scale', resolution[0], resolution[1])

        # Decide if we can copy the audio
        if container == in_format and audio_stream and audio_stream.get('codec_name') == acodec:
            audio_codec_final = 'copy'
        else:
            # Re-encode audio to the container's typical acodec
            audio_codec_final = acodec

        (
            ffmpeg
            .output(video, input_stream.audio, output_path,
                    vcodec=vcodec, acodec=audio_codec_final, format=container)
            .run(overwrite_output=True)
        )
        return output_path

    # ----------------------------------------------------
    # 2) Change frame rate
    # ----------------------------------------------------
    def change_framerate(
        self,
        input_path: str,
        output_path: str,
        framerate: int = 30
    ) -> str:
        """
        Change the video frame rate.
        Include audio in the output, preserving or transcoding as needed.
        """
        in_probe = ffmpeg.probe(input_path)
        in_format = in_probe['format']['format_name'].split(',')[0]
        streams = in_probe['streams']
        audio_stream = next((s for s in streams if s['codec_type'] == 'audio'), None)

        container, vcodec, acodec = _guess_container_and_codecs(output_path)
        input_stream = ffmpeg.input(input_path)

        # Filter the video for FPS
        video = input_stream.video.filter('fps', fps=framerate, round='up')

        # Decide if we can copy the audio
        if container == in_format and audio_stream and audio_stream.get('codec_name') == acodec:
            audio_codec_final = 'copy'
        else:
            audio_codec_final = acodec

        (
            ffmpeg
            .output(video, input_stream.audio, output_path,
                    vcodec=vcodec, acodec=audio_codec_final, format=container)
            .run(overwrite_output=True)
        )
        return output_path

    # ----------------------------------------------------
    # 3) Merge multiple videos
    # ----------------------------------------------------
    def merge_videos(
        self,
        input_paths: List[str],
        output_path: str,
        unify_format: Union[str, None] = None,
        resolution: Union[str, Tuple[int, int], None] = None,
        framerate: Union[str, int, None] = None
    ) -> str:
        """
        Merge multiple videos in the order specified. By default,
        uses the container of the first input if they all match,
        or unifies to that container if there's a mismatch.
        Optionally unify resolution/fps if specified.
        """
        if len(input_paths) < 2:
            raise ValueError("At least two videos are required to merge.")

        video_info = []
        containers = []
        for path in input_paths:
            probe = ffmpeg.probe(path)
            fmt_name = probe.get('format', {}).get('format_name', '')
            cont = fmt_name.split(',')[0]
            containers.append(cont)
            stream_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
            width = int(stream_info['width'])
            height = int(stream_info['height'])
            fps_str = stream_info.get('r_frame_rate', '30/1')
            num, den = fps_str.split('/')
            fps_val = float(num) / float(den)
            video_info.append((path, cont, width, height, fps_val))

        # Decide final container
        if unify_format is None:
            # default to container of first input if all are the same
            if len(set(containers)) == 1:
                final_container = containers[0]
            else:
                final_container = containers[0]
        else:
            final_container = unify_format

        # Also glean from output_path extension
        ext = os.path.splitext(output_path.lower())[1]
        if ext in ('.mpeg', '.mpg'):
            final_container = 'mpeg'
        elif ext == '.mp4':
            final_container = 'mp4'
        elif ext == '.mkv':
            final_container = 'matroska'

        # Determine the typical vcodec/acodec for that container
        if final_container == 'mpeg':
            vcodec, acodec = ('mpeg2video', 'mp2')
        elif final_container == 'mp4':
            vcodec, acodec = ('libx264', 'aac')
        elif final_container == 'matroska':
            vcodec, acodec = ('libx264', 'aac')
        else:
            # fallback
            vcodec, acodec = ('libx264', 'aac')

        # Decide final resolution
        widths = [v[2] for v in video_info]
        heights = [v[3] for v in video_info]
        fpses = [v[4] for v in video_info]
        
        if isinstance(resolution, tuple):
            final_res = resolution
        elif resolution == 'largest':
            final_res = (max(widths), max(heights))
        elif resolution == 'smallest':
            final_res = (min(widths), min(heights))
        elif resolution is None:
            final_res = (widths[0], heights[0])  # default to first input's
        else:
            raise ValueError("Invalid resolution parameter.")

        # Decide final framerate
        if isinstance(framerate, int):
            final_fps = float(framerate)
        elif framerate == 'largest':
            final_fps = math.ceil(max(fpses))
        elif framerate == 'smallest':
            final_fps = max(1, math.floor(min(fpses)))
        elif framerate is None:
            final_fps = fpses[0]  # default to first input's
        else:
            raise ValueError("Invalid framerate parameter.")

        same_container = all(c == final_container for c in containers)
        same_res = all((w == final_res[0] and h == final_res[1]) for _,_,w,h,_ in video_info)
        same_fps = all(abs(f - final_fps) < 0.0001 for _,_,_,_,f in video_info)

        need_transcode = not (same_container and same_res and same_fps)

        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        if need_transcode:
            # Transcode each
            transcoded_files = []
            for i, (ipath, icont, w, h, fval) in enumerate(video_info):
                out_temp = os.path.join(output_dir, f"merged_part_{i}.{final_container}")
                filters = []
                if (w,h) != final_res:
                    filters.append(('scale', final_res[0], final_res[1]))
                if abs(fval - final_fps) > 0.0001:
                    filters.append(('fps', final_fps, 'up'))

                inp = ffmpeg.input(ipath)
                vs = inp.video
                for flt in filters:
                    vs = vs.filter(*flt)

                # re-encode both video & audio
                (
                    ffmpeg
                    .output(vs, inp.audio, out_temp, 
                            vcodec=vcodec, acodec=acodec, format=final_container)
                    .run(overwrite_output=True)
                )
                transcoded_files.append(out_temp)

            # concat
            list_file = os.path.join(output_dir, "concat_list.txt")
            with open(list_file, 'w', encoding='utf-8') as f:
                for file_ in transcoded_files:
                    f.write(f"file '{os.path.abspath(file_).replace('\\','/')}'\n")

            (
                ffmpeg
                .input(list_file, format='concat', safe=0)
                .output(output_path, vcodec='copy', acodec='copy')
                .run(overwrite_output=True)
            )
            # for tfile in transcoded_files:
            #     os.remove(tfile)
            # os.remove(list_file)

        else:
            # direct concat
            list_file = os.path.join(output_dir, "concat_list.txt")
            with open(list_file, 'w', encoding='utf-8') as f:
                for v in video_info:
                    fpath = v[0]
                    f.write(f"file '{os.path.abspath(fpath).replace('\\','/')}'\n")

            (
                ffmpeg
                .input(list_file, format='concat', safe=0)
                .output(output_path, c='copy')
                .run(overwrite_output=True)
            )
            # os.remove(list_file)

        return output_path

    # ----------------------------------------------------
    # 4) Trim / split video
    # ----------------------------------------------------
    def trim_video(
        self,
        input_path: str,
        intervals: List[Tuple[float, float]],
        output_directory: str
    ) -> List[str]:
        """
        Trim or split into multiple fragments. 
        Attempt to keep same container if extension is the same. 
        If truly no changes in codecs are needed, we do -c copy, 
        else re-encode.
        """
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        in_probe = ffmpeg.probe(input_path)
        in_format = in_probe['format']['format_name'].split(',')[0]
        streams = in_probe['streams']
        audio_stream = next((s for s in streams if s['codec_type'] == 'audio'), None)
        video_stream = next((s for s in streams if s['codec_type'] == 'video'), None)
        if not video_stream:
            raise ValueError("No video stream in input.")

        output_paths = []
        # Derive extension from input container (just for demonstration)
        if in_format == 'mpeg':
            default_ext = '.mpeg'
        elif in_format == 'mp4':
            default_ext = '.mp4'
        elif in_format == 'matroska':
            default_ext = '.mkv'
        else:
            default_ext = '.mp4'  # fallback

        for i, (start, end) in enumerate(intervals):
            duration = end - start
            if duration <= 0:
                raise ValueError("Invalid interval with zero or negative duration.")

            out_file = os.path.join(output_directory, f"trimmed_part_{i}{default_ext}")
            container, vcodec, acodec = _guess_container_and_codecs(out_file)

            # If same container, we can attempt -c copy
            # This is typically fine for MPEG → MPEG, MP4 → MP4, etc.
            # but might fail if there's a partial GOP or other mismatch.
            # We'll try it. If it doesn't play, you can revert to re-encode logic.
            can_copy = (container == in_format)

            if can_copy:
                # attempt copy-based trim
                (
                    ffmpeg
                    .input(input_path, ss=start, t=duration)
                    .output(out_file, c='copy', format=container)
                    .run(overwrite_output=True)
                )
            else:
                # re-encode
                (
                    ffmpeg
                    .input(input_path, ss=start, t=duration)
                    .output(out_file, vcodec=vcodec, acodec=acodec, format=container)
                    .run(overwrite_output=True)
                )

            output_paths.append(out_file)

        return output_paths