import { list } from "@vercel/blob";
import { config } from "dotenv";
import { writeFileSync, readFileSync } from "fs";
import { join } from "path";

config({ path: ".env.local" });

const BLOB_READ_WRITE_TOKEN = process.env.BLOB_READ_WRITE_TOKEN;
if (!BLOB_READ_WRITE_TOKEN) process.exit(1);

async function updateBlobUrls() {
  try {
    const { blobs } = await list({ token: BLOB_READ_WRITE_TOKEN });
    const urlMapping: Record<string, string> = {};

    blobs.forEach(blob => {
      const match = blob.pathname.match(/([A-Z]+)_data\.json$/);
      if (match) urlMapping[match[1]] = blob.url;
    });

    writeFileSync(join(process.cwd(), "blob_mapping.json"), JSON.stringify(urlMapping, null, 2));

    const dataLoaderPath = join(process.cwd(), "src", "utils", "dataLoader.ts");
    const content = readFileSync(dataLoaderPath, "utf-8");

    const regex = /export function updateYahooBlobUrls[\s\S]*?console\.log\("✅ YAHOO_BUBBLE_URLS updated successfully"\);/;
    const newFunction = `
export function updateYahooBlobUrls(urlMapping: Record<string, string>): void {
  Object.entries(urlMapping).forEach(([stock, url]) => {
    if (YAHOO_BUBBLE_URLS.hasOwnProperty(stock)) {
      YAHOO_BUBBLE_URLS[stock as StockCode] = url;
    }
  });
  console.log("✅ YAHOO_BUBBLE_URLS updated successfully");
}`;
    writeFileSync(dataLoaderPath, content.replace(regex, newFunction));
  } catch (err) {
    console.error(err);
    process.exit(1);
  }
}

updateBlobUrls();
