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

    def __init__(self, output_dir: str = "./output"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Existing font_map initialization
        self.font_map = {
            "XB Roya": "./resources/fonts/XB ROYA.ttf",
            "Consolas": "./resources/fonts/consola.ttf",
            "Linux Libertine": "./resources/fonts/LinLibertine_R.ttf"
        }

    def _get_default_output_path(self, input_path: str, suffix: str) -> str:
        """Generate default output path with informative suffix"""
        basename = os.path.splitext(os.path.basename(input_path))[0]
        ext = os.path.splitext(input_path)[1]
        return os.path.join(self.output_dir, f"{basename}_{suffix}{ext}")

    # ----------------------------------------------------
    # 1) Change resolution
    # ----------------------------------------------------
    def change_resolution(
        self,
        input_path: str,
        output_path: str = None,
        resolution: Tuple[int, int] = (1280, 720),
    ) -> str:
        if output_path is None:
            res_str = f"{resolution[0]}x{resolution[1]}"
            output_path = self._get_default_output_path(input_path, f"res_{res_str}")
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
        output_path: str = None,
        framerate: int = 30
    ) -> str:
        """
        Change the video frame rate.
        Include audio in the output, preserving or transcoding as needed.
        """
        if output_path is None:
            output_path = self._get_default_output_path(input_path, f"fps_{framerate}")
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
        output_path: str = None,
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
        if output_path is None:
            # Use first video's extension for output
            ext = os.path.splitext(input_paths[0])[1]
            basename = "merged_" + "_".join(
                os.path.splitext(os.path.basename(p))[0] 
                for p in input_paths[:2]  # First 2 names only
            )
            if len(input_paths) > 2:
                basename += f"_and_{len(input_paths)-2}_more"
            output_path = os.path.join(self.output_dir, f"{basename}{ext}")
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
        output_directory: str = None
    ) -> List[str]:
        """
        Trim or split into multiple fragments. 
        Attempt to keep same container if extension is the same. 
        If truly no changes in codecs are needed, we do -c copy, 
        else re-encode.
        """
        if output_directory is None:
            output_directory = os.path.join(
                self.output_dir,
                f"{os.path.splitext(os.path.basename(input_path))[0]}_trimmed"
            )
            os.makedirs(output_directory, exist_ok=True)

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
    
        # ----------------------------------------------------
    # 5) Extract audio or video
    # ----------------------------------------------------
    def extract_audio(
        self,
        input_path: str,
        format: str,
        output_path: str = None
    ) -> str:
        """
        Extract only audio to a purely audio container format if possible,
        e.g. .m4a, .mp3, .wav. We do not want to produce a .mpeg file
        containing MP2 because it's often unplayable in many players.
        """
        if output_path is None:
            basename = os.path.splitext(os.path.basename(input_path))[0]
            output_path = os.path.join(self.output_dir, f"{basename}_audio_only.{format}")
        container, acodec = _guess_audio_container_and_codec(output_path)
        # We do -vn to drop video, and either copy or transcode to that audio codec.
        # Usually we just transcode, for consistent results.
        # If the user’s input audio is the same codec, we could do copy, but let’s
        # keep it simple: always transcode => ensures broad compatibility.
        (
            ffmpeg
            .input(input_path)
            .output(output_path, vn=None, acodec=acodec, format=container)
            .run(overwrite_output=True)
        )
        return output_path

    def extract_video_only(
        self,
        input_path: str,
        output_path: str = None
    ) -> str:
        """
        Extract only the video stream (drop audio),
        preserving container if possible.
        """
        if output_path is None:
            output_path = self._get_default_output_path(input_path, "video_only")
        container, vcodec, acodec = _guess_container_and_codecs(output_path)
        in_probe = ffmpeg.probe(input_path)
        streams = in_probe['streams']
        video_stream = next((s for s in streams if s['codec_type'] == 'video'), None)
        if not video_stream:
            raise ValueError("No video stream found in input.")

        in_vcodec = video_stream.get('codec_name', '')
        if in_vcodec == vcodec:
            final_vcodec = 'copy'
        else:
            final_vcodec = vcodec

        (
            ffmpeg
            .input(input_path)
            .output(output_path, an=None, vcodec=final_vcodec, format=container)
            .run(overwrite_output=True)
        )
        return output_path

    # ----------------------------------------------------
    # 6) Add caption
    # ----------------------------------------------------
    def add_caption(
        self,
        input_path: str,
        text: str,
        start_time: float,
        end_time: float,
        font: str = "Consolas",
        font_size: int = 24,
        font_color: str = "white",
        box_color: str = "black",
        box_alpha: float = 0.5,
        padding: int = 10,
        output_path: str = None,
    ) -> str:
        """
        Adds a caption with an auto bounding box and padding over [start_time, end_time].
        This requires re-encoding the video track (drawtext filter).
        Audio is copied or transcoded as needed.
        """
        if output_path is None:
            caption_text = text[:20] + "..." if len(text) > 20 else text
            caption_text = "".join(c for c in caption_text if c.isalnum() or c in " _-")
            output_path = self._get_default_output_path(
                input_path, f"caption_{caption_text}"
            )
        if font not in self.font_map:
            raise ValueError(f"Font '{font}' not recognized. "
                             f"Available fonts: {list(self.font_map.keys())}")
        fontfile = self.font_map[font]

        in_probe = ffmpeg.probe(input_path)
        in_format = in_probe['format']['format_name'].split(',')[0]
        streams = in_probe['streams']
        audio_stream = next((s for s in streams if s['codec_type'] == 'audio'), None)

        container, vcodec, acodec = _guess_container_and_codecs(output_path)
        vid_stream = next(s for s in streams if s['codec_type'] == 'video')
        width = vid_stream['width']
        height = vid_stream['height']

        # Approx text bounding
        char_width_factor = 0.6
        text_width = int(len(text) * font_size * char_width_factor)
        text_height = int(font_size * 1.2)
        box_w = text_width + 2 * padding
        box_h = text_height + 2 * padding

        # Position near bottom center
        x_box = (width - box_w) // 2
        y_box = int(height * 0.8)
        

        # Calculate centered text position within the box
        x_text = x_box + (box_w - text_width) // 2
        # Adjust y_text to vertically center the text. 
        # The y position in drawtext refers to the baseline, so we add half the box height.
        y_text = y_box + (box_h - text_height) // 2 + font_size // 2

        if container == in_format and audio_stream and audio_stream.get('codec_name') == acodec:
            audio_codec_final = 'copy'
        else:
            audio_codec_final = acodec

        drawbox_filter = {
            'x': x_box,
            'y': y_box,
            'w': box_w,
            'h': box_h,
            'color': f'{box_color}@{box_alpha}',
            't': 'fill',
            'enable': f'between(t,{start_time},{end_time})'
        }
        drawtext_filter = {
            'fontfile': fontfile,
            'text': text,
            'fontcolor': font_color,
            'fontsize': font_size,
            'x': x_text,
            'y': y_text,
            'enable': f'between(t,{start_time},{end_time})'
        }

        inp = ffmpeg.input(input_path)
        v = inp.video.filter('drawbox', **drawbox_filter)
        v = v.filter('drawtext', **drawtext_filter)

        (
            ffmpeg
            .output(v, inp.audio, output_path,
                    vcodec=vcodec, acodec=audio_codec_final, format=container)
            .run(overwrite_output=True)
        )

        return output_path
