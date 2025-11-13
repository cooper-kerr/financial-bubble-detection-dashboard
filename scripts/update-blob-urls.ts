import fs from "fs";
import path from "path";
import fetch from "node-fetch";
import { updateYahooBlobUrls } from "./dataLoader";

// Example mapping of stocks to source URLs (could be dynamic)
const STOCKS: string[] = [
  "AAPL", "SPX", "BAC", "C", "MSFT", "FB", "GE", "INTC", "CSCO",
  "BABA", "WFC", "JPM", "AMD", "TWTR", "F", "TSLA", "GOOG", "T",
  "XOM", "AMZN", "MS", "NVDA", "AIG", "GM", "DIS", "BA"
];

// Base URL where the latest Yahoo Finance JSONs are stored
const BASE_URL = "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com";

async function buildUpdatedMapping(): Promise<Record<string, string>> {
  const mapping: Record<string, string> = {};

  for (const stock of STOCKS) {
    // You could add logic here to dynamically determine latest JSON URLs if needed
    mapping[stock] = `${BASE_URL}/${stock}_data.json`;
  }

  return mapping;
}

async function updateDataLoader() {
  try {
    const newMapping = await buildUpdatedMapping();

    // Update the in-memory mapping in dataLoader.ts
    updateYahooBlobUrls(newMapping);

    // Optional: persist mapping to a JSON file for reference
    const filePath = path.resolve(__dirname, "../data/yahoo_blob_mapping.json");
    fs.writeFileSync(filePath, JSON.stringify(newMapping, null, 2));
    console.log(`✅ Updated Yahoo Finance URLs and saved mapping to ${filePath}`);
  } catch (error) {
    console.error("❌ Error updating Yahoo Finance URLs:", error);
  }
}

// Run the update
updateDataLoader();
