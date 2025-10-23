import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type {
	BubbleData,
	ChartDataPoint,
	DataSource,
	OptionType,
	PriceDifferenceDataPoint,
	RegularPriceData,
	StockCode,
} from "../types/bubbleData";
import {
	calculatePriceDifferences,
	getDateRange,
	loadBubbleData,
	loadRegularPriceData,
	transformDataForChart,
} from "../utils/dataLoader";

interface DashboardState {
	selectedStock: StockCode;
	dataSource: DataSource;
	startDate: Date | null;
	endDate: Date | null;
	bubbleData: BubbleData | null;
	regularPriceData: RegularPriceData[] | null;
	loading: boolean;
	error: string | null;
}

export function useDashboardData() {
	const [state, setState] = useState<DashboardState>({
		selectedStock: "SPX",
		dataSource: "WRDS",
		startDate: null,
		endDate: null,
		bubbleData: null,
		regularPriceData: null,
		loading: false,
		error: null,
	});

	// Ref to store timeout for debouncing date changes
	const dateChangeTimeoutRef = useRef<NodeJS.Timeout | null>(null);

	// Load data when stock changes
	useEffect(() => {
		let isCancelled = false;

		const loadData = async () => {
			// Show loading and fetch data
			setState((prev) => ({ ...prev, loading: true, error: null }));

			try {
				// Load both bubble data and regular price data in parallel
				const [data, regularData] = await Promise.allSettled([
					loadBubbleData(state.selectedStock, state.dataSource),
					loadRegularPriceData(state.selectedStock),
				]);

				// Check if component is still mounted and request is still valid
				if (isCancelled) return;

				// Handle bubble data result
				if (data.status === "rejected") {
					throw new Error(`Failed to load bubble data: ${data.reason}`);
				}

				const dateRange = getDateRange(data.value);

				// Handle regular price data result (optional, don't fail if not available)
				const regularPriceData =
					regularData.status === "fulfilled" ? regularData.value : null;
				if (regularData.status === "rejected") {
					console.error(
						`Regular price data failed to load for ${state.selectedStock}:`,
						regularData.reason,
					);
				} else if (regularPriceData) {
					console.log(
						`Regular price data loaded successfully for ${state.selectedStock}:`,
						{
							count: regularPriceData.length,
							sample: regularPriceData.slice(0, 2),
						},
					);
				}

				setState((prev) => ({
					...prev,
					bubbleData: data.value,
					regularPriceData,
					loading: false,
					// Set initial date range to full range if not already set
					startDate: prev.startDate || dateRange.min,
					endDate: prev.endDate || dateRange.max,
				}));
			} catch (error) {
				if (isCancelled) return;

				setState((prev) => ({
					...prev,
					loading: false,
					error: error instanceof Error ? error.message : "Failed to load data",
				}));
			}
		};

		loadData();

		// Cleanup function to cancel the request if component unmounts or stock changes
		return () => {
			isCancelled = true;
		};
	}, [state.selectedStock, state.dataSource]);

	// Cleanup timeout on unmount
	useEffect(() => {
		return () => {
			if (dateChangeTimeoutRef.current) {
				clearTimeout(dateChangeTimeoutRef.current);
			}
		};
	}, []);

	const setSelectedStock = useCallback((stock: StockCode) => {
		setState((prev) => ({ ...prev, selectedStock: stock }));
	}, []);

	const setDataSource = useCallback((dataSource: DataSource) => {
		setState((prev) => ({ ...prev, dataSource }));
	}, []);

	const setDateRange = useCallback(
		(startDate: Date | null, endDate: Date | null) => {
			// Clear existing timeout
			if (dateChangeTimeoutRef.current) {
				clearTimeout(dateChangeTimeoutRef.current);
			}

			// Debounce date changes to prevent excessive re-renders
			dateChangeTimeoutRef.current = setTimeout(() => {
				setState((prev) => ({ ...prev, startDate, endDate }));
			}, 100); // 100ms debounce
		},
		[],
	);

	const resetDateRange = useCallback(() => {
		if (state.bubbleData) {
			const dateRange = getDateRange(state.bubbleData);
			setState((prev) => ({
				...prev,
				startDate: dateRange.min,
				endDate: dateRange.max,
			}));
		}
	}, [state.bubbleData]);

	// Memoize chart data transformations for each option type
	const chartDataMemo = useMemo(() => {
		if (!state.bubbleData) {
			return {
				put: [],
				call: [],
				combined: [],
			};
		}

		return {
			put: transformDataForChart(
				state.bubbleData,
				"put",
				state.startDate || undefined,
				state.endDate || undefined,
			),
			call: transformDataForChart(
				state.bubbleData,
				"call",
				state.startDate || undefined,
				state.endDate || undefined,
			),
			combined: transformDataForChart(
				state.bubbleData,
				"combined",
				state.startDate || undefined,
				state.endDate || undefined,
			),
		};
	}, [state.bubbleData, state.startDate, state.endDate]);

	const getChartData = useCallback(
		(optionType: OptionType): ChartDataPoint[] => {
			return chartDataMemo[optionType];
		},
		[chartDataMemo],
	);

	const getPriceDifferenceData = useCallback((): PriceDifferenceDataPoint[] => {
		if (!state.bubbleData || !state.regularPriceData) {
			return [];
		}
		return calculatePriceDifferences(
			state.bubbleData,
			state.regularPriceData,
			state.startDate || undefined,
			state.endDate || undefined,
		);
	}, [
		state.bubbleData,
		state.regularPriceData,
		state.startDate,
		state.endDate,
	]);

	const getAvailableDateRange = useCallback(() => {
		if (!state.bubbleData) return null;
		return getDateRange(state.bubbleData);
	}, [state.bubbleData]);

	return {
		selectedStock: state.selectedStock,
		dataSource: state.dataSource,
		startDate: state.startDate,
		endDate: state.endDate,
		bubbleData: state.bubbleData,
		regularPriceData: state.regularPriceData,
		loading: state.loading,
		error: state.error,
		setSelectedStock,
		setDataSource,
		setDateRange,
		resetDateRange,
		getChartData,
		getPriceDifferenceData,
		getAvailableDateRange,
	};
}
