import os
from io import BytesIO
from pathlib import Path
from dataclasses import dataclass

import boto3
from botocore.response import StreamingBody

from pydub import AudioSegment

INPUT_AUDIO_DIR = Path("contract-song-audio-in")
OUTPUT_AUDIO_DIR = Path("contract-song-audio-out")
ALERT_SOUND_PATH = INPUT_AUDIO_DIR / "smash_challenger_alert.mp3"

# Decode once when the module loads
ALERT_SOUND_AUDIO = AudioSegment.from_file(
    ALERT_SOUND_PATH,
    format="mp3"
)

@dataclass
class PollyResponse:
    AudioStream: StreamingBody
    ContentType: str
    RequestCharacters: int

def get_polly_client():
    return boto3.client(
        "polly",
        region_name=os.getenv("AWS_REGION"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
    )

def generate_polly_audio_file(text: str) -> PollyResponse:
    """
    Takes in Text and returns a PollyResponse Object
    """
    polly = get_polly_client()
    response = polly.synthesize_speech(
        Text=text,
        OutputFormat="mp3",
        VoiceId="Brian"
    )
    polly_response = PollyResponse(
        AudioStream=response.get("AudioStream"),
        ContentType=response.get("ContentType"),
        RequestCharacters=response.get("RequestCharacters")
    )
    return polly_response

def write_combined_audio_file(polly_response: PollyResponse, output_filename: str) -> str:
    if not output_filename.endswith(".mp3"):
        output_filename += ".mp3"

    output_path = OUTPUT_AUDIO_DIR / output_filename

    polly_bytes = polly_response.AudioStream.read()

    polly_audio = AudioSegment.from_file(
        BytesIO(polly_bytes),
        format="mp3"
    )

    combined_audio = ALERT_SOUND_AUDIO + polly_audio

    combined_audio.export(
        output_path,
        format="mp3"
    )

    return str(output_path)
