import { list } from '@vercel/blob';
import { config } from 'dotenv';

// Load environment variables from .env.local
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
    
    // Create URL mapping for stock codes
    const urlMapping: Record<string, string> = {};
    
    blobs.forEach(blob => {
      // Extract stock code from filename: bubble_data_AAPL_splitadj_1996to2023.json -> AAPL
      const match = blob.pathname.match(/bubble_data_(.+)_splitadj_1996to2023\.json$/);
      if (match) {
        const stockCode = match[1];
        urlMapping[stockCode] = blob.url;
        console.log(`✅ ${stockCode}: ${blob.url}`);
      }
    });
    
    console.log('\n📋 URL Mapping (copy this):');
    console.log(JSON.stringify(urlMapping, null, 2));
    
    console.log('\n🔧 Next step: Update BLOB_URLS in src/utils/dataLoader.ts');
    
    return urlMapping;
  } catch (error) {
    console.error('❌ Error fetching blob URLs:', error);
    throw error;
  }
}

getBlobUrls().catch(console.error);
