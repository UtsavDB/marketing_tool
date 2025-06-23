import openai
import os
from datetime import datetime

def generate_audio_from_script(script, voice="alloy", model="tts-1", output_dir="output/audio"):
    """
    Generate speech audio from a script using OpenAI's text-to-speech API.
    Returns the path to the saved audio file.
    """

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"audio_{timestamp}.mp3"
    output_path = os.path.join(output_dir, filename)

    response = openai.audio.speech.create(
        model=model,
        voice=voice,
        input=script
    )
    response.save(output_path)
    return output_path