from __future__ import annotations

import json
import os
from pathlib import Path
import time

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload


SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
SHORT_HASHTAGS = "#Shorts #KidsShorts #Phonics #KidsLearning #EducationalShorts #LearnWithMe"


def _credentials() -> Credentials:
    raw = os.environ.get("YOUTUBE_TOKEN_JSON", "").strip()
    info = json.loads(raw) if raw else json.loads(Path("youtube_token.json").read_text(encoding="utf-8"))
    creds = Credentials.from_authorized_user_info(info, SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    if not creds.valid:
        raise RuntimeError("YouTube token is invalid or cannot be refreshed")
    return creds


def _shorts_description(description: str) -> str:
    body = description.strip()
    return f"{body}\n\n{SHORT_HASHTAGS}" if body else SHORT_HASHTAGS


def _video_metadata(title: str, description: str, privacy_status: str) -> dict:
    return {
        "snippet": {
            "title": title[:100],
            "description": _shorts_description(description),
            "categoryId": "27",
            "tags": ["kids", "phonics", "education", "Shorts", "KidsShorts"],
        },
        "status": {"privacyStatus": privacy_status, "selfDeclaredMadeForKids": True},
    }


def _validate_vertical_short(video: Path) -> None:
    import subprocess

    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream=width,height:format=duration", "-of", "json", str(video)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    data = json.loads(result.stdout)
    stream = next((item for item in data.get("streams", []) if item.get("width") and item.get("height")), None)
    duration = float(data.get("format", {}).get("duration", 0))
    if not stream or stream["height"] <= stream["width"]:
        raise RuntimeError("Short upload must be vertical; expected height greater than width")
    if duration <= 0 or duration > 180:
        raise RuntimeError(f"Short upload duration must be between 0 and 180 seconds; got {duration:.2f}")


def upload(video: Path, title: str, description: str, privacy_status: str = "public") -> str:
    _validate_vertical_short(video)
    youtube = build("youtube", "v3", credentials=_credentials(), cache_discovery=False)
    body = _video_metadata(title, description, privacy_status)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=MediaFileUpload(str(video), mimetype="video/mp4", resumable=True, chunksize=4 * 1024 * 1024))
    for attempt in range(5):
        try:
            response = None
            while response is None:
                _, response = request.next_chunk()
            return str(response["id"])
        except HttpError:
            if attempt == 4:
                raise
            time.sleep(2 ** attempt)
    raise RuntimeError("Upload did not return a video ID")
