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
BILINGUAL_DESCRIPTION = "Learn English words with clear pictures. बच्चों के लिए English words और pronunciation सीखें।"
SHORT_TAGS = [
    "phonics",
    "abc song",
    "alphabet",
    "kids learning",
    "abcd",
    "phonics song",
    "learn abc",
    "kids education",
    "preschool",
    "kindergarten",
    "toddlers",
    "nursery rhyme",
    "kids phonics",
    "letter sounds",
    "educational",
    "Shorts",
    "KidsShorts",
    "youtube shorts",
    "kids shorts",
    "children",
    "baby songs",
    "abc kids",
    "english alphabet",
    "English for kids",
    "Hindi learning",
]


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
    body = description.strip()[:4500]
    parts = [part for part in (body, BILINGUAL_DESCRIPTION, SHORT_HASHTAGS) if part]
    return "\n\n".join(parts)


def _video_metadata(title: str, description: str, privacy_status: str) -> dict:
    return {
        "snippet": {
            "title": title[:100],
            "description": _shorts_description(description),
            "categoryId": "27",
            "tags": SHORT_TAGS,
        },
        "status": {"privacyStatus": privacy_status, "selfDeclaredMadeForKids": True},
    }


def upload(video: Path, title: str, description: str, privacy_status: str = "public", thumbnail: Path | None = None) -> str:
    youtube = build("youtube", "v3", credentials=_credentials(), cache_discovery=False)
    body = _video_metadata(title, description, privacy_status)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=MediaFileUpload(str(video), mimetype="video/mp4", resumable=True, chunksize=4 * 1024 * 1024))
    for attempt in range(5):
        try:
            response = None
            while response is None:
                _, response = request.next_chunk()
            video_id = str(response["id"])
            if thumbnail and thumbnail.exists():
                try:
                    youtube.thumbnails().set(
                        videoId=video_id,
                        media_body=MediaFileUpload(str(thumbnail), mimetype="image/jpeg"),
                    ).execute()
                except HttpError:
                    pass
            return video_id
        except HttpError:
            if attempt == 4:
                raise
            time.sleep(2 ** attempt)
    raise RuntimeError("Upload did not return a video ID")
