# video_generator.py

import os
import textwrap
from datetime import datetime
from moviepy.editor import (
    ImageClip,
    AudioFileClip,
    concatenate_videoclips,
    CompositeAudioClip,
    VideoFileClip
)
from PIL import Image, ImageDraw, ImageFont
from pydub import AudioSegment

# ----------------------------------------------------------------------
# CONFIGURATION
# ----------------------------------------------------------------------
FONT_PATH = os.path.join(os.path.dirname(__file__), "..", "resources", "fonts", "Arial.ttf")
FONT_SIZE = 40
TEXT_COLOR = (255, 255, 255)
BG_COLOR = (0, 0, 0)
IMAGE_WIDTH = 1280
IMAGE_HEIGHT = 720
MAX_TEXT_WIDTH = 40
FADE_DURATION = 0.05
FPS = 24

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output", "media", "video")
os.makedirs(OUTPUT_DIR, exist_ok=True)
TEMP_DIR = os.path.join(os.path.dirname(__file__), "..", "output", "temp")
os.makedirs(TEMP_DIR, exist_ok=True)
current_time = datetime.now().strftime("%d_%m_%Y")

# ----------------------------------------------------------------------
# EXISTING TEXT-TO-VIDEO METHODS
# ----------------------------------------------------------------------
def generate_text_image(paragraph, index):
    img = Image.new("RGB", (IMAGE_WIDTH, IMAGE_HEIGHT), color=BG_COLOR)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    lines = textwrap.wrap(paragraph, width=MAX_TEXT_WIDTH)
    line_heights = [draw.textbbox((0, 0), line, font=font)[3] for line in lines]
    total_text_height = sum(line_heights) + (len(lines)-1)*10
    y = (IMAGE_HEIGHT - total_text_height) // 2
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x = (IMAGE_WIDTH - text_width) // 2
        draw.text((x, y), line, font=font, fill=TEXT_COLOR)
        y += (bbox[3] - bbox[1]) + 10
    path = os.path.join(TEMP_DIR, f"paragraph_{index}.png")
    img.save(path)
    return path


# ----------------------------------------------------------------------
# NEW METHOD: IMAGE-BASED VIDEO GENERATION
# ----------------------------------------------------------------------
def generate_video_from_images(image_paths: list, audio_path: str, stock_symbol: str, fps: int = FPS, total_duration=58,language="english") -> str:
    """
    Creates a video from a list of exactly four images, ensuring the total duration is less than 60 seconds,
    with background audio.

    :param image_paths: List of 4 file paths to the images to include in order.
    :param audio_path: Path to the MP3 audio file to play in the background.
    :param stock_symbol: Stock symbol to use for naming the output file.
    :param fps: Frames per second for the output video.
    :param total_duration: Total duration of the video in seconds (default is 58 seconds).
    :return: The path to the generated video file.
    """
    
    duration_per_image = total_duration // len(image_paths)
    
    # Create ImageClips
    clips = []
    duration_per_image = total_duration / len(image_paths)  # Calculate duration per image
    for i, img in enumerate(image_paths):
        clip = ImageClip(img).set_duration(duration_per_image)  # Set duration for each clip
        if i > 0:  # Add transition effect for all clips except the first one
            clip = clip.crossfadein(1)  # 1-second crossfade transition
        clips.append(clip)
    
    # Concatenate clips
    video = concatenate_videoclips(clips, method="compose")
    
    # Attach audio
    audio = AudioFileClip(audio_path)
    video = video.set_audio(audio)
    
    # Generate output file name
    file_name = f"{stock_symbol}_{language}_{current_time}.mp4"
    output_path = os.path.join(OUTPUT_DIR, file_name)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Write file
    video.write_videofile(output_path, fps=fps)
    return output_path


# ----------------------------------------------------------------------
# This version is taking file name as input. It should replace the function which is taking prefix as an input. Keeping earlier version for backward compatibility.
# ----------------------------------------------------------------------
def generate_video_from_images(image_paths: list, audio_path: str, file_name: str, fps: int = FPS, total_duration=58,language="english", module: str="horoscope") -> str:
    """
    Creates a video from a list of exactly four images, ensuring the total duration is less than 60 seconds,
    with background audio.

    :param image_paths: List of 4 file paths to the images to include in order.
    :param audio_path: Path to the MP3 audio file to play in the background.
    :param stock_symbol: Stock symbol to use for naming the output file.
    :param fps: Frames per second for the output video.
    :param total_duration: Total duration of the video in seconds (default is 58 seconds).
    :return: The path to the generated video file.
    """
    # Generate output file name
    if not file_name.endswith(".mp4"):
        file_name += ".mp4"
        
    output_path = os.path.join(OUTPUT_DIR, module, file_name)
    # Check if the file already exists
    if os.path.exists(output_path):
        return output_path  # Skip execution and return the existing file path
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    
    # Create ImageClips
    clips = []
    # Load audio to get its duration
    audio = AudioFileClip(audio_path)
    audio_duration = audio.duration  # Duration of the audio file in seconds
    
    # Calculate duration per image based on audio duration
    duration_per_image = audio_duration / len(image_paths)
    
    for i, img in enumerate(image_paths):
        clip = ImageClip(img).set_duration(duration_per_image)  # Set duration for each clip
        if i > 0:  # Add transition effect for all clips except the first one
            clip = clip.crossfadein(1)  # 1-second crossfade transition
        clips.append(clip)
    
    # Concatenate clips
    video = concatenate_videoclips(clips, method="compose")
    
    # Attach audio
    audio = AudioFileClip(audio_path)
    video = video.set_audio(audio)
    
    
    # Write file
    video.write_videofile(output_path, fps=fps)
    return output_path

def combine_videos(video_paths: list, output_file_name: str = "combined_video.mp4", fps: int = FPS) -> dict:
    """
    Combines a list of video files into a single video and returns a JSON containing the path of the new video,
    timestamps of the stitched videos, the source file paths, and the stitched video name.

    :param video_paths: List of file paths to the video files to combine.
    :param output_file_name: Name of the output combined video file.
    :param fps: Frames per second for the output video.
    :return: A dictionary with the path of the new video, timestamps of the stitched videos, source file paths, and the stitched video name.
    """
    from moviepy.editor import VideoFileClip, concatenate_videoclips

    # Load video clips
    clips = []
    timestamps = []
    current_time = 0

    for video_path in video_paths:
        clip = VideoFileClip(video_path)
        clips.append(clip)
        timestamps.append({"start": current_time, "end": current_time + clip.duration, "source": video_path})
        current_time += clip.duration

    # Concatenate video clips
    combined_video = concatenate_videoclips(clips, method="compose")

    # Generate output file path
    if not output_file_name.endswith(".mp4"):
        output_file_name += ".mp4"

    output_path = os.path.join(OUTPUT_DIR, output_file_name)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Write the combined video to file
    combined_video.write_videofile(output_path, fps=fps)

    # Return JSON with details
    return {
        "output_path": output_path,
        "timestamps": timestamps,
        "file_name": output_file_name
    }
