import type {
  BubbleData,
  ChartDataPoint,
  DataSource,
  OptionType,
  PriceDifferenceDataPoint,
  RegularPriceData,
  StockCode,
} from "../types/bubbleData";

// -----------------------------
// WRDS / Static JSON URLs (unchanged branch)
// -----------------------------
const BLOB_URLS: Record<StockCode, string> = {
  // Keep empty or add static URLs if available
};

// -----------------------------
// Yahoo Finance JSON URLs (to be updated automatically)
// -----------------------------
const YAHOO_BLOB_URLS: Record<StockCode, string> = {
  AAPL: "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/AAPL_data.json",
  AIG: "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/AIG_data.json",
  AMD: "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/AMD_data.json",
  AMZN: "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/AMZN_data.json",
  BABA: "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/BABA_data.json",
  BAC: "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/BAC_data.json",
  BA: "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/BA_data.json",
  CSCO: "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/CSCO_data.json",
  C: "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/C_data.json",
  DIS: "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/DIS_data.json",
  FB: "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/FB_data.json",
  F: "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/F_data.json",
  GE: "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/GE_data.json",
  GM: "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/GM_data.json",
  GOOG: "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/GOOG_data.json",
  INTC: "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/INTC_data.json",
  JPM: "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/JPM_data.json",
  MSFT: "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/MSFT_data.json",
  MS: "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/MS_data.json",
  NVDA: "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/NVDA_data.json",
  SPX: "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/SPX_data.json",
  TSLA: "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/TSLA_data.json",
  TWTR: "https://fposl6nafeqvtwpj.public.blob.storage.vercel.com/TWTR_data.json",
  T: "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/T_data.json",
  WFC: "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/WFC_data.json",
  XOM: "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/XOM_data.json",
};

// -----------------------------
// Update Yahoo Finance URLs
// -----------------------------
export function updateYahooBlobUrls(urlMapping: Record<string, string>): void {
  Object.entries(urlMapping).forEach(([stock, url]) => {
    if (YAHOO_BLOB_URLS.hasOwnProperty(stock)) {
      YAHOO_BLOB_URLS[stock as StockCode] = url;
    } else {
      console.warn(`⚠️ Skipped unknown stock code in mapping: ${stock}`);
    }
  });
  console.log("✅ YAHOO_BLOB_URLS updated successfully");
}

// -----------------------------
// Load bubble data
// -----------------------------
export async function loadBubbleData(
  stockCode: StockCode,
  dataSource: DataSource
): Promise<BubbleData> {
  try {
    let url: string;
    if (dataSource === "WRDS") {
      url = BLOB_URLS[stockCode] || `/data/bubble_data_${stockCode}_splitadj_1996to2023.json`;
    } else {
      const currentYear = new Date().getFullYear();
      url =
        YAHOO_BLOB_URLS[stockCode] ||
        `/data/bubble_data_${stockCode}_splitadj_2025to${currentYear}.json`;
    }

    console.log(`📡 Fetching ${dataSource} data for ${stockCode} from:`, url);

    const res = await fetch(url);
    if (!res.ok) {
      throw new Error(`Failed to fetch ${stockCode} (${dataSource}): ${res.statusText}`);
    }

    const data: BubbleData = await res.json();
    return data;
  } catch (err) {
    console.error(`❌ Error loading bubble data for ${stockCode}:`, err);
    throw err;
  }
}

// -----------------------------
// Other utility functions (unchanged)...
// transformDataForChart, getDateRange, loadRegularPriceData, calculatePriceDifferences
