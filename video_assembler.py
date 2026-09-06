"""
배경 영상 클립들 + 나레이션 음성 + 문장별 자막을 합쳐서
9:16 세로 쇼츠(mp4)를 만듭니다. 순수 ffmpeg CLI만 사용합니다.
"""
import os
import platform
import subprocess
import textwrap
import config


def _find_font_path() -> str:
    """OS별로 사용 가능한 굵은 글꼴 경로를 찾음"""
    system = platform.system()
    candidates = []
    if system == "Windows":
        candidates = [
            r"C:\Windows\Fonts\arialbd.ttf",
            r"C:\Windows\Fonts\malgunbd.ttf",
            r"C:\Windows\Fonts\segoeuib.ttf",
        ]
    elif system == "Darwin":  # macOS
        candidates = [
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]
    else:  # Linux (GitHub Actions 등)
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        ]

    for path in candidates:
        if os.path.exists(path):
            return path

    raise RuntimeError(
        "자막용 폰트를 찾지 못했습니다. video_assembler.py의 _find_font_path()에서 "
        "본인 컴퓨터에 실제로 있는 .ttf 폰트 경로를 candidates 리스트에 추가해주세요."
    )


FONT_PATH = _find_font_path()


def _escape_path_for_ffmpeg(path: str) -> str:
    """ffmpeg drawtext의 fontfile 값에 안전하게 넣기 위해 경로를 이스케이프"""
    path = path.replace("\\", "/")
    path = path.replace(":", r"\:")
    return path


def _escape_drawtext(text: str) -> str:
    """
    ffmpeg drawtext의 text= 값(작은따옴표로 감싼 상태)에 안전하게 넣기 위한 이스케이프.
    작은따옴표는 '\\'' 로 치환해야 함 (따옴표를 닫았다가 이스케이프된 따옴표를 넣고 다시 여는 방식).
    """
    text = text.replace("\\", "\\\\")
    text = text.replace("%", "\\%")
    text = text.replace(":", "\\:")
    text = text.replace("'", "'\\''")
    return text


def _wrap(text: str, width: int = 24) -> str:
    return "\n".join(textwrap.wrap(text, width=width))


def _compute_sentence_timings(sentences, total_duration):
    """문장 길이(글자 수) 비례로 각 문장의 시작/끝 시간을 근사 계산"""
    lengths = [max(len(s), 1) for s in sentences]
    total_len = sum(lengths)
    timings = []
    t = 0.0
    for s, length in zip(sentences, lengths):
        duration = total_duration * (length / total_len)
        timings.append((t, t + duration, s))
        t += duration
    return timings


def build_background(clip_paths, target_duration, out_path):
    """여러 배경 클립을 자르고 이어붙여 target_duration 길이의 9:16 무음 영상 생성"""
    n = len(clip_paths)
    per_clip = max(target_duration / n, 2.0)

    inputs = []
    filters = []
    for i, path in enumerate(clip_paths):
        inputs += ["-i", path]
        filters.append(
            f"[{i}:v]scale=w={config.VIDEO_WIDTH}:h={config.VIDEO_HEIGHT}:"
            f"force_original_aspect_ratio=increase,"
            f"crop={config.VIDEO_WIDTH}:{config.VIDEO_HEIGHT},"
            f"trim=duration={per_clip:.2f},setpts=PTS-STARTPTS[v{i}]"
        )
    concat_inputs = "".join(f"[v{i}]" for i in range(n))
    filters.append(f"{concat_inputs}concat=n={n}:v=1:a=0[bg]")

    filter_complex = ";".join(filters)

    cmd = [
        "ffmpeg", "-y", *inputs,
        "-filter_complex", filter_complex,
        "-map", "[bg]",
        "-t", f"{target_duration:.2f}",
        "-an", out_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return out_path


def add_captions_and_audio(background_path, audio_path, sentences, total_duration, out_path):
    """무음 배경영상에 문장별 자막(drawtext)과 나레이션 오디오를 입힘"""
    timings = _compute_sentence_timings(sentences, total_duration)
    font_for_ffmpeg = _escape_path_for_ffmpeg(FONT_PATH)

    drawtext_filters = []
    for start, end, sentence in timings:
        wrapped = _escape_drawtext(_wrap(sentence))
        drawtext_filters.append(
            "drawtext=fontfile='{font}':text='{text}':"
            "fontcolor=white:fontsize=64:borderw=4:bordercolor=black@0.8:"
            "line_spacing=10:x=(w-text_w)/2:y=h-h/3.2:"
            "enable='between(t,{start:.2f},{end:.2f})'".format(
                font=font_for_ffmpeg, text=wrapped, start=start, end=end
            )
        )
    vf_chain = ",".join(drawtext_filters)

    cmd = [
        "ffmpeg", "-y",
        "-i", background_path,
        "-i", audio_path,
        "-vf", vf_chain,
        "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-c:a", "aac",
        "-shortest",
        out_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("=== ffmpeg 오류 상세 ===")
        print(result.stderr[-3000:])  # 마지막 3000자만 출력 (너무 길지 않게)
        raise RuntimeError("ffmpeg 자막 합성 실패")
    return out_path


def assemble(clip_paths, audio_path, sentences, total_duration, out_path):
    bg_path = os.path.join(config.OUTPUT_DIR, "_bg_temp.mp4")
    build_background(clip_paths, total_duration, bg_path)
    add_captions_and_audio(bg_path, audio_path, sentences, total_duration, out_path)
    os.remove(bg_path)
    return out_path
