import os
import subprocess
import tempfile

import yt_dlp

# Duración de cada segmento al dividir audio largo (segundos)
CHUNK_DURATION_SEC = 600  # 10 min

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Cache model in a module-level variable to avoid reloading (lazy import to let app start)
_whisper_models = {}


def _get_model(model_size: str = "small"):
    from faster_whisper import WhisperModel
    if model_size not in _whisper_models:
        _whisper_models[model_size] = WhisperModel(
            model_size,
            device="cpu",
            compute_type="int8",
            download_root=os.environ.get("WHISPER_CACHE", "/app/data/whisper_models"),
        )
    return _whisper_models[model_size]


def download_audio(url: str) -> tuple[str | None, str | None]:
    """
    Download audio only from YouTube URL. Returns (path_to_audio_file, error_message).
    Caller must delete the file when done.
    """
    tmp = tempfile.NamedTemporaryFile(prefix="yt_", delete=False, suffix=".mp3")
    tmp.close()
    base = tmp.name  # e.g. /tmp/yt_xxx.mp3 -> we use base without .mp3 for outtmpl
    base_no_ext = base.rsplit(".", 1)[0] if "." in base else base
    outtmpl = base_no_ext + ".%(ext)s"
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "user_agent": USER_AGENT,
        "format": "bestaudio/best",
        "outtmpl": outtmpl,
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}],
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        mp3_path = base_no_ext + ".mp3"
        if os.path.isfile(mp3_path) and os.path.getsize(mp3_path) > 0:
            for f in os.listdir(os.path.dirname(base_no_ext)):
                p = os.path.join(os.path.dirname(base_no_ext), f)
                if p != mp3_path and p.startswith(base_no_ext):
                    try:
                        os.remove(p)
                    except OSError:
                        pass
            return mp3_path, None
        return None, "No se pudo extraer el audio."
    except yt_dlp.utils.DownloadError as e:
        for f in os.listdir(os.path.dirname(base_no_ext)):
            if f.startswith(os.path.basename(base_no_ext)):
                try:
                    os.remove(os.path.join(os.path.dirname(base_no_ext), f))
                except OSError:
                    pass
        return None, str(e).split("\n")[0] if str(e) else "Error al descargar el audio."
    except Exception as e:
        for f in os.listdir(os.path.dirname(base_no_ext)):
            if f.startswith(os.path.basename(base_no_ext)):
                try:
                    os.remove(os.path.join(os.path.dirname(base_no_ext), f))
                except OSError:
                    pass
        return None, str(e)[:200]


def get_audio_duration(audio_path: str) -> float:
    """
    Return duration in seconds using ffprobe. Returns 0.0 on error.
    """
    try:
        out = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                audio_path,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if out.returncode == 0 and out.stdout.strip():
            return float(out.stdout.strip())
    except (subprocess.TimeoutExpired, ValueError, FileNotFoundError):
        pass
    return 0.0


def split_audio_into_chunks(
    audio_path: str,
    chunk_sec: int = CHUNK_DURATION_SEC,
) -> list[str]:
    """
    Split audio into chunks of chunk_sec seconds with ffmpeg.
    Returns list of paths to chunk files (same dir as audio_path).
    Caller must delete the returned files when done.
    """
    duration = get_audio_duration(audio_path)
    if duration <= 0:
        return []
    if duration <= chunk_sec:
        return [audio_path]

    base_dir = os.path.dirname(audio_path)
    base_name = os.path.splitext(os.path.basename(audio_path))[0]
    chunk_paths = []
    start = 0.0
    idx = 0
    while start < duration:
        chunk_path = os.path.join(base_dir, f"{base_name}_chunk{idx:04d}.mp3")
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i", audio_path,
                    "-ss", str(start),
                    "-t", str(chunk_sec),
                    "-acodec", "copy",
                    "-vn",
                    chunk_path,
                ],
                capture_output=True,
                timeout=120,
            )
            if os.path.isfile(chunk_path) and os.path.getsize(chunk_path) > 0:
                chunk_paths.append(chunk_path)
            else:
                try:
                    os.remove(chunk_path)
                except OSError:
                    pass
        except (subprocess.TimeoutExpired, FileNotFoundError):
            break
        start += chunk_sec
        idx += 1
    return chunk_paths


def transcribe_audio(
    audio_path: str,
    model_size: str = "small",
    language: str | None = None,
    include_timestamps: bool = True,
    time_offset_sec: float = 0.0,
) -> str:
    """
    Transcribe audio file with faster-whisper. Returns full transcript text.
    time_offset_sec: add this to each segment start (for concatenating chunked transcripts).
    """
    model = _get_model(model_size)
    lang = None if (language == "auto" or not language) else language
    segments, info = model.transcribe(audio_path, language=lang, word_timestamps=False)
    lines = []
    for seg in segments:
        if include_timestamps:
            start = int(seg.start) + int(time_offset_sec)
            m, s = divmod(start, 60)
            h, m = divmod(m, 60)
            ts = f"{h:02d}:{m:02d}:{s:02d}"
            lines.append(f"[{ts}] {seg.text.strip()}")
        else:
            lines.append(seg.text.strip())
    return "\n".join(lines).strip()
