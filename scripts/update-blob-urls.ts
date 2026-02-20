import { put } from "@vercel/blob";
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

      // Upload to Blob under the same filename, overwriting any previous version.
      // addRandomSuffix: false keeps URLs deterministic between daily runs.
      const blob = await put(filename, fileContent, {
        access: "public",
        token: BLOB_READ_WRITE_TOKEN,
        addRandomSuffix: false,
        contentType: "application/json",
      });

      console.log(`⬆️  Uploaded ${filename} → ${blob.url}`);

      // Match filenames like: bubble_data_AAPL_splitadj_2025to2025.json
      const match = filename.match(/^bubble_data_([^_]+(?:_[^_]+)*)_splitadj_/);
      if (match) {
        const stock = match[1];
        urlMapping[stock] = blob.url;
        console.log(`✅ Mapped ${stock} → ${blob.url}`);
      } else {
        console.warn(`⚠️  Could not extract stock code from filename: ${filename}`);
      }
    }

    if (Object.keys(urlMapping).length === 0) {
      console.error("❌ No stock codes could be extracted — check filename format.");
      process.exit(1);
    }

    // ── Step 2: Upload blob_mapping.json to Blob ──
    // dataLoader.ts fetches this at runtime to get the current URLs.
    // This replaces the old approach of modifying dataLoader.ts source and committing to git.
    const mappingJson = JSON.stringify(urlMapping, null, 2);

    const mappingBlob = await put("blob_mapping.json", mappingJson, {
      access: "public",
      token: BLOB_READ_WRITE_TOKEN,
      addRandomSuffix: false,
      contentType: "application/json",
    });

    console.log(`✅ Uploaded blob_mapping.json to Blob → ${mappingBlob.url}`);

    // Also save locally for debugging reference (not committed to git)
    const localMappingPath = join(process.cwd(), "blob_mapping.json");
    writeFileSync(localMappingPath, mappingJson);
    console.log(`💾 Saved blob_mapping.json locally for reference`);

    console.log(`\n🎉 Done. ${Object.keys(urlMapping).length} stocks uploaded and mapped.`);
    console.log(`   dataLoader.ts will fetch the mapping at runtime from:\n   ${mappingBlob.url}`);

  } catch (err) {
    console.error("❌ Failed to update blob URLs:", err);
    process.exit(1);
  }
}

updateBlobUrls();
