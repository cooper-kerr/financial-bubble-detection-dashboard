import { list } from "@vercel/blob";
import { config } from "dotenv";
import { writeFileSync, readFileSync } from "fs";
import { join } from "path";

config({ path: ".env.local" });

const BLOB_READ_WRITE_TOKEN = process.env.BLOB_READ_WRITE_TOKEN;

if (!BLOB_READ_WRITE_TOKEN) {
  console.error("❌ BLOB_READ_WRITE_TOKEN environment variable missing");
  process.exit(1);
}

async function updateBlobUrls() {
  try {
    const { blobs } = await list();

    const urlMapping: Record<string, string> = {};
    blobs.forEach(blob => {
      const match = blob.pathname.match(/([A-Z]+)_data\.json$/);
      if (match) {
        const stock = match[1];
        urlMapping[stock] = blob.url;
        console.log(`✅ Found blob URL for ${stock}: ${blob.url}`);
      }
    });

    // Save mapping
    const mappingPath = join(process.cwd(), "blob_mapping.json");
    writeFileSync(mappingPath, JSON.stringify(urlMapping, null, 2));
    console.log(`💾 Saved blob_mapping.json`);

    // Update dataLoader.ts
    const dataLoaderPath = join(process.cwd(), "src", "utils", "dataLoader.ts");
    const content = readFileSync(dataLoaderPath, "utf-8");

    const regex = /export function updateYahooBlobUrls[\s\S]*?console\.log\("✅ YAHOO_BLOB_URLS updated successfully"\);/;
    const newFunction = `
export function updateYahooBlobUrls(urlMapping: Record<string, string>): void {
  Object.entries(urlMapping).forEach(([stock, url]) => {
    if (YAHOO_BLOB_URLS.hasOwnProperty(stock)) {
      YAHOO_BLOB_URLS[stock as StockCode] = url;
    } else {
      console.warn(\`⚠️ Skipped unknown stock code in mapping: \${stock}\`);
    }
  });
  console.log("✅ YAHOO_BLOB_URLS updated successfully");
}`;
    const updatedContent = content.replace(regex, newFunction);
    writeFileSync(dataLoaderPath, updatedContent, "utf-8");

    console.log("✅ Updated dataLoader.ts with new blob URLs function");
  } catch (err) {
    console.error("❌ Failed to update blob URLs:", err);
    process.exit(1);
  }
}

updateBlobUrls();
