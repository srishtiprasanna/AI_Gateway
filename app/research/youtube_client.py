import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():

    server_params = StdioServerParameters(
        command="python",
        args=["app/research/youtube_server.py"],
    )

    print("CONNECTING TO YOUTUBE MCP...")
    print("=" * 50)

    async with stdio_client(server_params) as (read, write):

        async with ClientSession(read, write) as session:

            await session.initialize()

            print("\nAVAILABLE YOUTUBE MCP TOOLS")
            print("=" * 50)

            tools = await session.list_tools()

            for tool in tools.tools:
                print(f"\nTool: {tool.name}")
                print(f"Description: {tool.description}")

            print("\nTESTING YOUTUBE SEARCH")
            print("=" * 50)

            result = await session.call_tool(
                "search_youtube",
                {
                    "query": "agentic AI",
                    "max_results": 5
                }
            )

            print("\nYOUTUBE SEARCH RESULTS")
            print("=" * 50)
            print(result)


if __name__ == "__main__":
    asyncio.run(main())