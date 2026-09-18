import asyncio
import ast

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client

from app.gateway.client import generate


# --------------------------------------------------
# 1. ARXIV MCP
# --------------------------------------------------

async def search_arxiv(topic: str):

    server_params = StdioServerParameters(
        command="uvx",
        args=["arxiv-mcp-server"],
    )

    async with stdio_client(server_params) as (read, write):

        async with ClientSession(read, write) as session:

            await session.initialize()

            result = await session.call_tool(
                "search_papers",
                {
                    "query": topic,
                    "max_results": 3,
                    "abstract_mode": "snippet",
                },
            )

            return result.content[0].text


# --------------------------------------------------
# 2. WEB SEARCH MCP
# --------------------------------------------------

async def search_web(topic: str):

    MCP_URL = "https://search.parallel.ai/mcp"

    async with streamable_http_client(MCP_URL) as (
        read_stream,
        write_stream,
    ):

        async with ClientSession(
            read_stream,
            write_stream
        ) as session:

            await session.initialize()

            result = await session.call_tool(
                "web_search",
                {
                    "objective": f"Find reliable information about {topic}",
                    "search_queries": [
                        f"{topic} overview",
                        f"{topic} research",
                        f"{topic} applications",
                    ],
                },
            )

            return result.content[0].text


# --------------------------------------------------
# 3. YOUTUBE MCP
# --------------------------------------------------

async def search_youtube(topic: str):

    server_params = StdioServerParameters(
        command="python",
        args=["app/research/youtube_server.py"],
    )

    async with stdio_client(server_params) as (read, write):

        async with ClientSession(read, write) as session:

            await session.initialize()

            search_result = await session.call_tool(
                "search_youtube",
                {
                    "query": topic,
                    "max_results": 3,
                },
            )

            videos = ast.literal_eval(
                search_result.structured_content["result"]
            )

            if not videos:
                return {
                    "video": None,
                    "transcript": None,
                }

            selected_video = videos[0]

            transcript_result = await session.call_tool(
                "get_transcript",
                {
                    "video_id": selected_video["video_id"],
                },
            )

            transcript = transcript_result.content[0].text

            return {
                "video": selected_video,
                "transcript": transcript,
            }


# --------------------------------------------------
# 4. MEMORY MCP
# --------------------------------------------------

async def read_memory(topic: str):

    import os
    from dotenv import load_dotenv

    load_dotenv()

    api_key = os.getenv("MNEMOVERSE_API_KEY")

    if not api_key:
        raise RuntimeError("MNEMOVERSE_API_KEY is not set.")

    server_params = StdioServerParameters(
        command="npx",
        args=[
            "-y",
            "@mnemoverse/mcp-memory-server@latest",
        ],
        env={
            "MNEMOVERSE_API_KEY": api_key,
            "MNEMOVERSE_API_URL": "https://core.mnemoverse.com/api/v1",
        },
    )

    async with stdio_client(server_params) as (read, write):

        async with ClientSession(read, write) as session:

            await session.initialize()

            result = await session.call_tool(
                "memory_read",
                {
                    "query": topic,
                },
            )

            return result.content[0].text


# --------------------------------------------------
# 5. AI GATEWAY SYNTHESIS
# --------------------------------------------------

async def generate_research_report(
    topic: str,
    arxiv_results: str,
    web_results: str,
    youtube_results: dict,
    memory_results: str,
):

    youtube_text = ""

    if youtube_results["video"]:

        youtube_text = f"""
YouTube Video:
Title: {youtube_results["video"]["title"]}
URL: {youtube_results["video"]["url"]}

Transcript:
{youtube_results["transcript"][:6000]}
"""

    prompt = f"""
You are an AI research assistant.

The user asked you to research:

{topic}

You have collected evidence from multiple MCP sources.

IMPORTANT:
- Do not answer purely from your own knowledge.
- Base your report primarily on the evidence provided below.
- Clearly distinguish information from different sources.
- Do not invent papers, URLs, statistics, or claims.
- If the evidence is insufficient, say so.

====================
ARXIV EVIDENCE
====================

{arxiv_results[:5000]}


====================
WEB SEARCH EVIDENCE
====================

{web_results[:7000]}


====================
YOUTUBE EVIDENCE
====================

{youtube_text}


====================
MEMORY EVIDENCE
====================

{memory_results[:3000]}


====================
TASK
====================

Create a clear research report with these sections:

1. Overview
2. Key Findings
3. Academic Research
4. Current Web Information
5. YouTube Explanation
6. Important Takeaways
7. Conclusion

For academic papers, mention the paper title and explain its main relevance.

For the YouTube source, include the video title and URL and summarize what the transcript explains.

Keep the report factual, readable, and concise.
"""

    result = await generate(
        prompt,
        model="fast",
    )

    return result


# --------------------------------------------------
# 6. MAIN RESEARCH AGENT
# --------------------------------------------------

async def research(topic: str):

    print("\n")
    print("=" * 60)
    print("AI RESEARCH AGENT")
    print("=" * 60)

    print(f"\nResearch Topic: {topic}")

    print("\n[1/5] Searching academic papers...")
    arxiv_results = await search_arxiv(topic)
    print("✓ arXiv search completed")

    print("\n[2/5] Searching the web...")
    web_results = await search_web(topic)
    print("✓ Web search completed")

    print("\n[3/5] Searching YouTube...")
    youtube_results = await search_youtube(topic)
    print("✓ YouTube search completed")

    print("\n[4/5] Checking research memory...")
    memory_results = await read_memory(topic)
    print("✓ Memory search completed")

    print("\n[5/5] Synthesizing research with AI Gateway...")
    gateway_result = await generate_research_report(
        topic,
        arxiv_results,
        web_results,
        youtube_results,
        memory_results,
    )
    print("✓ AI Gateway synthesis completed")

    print("\n")
    print("=" * 60)
    print("FINAL RESEARCH REPORT")
    print("=" * 60)

    print(gateway_result["response"])

    print("\n")
    print("=" * 60)
    print("AI GATEWAY METADATA")
    print("=" * 60)

    print("Provider:", gateway_result["provider"])
    print("Model:", gateway_result["model"])
    print("Latency:", gateway_result["latency"], "seconds")
    print("Usage:", gateway_result["usage"])

    return {
        "topic": topic,
        "report": gateway_result["response"],
        "sources": {
            "arxiv": arxiv_results,
            "web": web_results,
            "youtube": youtube_results,
            "memory": memory_results,
        },
        "gateway": {
            "provider": gateway_result["provider"],
            "model": gateway_result["model"],
            "latency": gateway_result["latency"],
            "usage": gateway_result["usage"],
        },
    }


async def main():

    topic = "agentic AI"

    await research(topic)


if __name__ == "__main__":
    asyncio.run(main())