"""
멀티 채널 설정.

실행 시 main.py --channel psychology 처럼 채널을 지정하면,
channels/psychology.json 설정을 불러와서 그 채널 전용으로 동작합니다.
(대본 스타일, 유튜브 업로드 계정, 생성 이력이 채널마다 완전히 분리됩니다)
"""
import json
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# main.py가 실행 시 os.environ["CHANNEL_ID"]를 먼저 세팅해줍니다.
CHANNEL_ID = os.environ.get("CHANNEL_ID")
if not CHANNEL_ID:
    raise SystemExit(
        "채널이 지정되지 않았습니다.\n"
        "실행 예: python main.py --channel psychology\n"
        f"(channels/ 폴더 목록: {os.listdir(os.path.join(BASE_DIR, 'channels'))})"
    )

CHANNEL_CONFIG_PATH = os.path.join(BASE_DIR, "channels", f"{CHANNEL_ID}.json")
if not os.path.exists(CHANNEL_CONFIG_PATH):
    raise SystemExit(
        f"channels/{CHANNEL_ID}.json 파일이 없습니다. "
        "먼저 channels/ 폴더 안에 해당 이름의 채널 설정 파일을 만들어주세요."
    )

with open(CHANNEL_CONFIG_PATH, "r", encoding="utf-8") as f:
    CHANNEL = json.load(f)

# --- 공용 API 키 (모든 채널이 공유) ---
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

# --- 업로드 옵션 ---
YOUTUBE_PRIVACY_STATUS = os.getenv("YOUTUBE_PRIVACY_STATUS", "private")
DISCLOSE_SYNTHETIC_MEDIA = os.getenv("DISCLOSE_SYNTHETIC_MEDIA", "true").lower() == "true"

# --- 생성 설정 ---
CLAUDE_MODEL = "claude-sonnet-5"
TTS_VOICE = CHANNEL.get("tts_voice", "en-US-AriaNeural")
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920

# --- 채널별로 완전히 분리되는 경로 ---
DATA_DIR = os.path.join(BASE_DIR, "data", CHANNEL_ID)
OUTPUT_DIR = os.path.join(DATA_DIR, "output")
ASSETS_DIR = os.path.join(DATA_DIR, "assets")
USED_TOPICS_PATH = os.path.join(DATA_DIR, "used_topics.json")

CREDENTIALS_DIR = os.path.join(BASE_DIR, "credentials")
TOKEN_PATH = os.path.join(CREDENTIALS_DIR, f"token_{CHANNEL_ID}.json")
CLIENT_SECRET_PATH = os.path.join(CREDENTIALS_DIR, f"client_secret_{CHANNEL_ID}.json")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)
os.makedirs(CREDENTIALS_DIR, exist_ok=True)
