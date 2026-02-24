export interface TauGroupInfo {
	name: string;
	range: string;
	mean: number;
}

export interface BubbleEstimate {
	mu: number;
	lb: number;
	ub: number;
	/** Newey-West standard error of the bubble estimate.
	 *  Optional — present in JSONs generated after the se-emission change.
	 *  Used by the frontend to recompute CI bounds for any confidence level. */
	se?: number;
}

export interface DailyGroupedData {
	put: BubbleEstimate;
	call: BubbleEstimate;
	combined: BubbleEstimate;
}

export interface TimeSeriesDataPoint {
	date: string;
	stock_prices: {
		adjusted: number;
		regular?: number; // Optional regular price for comparison
	};
	bubble_estimates: {
		daily_grouped: DailyGroupedData[];
	};
}

export interface BubbleDataMetadata {
	stockcode: string;
	start_date_param: string;
	end_date_param: string;
	rolling_window_days: number;
	num_steps: number;
	optimization_threshold: number;
	h_number_sd: number;
	tau_groups_info: TauGroupInfo[];
	option_types_info: string[];
	time_series_start_date: string;
	time_series_end_date: string;
}

export interface BubbleData {
	metadata: BubbleDataMetadata;
	time_series_data: TimeSeriesDataPoint[];
}

export type OptionType = "put" | "call" | "combined";

export interface ChartDataPoint {
	date: string;
	stockPrice: number;
	tau1: BubbleEstimate;
	tau2: BubbleEstimate;
	tau3: BubbleEstimate;
}

// New interface for regular price data
export interface RegularPriceData {
	date: string;
	price: number;
}

// New interface for price difference chart data
export interface PriceDifferenceDataPoint {
	date: string;
	adjustedPrice: number;
	regularPrice: number;
	difference: number;
	percentageDifference: number;
}

export const STOCK_LIST = [
	"SPX",
	"AAPL",
	"BAC",
	"C",
	"MSFT",
	"FB",
	"GE",
	"INTC",
	"CSCO",
	"BABA",
	"WFC",
	"JPM",
	"AMD",
	"META",
	"F",
	"TSLA",
	"GOOG",
	"T",
	"XOM",
	"AMZN",
	"MS",
	"NVDA",
	"AIG",
	"GM",
	"DIS",
	"BA",
] as const;

export type StockCode = (typeof STOCK_LIST)[number];

export type DataSource = "WRDS" | "Yahoo Finance";

export const TAU_COLORS = {
	tau1: "#1f77b4", // Blue
	tau2: "#2ca02c", // Green
	tau3: "#ff7f0e", // Orange
	stockPrice: "#d62728", // Red
} as const;

// ─────────────────────────────────────────────────────────────────────────────
// Confidence level support
// ─────────────────────────────────────────────────────────────────────────────

/** Supported confidence levels for the CI display. */
export const CONFIDENCE_LEVELS = [0.90, 0.95, 0.99] as const;
export type ConfidenceLevel = (typeof CONFIDENCE_LEVELS)[number];

/** The reference z-value at which the stored lb/ub were computed (95%). */
export const Z_REFERENCE = 1.96;
export const CONFIDENCE_REFERENCE: ConfidenceLevel = 0.95;

/** Normal quantile (z_{α/2}) for each supported confidence level. */
export const Z_SCORES: Record<ConfidenceLevel, number> = {
	0.90: 1.645,
	0.95: 1.960,
	0.99: 2.576,
};

/**
 * Recompute BubbleEstimate bounds for a given confidence level.
 *
 * Math (from Jarrow & Kwok eq. 19):
 *   lb_new = lb_ref − (z_new − z_ref) × se
 *   ub_new = ub_ref + (z_new − z_ref) × se
 *
 * The identification-bound terms (Aₗ, Aᵤ) cancel in the difference,
 * so we only need `se` and the reference z (1.96 at 95%).
 *
 * If `se` is missing (old JSON), returns the estimate unchanged.
 */
export function recomputeEstimateForCI(
	est: BubbleEstimate,
	confidenceLevel: ConfidenceLevel,
): BubbleEstimate {
	if (est.se === undefined || confidenceLevel === CONFIDENCE_REFERENCE) {
		return est;
	}
	const delta = (Z_SCORES[confidenceLevel] - Z_REFERENCE) * est.se;
	return {
		mu: est.mu,
		lb: est.lb - delta,
		ub: est.ub + delta,
		se: est.se,
	};
}
