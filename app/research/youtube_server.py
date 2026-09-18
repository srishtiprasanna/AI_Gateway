from mcp.server.mcpserver import MCPServer
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp

server = MCPServer(
    name="YouTube Research MCP",
    description="MCP server for searching YouTube videos and retrieving transcripts."
)


@server.tool(
    name="search_youtube",
    description="Search YouTube for videos related to a research topic."
)
def search_youtube(query: str, max_results: int = 5) -> str:
    try:
        ydl_opts = {
            "quiet": True,
            "extract_flat": True,
            "skip_download": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            results = ydl.extract_info(
                f"ytsearch{max_results}:{query}",
                download=False
            )

        videos = []

        for entry in results.get("entries", []):
            videos.append({
                "title": entry.get("title"),
                "video_id": entry.get("id"),
                "url": f"https://www.youtube.com/watch?v={entry.get('id')}"
            })

        return str(videos)

    except Exception as e:
        return f"Could not search YouTube: {str(e)}"


@server.tool(
    name="get_transcript",
    description="Get the transcript of a YouTube video using its video ID."
)
def get_transcript(video_id: str) -> str:
    try:
        api = YouTubeTranscriptApi()

        transcript = api.fetch(video_id)

        text = " ".join(
            snippet.text
            for snippet in transcript
        )

        return text

    except Exception as e:
        return f"Could not retrieve transcript: {str(e)}"


if __name__ == "__main__":
    server.run()