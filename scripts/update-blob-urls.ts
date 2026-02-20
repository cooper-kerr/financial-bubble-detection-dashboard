import { put, list } from "@vercel/blob";
import { config } from "dotenv";
import { writeFileSync, readFileSync, readdirSync } from "fs";
import { join } from "path";

config({ path: ".env.local" });

const BLOB_READ_WRITE_TOKEN = process.env.BLOB_READ_WRITE_TOKEN;
if (!BLOB_READ_WRITE_TOKEN) {
  console.error("❌ BLOB_READ_WRITE_TOKEN environment variable missing");
  process.exit(1);
}

// Directory where bubble_estimator.py writes its JSON files
const JSON_OUTPUT_DIR = join(process.cwd(), "public", "data");

async function updateBlobUrls() {
  try {
    const urlMapping: Record<string, string> = {};

    // ── Step 1: Upload every JSON from public/data/ to Vercel Blob ──
    const jsonFiles = readdirSync(JSON_OUTPUT_DIR).filter(f => f.endsWith(".json"));

    if (jsonFiles.length === 0) {
      console.error("❌ No JSON files found in public/data/ — did bubble_estimator.py run?");
      process.exit(1);
    }

    console.log(`📦 Found ${jsonFiles.length} JSON files to upload...`);

    for (const filename of jsonFiles) {
      const localPath = join(JSON_OUTPUT_DIR, filename);
      const fileContent = readFileSync(localPath);

      // Upload to Blob under the same filename, overwriting any previous version
      const blob = await put(filename, fileContent, {
        access: "public",
        token: BLOB_READ_WRITE_TOKEN,
        addRandomSuffix: false,   // keep deterministic URLs so the mapping stays stable
        contentType: "application/json",
      });

      console.log(`⬆️  Uploaded ${filename} → ${blob.url}`);

      // Match filenames like: bubble_data_AAPL_splitadj_2025to2025.json
      //                    or bubble_data_SPX_splitadj_2025to2025.json
      const match = filename.match(/^bubble_data_([^_]+(?:_[^_]+)*)_splitadj_/);
      if (match) {
        const stock = match[1];   // e.g. "AAPL", "SPX", "BAC"
        urlMapping[stock] = blob.url;
        console.log(`✅ Mapped ${stock} → ${blob.url}`);
      } else {
        console.warn(`⚠️  Could not extract stock code from filename: ${filename}`);
      }
    }

    if (Object.keys(urlMapping).length === 0) {
      console.error("❌ No stock codes could be extracted from uploaded files — check filename format.");
      process.exit(1);
    }

    // ── Step 2: Save blob_mapping.json locally (for reference / debugging) ──
    const mappingPath = join(process.cwd(), "blob_mapping.json");
    writeFileSync(mappingPath, JSON.stringify(urlMapping, null, 2));
    console.log(`💾 Saved blob_mapping.json with ${Object.keys(urlMapping).length} entries`);

    // ── Step 3: Update dataLoader.ts with the new URL mapping function ──
    const dataLoaderPath = join(process.cwd(), "src", "utils", "dataLoader.ts");
    const content = readFileSync(dataLoaderPath, "utf-8");

    const regex = /export function updateYahooBlobUrls[\s\S]*?console\.log\("✅ YAHOO_BLOB_URLS updated successfully"\);/;

    const newFunction = `export function updateYahooBlobUrls(urlMapping: Record<string, string>): void {
  Object.entries(urlMapping).forEach(([stock, url]) => {
    if (YAHOO_BLOB_URLS.hasOwnProperty(stock)) {
      YAHOO_BLOB_URLS[stock as StockCode] = url;
    } else {
      console.warn(\`⚠️ Skipped unknown stock code in mapping: \${stock}\`);
    }
  });
  console.log("✅ YAHOO_BLOB_URLS updated successfully");
}`;

    if (!regex.test(content)) {
      console.error("❌ Could not find updateYahooBlobUrls function in dataLoader.ts — regex did not match.");
      console.error("   Check that the function signature and final console.log line haven't changed.");
      process.exit(1);
    }

    const updatedContent = content.replace(regex, newFunction);
    writeFileSync(dataLoaderPath, updatedContent, "utf-8");
    console.log("✅ Updated dataLoader.ts with new blob URLs function");

  } catch (err) {
    console.error("❌ Failed to update blob URLs:", err);
    process.exit(1);
  }
}

updateBlobUrls();
