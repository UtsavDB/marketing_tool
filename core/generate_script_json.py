import os
import argparse
import base64

from openai import AzureOpenAI
import sys
from datetime import datetime
from core.common import debug_print


def invoke_openai(prompt):
    """
    Invoke OpenAI API with the given prompt and parameters.
    Compatible with OpenAI Python SDK v1.0+.
    """
    # Make sure these are set in your environment or .env
    api_key     = os.getenv("OPENAI_API_KEY")
    api_base    = os.getenv("OPENAI_API_BASE")
    api_version = os.getenv("OPENAI_API_VERSION")
    model = os.getenv("OPENAI_DEPLOYMENT_NAME")
    
    if not all([api_key, api_base, api_version]):
        raise RuntimeError("Please set OPENAI_API_KEY, OPENAI_API_BASE and OPENAI_API_VERSION")

    client = AzureOpenAI(
        api_key=api_key,
        api_version=api_version,
        azure_endpoint=api_base
    )

    debug_print("Invoking OpenAI API with model:", model)

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content
