export interface TauGroupInfo {
	name: string;
	range: string;
	mean: number;
}

export interface BubbleEstimate {
	mu: number;
	lb: number;
	ub: number;
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
	"TWTR",
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

export const TAU_COLORS = {
	tau1: "#1f77b4", // Blue
	tau2: "#2ca02c", // Green
	tau3: "#ff7f0e", // Orange
	stockPrice: "#d62728", // Red
} as const;
