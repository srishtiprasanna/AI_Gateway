import asyncio
import os

from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


load_dotenv()

API_KEY = os.getenv("MNEMOVERSE_API_KEY")

if not API_KEY:
    raise RuntimeError("MNEMOVERSE_API_KEY is not set.")


async def main():

    server_params = StdioServerParameters(
        command="npx",
        args=[
            "-y",
            "@mnemoverse/mcp-memory-server@latest",
        ],
        env={
            "MNEMOVERSE_API_KEY": API_KEY,
            "MNEMOVERSE_API_URL": "https://core.mnemoverse.com/api/v1",
        },
    )

    print("CONNECTING TO MEMORY MCP...")
    print("=" * 50)

    async with stdio_client(server_params) as (read, write):

        async with ClientSession(read, write) as session:

            await session.initialize()

            print("\nTESTING MEMORY WRITE")
            print("=" * 50)

            write_result = await session.call_tool(
                "memory_write",
                {
                    "content": (
                        "The AI Research Agent project uses five MCP sources: "
                        "arXiv for academic papers, Wikipedia for background "
                        "knowledge, Parallel Search for current web information, "
                        "YouTube for videos and transcripts, and Mnemoverse "
                        "for persistent research memory."
                    )
                }
            )

            print(write_result)

            print("\nTESTING MEMORY READ")
            print("=" * 50)

            read_result = await session.call_tool(
                "memory_read",
                {
                    "query": "AI Research Agent MCP sources"
                }
            )

            print(read_result)


if __name__ == "__main__":
    asyncio.run(main())