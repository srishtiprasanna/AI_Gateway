import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


MCP_URL = "https://search.parallel.ai/mcp"


async def search_web(topic: str):
    """
    Search the web using the Parallel Search MCP server.
    """

    async with streamable_http_client(MCP_URL) as (
        read_stream,
        write_stream,
    ):

        async with ClientSession(read_stream, write_stream) as session:

            # Start MCP session
            await session.initialize()

            # Search the web
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

            return result


async def main():

    topic = "agentic AI"

    print("AI RESEARCH AGENT - WEB SEARCH")
    print("=" * 50)

    result = await search_web(topic)

    print("\nRESEARCH RESULTS")
    print("=" * 50)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())