import { put } from "@vercel/blob";
import { config } from "dotenv";
import { createHash } from "crypto";
import { appendFileSync, existsSync, writeFileSync, readFileSync, readdirSync } from "fs";
import { join } from "path";

config({ path: ".env.local" });

const BLOB_READ_WRITE_TOKEN = process.env.BLOB_READ_WRITE_TOKEN;
const BLOB_BASE_URL = process.env.BLOB_BASE_URL;
if (!BLOB_READ_WRITE_TOKEN) {
  console.error("❌ BLOB_READ_WRITE_TOKEN environment variable missing");
  process.exit(1);
}
if (!BLOB_BASE_URL) {
  console.error("❌ BLOB_BASE_URL environment variable missing");
  process.exit(1);
}

// Directory where bubble_estimator.py writes its JSON files
const JSON_OUTPUT_DIR = join(process.cwd(), "public", "data");
const HASH_MANIFEST_BLOB_NAME = "blob_hash_manifest.json";
const HASH_MANIFEST_URL = `${BLOB_BASE_URL}/${HASH_MANIFEST_BLOB_NAME}`;
const BLOB_MAPPING_URL = `${BLOB_BASE_URL}/blob_mapping.json`;
const NORMALIZED_BLOB_BASE_URL = BLOB_BASE_URL.replace(/\/+$/, "");

function sha256(content: Buffer): string {
  return createHash("sha256").update(content).digest("hex");
}

async function fetchJsonOrNull<T>(url: string): Promise<T | null> {
  try {
    const response = await fetch(url);
    if (!response.ok) {
      if (response.status === 404) {
        return null;
      }
      throw new Error(`${response.status} ${response.statusText}`);
    }
    return (await response.json()) as T;
  } catch (error) {
    console.warn(`⚠️  Failed to fetch ${url}; treating as empty state.`, error);
    return null;
  }
}

function setGithubOutput(name: string, value: string) {
  const githubOutputPath = process.env.GITHUB_OUTPUT;
  if (!githubOutputPath || !existsSync(githubOutputPath)) {
    return;
  }
  appendFileSync(githubOutputPath, `${name}=${value}\n`);
}

function assertBlobUrlMatchesConfiguredStore(url: string, filename: string) {
  if (!url.startsWith(`${NORMALIZED_BLOB_BASE_URL}/`)) {
    throw new Error(
      `${filename} uploaded to ${url}, but BLOB_BASE_URL is ${NORMALIZED_BLOB_BASE_URL}. ` +
      "The Blob token and BLOB_BASE_URL secret are pointing at different stores.",
    );
  }
}

function contentAddressedJsonBlobName(filename: string, fileHash: string) {
  const stem = filename.replace(/\.json$/, "");
  return `yahoo-json/${stem}-${fileHash.slice(0, 12)}.json`;
}

async function updateBlobUrls() {
  try {
    if (!existsSync(JSON_OUTPUT_DIR)) {
      throw new Error(
        `Missing ${JSON_OUTPUT_DIR}. Generate Yahoo JSON first or download the synthetic-yahoo-mat-json artifact before uploading.`,
      );
    }

    const urlMapping = (await fetchJsonOrNull<Record<string, string>>(BLOB_MAPPING_URL)) ?? {};
    const previousHashManifest =
      (await fetchJsonOrNull<Record<string, string>>(HASH_MANIFEST_URL)) ?? {};
    const nextHashManifest: Record<string, string> = {};
    let changedUploads = 0;
    let mappingChanged = false;

    // ── Step 1: Upload every JSON from public/data/ to Vercel Blob ──
    const jsonFiles = readdirSync(JSON_OUTPUT_DIR).filter(f => f.endsWith(".json"));

    if (jsonFiles.length === 0) {
      throw new Error("No JSON files found in public/data/ — did bubble_estimator.py run or did the artifact download succeed?");
    }

    console.log(`📦 Found ${jsonFiles.length} JSON files to evaluate...`);

    for (const filename of jsonFiles) {
      const localPath = join(JSON_OUTPUT_DIR, filename);
      const fileContent = readFileSync(localPath);
      const fileHash = sha256(fileContent);

      const match = filename.match(/^bubble_data_([^_]+(?:_[^_]+)*)_splitadj_/);
      if (!match) {
        console.warn(`⚠️  Could not extract stock code from filename: ${filename}`);
        continue;
      }

      const stock = match[1];
      nextHashManifest[filename] = fileHash;
      const blobName = contentAddressedJsonBlobName(filename, fileHash);
      const expectedBlobUrl = `${NORMALIZED_BLOB_BASE_URL}/${blobName}`;

      if (previousHashManifest[filename] === fileHash && urlMapping[stock] === expectedBlobUrl) {
        console.log(`⏭️  No content change for ${filename}; reusing existing Blob URL.`);
        continue;
      }

      // Upload changed JSON under a content-addressed name so immediate live
      // validation and production clients never race stale cached overwrites.
      const blob = await put(blobName, fileContent, {
        access: "public",
        token: BLOB_READ_WRITE_TOKEN,
        addRandomSuffix: false,
        allowOverwrite: true,
        contentType: "application/json",
      });
      assertBlobUrlMatchesConfiguredStore(blob.url, filename);

      changedUploads += 1;
      if (urlMapping[stock] !== blob.url) {
        mappingChanged = true;
      }
      urlMapping[stock] = blob.url;
      console.log(`⬆️  Uploaded ${filename} → ${blob.url}`);
      console.log(`✅ Mapped ${stock} → ${blob.url}`);
    }

    if (Object.keys(nextHashManifest).length === 0) {
      console.error("❌ No stock codes could be extracted — check filename format.");
      process.exit(1);
    }

    // Remove stale mappings when a local file disappeared from public/data.
    const expectedStocks = new Set(
      jsonFiles
        .map((filename) => filename.match(/^bubble_data_([^_]+(?:_[^_]+)*)_splitadj_/)?.[1])
        .filter((stock): stock is string => Boolean(stock)),
    );
    for (const stock of Object.keys(urlMapping)) {
      if (!expectedStocks.has(stock)) {
        delete urlMapping[stock];
        mappingChanged = true;
      }
    }

    // ── Step 2: Upload blob_mapping.json and the hash manifest only when needed ──
    const mappingJson = JSON.stringify(urlMapping, null, 2);
    const hashManifestJson = JSON.stringify(nextHashManifest, null, 2);
    const manifestChanged =
      JSON.stringify(previousHashManifest) !== JSON.stringify(nextHashManifest);

    if (changedUploads === 0 && !mappingChanged && !manifestChanged) {
      console.log("🎉 No JSON content changes detected; skipping mapping and manifest uploads.");
      writeFileSync(join(process.cwd(), "blob_mapping.json"), mappingJson);
      setGithubOutput("blob_changed", "false");
      setGithubOutput("json_upload_count", "0");
      return;
    }

    const mappingBlob = await put("blob_mapping.json", mappingJson, {
      access: "public",
      token: BLOB_READ_WRITE_TOKEN,
      addRandomSuffix: false,
      allowOverwrite: true,
      contentType: "application/json",
    });
    assertBlobUrlMatchesConfiguredStore(mappingBlob.url, "blob_mapping.json");

    console.log(`✅ Uploaded blob_mapping.json to Blob → ${mappingBlob.url}`);

    const hashManifestBlob = await put(HASH_MANIFEST_BLOB_NAME, hashManifestJson, {
      access: "public",
      token: BLOB_READ_WRITE_TOKEN,
      addRandomSuffix: false,
      allowOverwrite: true,
      contentType: "application/json",
    });
    assertBlobUrlMatchesConfiguredStore(hashManifestBlob.url, HASH_MANIFEST_BLOB_NAME);

    console.log(`✅ Uploaded ${HASH_MANIFEST_BLOB_NAME} to Blob → ${hashManifestBlob.url}`);

    // Also save locally for debugging reference (not committed to git)
    const localMappingPath = join(process.cwd(), "blob_mapping.json");
    writeFileSync(localMappingPath, mappingJson);
    console.log(`💾 Saved blob_mapping.json locally for reference`);
    setGithubOutput("blob_changed", "true");
    setGithubOutput("json_upload_count", String(changedUploads));

    console.log(`\n🎉 Done. ${changedUploads} JSON file(s) uploaded and ${Object.keys(urlMapping).length} stocks mapped.`);
    console.log(`   dataLoader.ts will fetch the mapping at runtime from:\n   ${mappingBlob.url}`);

  } catch (err) {
    console.error("❌ Failed to update blob URLs:", err);
    process.exit(1);
  }
}

updateBlobUrls();
