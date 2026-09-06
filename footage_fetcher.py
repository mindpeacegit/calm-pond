"""
Pexels API(무료)에서 키워드에 맞는 세로형(9:16) 스톡 영상을 검색해 다운로드합니다.

Pexels 무료 API는 가끔 일시적으로 401/429를 반환하는 경우가 있어(레이트리밋 등),
자동으로 잠깐 대기 후 재시도하는 로직을 포함합니다.
"""
import os
import time
import requests
import config

PEXELS_SEARCH_URL = "https://api.pexels.com/videos/search"
RETRY_DELAYS = [3, 8, 15]  # 초 단위, 순서대로 대기하며 재시도


def _search_vertical_clips(keyword: str, per_page: int = 5):
    headers = {"Authorization": config.PEXELS_API_KEY}
    params = {"query": keyword, "orientation": "portrait", "per_page": per_page}

    last_error = None
    for attempt, delay in enumerate([0] + RETRY_DELAYS, start=1):
        if delay:
            print(f"  Pexels 요청 실패, {delay}초 대기 후 재시도 ({attempt}/{len(RETRY_DELAYS)+1})...")
            time.sleep(delay)
        resp = requests.get(PEXELS_SEARCH_URL, headers=headers, params=params, timeout=30)
        if resp.status_code == 200:
            return resp.json().get("videos", [])
        last_error = resp

    last_error.raise_for_status()
    return []


def _best_file_url(video: dict) -> str:
    """세로형 HD 파일 우선 선택"""
    files = sorted(
        [f for f in video["video_files"] if f.get("width", 0) <= f.get("height", 1)],
        key=lambda f: f.get("height", 0),
        reverse=True,
    )
    if not files:
        files = video["video_files"]
    return files[0]["link"]


def download_clips(keywords: list, min_total_seconds: float) -> list:
    """
    키워드 리스트로 영상을 검색하고, 합쳐서 min_total_seconds 이상 되도록
    로컬에 다운로드한 뒤 파일 경로 리스트를 반환합니다.
    """
    downloaded = []
    total_duration = 0.0

    for keyword in keywords:
        if total_duration >= min_total_seconds:
            break
        print(f"  검색 중: '{keyword}'")
        clips = _search_vertical_clips(keyword)
        for clip in clips:
            if total_duration >= min_total_seconds:
                break
            url = _best_file_url(clip)
            filename = os.path.join(config.ASSETS_DIR, f"clip_{len(downloaded)}.mp4")
            with requests.get(url, stream=True, timeout=60) as r:
                r.raise_for_status()
                with open(filename, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1 << 20):
                        f.write(chunk)
            downloaded.append(filename)
            total_duration += clip.get("duration", 5)

    if not downloaded:
        raise RuntimeError(
            f"'{keywords}' 키워드로 배경 영상을 찾지 못했습니다. "
            "키워드를 더 일반적인 영어 단어로 바꿔보세요."
        )
    return downloaded


if __name__ == "__main__":
    files = download_clips(["ocean", "space"], min_total_seconds=20)
    print(files)
