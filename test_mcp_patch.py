import asyncio

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


async def run_test():
    p = StdioServerParameters(command='node', args=['C:\\Users\\mauro\\AppData\\Roaming\\npm\\node_modules\\@openbnb\\mcp-server-airbnb\\dist\\index.js'], env={"NODE_TLS_REJECT_UNAUTHORIZED": "0"})
    async with stdio_client(p) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            print("Calling airbnb_listing_price...")
            res = await s.call_tool('airbnb_listing_price', arguments={'id': '1589943047991118285', 'checkin': '2026-08-10', 'checkout': '2026-08-15'})
            print(res.content[0].text)

if __name__ == '__main__':
    asyncio.run(run_test())
