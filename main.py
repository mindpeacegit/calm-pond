"""
채널을 지정해서 파이프라인을 실행합니다.

실행 예:
    python main.py --channel psychology
    python main.py --channel quantum_computing
"""
import argparse
import os
import sys

parser = argparse.ArgumentParser(description="채널별 쇼츠 자동 생성/업로드")
parser.add_argument(
    "--channel", required=True,
    help="channels/ 폴더 안의 채널 설정 파일 이름 (확장자 제외). 예: psychology"
)
args = parser.parse_args()
os.environ["CHANNEL_ID"] = args.channel

# config는 CHANNEL_ID가 설정된 뒤에 import 해야 함
import config
import traceback
from datetime import datetime
import script_generator
import tts_generator
import footage_fetcher
import video_assembler
import youtube_uploader


def run_once():
    print(f"채널: {config.CHANNEL['display_name']} ({config.CHANNEL_ID})")

    print("=== 1. 대본 생성 중 ===")
    script = script_generator.generate_script()
    print(f"주제: {script['topic']}")
    print(f"제목: {script['title']}")

    print("=== 2. 나레이션 음성 생성 중 ===")
    audio_path = os.path.join(config.OUTPUT_DIR, "narration.mp3")
    tts_generator.generate_narration(script["narration"], audio_path, config.TTS_VOICE)
    duration = tts_generator.get_audio_duration(audio_path)
    print(f"음성 길이: {duration:.1f}초")

    print("=== 3. 배경 영상 다운로드 중 ===")
    clips = footage_fetcher.download_clips(
        script["search_keywords"], min_total_seconds=duration + 5
    )
    print(f"다운로드된 클립: {len(clips)}개")

    print("=== 4. 영상 합성 중 (시간이 좀 걸립니다) ===")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    final_path = os.path.join(config.OUTPUT_DIR, f"short_{timestamp}.mp4")
    video_assembler.assemble(clips, audio_path, script["sentences"], duration, final_path)
    print(f"완성된 영상: {final_path}")

    print("=== 5. 유튜브 업로드 중 ===")
    video_id = youtube_uploader.upload_short(
        final_path, script["title"], script["description"], script["tags"]
    )
    print(f"완료! channel={config.CHANNEL_ID}, "
          f"privacyStatus={config.YOUTUBE_PRIVACY_STATUS}, video_id={video_id}")

    for c in clips:
        try:
            os.remove(c)
        except OSError:
            pass


if __name__ == "__main__":
    try:
        run_once()
    except Exception:
        print("파이프라인 실행 중 오류 발생:", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)
