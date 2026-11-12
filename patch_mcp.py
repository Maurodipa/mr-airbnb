
mcp_path = r"C:\Users\mauro\AppData\Roaming\npm\node_modules\@openbnb\mcp-server-airbnb\dist\index.js"

with open(mcp_path, encoding="utf-8") as f:
    content = f.read()

# 1. Add AIRBNB_LISTING_PRICE_TOOL
tool_def = """
const AIRBNB_LISTING_PRICE_TOOL = {
    name: "airbnb_listing_price",
    description: "Get the pricing details for a specific Airbnb listing.",
    inputSchema: {
        type: "object",
        properties: {
            id: { type: "string", description: "The Airbnb listing ID" },
            checkin: { type: "string", description: "Check-in date (YYYY-MM-DD)" },
            checkout: { type: "string", description: "Check-out date (YYYY-MM-DD)" }
        },
        required: ["id", "checkin", "checkout"]
    }
};
"""

if "AIRBNB_LISTING_PRICE_TOOL" not in content:
    content = content.replace("const AIRBNB_TOOLS = [", tool_def + "\nconst AIRBNB_TOOLS = [\n    AIRBNB_LISTING_PRICE_TOOL,")

# 2. Add handleAirbnbListingPrice
handler_def = """
async function handleAirbnbListingPrice(params) {
    const { id, checkin, checkout } = params;
    const url = "https://www.airbnb.com/api/v3/StaysPdpBookItQuery";
    const b64Id = Buffer.from(`DemandStayListing:${id}`).toString('base64');
    
    const payload = {
        operationName: "StaysPdpBookItQuery",
        variables: {
            id: b64Id,
            dateRange: { startDate: checkin, endDate: checkout },
            guestCounts: { numberOfAdults: 2 },
            includePdpMigrationBookItCalendarSheetFragment: true,
            includePdpMigrationBookItFloatingFooterFragment: true,
            includePdpMigrationBookItNavFragment: true,
            includePdpMigrationBookItSidebarFragment: true,
            includePdpMigrationCancellationPolicyPickerModalFragment: true,
            includeOverviewMerchandisingTipsFragment: true
        },
        extensions: { persistedQuery: { version: 1, sha256Hash: "9dfddf66545e678cb5cb06e0ce5a327e5cbd13309254d94d11500c91d9fbcd40" } }
    };
    
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Airbnb-API-Key': 'd306zoyjsyarp7ifhu67rjxn52tv0t20',
                'X-Airbnb-Currency': 'EUR',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            },
            body: JSON.stringify(payload)
        });
        const data = await response.json();
        const bookIt = data?.data?.node?.pdpPresentation?.bookIt;
        let available = true;
        if (bookIt?.availability?.isAvailable === false) {
            available = false;
        }
        const priceDetails = bookIt?.structuredDisplayPrice?.explanationData?.priceDetails;
        const minStay = bookIt?.availability?.minNights || 1;
        
        return {
            content: [{
                type: "text",
                text: JSON.stringify({ available, priceDetails: priceDetails || null, minStay }, null, 2)
            }],
            isError: false
        };
    } catch (error) {
        return {
            content: [{ type: "text", text: JSON.stringify({ error: String(error) }) }],
            isError: true
        };
    }
}
"""

if "handleAirbnbListingPrice" not in content:
    content = content.replace("// Server setup", handler_def + "\n// Server setup")

# 3. Add to switch statement
switch_case = """
            case "airbnb_listing_price": {
                result = await handleAirbnbListingPrice(request.params.arguments);
                break;
            }
"""
if "case \"airbnb_listing_price\":" not in content:
    content = content.replace("default:", switch_case + "            default:")

with open(mcp_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Patched MCP server successfully.")
