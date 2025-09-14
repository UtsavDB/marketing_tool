"""Compatibility wrapper for image-based OpenAI invocation.

This module exposes a thin proxy around
``generate_script_json.invoke_openai_with_image`` so that other modules can
import it from ``core.invoke_openai_with_image`` without referencing the
larger script generation module directly.
"""

from .generate_script_json import invoke_openai_with_image as _invoke


def invoke_openai_with_image(prompt: str, image_path: str, temperature: float = 0):
    """Invoke OpenAI with a prompt and image.

    This function forwards its arguments to
    :func:`core.generate_script_json.invoke_openai_with_image`.
    """
    return _invoke(prompt, image_path, temperature=temperature)
