import os
from dataclasses import dataclass

import boto3
from botocore.response import StreamingBody

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

def write_polly_audio_file(polly_response: PollyResponse, output_filename: str):
    """
    output_filename should be a combo of {SpotifySong.id}-{players}
    """
    audio_bytes = polly_response.AudioStream.read()

    with open(f"contract-song-audio/{output_filename}.mp3", "wb") as f:
        f.write(audio_bytes)
