"""Render a video by overlaying text onto an image background with audio."""

import os
from datetime import datetime
from core.common import VIDEO_OUTPUT_FOLDER
from moviepy.editor import (
    TextClip,
    AudioFileClip,
    ImageClip,
    CompositeVideoClip,
    concatenate_videoclips,
)

def generate_video_for_paragraphs(text_audio_mapping, background_image_path=None, output_path=None):
    """
    Generate a video using a provided background image with the same resolution.
    Text from paragraphs is rendered on top of the background image for the duration of its audio.

    Args:
        text_audio_mapping (dict): A dict with key "paragraphs", a list of dicts each containing:
            - "text_to_be_rendered": str, the text to display
            - "audio_file_path": str, path to the audio file
        background_image_path (str, optional): Path to the background image file. If None, uses black background.
        output_path (str, optional): Path to save the output video. If None, a timestamped file is created in VIDEO_OUTPUT_FOLDER.

    Returns:
        str: Path to the saved video file.
    """
    # Use black background if image not provided or not found
    if not background_image_path or not os.path.exists(background_image_path):
        from moviepy.editor import ColorClip
        bg_image = ColorClip(size=(1280, 720), color=(0, 0, 0)).set_duration(1)
        font_color = 'white'
        width, height = bg_image.size
    else:
        bg_image = ImageClip(background_image_path)
        font_color = 'white'
        width, height = bg_image.size

    # Ensure output folder exists
    os.makedirs(VIDEO_OUTPUT_FOLDER, exist_ok=True)
    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(VIDEO_OUTPUT_FOLDER, f"video_{timestamp}.mp4")

    clips = []
    for para in text_audio_mapping.get("paragraphs", []):
        text = para.get("text_to_be_rendered", "")
        audio_file = para.get("audio_file_path")
        if not audio_file or not os.path.exists(audio_file):
            continue

        # Load audio clip to get duration
        audio_clip = AudioFileClip(audio_file)
        duration = audio_clip.duration

        # Create a background clip of the same resolution for this duration
        bg_clip = bg_image.set_duration(duration)

        # Create text clip with word-wrap/caption to fit width
        txt_clip = (TextClip(text, fontsize=70, color='white', method='caption', size=(width, None), align='center')
                    .set_duration(duration)
                    .set_position(('center', 'center')))

        # Composite text over the background, and attach audio
        video_clip = CompositeVideoClip([bg_clip, txt_clip]).set_audio(audio_clip)
        clips.append(video_clip)

    if not clips:
        raise RuntimeError("No valid clips to concatenate.")

    # Concatenate all clips and write final video
    final_clip = concatenate_videoclips(clips, method="compose")
    final_clip.write_videofile(output_path, fps=24, codec='libx264', audio_codec='aac')

    return output_path
