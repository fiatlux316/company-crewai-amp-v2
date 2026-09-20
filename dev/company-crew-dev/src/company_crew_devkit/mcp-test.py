import asyncio
 
from mcp import ClientSession
from mcp.client.streamable_http import (
    streamablehttp_client,
)
 
 
async def main():
 
    url = "http://localhost:8090/mcp"
 
    print("MCP URL:", url)
 
    async with streamablehttp_client(url) as streams:
 
        read_stream = streams[0]
        write_stream = streams[1]
 
        async with ClientSession(
            read_stream,
            write_stream,
        ) as session:
 
            print("Initializing...")
 
            result = await session.initialize()
 
            print("Initialize OK")
            print(result)
 
            tools = await session.list_tools()
 
            print("\nTools:")
 
            for tool in tools.tools:
                print(
                    "-",
                    tool.name,
                    tool.description
                )
 
 
if __name__ == "__main__":
    asyncio.run(main())
 