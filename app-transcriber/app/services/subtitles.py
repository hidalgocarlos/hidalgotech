import os
import re
import tempfile

import yt_dlp

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def _parse_vtt_srt(content: str, include_timestamps: bool) -> str:
    """Parse VTT or SRT content to plain text, optionally with timestamps."""
    lines = content.strip().splitlines()
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Skip WEBVTT header and empty lines
        if line.strip().startswith("WEBVTT") or not line.strip():
            i += 1
            continue
        # Skip sequence number (SRT) or timestamp line (00:00:00.000 --> 00:00:02.000)
        if re.match(r"^\d+$", line.strip()):
            i += 1
            if i < len(lines) and re.match(r"^\d{2}:\d{2}", lines[i]):
                if include_timestamps:
                    ts = lines[i].split("-->")[0].strip()
                    result.append(f"[{ts}]")
                i += 1
            continue
        if re.match(r"^\d{2}:\d{2}", line):
            if include_timestamps and "-->" in line:
                ts = line.split("-->")[0].strip()
                result.append(f"[{ts}]")
            i += 1
            continue
        # Text line
        text = line.strip()
        if text and not text.startswith("NOTE"):
            result.append(text)
        i += 1
    return "\n".join(result) if result else ""


def get_subtitles(url: str, language: str = "auto", include_timestamps: bool = True) -> tuple[str | None, str | None]:
    """
    Try to get subtitles for a YouTube video via yt-dlp.
    Returns (transcript_text, error_message). transcript_text is None on failure.
    """
    with tempfile.TemporaryDirectory(prefix="transcriber_subs_") as tmpdir:
        outtmpl = os.path.join(tmpdir, "%(id)s")
        langs = ["es", "en", "a.*"] if language == "auto" else [language, "a.*"]
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "user_agent": USER_AGENT,
            "skip_download": True,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": langs,
            "subtitlesformat": "vtt/best",
            "outtmpl": outtmpl,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
            if not info:
                return None, "No se pudo obtener información del vídeo."
            # Find subtitle file in tmpdir
            for f in os.listdir(tmpdir):
                if f.endswith(".vtt") or f.endswith(".srt"):
                    path = os.path.join(tmpdir, f)
                    with open(path, "r", encoding="utf-8", errors="replace") as fp:
                        raw = fp.read()
                    text = _parse_vtt_srt(raw, include_timestamps)
                    if text.strip():
                        return text.strip(), None
            return None, "No hay subtítulos disponibles para este vídeo."
        except yt_dlp.utils.DownloadError as e:
            return None, str(e).split("\n")[0] if str(e) else "Error al obtener subtítulos."
        except Exception as e:
            return None, str(e)[:200]
