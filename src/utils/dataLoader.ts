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
// WRDS / Static JSON URLs (unchanged)
// -----------------------------
const BLOB_URLS: Record<StockCode, string> = {
  // Add WRDS or static JSON URLs if needed
};

// -----------------------------
// Yahoo Finance JSON URLs (pre-populated)
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
  TWTR: "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/TWTR_data.json",
  T: "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/T_data.json",
  WFC: "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/WFC_data.json",
  XOM: "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/XOM_data.json",
};

// -----------------------------
// Update Yahoo Finance URLs (automation)
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
// Load bubble data
// -----------------------------
export async function loadBubbleData(
  stockCode: StockCode,
  dataSource: DataSource
): Promise<BubbleData> {
  const url =
    dataSource === "WRDS"
      ? BLOB_URLS[stockCode] || `/data/bubble_data_${stockCode}_splitadj_1996to2023.json`
      : YAHOO_BLOB_URLS[stockCode] || `/data/bubble_data_${stockCode}_splitadj_2025to${new Date().getFullYear()}.json`;

  const response = await fetch(url);
  if (!response.ok) throw new Error(`Failed to load ${stockCode} from ${dataSource}: ${response.statusText}`);
  return response.json();
}

// -----------------------------
// Transform bubble data for chart
// -----------------------------
export function transformDataForChart(
  bubbleData: BubbleData,
  optionType: OptionType,
  startDate?: Date,
  endDate?: Date
): ChartDataPoint[] {
  let filtered = bubbleData.time_series_data;

  if (startDate || endDate) {
    const s = startDate?.getTime();
    const e = endDate?.getTime();
    filtered = bubbleData.time_series_data.filter(pt => {
      const t = new Date(pt.date).getTime();
      if (s && t < s) return false;
      if (e && t > e) return false;
      return true;
    });
  }

  return filtered.map(pt => ({
    date: pt.date,
    stockPrice: pt.stock_prices.adjusted,
    tau1: pt.bubble_estimates.daily_grouped[0][optionType],
    tau2: pt.bubble_estimates.daily_grouped[1][optionType],
    tau3: pt.bubble_estimates.daily_grouped[2][optionType],
  }));
}

// -----------------------------
// Get date range
// -----------------------------
export function getDateRange(bubbleData: BubbleData): { min: Date; max: Date } {
  const times = bubbleData.time_series_data.map(pt => new Date(pt.date).getTime());
  return { min: new Date(Math.min(...times)), max: new Date(Math.max(...times)) };
}

// -----------------------------
// Load regular price data
// -----------------------------
const REGULAR_PRICE_URLS = { ...YAHOO_BLOB_URLS };

export async function loadRegularPriceData(stockCode: StockCode): Promise<RegularPriceData[]> {
  const url = REGULAR_PRICE_URLS[stockCode];
  const resp = await fetch(url);
  if (!resp.ok) throw new Error(`Failed to load regular price data for ${stockCode}`);
  const data = await resp.json();
  if (Array.isArray(data.daily_data)) return data.daily_data.map(pt => ({ date: pt.date, price: pt.raw_price }));
  if (Array.isArray(data)) return data.map(pt => ({ date: pt.date, price: pt.price ?? pt.close ?? pt.raw_price }));
  return [];
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
  const regularMap = new Map(regularPriceData.map(pt => [pt.date.split("T")[0], pt.price]));
  let filtered = bubbleData.time_series_data;
  if (startDate || endDate) {
    const s = startDate?.getTime();
    const e = endDate?.getTime();
    filtered = filtered.filter(pt => {
      const t = new Date(pt.date).getTime();
      return (!s || t >= s) && (!e || t <= e);
    });
  }
  return filtered.map(pt => {
    const normDate = pt.date.split("T")[0];
    const reg = regularMap.get(normDate);
    if (reg === undefined) return null;
    const adj = pt.stock_prices.adjusted;
    const diff = adj - reg;
    return { date: pt.date, adjustedPrice: adj, regularPrice: reg, difference: diff, percentageDifference: (diff / reg) * 100 };
  }).filter(Boolean) as PriceDifferenceDataPoint[];
}

// -----------------------------
// Dummy formatTooltipData (build dependency for BubbleChart.tsx)
// -----------------------------
export function formatTooltipData(...args: any[]): any {
  return args;
}
