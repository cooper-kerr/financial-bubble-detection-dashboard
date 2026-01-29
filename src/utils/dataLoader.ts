import type {
  BubbleData,
  ChartDataPoint,
  DataSource,
  OptionType,
  PriceDifferenceDataPoint,
  RegularPriceData,
  StockCode,
} from "../types/bubbleData";

import blobMappingJson from "../../public/blob_mapping.json";

const CURRENT_YEAR = new Date().getFullYear();

// Default Vercel Blob Storage URLs
let BLOB_URLS: Record<StockCode, string> = {
  AAPL: `https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_AAPL_splitadj_1996to2023.json`,
  AIG: `https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_AIG_splitadj_1996to2023.json`,
  AMD: `https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_AMD_splitadj_1996to2023.json`,
  AMZN: `https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_AMZN_splitadj_1996to2023.json`,
  BABA: `https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_BABA_splitadj_1996to2023.json`,
  BAC: `https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_BAC_splitadj_1996to2023.json`,
  BA: `https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_BA_splitadj_1996to2023.json`,
  CSCO: `https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_CSCO_splitadj_1996to2023.json`,
  C: `https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_C_splitadj_1996to2023.json`,
  DIS: `https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_DIS_splitadj_1996to2023.json`,
  FB: `https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_FB_splitadj_1996to2023.json`,
  F: `https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_F_splitadj_1996to2023.json`,
  GE: `https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_GE_splitadj_1996to2023.json`,
  GM: `https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_GM_splitadj_1996to2023.json`,
  GOOG: `https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_GOOG_splitadj_1996to2023.json`,
  INTC: `https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_INTC_splitadj_1996to2023.json`,
  JPM: `https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_JPM_splitadj_1996to2023.json`,
  MSFT: `https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_MSFT_splitadj_1996to2023.json`,
  MS: `https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_MS_splitadj_1996to2023.json`,
  NVDA: `https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_NVDA_splitadj_1996to2023.json`,
  "^SPX": `https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_SPX_splitadj_1996to2023.json`,
  TSLA: `https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_TSLA_splitadj_1996to2023.json`,
  TWTR: `https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_TWTR_splitadj_1996to2023.json`,
  T: `https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_T_splitadj_1996to2023.json`,
  WFC: `https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_WFC_splitadj_1996to2023.json`,
  XOM: `https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_XOM_splitadj_1996to2023.json`,
};

// Regular price URLs
let REGULAR_PRICE_URLS: Record<StockCode, string> = {
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
  "^SPX": "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/SPX_data.json",
  TSLA: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/TSLA_data.json",
  TWTR: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/TWTR_data.json",
  T: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/T_data.json",
  WFC: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/WFC_data.json",
  XOM: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/XOM_data.json",
};

/**
 * Update BLOB_URLS and REGULAR_PRICE_URLS from blob_mapping.json
 */
export function updateBlobUrlsFromMapping(): void {
  Object.entries(blobMappingJson).forEach(([stock, url]) => {
    if (BLOB_URLS.hasOwnProperty(stock as StockCode)) {
      BLOB_URLS[stock as StockCode] = url as string;
    } else if (REGULAR_PRICE_URLS.hasOwnProperty(stock as StockCode)) {
      REGULAR_PRICE_URLS[stock as StockCode] = url as string;
    } else {
      console.warn(`⚠️ Skipped unknown stock code in mapping: ${stock}`);
    }
  });

  console.log("✅ Blob URLs updated from blob_mapping.json");
}

// --- Load bubble data ---
export async function loadBubbleData(
  stockCode: StockCode,
  dataSource: DataSource,
): Promise<BubbleData> {
  try {
    const url =
      dataSource === "WRDS"
        ? BLOB_URLS[stockCode]
        : `https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_${stockCode}_splitadj_2025to${CURRENT_YEAR}.json`;

    const res = await fetch(url);
    if (!res.ok) throw new Error(`Failed to load data: ${res.statusText}`);
    return await res.json();
  } catch (err) {
    console.error(err);
    throw err;
  }
}

// --- Transform bubble data for charts ---
export function transformDataForChart(
  bubbleData: BubbleData,
  optionType: OptionType,
  startDate?: Date,
  endDate?: Date,
): ChartDataPoint[] {
  const filtered = bubbleData.time_series_data.filter((p) => {
    const t = new Date(p.date).getTime();
    if (startDate && t < startDate.getTime()) return false;
    if (endDate && t > endDate.getTime()) return false;
    return true;
  });

  return filtered.map((p) => ({
    date: p.date,
    stockPrice: p.stock_prices.adjusted,
    tau1: p.bubble_estimates.daily_grouped[0][optionType],
    tau2: p.bubble_estimates.daily_grouped[1][optionType],
    tau3: p.bubble_estimates.daily_grouped[2][optionType],
  }));
}

// --- Date range helper ---
export function getDateRange(bubbleData: BubbleData): { min: Date; max: Date } {
  const times = bubbleData.time_series_data.map((p) => new Date(p.date).getTime());
  return { min: new Date(Math.min(...times)), max: new Date(Math.max(...times)) };
}

// --- Format tooltip data ---
export function formatTooltipData(dataPoint: ChartDataPoint, tauGroupsInfo: { mean: number }[]) {
  const date = new Date(dataPoint.date).toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  return ["tau1", "tau2", "tau3"].reduce((acc, tau, i) => {
    acc[tau] = {
      name: `Tau Group ${i + 1} (${tauGroupsInfo[i]?.mean ?? [0.25, 0.5, 1][i]})`,
      estimate: (dataPoint as any)[tau].mu.toFixed(3),
      lowerBound: (dataPoint as any)[tau].lb.toFixed(3),
      upperBound: (dataPoint as any)[tau].ub.toFixed(3),
    };
    return acc;
  }, { date, stockPrice: dataPoint.stockPrice.toFixed(2) } as any);
}

// --- Load regular price data ---
export async function loadRegularPriceData(stockCode: StockCode): Promise<RegularPriceData[]> {
  try {
    const url = REGULAR_PRICE_URLS[stockCode];
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Failed to load regular price data: ${res.statusText}`);

    const data = await res.json();
    if (Array.isArray(data.daily_data)) {
      return data.daily_data.map((p) => ({ date: p.date, price: p.raw_price }));
    } else if (Array.isArray(data)) {
      return data.map((p: any) => ({ date: p.date, price: p.price ?? p.close ?? p.raw_price }));
    } else if (data.data && Array.isArray(data.data)) {
      return data.data.map((p: any) => ({ date: p.date, price: p.price ?? p.close ?? p.raw_price }));
    }
    throw new Error(`Unexpected regular price data format for ${stockCode}`);
  } catch (err) {
    console.error(err);
    throw err;
  }
}

// --- Calculate price differences ---
export function calculatePriceDifferences(
  bubbleData: BubbleData,
  regularPriceData: RegularPriceData[],
  startDate?: Date,
  endDate?: Date,
): PriceDifferenceDataPoint[] {
  const regMap = new Map(
    regularPriceData.map((p) => [p.date.split("T")[0], p.price]),
  );

  const filtered = bubbleData.time_series_data.filter((p) => {
    const t = new Date(p.date).getTime();
    if (startDate && t < startDate.getTime()) return false;
    if (endDate && t > endDate.getTime()) return false;
    return true;
  });

  return filtered
    .map((p) => {
      const dateKey = p.date.split("T")[0];
      const regularPrice = regMap.get(dateKey);
      if (regularPrice === undefined) return null;
      const adjustedPrice = p.stock_prices.adjusted;
      const diff = adjustedPrice - regularPrice;
      return {
        date: p.date,
        adjustedPrice,
        regularPrice,
        difference: diff,
        percentageDifference: (diff / regularPrice) * 100,
      };
    })
    .filter(Boolean) as PriceDifferenceDataPoint[];
}
