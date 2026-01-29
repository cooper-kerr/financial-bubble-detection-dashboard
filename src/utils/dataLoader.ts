import type {
	BubbleData,
	ChartDataPoint,
	DataSource,
	OptionType,
	PriceDifferenceDataPoint,
	RegularPriceData,
	StockCode,
} from "../types/bubbleData";

// Vercel Blob Storage URLs for each stock
const BLOB_URLS: Record<StockCode, string> = {
	AAPL: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_AAPL_splitadj_1996to2023.json",
	AIG: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_AIG_splitadj_1996to2023.json",
	AMD: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_AMD_splitadj_1996to2023.json",
	AMZN: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_AMZN_splitadj_1996to2023.json",
	BABA: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_BABA_splitadj_1996to2023.json",
	BAC: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_BAC_splitadj_1996to2023.json",
	BA: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_BA_splitadj_1996to2023.json",
	CSCO: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_CSCO_splitadj_1996to2023.json",
	C: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_C_splitadj_1996to2023.json",
	DIS: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_DIS_splitadj_1996to2023.json",
	FB: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_FB_splitadj_1996to2023.json",
	F: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_F_splitadj_1996to2023.json",
	GE: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_GE_splitadj_1996to2023.json",
	GM: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_GM_splitadj_1996to2023.json",
	GOOG: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_GOOG_splitadj_1996to2023.json",
	INTC: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_INTC_splitadj_1996to2023.json",
	JPM: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_JPM_splitadj_1996to2023.json",
	MSFT: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_MSFT_splitadj_1996to2023.json",
	MS: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_MS_splitadj_1996to2023.json",
	NVDA: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_NVDA_splitadj_1996to2023.json",
	SPX: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_SPX_splitadj_1996to2023.json",
	TSLA: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_TSLA_splitadj_1996to2023.json",
	META: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_TWTR_splitadj_1996to2023.json",
	T: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_T_splitadj_1996to2023.json",
	WFC: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_WFC_splitadj_1996to2023.json",
	XOM: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_XOM_splitadj_1996to2023.json",
};

// Regular price data URLs from blob storage
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
	META: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/TWTR_data.json",
	T: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/T_data.json",
	WFC: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/WFC_data.json",
	XOM: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/XOM_data.json",
};

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
			url = `/data/bubble_data_${stockCode}_splitadj_2025to${currentYear}.json`;
		}

		const response = await fetch(url);
		if (!response.ok) {
			throw new Error(
				`Failed to load data for ${stockCode} from ${dataSource}: ${response.statusText}`,
			);
		}

		const data: BubbleData = await response.json();
		data.time_series_data.sort(
		    (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
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
): ChartDataPoint[] {
	let filteredData = bubbleData.time_series_data;

	// Filter by date range if provided - optimize by pre-converting dates
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

	const result = filteredData.map((point) => ({
		date: point.date,
		stockPrice: point.stock_prices.adjusted,
		tau1: point.bubble_estimates.daily_grouped[0][optionType],
		tau2: point.bubble_estimates.daily_grouped[1][optionType],
		tau3: point.bubble_estimates.daily_grouped[2][optionType],
	}));

	return result;
}

export function getDateRange(bubbleData: BubbleData): { min: Date; max: Date } {
	// Find min/max in single pass
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

// Load regular price data
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
		console.log(`Raw regular price data for ${stockCode}:`, {
			type: typeof data,
			isArray: Array.isArray(data),
			keys: typeof data === "object" ? Object.keys(data) : "N/A",
			sampleData: Array.isArray(data)
				? data.slice(0, 2)
				: data.data
					? data.data.slice(0, 2)
					: typeof data === "object"
						? Object.entries(data).slice(0, 2)
						: data,
		});

		// Handle the actual data structure:
		// { daily_data: [{ date: "YYYY-MM-DD", raw_price: number }, ...] }
		if (data.daily_data && Array.isArray(data.daily_data)) {
			const result = data.daily_data.map(
				(point: {
					date: string;
					raw_price: number;
				}) => ({
					date: point.date,
					price: point.raw_price,
				}),
			);
			console.log(`Processed regular price data for ${stockCode}:`, {
				count: result.length,
				sample: result.slice(0, 2),
			});
			return result;
		}

		// Fallback for other possible structures
		if (Array.isArray(data)) {
			const result = data.map((point) => ({
				date: point.date,
				price: point.price || point.close || point.value || point.raw_price,
			}));
			console.log(`Processed regular price data for ${stockCode}:`, {
				count: result.length,
				sample: result.slice(0, 2),
			});
			return result;
		}

		if (data.data && Array.isArray(data.data)) {
			const result = data.data.map(
				(point: {
					date: string;
					price: number;
					close: number;
					value: number;
					raw_price: number;
				}) => ({
					date: point.date,
					price: point.price || point.close || point.value || point.raw_price,
				}),
			);
			console.log(`Processed regular price data for ${stockCode}:`, {
				count: result.length,
				sample: result.slice(0, 2),
			});
			return result;
		}

		throw new Error(`Unexpected data format for ${stockCode}`);
	} catch (error) {
		console.error(`Error loading regular price data for ${stockCode}:`, error);
		throw error;
	}
}

// Calculate price differences between adjusted and regular prices
export function calculatePriceDifferences(
	bubbleData: BubbleData,
	regularPriceData: RegularPriceData[],
	startDate?: Date,
	endDate?: Date,
): PriceDifferenceDataPoint[] {
	console.log("calculatePriceDifferences called with:", {
		bubbleDataPoints: bubbleData.time_series_data.length,
		regularDataPoints: regularPriceData.length,
		bubbleDataDateRange: {
			first: bubbleData.time_series_data[0]?.date,
			last: bubbleData.time_series_data[bubbleData.time_series_data.length - 1]
				?.date,
		},
		regularDataDateRange: {
			first: regularPriceData[0]?.date,
			last: regularPriceData[regularPriceData.length - 1]?.date,
		},
		bubbleDataSample: bubbleData.time_series_data
			.slice(0, 2)
			.map((p) => ({ date: p.date, price: p.stock_prices.adjusted })),
		regularDataSample: regularPriceData.slice(0, 2),
	});

	// Create a map of regular prices by date for quick lookup
	// Normalize dates to YYYY-MM-DD format for matching
	const regularPriceMap = new Map<string, number>();
	for (const point of regularPriceData) {
		// Ensure date is in YYYY-MM-DD format
		const normalizedDate = point.date.split("T")[0]; // Remove time part if present
		regularPriceMap.set(normalizedDate, point.price);
	}

	let filteredData = bubbleData.time_series_data;

	// Filter by date range if provided
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

	// Calculate differences for matching dates
	const result: PriceDifferenceDataPoint[] = [];
	let matchCount = 0;
	let noMatchCount = 0;

	for (const point of filteredData) {
		// Normalize bubble data date to YYYY-MM-DD format for matching
		const normalizedBubbleDate = point.date.split("T")[0]; // Remove time part if present
		const regularPrice = regularPriceMap.get(normalizedBubbleDate);
		if (regularPrice !== undefined) {
			const adjustedPrice = point.stock_prices.adjusted;
			const difference = adjustedPrice - regularPrice;
			const percentageDifference = (difference / regularPrice) * 100;

			result.push({
				date: point.date, // Keep original date format for display
				adjustedPrice,
				regularPrice,
				difference,
				percentageDifference,
			});
			matchCount++;
		} else {
			noMatchCount++;
			if (noMatchCount <= 5) {
				// Log first 5 non-matches for debugging
				console.log(`No match found for bubble date: ${normalizedBubbleDate}`);
			}
		}
	}

	console.log("calculatePriceDifferences result:", {
		totalMatches: matchCount,
		totalNoMatches: noMatchCount,
		resultLength: result.length,
		sample: result.slice(0, 2),
	});

	return result;
}
