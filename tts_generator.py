"""
edge-tts (무료, Microsoft Edge의 온라인 TTS 엔진 이용)로 나레이션 음성을 생성합니다.
API 키가 필요 없습니다.
"""
import asyncio
import subprocess
import edge_tts
import config


async def _synthesize(text: str, out_path: str, voice: str):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(out_path)


def generate_narration(text: str, out_path: str, voice: str = None):
    voice = voice or config.TTS_VOICE
    asyncio.run(_synthesize(text, out_path, voice))
    return out_path


def get_audio_duration(path: str) -> float:
    """ffprobe로 오디오 길이(초)를 반환"""
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", path,
        ],
        capture_output=True, text=True, check=True,
    )
    return float(result.stdout.strip())


if __name__ == "__main__":
    out = generate_narration("This is a test of the automated narration system.", "test.mp3")
    print("saved:", out, "duration:", get_audio_duration(out))
