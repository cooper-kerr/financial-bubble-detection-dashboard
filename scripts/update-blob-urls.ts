import { list } from '@vercel/blob';
import { config } from 'dotenv';
import { readFileSync, writeFileSync } from 'fs';
import { join } from 'path';

// Load environment variables
config({ path: '.env.local' });

const BLOB_READ_WRITE_TOKEN = process.env.BLOB_READ_WRITE_TOKEN;

if (!BLOB_READ_WRITE_TOKEN) {
  console.error('❌ BLOB_READ_WRITE_TOKEN environment variable is required');
  process.exit(1);
}

async function updateBlobUrls() {
  try {
    console.log('🔍 Fetching blob URLs from Vercel...');
    const { blobs } = await list();

    if (!blobs || blobs.length === 0) {
      throw new Error('No blobs found in Vercel storage.');
    }

    // Create URL mapping
    const urlMapping: Record<string, string> = {};
    blobs.forEach(blob => {
      const match = blob.pathname.match(/bubble_data_(.+)_splitadj_1996to2023\.json$/);
      if (match) {
        const stockCode = match[1];
        urlMapping[stockCode] = blob.url;
        console.log(`✅ ${stockCode}: ${blob.url}`);
      }
    });

    // Save mapping for reference (optional)
    writeFileSync(join(process.cwd(), 'blob_mapping.json'), JSON.stringify(urlMapping, null, 2), 'utf-8');
    console.log('📄 Saved blob_mapping.json');

    // Update dataLoader.ts
    const dataLoaderPath = join(process.cwd(), 'src', 'utils', 'dataLoader.ts');
    let content = readFileSync(dataLoaderPath, 'utf-8');

    const blobUrlsRegex = /const BLOB_URLS: Record<StockCode, string> = \{[\s\S]*?\};/;
    const newBlobUrls = `const BLOB_URLS: Record<StockCode, string> = ${JSON.stringify(urlMapping, null, 2)};`;

    content = content.replace(blobUrlsRegex, newBlobUrls);
    writeFileSync(dataLoaderPath, content, 'utf-8');

    console.log('✅ Updated BLOB_URLS in dataLoader.ts');
  } catch (error) {
    console.error('❌ Failed to update BLOB_URLS:', error);
    process.exit(1);
  }
}

updateBlobUrls();
