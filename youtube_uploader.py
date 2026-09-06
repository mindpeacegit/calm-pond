"""
YouTube Data API v3를 이용해 영상을 업로드합니다.

최초 1회는 반드시 로컬(내 컴퓨터)에서 실행해서 브라우저 로그인 인증을 거쳐야 합니다.
인증이 끝나면 token.json이 생성되고, 이후에는 GitHub Actions 등 무인 환경에서도
token.json만 있으면 자동 업로드가 가능합니다. (README 참고)
"""
import os
import google.auth.transport.requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import config

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def _get_credentials():
    creds = None
    if os.path.exists(config.TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(config.TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(google.auth.transport.requests.Request())
        else:
            # 최초 1회, 로컬 환경에서만 실행 가능 (브라우저 창이 뜸)
            flow = InstalledAppFlow.from_client_secrets_file(
                config.CLIENT_SECRET_PATH, SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open(config.TOKEN_PATH, "w") as f:
            f.write(creds.to_json())
    return creds


def upload_short(video_path, title, description, tags):
    creds = _get_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "tags": tags,
            "categoryId": "27",  # Education
        },
        "status": {
            "privacyStatus": config.YOUTUBE_PRIVACY_STATUS,  # 기본값: private (안전)
            "selfDeclaredMadeForKids": False,
        },
    }

    # 실사같은 합성/변형 콘텐츠 공개 표시 (2024.10 추가된 필드)
    # 순수 스톡영상+TTS 나레이션은 "실제 사람/사건을 조작"하는 콘텐츠가 아니라
    # 필수는 아니지만, 투명성을 위해 기본적으로 켜두는 것을 권장합니다.
    if config.DISCLOSE_SYNTHETIC_MEDIA:
        body["status"]["containsSyntheticMedia"] = True

    media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"업로드 진행률: {int(status.progress() * 100)}%")

    video_id = response["id"]
    print(f"업로드 완료: https://youtube.com/shorts/{video_id}")
    return video_id
