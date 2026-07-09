import { put } from "@vercel/blob";
import { createReadStream } from "node:fs";

const [, , localPath, blobPath] = process.argv;
const BLOB_READ_WRITE_TOKEN = process.env.BLOB_READ_WRITE_TOKEN;
const BLOB_BASE_URL = process.env.BLOB_BASE_URL?.replace(/\/+$/, "");

if (!localPath || !blobPath) {
  console.error("Usage: tsx scripts/upload-csv-to-blob.ts <local-path> <blob-path>");
  process.exit(2);
}

if (!BLOB_READ_WRITE_TOKEN) {
  console.error("BLOB_READ_WRITE_TOKEN environment variable is not set.");
  process.exit(1);
}

if (!BLOB_BASE_URL) {
  console.error("BLOB_BASE_URL environment variable is not set.");
  process.exit(1);
}

try {
  const blob = await put(blobPath, createReadStream(localPath), {
    access: "public",
    token: BLOB_READ_WRITE_TOKEN,
    addRandomSuffix: false,
    allowOverwrite: true,
    contentType: "text/csv",
    multipart: true,
  });

  if (!blob.url.startsWith(`${BLOB_BASE_URL}/`)) {
    throw new Error(
      `${blobPath} uploaded to ${blob.url}, but BLOB_BASE_URL is ${BLOB_BASE_URL}. ` +
        "The Blob token and BLOB_BASE_URL secret are pointing at different stores.",
    );
  }

  console.log(blob.url);
} catch (error) {
  console.error(error);
  process.exit(1);
}
