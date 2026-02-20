import { put } from "@vercel/blob";
import { readdirSync, readFileSync } from "fs";
import { join } from "path";

const token = process.env.BLOB_READ_WRITE_TOKEN!;
const csvDir = join(process.cwd(), "data", "csv");

const files = readdirSync(csvDir).filter(f => f.endsWith(".csv"));
console.log(`Found ${files.length} CSV files to upload...`);

for (const filename of files) {
  const content = readFileSync(join(csvDir, filename));
  const blob = await put(`csv/${filename}`, content, {
    access: "public",
    token,
    addRandomSuffix: false,
    contentType: "text/csv",
  });
  console.log(`✅ ${filename} → ${blob.url}`);
}
