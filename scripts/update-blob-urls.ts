import { readFileSync, writeFileSync } from 'fs';
import { join } from 'path';

// This script helps you update the BLOB_URLS in dataLoader.ts
// Run this after uploading files to get the URL mapping

const urlMapping = {
  // Paste your URL mapping here from the upload script output
  // Example:
  // "AAPL": "https://your-blob-store.vercel-storage.com/bubble_data_AAPL_splitadj_1996to2023.json",
  // "SPX": "https://your-blob-store.vercel-storage.com/bubble_data_SPX_splitadj_1996to2023.json",
  // ... etc
};

function updateBlobUrls() {
  const dataLoaderPath = join(process.cwd(), 'src', 'utils', 'dataLoader.ts');
  let content = readFileSync(dataLoaderPath, 'utf-8');
  
  // Find the BLOB_URLS object and replace it
  const blobUrlsRegex = /const BLOB_URLS: Record<StockCode, string> = \{[\s\S]*?\};/;
  
  const newBlobUrls = `const BLOB_URLS: Record<StockCode, string> = ${JSON.stringify(urlMapping, null, 2)};`;
  
  content = content.replace(blobUrlsRegex, newBlobUrls);
  
  writeFileSync(dataLoaderPath, content, 'utf-8');
  
  console.log('✅ Updated BLOB_URLS in dataLoader.ts');
  console.log('📁 File:', dataLoaderPath);
}

if (Object.keys(urlMapping).length === 0) {
  console.log('❌ Please update the urlMapping object in this script first!');
  console.log('📋 Copy the URL mapping from the upload script output');
} else {
  updateBlobUrls();
}
