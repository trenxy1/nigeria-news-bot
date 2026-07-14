"""
Step 6: Upload the finished video to YouTube.

ONE-TIME SETUP:
1. Go to https://console.cloud.google.com/ -> create a project.
2. Enable "YouTube Data API v3" for that project.
3. Go to "Credentials" -> Create Credentials -> OAuth client ID -> type "Desktop app".
4. Download the JSON, save it as client_secret.json in this folder
   (path is set in config.YOUTUBE_CLIENT_SECRET_FILE).
5. First time you run this script it will open a browser window asking you
   to log into the YouTube account you want to upload to. After you approve,
   a youtube_token.json is saved so you won't have to log in again.

Install deps: pip install google-auth-oauthlib google-api-python-client --break-system-packages
"""
import json
from pathlib import Path

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.http
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

import config

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def _get_authenticated_service():
    """
    Loads credentials in this order:
    1. YOUTUBE_TOKEN_JSON env var / GitHub Secret (used in CI — no browser available)
    2. Local youtube_token.json file (used the one time you run this interactively,
       e.g. in a GitHub Codespace, to generate that token in the first place)
    """
    creds = None

    if config.YOUTUBE_TOKEN_JSON_ENV:
        creds = Credentials.from_authorized_user_info(
            json.loads(config.YOUTUBE_TOKEN_JSON_ENV), SCOPES
        )
    else:
        token_path = Path(config.YOUTUBE_TOKEN_FILE)
        if token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not Path(config.YOUTUBE_CLIENT_SECRET_FILE).exists():
                raise RuntimeError(
                    f"Missing {config.YOUTUBE_CLIENT_SECRET_FILE}. This one-time auth step "
                    "must be run interactively (e.g. in a GitHub Codespace), not in CI. "
                    "See README.md 'One-time YouTube authorization' section."
                )
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                config.YOUTUBE_CLIENT_SECRET_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)
        Path(config.YOUTUBE_TOKEN_FILE).write_text(creds.to_json())
        print("Save the contents of youtube_token.json as a GitHub Secret named "
              "YOUTUBE_TOKEN_JSON so future automated runs don't need to re-authenticate.")

    return googleapiclient.discovery.build("youtube", "v3", credentials=creds)


def upload_video(video_path: Path, title: str, description: str,
                  tags: list[str] | None = None, privacy: str = "unlisted") -> str:
    """privacy: 'private' | 'unlisted' | 'public'. Start with 'unlisted' to review."""
    youtube = _get_authenticated_service()

    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags or config.YOUTUBE_DEFAULT_TAGS,
            "categoryId": config.YOUTUBE_CATEGORY_ID,
        },
        "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": False},
    }

    media = googleapiclient.http.MediaFileUpload(str(video_path), chunksize=-1, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Uploading... {int(status.progress() * 100)}%")

    video_id = response["id"]
    print(f"[OK] Uploaded: https://youtu.be/{video_id}")
    return video_id


if __name__ == "__main__":
    print("Import and call upload_video(...) from main.py after a video is built.")
  
