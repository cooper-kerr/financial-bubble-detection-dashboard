import { list } from '@vercel/blob';
import { config } from 'dotenv';
import { writeFileSync, readFileSync } from 'fs';
import { join } from 'path';

config({ path: '.env.local' });

const BLOB_READ_WRITE_TOKEN = process.env.BLOB_READ_WRITE_TOKEN;

if (!BLOB_READ_WRITE_TOKEN) {
  console.error('❌ BLOB_READ_WRITE_TOKEN environment variable is required');
  process.exit(1);
}

async function getBlobUrls() {
  try {
    console.log('🔍 Fetching blob URLs...');
    
    const { blobs } = await list();
    console.log(`📁 Found ${blobs.length} blobs`);

    const urlMapping: Record<string, string> = {};

    blobs.forEach(blob => {
      // Only match Yahoo Finance JSONs (adjust pattern if needed)
      const match = blob.pathname.match(/bubble_data_(.+)_yahoo\.json$/);
      if (match) {
        const stockCode = match[1];
        urlMapping[stockCode] = blob.url;
        console.log(`✅ ${stockCode}: ${blob.url}`);
      }
    });

    const mappingPath = join(process.cwd(), 'blob_mapping.json');
    writeFileSync(mappingPath, JSON.stringify(urlMapping, null, 2));
    console.log(`💾 Saved URL mapping to ${mappingPath}`);

    // Update dataLoader.ts automatically
    const dataLoaderPath = join(process.cwd(), 'src', 'utils', 'dataLoader.ts');
    let content = readFileSync(dataLoaderPath, 'utf-8');

    const blobUrlsRegex = /const BLOB_URLS: Record<StockCode, string> = \{[\s\S]*?\};/;
    const newBlobUrls = `const BLOB_URLS: Record<StockCode, string> = ${JSON.stringify(urlMapping, null, 2)};`;

    content = content.replace(blobUrlsRegex, newBlobUrls);
    writeFileSync(dataLoaderPath, content, 'utf-8');
    console.log(`✅ Updated BLOB_URLS in ${dataLoaderPath}`);

    return urlMapping;
  } catch (error) {
    console.error('❌ Error fetching blob URLs:', error);
    throw error;
  }
}

getBlobUrls().catch(console.error);
