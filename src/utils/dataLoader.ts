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
  // Example: fill in your WRDS‑blob or static JSON URLs here if you have them
  // AAPL: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_AAPL_splitadj_1996to2023.json",
  // ...
};

// -----------------------------
// Yahoo Finance JSON URLs (to be updated automatically)
// -----------------------------
const YAHOO_BLOB_URLS: Record<StockCode, string> = {
  "AAPL": "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/AAPL_data.json",
  "AIG": "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/AIG_data.json",
  "AMD": "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/AMD_data.json",
  "AMZN": "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/AMZN_data.json",
  "BABA": "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/BABA_data.json",
  "BAC": "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/BAC_data.json",
  "BA": "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/BA_data.json",
  "CSCO": "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/CSCO_data.json",
  "C": "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/C_data.json",
  "DIS": "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/DIS_data.json",
  "FB": "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/FB_data.json",
  "F": "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/F_data.json",
  "GE": "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/GE_data.json",
  "GM": "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/GM_data.json",
  "GOOG": "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/GOOG_data.json",
  "INTC": "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/INTC_data.json",
  "JPM": "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/JPM_data.json",
  "MSFT": "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/MSFT_data.json",
  "MS": "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/MS_data.json",
  "NVDA": "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/NVDA_data.json",
  "SPX": "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/SPX_data.json",
  "TSLA": "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/TSLA_data.json",
  "TWTR": "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/TWTR_data.json",
  "T": "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/T_data.json",
  "WFC": "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/WFC_data.json",
  "XOM": "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/XOM_data.json"
};

// -----------------------------
// Function to inject updated Yahoo Finance URLs
// This will be called by your automation script.
// -----------------------------
export function updateYahooBlobUrls(urlMapping: Record<string, string>): void {
  for (const [stock, url] of Object.entries(urlMapping)) {
    if (stock in YAHOO_BLOB_URLS) {
      YAHOO_BLOB_URLS[stock as StockCode] = url;
    }
  }
  console.log("✅ Updated YAHOO_BLOB_URLS with automation mapping");
}

// -----------------------------
// Load bubble data depending on source
// -----------------------------
export async function loadBubbleData(
  stockCode: StockCode,
  dataSource: DataSource,
): Promise<BubbleData> {
  try {
    let url: string;
    if (dataSource === "WRDS") {
      url =
        BLOB_URLS[stockCode] ||
        `/data/bubble_data_${stockCode}_splitadj_1996to2023.json`;
    } else {
      const currentYear = new Date().getFullYear();
      url =
        YAHOO_BLOB_URLS[stockCode] ||
        `/data/bubble_data_${stockCode}_splitadj_2025to${currentYear}.json`;
    }

    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(
        `Failed to load data for ${stockCode} from ${dataSource}: ${response.statusText}`
      );
    }

    const data: BubbleData = await response.json();
    return data;
  } catch (error) {
    console.error(
      `Error loading bubble data for ${stockCode} from ${dataSource}:`,
      error
    );
    throw error;
  }
}

// -----------------------------
// Transform data for chart view
// -----------------------------
export function transformDataForChart(
  bubbleData: BubbleData,
  optionType: OptionType,
  startDate?: Date,
  endDate?: Date
): ChartDataPoint[] {
  let filteredData = bubbleData.time_series_data;

  if (startDate || endDate) {
    const startTime = startDate?.getTime();
    const endTime = endDate?.getTime();
    filteredData = bubbleData.time_series_data.filter((point) => {
      const pointTime = new Date(point.date).getTime();
      if (startTime && pointTime < startTime) return false;
      if (endTime && pointTime > endTime) return false;
      return true;
    });
  }

  return filteredData.map((point) => ({
    date: point.date,
    stockPrice: point.stock_prices.adjusted,
    tau1: point.bubble_estimates.daily_grouped[0][optionType],
    tau2: point.bubble_estimates.daily_grouped[1][optionType],
    tau3: point.bubble_estimates.daily_grouped[2][optionType],
  }));
}

// -----------------------------
// Get date range from bubble data
// -----------------------------
export function getDateRange(bubbleData: BubbleData): { min: Date; max: Date } {
  let minTime = Number.POSITIVE_INFINITY;
  let maxTime = Number.NEGATIVE_INFINITY;

  for (const point of bubbleData.time_series_data) {
    const t = new Date(point.date).getTime();
    if (t < minTime) minTime = t;
    if (t > maxTime) maxTime = t;
  }

  return {
    min: new Date(minTime),
    max: new Date(maxTime),
  };
}

// -----------------------------
// Load regular price data (unchanged branch)
// -----------------------------
const REGULAR_PRICE_URLS: Record<StockCode, string> = {
  AAPL: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/AAPL_data.json",
  AIG: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/AIG_data.json",
  AMD: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/AMD_data.json",
  AMZN: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/AMZN_data.json",
  BABA: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/BABA_data.json",
  BAC: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/BAC_data.json",
  BA: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/BA_data.json",
  CSCO: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/CSCO_data.json",
  C: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/C_data.json",
  DIS: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/DIS_data.json",
  FB: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/FB_data.json",
  F: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/F_data.json",
  GE: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/GE_data.json",
  GM: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/GM_data.json",
  GOOG: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/GOOG_data.json",
  INTC: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/INTC_data.json",
  JPM: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/JPM_data.json",
  MSFT: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/MSFT_data.json",
  MS: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/MS_data.json",
  NVDA: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/NVDA_data.json",
  SPX: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/SPX_data.json",
  TSLA: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/TSLA_data.json",
  TWTR: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/TWTR_data.json",
  T: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/T_data.json",
  WFC: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/WFC_data.json",
  XOM: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/XOM_data.json",
};

export async function loadRegularPriceData(
  stockCode: StockCode
): Promise<RegularPriceData[]> {
  try {
    const url = REGULAR_PRICE_URLS[stockCode];
    console.log(`Loading regular price data for ${stockCode} from:`, url);
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(
        `Failed to load regular price data for ${stockCode}: ${response.statusText}`
      );
    }
    const data = await response.json();
    if (data.daily_data && Array.isArray(data.daily_data)) {
      return data.daily_data.map((pt: { date: string; raw_price: number }) => ({
        date: pt.date,
        price: pt.raw_price,
      }));
    }
    if (Array.isArray(data)) {
      return data.map((pt: any) => ({
        date: pt.date,
        price: pt.price ?? pt.close ?? pt.value ?? pt.raw_price,
      }));
    }
    if (data.data && Array.isArray(data.data)) {
      return data.data.map((pt: any) => ({
        date: pt.date,
        price: pt.price ?? pt.close ?? pt.value ?? pt.raw_price,
      }));
    }
    throw new Error(`Unexpected regular price data format for ${stockCode}`);
  } catch (error) {
    console.error(
      `Error loading regular price data for ${stockCode}:`,
      error
    );
    throw error;
  }
}

// -----------------------------
// Calculate price differences
// -----------------------------
export function calculatePriceDifferences(
  bubbleData: BubbleData,
  regularPriceData: RegularPriceData[],
  startDate?: Date,
  endDate?: Date
): PriceDifferenceDataPoint[] {
  console.log("calculatePriceDifferences called", {
    bubbleDataPoints: bubbleData.time_series_data.length,
    regularDataPoints: regularPriceData.length,
    // ... other debug info
  });

  const regularPriceMap = new Map<string, number>();
  for (const pt of regularPriceData) {
    regularPriceMap.set(pt.date.split("T")[0], pt.price);
  }

  let filtered = bubbleData.time_series_data;
  if (startDate || endDate) {
    const s = startDate?.getTime();
    const e = endDate?.getTime();
    filtered = bubbleData.time_series_data.filter((pt) => {
      const t = new Date(pt.date).getTime();
      if (s && t < s) return false;
      if (e && t > e) return false;
      return true;
    });
  }

  const result: PriceDifferenceDataPoint[] = [];
  for (const pt of filtered) {
    const normDate = pt.date.split("T")[0];
    const reg = regularPriceMap.get(normDate);
    if (reg !== undefined) {
      const adj = pt.stock_prices.adjusted;
      const diff = adj - reg;
      const pct = (diff / reg) * 100;
      result.push({
        date: pt.date,
        adjustedPrice: adj,
        regularPrice: reg,
        difference: diff,
        percentageDifference: pct,
      });
    }
  }

  return result;
}
