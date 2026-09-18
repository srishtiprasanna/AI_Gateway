import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():

    server_params = StdioServerParameters(
        command="wikipedia-mcp",
        args=[],
    )

    print("CONNECTING TO WIKIPEDIA MCP...")
    print("=" * 50)

    async with stdio_client(server_params) as (read, write):

        async with ClientSession(read, write) as session:

            await session.initialize()

            print("\nAVAILABLE WIKIPEDIA MCP TOOLS")
            print("=" * 50)

            tools = await session.list_tools()

            for tool in tools.tools:
                print(f"\nTool: {tool.name}")
                print(f"Description: {tool.description}")

            print("\nWIKIPEDIA MCP CONNECTED SUCCESSFULLY!")


if __name__ == "__main__":
    asyncio.run(main())