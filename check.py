import asyncio
from mcp import Client

async def main():
    async with Client("http://127.0.0.1:8000/mcp") as client:
        tools = await client.list_tools()
        print([t.name for t in tools.tools])
        result = await client.call_tool("whats_due", {"person": "Mom"})
        print(result.content[0].text)

asyncio.run(main())