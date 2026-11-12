
mcp_path = r"C:\Users\mauro\AppData\Roaming\npm\node_modules\@openbnb\mcp-server-airbnb\dist\index.js"

with open(mcp_path, encoding="utf-8") as f:
    content = f.read()

# 1. Patch airbnb_listing_details to return ALL sections
old_details_logic = """            details = sections
                .filter((section) => allowSectionSchema.hasOwnProperty(section.sectionId))
                .map((section) => {
                return {
                    id: section.sectionId,
                    ...flattenArraysInObject(pickBySchema(section.section, allowSectionSchema[section.sectionId]))
                };
            });"""
new_details_logic = "            details = sections;"
if old_details_logic in content:
    content = content.replace(old_details_logic, new_details_logic)
    print("Patched airbnb_listing_details to return all sections.")
else:
    print("Could not find old_details_logic for airbnb_listing_details. Maybe already patched?")

# 2. Patch airbnb_listing_price to return FULL bookIt data
old_price_logic = """        const priceDetails = bookIt?.structuredDisplayPrice?.explanationData?.priceDetails;
        const minStay = bookIt?.availability?.minNights || 1;
        
        return {
            content: [{
                type: "text",
                text: JSON.stringify({ available, priceDetails: priceDetails || null, minStay }, null, 2)
            }],
            isError: false
        };"""
new_price_logic = """        return {
            content: [{
                type: "text",
                text: JSON.stringify({ available, fullBookItData: bookIt }, null, 2)
            }],
            isError: false
        };"""
if old_price_logic in content:
    content = content.replace(old_price_logic, new_price_logic)
    print("Patched airbnb_listing_price to return full bookIt data.")
else:
    print("Could not find old_price_logic for airbnb_listing_price.")

with open(mcp_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Patching complete.")
