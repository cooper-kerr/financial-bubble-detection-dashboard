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

// Define which stocks are hosted as Yahoo Finance JSONs
const YAHOO_STOCKS: string[] = [
  "AAPL","SPX","BAC","C","MSFT","FB","GE","INTC","CSCO",
  "BABA","WFC","JPM","AMD","TWTR","F","TSLA","GOOG","T",
  "XOM","AMZN","MS","NVDA","AIG","GM","DIS","BA"
];

async function updateYahooBlobUrls() {
  try {
    console.log('🔍 Fetching blob URLs from Vercel...');
    const { blobs } = await list();

    if (!blobs || blobs.length === 0) {
      throw new Error('No blobs found in Vercel storage.');
    }

    // Build mapping only for Yahoo Finance JSONs
    const urlMapping: Record<string, string> = {};
    blobs.forEach(blob => {
      const match = blob.pathname.match(/([A-Z]+)_data\.json$/);
      if (match) {
        const stockCode = match[1];
        if (YAHOO_STOCKS.includes(stockCode)) {
          urlMapping[stockCode] = blob.url;
          console.log(`✅ ${stockCode}: ${blob.url}`);
        }
      }
    });

    // Save mapping for reference (optional)
    const mappingPath = join(process.cwd(), 'yahoo_blob_mapping.json');
    writeFileSync(mappingPath, JSON.stringify(urlMapping, null, 2), 'utf-8');
    console.log(`📄 Saved ${mappingPath}`);

    // Update dataLoader.ts for Yahoo URLs
    const dataLoaderPath = join(process.cwd(), 'src', 'utils', 'dataLoader.ts');
    let content = readFileSync(dataLoaderPath, 'utf-8');

    // Only replace the YAHOO_BLOB_URLS object
    const yahooUrlsRegex = /const YAHOO_BLOB_URLS: Record<StockCode, string> = \{[\s\S]*?\};/;
    const newYahooUrls = `const YAHOO_BLOB_URLS: Record<StockCode, string> = ${JSON.stringify(urlMapping, null, 2)};`;

    if (yahooUrlsRegex.test(content)) {
      content = content.replace(yahooUrlsRegex, newYahooUrls);
      console.log('✅ Updated YAHOO_BLOB_URLS in dataLoader.ts');
    } else {
      console.warn('⚠️ YAHOO_BLOB_URLS not found in dataLoader.ts. Adding new mapping.');
      content = newYahooUrls + "\n\n" + content;
    }

    writeFileSync(dataLoaderPath, content, 'utf-8');
    console.log('✅ Finished updating dataLoader.ts');
  } catch (error) {
    console.error('❌ Failed to update Yahoo BLOB URLs:', error);
    process.exit(1);
  }
}

updateYahooBlobUrls();
