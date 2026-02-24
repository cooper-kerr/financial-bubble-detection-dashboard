import type {
	BubbleData,
	ChartDataPoint,
	ConfidenceLevel,
	DataSource,
	OptionType,
	PriceDifferenceDataPoint,
	RegularPriceData,
	StockCode,
} from "../types/bubbleData";
import { recomputeEstimateForCI } from "../types/bubbleData";

// ─────────────────────────────────────────────────────────────────────────────
// WRDS (static historical dataset) — hardcoded Blob URLs, these never change
// ─────────────────────────────────────────────────────────────────────────────
const WRDS_BLOB_URLS: Record<StockCode, string> = {
	AAPL: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_AAPL_splitadj_1996to2023.json",
	AIG:  "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_AIG_splitadj_1996to2023.json",
	AMD:  "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_AMD_splitadj_1996to2023.json",
	AMZN: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_AMZN_splitadj_1996to2023.json",
	BABA: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_BABA_splitadj_1996to2023.json",
	BAC:  "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_BAC_splitadj_1996to2023.json",
	BA:   "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_BA_splitadj_1996to2023.json",
	CSCO: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_CSCO_splitadj_1996to2023.json",
	C:    "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_C_splitadj_1996to2023.json",
	DIS:  "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_DIS_splitadj_1996to2023.json",
	FB:   "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_FB_splitadj_1996to2023.json",
	F:    "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_F_splitadj_1996to2023.json",
	GE:   "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_GE_splitadj_1996to2023.json",
	GM:   "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_GM_splitadj_1996to2023.json",
	GOOG: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_GOOG_splitadj_1996to2023.json",
	INTC: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_INTC_splitadj_1996to2023.json",
	JPM:  "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_JPM_splitadj_1996to2023.json",
	MSFT: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_MSFT_splitadj_1996to2023.json",
	MS:   "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_MS_splitadj_1996to2023.json",
	NVDA: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_NVDA_splitadj_1996to2023.json",
	SPX:  "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_SPX_splitadj_1996to2023.json",
	TSLA: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_TSLA_splitadj_1996to2023.json",
	META: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_TWTR_splitadj_1996to2023.json",
	T:    "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_T_splitadj_1996to2023.json",
	WFC:  "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_WFC_splitadj_1996to2023.json",
	XOM:  "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_XOM_splitadj_1996to2023.json",
};

// ─────────────────────────────────────────────────────────────────────────────
// Regular price data URLs (static, unchanged)
// ─────────────────────────────────────────────────────────────────────────────
const REGULAR_PRICE_URLS: Record<StockCode, string> = {
	AAPL: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/AAPL_data.json",
	AIG:  "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/AIG_data.json",
	AMD:  "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/AMD_data.json",
	AMZN: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/AMZN_data.json",
	BABA: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/BABA_data.json",
	BAC:  "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/BAC_data.json",
	BA:   "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/BA_data.json",
	CSCO: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/CSCO_data.json",
	C:    "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/C_data.json",
	DIS:  "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/DIS_data.json",
	FB:   "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/FB_data.json",
	F:    "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/F_data.json",
	GE:   "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/GE_data.json",
	GM:   "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/GM_data.json",
	GOOG: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/GOOG_data.json",
	INTC: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/INTC_data.json",
	JPM:  "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/JPM_data.json",
	MSFT: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/MSFT_data.json",
	MS:   "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/MS_data.json",
	NVDA: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/NVDA_data.json",
	SPX:  "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/SPX_data.json",
	TSLA: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/TSLA_data.json",
	META: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/TWTR_data.json",
	T:    "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/T_data.json",
	WFC:  "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/WFC_data.json",
	XOM:  "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/XOM_data.json",
};

// ─────────────────────────────────────────────────────────────────────────────
// Yahoo (daily-updated) URL mapping — fetched at runtime from blob_mapping.json
// which update-blob-urls.ts uploads to Blob after each nightly run.
// Cached in memory for the lifetime of the page so we only fetch it once.
// ─────────────────────────────────────────────────────────────────────────────
const BLOB_MAPPING_URL =
	"https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/blob_mapping.json";

let yahooUrlCache: Record<string, string> | null = null;

async function getYahooUrlMapping(): Promise<Record<string, string>> {
	if (yahooUrlCache) return yahooUrlCache;

	const response = await fetch(BLOB_MAPPING_URL, {
		// Revalidate at most once per hour so the page picks up same-day updates
		// without hammering Blob on every render
		next: { revalidate: 3600 },
	} as RequestInit);

	if (!response.ok) {
		throw new Error(
			`Failed to fetch blob_mapping.json: ${response.status} ${response.statusText}`,
		);
	}

	yahooUrlCache = await response.json();
	return yahooUrlCache as Record<string, string>;
}

// ─────────────────────────────────────────────────────────────────────────────
// Public API
// ─────────────────────────────────────────────────────────────────────────────
export async function loadBubbleData(
	stockCode: StockCode,
	dataSource: DataSource,
): Promise<BubbleData> {
	try {
		let url: string;

		if (dataSource === "WRDS") {
			// Static historical dataset — URL never changes
			url = WRDS_BLOB_URLS[stockCode];
			if (!url) {
				throw new Error(`No WRDS URL configured for stock: ${stockCode}`);
			}
		} else {
			// Yahoo daily dataset — fetch current URL from blob_mapping.json
			const mapping = await getYahooUrlMapping();
			url = mapping[stockCode];
			if (!url) {
				throw new Error(
					`No Yahoo Blob URL found for ${stockCode} in blob_mapping.json. ` +
					`The nightly action may not have run yet, or this ticker is missing.`,
				);
			}
		}

		const response = await fetch(url);
		if (!response.ok) {
			throw new Error(
				`Failed to load data for ${stockCode} from ${dataSource}: ${response.statusText}`,
			);
		}

		const data: BubbleData = await response.json();
		data.time_series_data.sort(
			(a, b) => new Date(a.date).getTime() - new Date(b.date).getTime(),
		);
		return data;
	} catch (error) {
		console.error(`Error loading data for ${stockCode} from ${dataSource}:`, error);
		throw error;
	}
}

export function transformDataForChart(
	bubbleData: BubbleData,
	optionType: OptionType,
	startDate?: Date,
	endDate?: Date,
	confidenceLevel: ConfidenceLevel = 0.95,
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
		tau1: recomputeEstimateForCI(
			point.bubble_estimates.daily_grouped[0][optionType],
			confidenceLevel,
		),
		tau2: recomputeEstimateForCI(
			point.bubble_estimates.daily_grouped[1][optionType],
			confidenceLevel,
		),
		tau3: recomputeEstimateForCI(
			point.bubble_estimates.daily_grouped[2][optionType],
			confidenceLevel,
		),
	}));
}

export function getDateRange(bubbleData: BubbleData): { min: Date; max: Date } {
	let minTime = Number.POSITIVE_INFINITY;
	let maxTime = Number.NEGATIVE_INFINITY;

	for (const point of bubbleData.time_series_data) {
		const time = new Date(point.date).getTime();
		if (time < minTime) minTime = time;
		if (time > maxTime) maxTime = time;
	}

	return {
		min: new Date(minTime),
		max: new Date(maxTime),
	};
}

export function formatTooltipData(
	dataPoint: ChartDataPoint,
	tauGroupsInfo: { mean: number }[],
) {
	const date = new Date(dataPoint.date).toLocaleDateString("en-US", {
		year: "numeric",
		month: "long",
		day: "numeric",
	});

	return {
		date,
		stockPrice: dataPoint.stockPrice.toLocaleString("en-US", {
			minimumFractionDigits: 2,
			maximumFractionDigits: 2,
		}),
		tau1: {
			name: `Tau Group 1 (${tauGroupsInfo[0]?.mean || 0.25})`,
			estimate: dataPoint.tau1.mu.toFixed(3),
			lowerBound: dataPoint.tau1.lb.toFixed(3),
			upperBound: dataPoint.tau1.ub.toFixed(3),
		},
		tau2: {
			name: `Tau Group 2 (${tauGroupsInfo[1]?.mean || 0.5})`,
			estimate: dataPoint.tau2.mu.toFixed(3),
			lowerBound: dataPoint.tau2.lb.toFixed(3),
			upperBound: dataPoint.tau2.ub.toFixed(3),
		},
		tau3: {
			name: `Tau Group 3 (${tauGroupsInfo[2]?.mean || 1.0})`,
			estimate: dataPoint.tau3.mu.toFixed(3),
			lowerBound: dataPoint.tau3.lb.toFixed(3),
			upperBound: dataPoint.tau3.ub.toFixed(3),
		},
	};
}

export async function loadRegularPriceData(
	stockCode: StockCode,
): Promise<RegularPriceData[]> {
	try {
		const url = REGULAR_PRICE_URLS[stockCode];
		console.log(`Loading regular price data for ${stockCode} from:`, url);
		const response = await fetch(url);

		if (!response.ok) {
			throw new Error(
				`Failed to load regular price data for ${stockCode}: ${response.statusText}`,
			);
		}

		const data = await response.json();

		// Handle { daily_data: [{ date, raw_price }] }
		if (data.daily_data && Array.isArray(data.daily_data)) {
			return data.daily_data.map(
				(point: { date: string; raw_price: number }) => ({
					date: point.date,
					price: point.raw_price,
				}),
			);
		}

		// Fallback: flat array
		if (Array.isArray(data)) {
			return data.map((point) => ({
				date: point.date,
				price: point.price || point.close || point.value || point.raw_price,
			}));
		}

		// Fallback: { data: [...] }
		if (data.data && Array.isArray(data.data)) {
			return data.data.map(
				(point: { date: string; price: number; close: number; value: number; raw_price: number }) => ({
					date: point.date,
					price: point.price || point.close || point.value || point.raw_price,
				}),
			);
		}

		throw new Error(`Unexpected data format for ${stockCode}`);
	} catch (error) {
		console.error(`Error loading regular price data for ${stockCode}:`, error);
		throw error;
	}
}

export function calculatePriceDifferences(
	bubbleData: BubbleData,
	regularPriceData: RegularPriceData[],
	startDate?: Date,
	endDate?: Date,
): PriceDifferenceDataPoint[] {
	const regularPriceMap = new Map<string, number>();
	for (const point of regularPriceData) {
		const normalizedDate = point.date.split("T")[0];
		regularPriceMap.set(normalizedDate, point.price);
	}

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

	const result: PriceDifferenceDataPoint[] = [];

	for (const point of filteredData) {
		const normalizedBubbleDate = point.date.split("T")[0];
		const regularPrice = regularPriceMap.get(normalizedBubbleDate);
		if (regularPrice !== undefined) {
			const adjustedPrice = point.stock_prices.adjusted;
			const difference = adjustedPrice - regularPrice;
			const percentageDifference = (difference / regularPrice) * 100;
			result.push({
				date: point.date,
				adjustedPrice,
				regularPrice,
				difference,
				percentageDifference,
			});
		}
	}

	return result;
}
