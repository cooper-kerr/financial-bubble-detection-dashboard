import type {
	BubbleData,
	ChartDataPoint,
	OptionType,
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
	TWTR: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_TWTR_splitadj_1996to2023.json",
	T: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_T_splitadj_1996to2023.json",
	WFC: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_WFC_splitadj_1996to2023.json",
	XOM: "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_XOM_splitadj_1996to2023.json",
};

export async function loadBubbleData(
	stockCode: StockCode,
): Promise<BubbleData> {
	try {
		// Try Blob Storage first, fallback to local files
		const blobUrl = BLOB_URLS[stockCode];
		const url = blobUrl || `/data/bubble_data_${stockCode}_splitadj_1996to2023.json`;

		const response = await fetch(url);
		if (!response.ok) {
			throw new Error(
				`Failed to load data for ${stockCode}: ${response.statusText}`,
			);
		}

		const data: BubbleData = await response.json();
		return data;
	} catch (error) {
		console.error(`Error loading data for ${stockCode}:`, error);
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
			style: "currency",
			currency: "USD",
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
