import asyncio

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


async def test():
    p = StdioServerParameters(command='uv', args=['run', 'python', 'mcp_server.py'])
    async with stdio_client(p) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            res = await s.call_tool('get_pure_rate', arguments={'apartment_id': '1589943047991118285', 'date': '2026-06-30'})
            print(res.content[0].text)

if __name__ == '__main__':
    asyncio.run(test())
