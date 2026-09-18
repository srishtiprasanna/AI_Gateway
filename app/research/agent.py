import asyncio
import ast

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client

from app.gateway.client import generate


# ============================================================
# LLM ROUTER
# ============================================================

async def choose_mcps(topic: str):

    prompt = f"""
You are a router inside an AI research agent.

Your task is to decide which research tools are needed for the user's request.

USER REQUEST:
{topic}

AVAILABLE TOOLS:

arxiv:
Use for academic papers, research papers, scientific studies,
scholarly research, or academic evidence.

web:
Use for latest, recent, current, news, trends, or up-to-date information.

youtube:
Use when the user asks for YouTube videos, lectures,
video explanations, demonstrations, or transcripts.

memory:
Use when the user asks about previous research, stored information,
past findings, or previous research context.

IMPORTANT RULES:

1. For "latest", "recent", "current", or "new developments",
   ALWAYS select "web".

2. For academic research or papers,
   select "arxiv".

3. For YouTube videos, lectures, or transcripts,
   select "youtube".

4. For previous or stored research,
   select "memory".

5. You can select more than one tool.

6. You MUST select at least one tool.

7. NEVER return an empty list.

RETURN FORMAT:

Return ONLY a Python-style list.

Examples:

["web"]

["arxiv"]

["youtube"]

["memory"]

["arxiv", "youtube"]

["web", "youtube"]

["arxiv", "web", "youtube"]

Do not explain your answer.
Do not return sentences.
Do not return markdown.
Do not return safety classifications.

Your entire response must be ONLY the list.

USER REQUEST:
{topic}
"""

    valid_mcps = {
        "arxiv",
        "web",
        "youtube",
        "memory",
    }

    for attempt in range(3):

        result = await generate(
            prompt,
            model="fast",
        )

        response = result["response"].strip()

        # ----------------------------------------------------
        # DEBUG: SHOW EXACT LLM RESPONSE
        # ----------------------------------------------------

        print("\n========== ROUTER RAW RESPONSE ==========")
        print(repr(response))
        print("==========================================")

        try:

            selected_mcps = ast.literal_eval(response)

            print(
                "Router parsed result:",
                selected_mcps
            )

            if (
                isinstance(selected_mcps, list)
                and len(selected_mcps) > 0
                and all(
                    mcp in valid_mcps
                    for mcp in selected_mcps
                )
            ):

                return selected_mcps

            print(
                f"⚠ Router returned an invalid/empty list "
                f"(attempt {attempt + 1}/3)"
            )

        except (ValueError, SyntaxError) as e:

            print(
                f"⚠ Could not parse router response "
                f"(attempt {attempt + 1}/3): {e}"
            )

    raise RuntimeError(
        "The LLM router failed to return a valid MCP selection "
        "after 3 attempts."
    )


# ============================================================
# ARXIV MCP
# ============================================================

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


# ============================================================
# PARALLEL SEARCH MCP
# ============================================================

async def search_web(topic: str):

    MCP_URL = "https://search.parallel.ai/mcp"

    async with streamable_http_client(MCP_URL) as (
        read_stream,
        write_stream,
    ):

        async with ClientSession(
            read_stream,
            write_stream,
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


# ============================================================
# YOUTUBE MCP
# ============================================================

async def search_youtube(topic: str):

    server_params = StdioServerParameters(
        command="python",
        args=["app/research/youtube_server.py"],
    )

    async with stdio_client(server_params) as (read, write):

        async with ClientSession(read, write) as session:

            await session.initialize()

            # ------------------------------------------------
            # SEARCH YOUTUBE
            # ------------------------------------------------

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

            # ------------------------------------------------
            # GET TRANSCRIPT
            # ------------------------------------------------

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


# ============================================================
# MEMORY MCP
# ============================================================

async def read_memory(topic: str):

    import os

    from dotenv import load_dotenv

    load_dotenv()

    api_key = os.getenv("MNEMOVERSE_API_KEY")

    if not api_key:

        raise RuntimeError(
            "MNEMOVERSE_API_KEY is not set."
        )

    server_params = StdioServerParameters(
        command="npx",
        args=[
            "-y",
            "@mnemoverse/mcp-memory-server@latest",
        ],
        env={
            "MNEMOVERSE_API_KEY": api_key,
            "MNEMOVERSE_API_URL": (
                "https://core.mnemoverse.com/api/v1"
            ),
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


# ============================================================
# AI GATEWAY - RESEARCH REPORT GENERATION
# ============================================================

async def generate_research_report(
    topic: str,
    selected_mcps: list,
    arxiv_results: str,
    web_results: str,
    youtube_results: dict,
    memory_results: str,
):

    # --------------------------------------------------------
    # BUILD EVIDENCE ONLY FROM SELECTED MCPs
    # --------------------------------------------------------

    evidence_sections = []

    if "arxiv" in selected_mcps:

        evidence_sections.append(
            f"""
====================
ARXIV MCP EVIDENCE
====================

{arxiv_results[:5000]}
"""
        )

    if "web" in selected_mcps:

        evidence_sections.append(
            f"""
====================
WEB SEARCH MCP EVIDENCE
====================

{web_results[:7000]}
"""
        )

    if "youtube" in selected_mcps:

        youtube_text = ""

        if youtube_results["video"]:

            youtube_text = f"""
YouTube Video:
Title: {youtube_results["video"]["title"]}
URL: {youtube_results["video"]["url"]}

Transcript:
{youtube_results["transcript"][:6000]}
"""

        else:

            youtube_text = "No YouTube evidence was retrieved."

        evidence_sections.append(
            f"""
====================
YOUTUBE MCP EVIDENCE
====================

{youtube_text}
"""
        )

    if "memory" in selected_mcps:

        evidence_sections.append(
            f"""
====================
MEMORY MCP EVIDENCE
====================

{memory_results[:3000]}
"""
        )

    evidence = "\n".join(evidence_sections)

    # --------------------------------------------------------
    # SOURCE INFORMATION
    # --------------------------------------------------------

    selected_source_names = []

    if "arxiv" in selected_mcps:
        selected_source_names.append("arXiv")

    if "web" in selected_mcps:
        selected_source_names.append("Web Search")

    if "youtube" in selected_mcps:
        selected_source_names.append("YouTube")

    if "memory" in selected_mcps:
        selected_source_names.append("Memory")

    selected_sources_text = ", ".join(
        selected_source_names
    )

    # --------------------------------------------------------
    # GATEWAY PROMPT
    # --------------------------------------------------------

    prompt = f"""
You are an AI research assistant.

The user asked:

{topic}

The research agent dynamically selected these MCP sources:

{selected_sources_text}

IMPORTANT SOURCE RULES:

1. ONLY use the evidence provided below.

2. Do NOT use your own background knowledge to add facts.

3. Do NOT invent information.

4. Do NOT claim that an MCP was used if it was not selected.

5. If a paper was discovered through the Web Search MCP,
   describe it as a web-discovered source.
   Do NOT say that it came from the arXiv MCP.

6. If arXiv was not selected, do not create or imply
   an arXiv research result.

7. If YouTube was not selected, do not mention any YouTube
   video or transcript.

8. If Memory was not selected, do not claim that previous
   research was retrieved from memory.

9. Every factual claim in the report must be supported by
   the evidence provided below.

10. If the evidence is insufficient, clearly say so.

====================
SELECTED MCP EVIDENCE
====================

{evidence}

====================
REPORT FORMAT
====================

Create a clear research report.

Use these sections:

# 1. Overview

Give a short overview based only on the retrieved evidence.

# 2. Key Findings

List the most important findings from the selected sources.

# 3. Source-Based Findings

Explain the findings according to the MCP sources that were
actually selected.

For example:

## Web Search Findings

Use this section only if web was selected.

## Academic Findings

Use this section only if arxiv was selected.

## YouTube Findings

Use this section only if youtube was selected.

## Memory Findings

Use this section only if memory was selected.

IMPORTANT:
Do not create sections for sources that were not selected.

# 4. Important Takeaways

Summarize the main points supported by the evidence.

# 5. Conclusion

Give a concise conclusion based only on the retrieved evidence.

SOURCE ATTRIBUTION:

When information comes from a particular source, make that clear.

For example:

"According to the web search results..."

"According to the arXiv paper..."

"According to the YouTube transcript..."

"According to the stored memory..."

Do not confuse the source through which information was discovered
with the original publisher of that information.

Keep the report factual, readable, and concise.
"""

    result = await generate(
        prompt,
        model="fast",
    )

    return result


# ============================================================
# DYNAMIC RESEARCH AGENT
# ============================================================

async def research(topic: str):

    print("\n")
    print("=" * 60)
    print("AI RESEARCH AGENT")
    print("=" * 60)

    print(f"\nResearch Topic: {topic}")

    # --------------------------------------------------------
    # STEP 1: LLM ROUTER
    # --------------------------------------------------------

    print("\n[1] Selecting research sources...")

    selected_mcps = await choose_mcps(topic)

    print("\nRouter selected:", selected_mcps)

    # --------------------------------------------------------
    # EMPTY RESULTS
    # --------------------------------------------------------

    arxiv_results = ""

    web_results = ""

    youtube_results = {
        "video": None,
        "transcript": None,
    }

    memory_results = ""

    # --------------------------------------------------------
    # STEP 2: RUN ONLY SELECTED MCPs
    # --------------------------------------------------------

    if "arxiv" in selected_mcps:

        print("\n→ Running arXiv MCP...")

        arxiv_results = await search_arxiv(topic)

        print("✓ arXiv search completed")

    else:

        print("\n→ Skipping arXiv MCP")


    if "web" in selected_mcps:

        print("\n→ Running Web Search MCP...")

        web_results = await search_web(topic)

        print("✓ Web search completed")

    else:

        print("\n→ Skipping Web Search MCP")


    if "youtube" in selected_mcps:

        print("\n→ Running YouTube MCP...")

        youtube_results = await search_youtube(topic)

        print("✓ YouTube search completed")

    else:

        print("\n→ Skipping YouTube MCP")


    if "memory" in selected_mcps:

        print("\n→ Running Memory MCP...")

        memory_results = await read_memory(topic)

        print("✓ Memory search completed")

    else:

        print("\n→ Skipping Memory MCP")


    # --------------------------------------------------------
    # STEP 3: AI GATEWAY SYNTHESIS
    # --------------------------------------------------------

    print("\n[2] Synthesizing research with AI Gateway...")

    gateway_result = await generate_research_report(
        topic,
        selected_mcps,
        arxiv_results,
        web_results,
        youtube_results,
        memory_results,
    )

    print("✓ AI Gateway synthesis completed")

    # --------------------------------------------------------
    # STEP 4: FINAL REPORT
    # --------------------------------------------------------

    print("\n")
    print("=" * 60)
    print("FINAL RESEARCH REPORT")
    print("=" * 60)

    print(gateway_result["response"])

    # --------------------------------------------------------
    # STEP 5: GATEWAY METADATA
    # --------------------------------------------------------

    print("\n")
    print("=" * 60)
    print("AI GATEWAY METADATA")
    print("=" * 60)

    print(
        "Provider:",
        gateway_result["provider"]
    )

    print(
        "Model:",
        gateway_result["model"]
    )

    print(
        "Latency:",
        gateway_result["latency"],
        "seconds"
    )

    print(
        "Usage:",
        gateway_result["usage"]
    )

    # --------------------------------------------------------
    # RETURN RESULT
    # --------------------------------------------------------

    return {
        "topic": topic,

        "selected_mcps": selected_mcps,

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


# ============================================================
# DIRECT TEST
# ============================================================

async def main():

    topic = "What previous research findings do I have about RAG?"
    
    await research(topic)


if __name__ == "__main__":
    asyncio.run(main())