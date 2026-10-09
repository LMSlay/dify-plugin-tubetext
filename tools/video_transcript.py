import re
from typing import Any

from dify_plugin import Tool

from tools.common import TubeTextMixin, transcripts_as_text
from tubetext_client import TubeTextError, split_list, to_int

YOUTUBE_RE = re.compile(r"(^|[/.])(youtube\.com|youtu\.be)(/|$)|^[A-Za-z0-9_-]{11}$", re.I)
TIKTOK_RE = re.compile(r"(^|[/.])tiktok\.com(/|$)|^\d{15,21}$", re.I)


def platform_of(link: str) -> str | None:
    host_and_path = re.sub(r"^https?://", "", link.strip())
    if TIKTOK_RE.search(host_and_path):
        return "tiktok"
    if YOUTUBE_RE.search(host_and_path):
        return "youtube"
    return None


class VideoTranscriptTool(TubeTextMixin, Tool):
    simple_fields = [
        "status", "platform", "input", "url", "title", "author", "durationSeconds", "viewCount",
        "publishedAt", "language", "source", "wordCount", "transcript", "timestampedText", "error",
    ]

    def build_jobs(self, params: dict[str, Any]) -> list[tuple[str, dict[str, Any], int]]:
        links = split_list(params.get("urls"))
        if not links:
            raise TubeTextError("Add at least one YouTube or TikTok link in 'Links'.")
        if len(links) > 50:
            raise TubeTextError("'Links' accepts up to 50 links per call.")
        youtube, tiktok, unknown = [], [], []
        for link in links:
            {"youtube": youtube, "tiktok": tiktok}.get(platform_of(link), unknown).append(link)
        if unknown:
            raise TubeTextError(
                "These are not YouTube or TikTok links: " + ", ".join(unknown[:5])
                + ". 'Links' accepts YouTube videos, Shorts, playlists, channels and TikTok videos."
            )
        timestamps = bool(params.get("timestamps", True))
        ai = bool(params.get("ai_transcription", False))
        languages = split_list(params.get("languages"))
        jobs = []
        if youtube:
            per_source = to_int(params.get("max_videos"), 5, 1, 100)
            jobs.append(("youtube_transcript", {
                "urls": youtube,
                "languages": languages or ["en"],
                "maxVideosPerSource": per_source,
                "includeTimestampedText": timestamps,
                "aiFallback": ai,
            }, len(youtube) * per_source))
        if tiktok:
            jobs.append(("tiktok_transcript", {
                "urls": tiktok,
                "languages": languages,
                "aiTranscription": "missing" if ai else "off",
                "includeTimestampedText": timestamps,
            }, len(tiktok)))
        return jobs

    def normalize(self, actor_key: str, item: dict[str, Any]) -> dict[str, Any]:
        if actor_key == "tiktok_transcript":
            extra = {
                "platform": "tiktok",
                "title": item.get("description"),
                "author": item.get("authorUsername"),
                "viewCount": item.get("playCount"),
                "publishedAt": item.get("createTime"),
            }
        else:
            extra = {
                "platform": "youtube",
                "author": item.get("channelName"),
                "publishedAt": item.get("publishDate"),
            }
        return {**item, **{k: v for k, v in extra.items() if v is not None}}

    def to_text(self, items: list[dict[str, Any]]) -> str | None:
        return transcripts_as_text(items) if items else None
