import { describe, expect, it } from "vitest";
import type { BubbleData } from "../types/bubbleData";
import {
	calculatePriceDifferences,
	getDateRange,
	getEmbeddedRegularPriceData,
	transformDataForChart,
} from "./dataLoader";

const estimate = (mu: number) => ({
	mu,
	lb: mu - 0.1,
	ub: mu + 0.1,
});

const sampleBubbleData: BubbleData = {
	metadata: {
		stockcode: "TEST",
		start_date_param: "2024-01-01",
		end_date_param: "2024-01-03",
		rolling_window_days: 250,
		num_steps: 3,
		optimization_threshold: 0.01,
		h_number_sd: 1,
		tau_groups_info: [
			{ name: "Short", range: "0-0.33", mean: 0.25 },
			{ name: "Medium", range: "0.33-0.66", mean: 0.5 },
			{ name: "Long", range: "0.66-1", mean: 1 },
		],
		option_types_info: ["put", "call", "combined"],
		time_series_start_date: "2024-01-01",
		time_series_end_date: "2024-01-03",
	},
	time_series_data: [
		{
			date: "2024-01-01T00:00:00.000Z",
			stock_prices: { adjusted: 100, regular: 95 },
			bubble_estimates: {
				daily_grouped: [
					{ put: estimate(0.1), call: estimate(0.2), combined: estimate(0.3) },
					{ put: estimate(0.4), call: estimate(0.5), combined: estimate(0.6) },
					{ put: estimate(0.7), call: estimate(0.8), combined: estimate(0.9) },
				],
			},
		},
		{
			date: "2024-01-02T00:00:00.000Z",
			stock_prices: { adjusted: 110, regular: 100 },
			bubble_estimates: {
				daily_grouped: [
					{ put: estimate(1.1), call: estimate(1.2), combined: estimate(1.3) },
					{ put: estimate(1.4), call: estimate(1.5), combined: estimate(1.6) },
					{ put: estimate(1.7), call: estimate(1.8), combined: estimate(1.9) },
				],
			},
		},
		{
			date: "2024-01-03T00:00:00.000Z",
			stock_prices: { adjusted: 130 },
			bubble_estimates: {
				daily_grouped: [
					{ put: estimate(2.1), call: estimate(2.2), combined: estimate(2.3) },
					{ put: estimate(2.4), call: estimate(2.5), combined: estimate(2.6) },
					{ put: estimate(2.7), call: estimate(2.8), combined: estimate(2.9) },
				],
			},
		},
	],
};

describe("dataLoader transformations", () => {
	it("filters chart data by date and selects the requested option type", () => {
		const chartData = transformDataForChart(
			sampleBubbleData,
			"combined",
			new Date("2024-01-02T00:00:00.000Z"),
			new Date("2024-01-03T00:00:00.000Z"),
		);

		expect(chartData).toHaveLength(2);
		expect(chartData[0]).toMatchObject({
			date: "2024-01-02T00:00:00.000Z",
			stockPrice: 110,
			tau1: estimate(1.3),
			tau2: estimate(1.6),
			tau3: estimate(1.9),
		});
		expect(chartData[1].tau1).toEqual(estimate(2.3));
	});

	it("returns the minimum and maximum dates from unsorted time series data", () => {
		const dateRange = getDateRange({
			...sampleBubbleData,
			time_series_data: [
				sampleBubbleData.time_series_data[2],
				sampleBubbleData.time_series_data[0],
				sampleBubbleData.time_series_data[1],
			],
		});

		expect(dateRange.min.toISOString()).toBe("2024-01-01T00:00:00.000Z");
		expect(dateRange.max.toISOString()).toBe("2024-01-03T00:00:00.000Z");
	});

	it("prefers embedded price_series_data for regular price extraction", () => {
		const regularPrices = getEmbeddedRegularPriceData({
			...sampleBubbleData,
			price_series_data: [
				{ date: "2024-01-01", regular: 90, adjusted: 100 },
				{ date: "2024-01-02", regular: 100, adjusted: 110 },
			],
		});

		expect(regularPrices).toEqual([
			{ date: "2024-01-01", price: 90 },
			{ date: "2024-01-02", price: 100 },
		]);
	});

	it("calculates price differences from external regular prices with date filtering", () => {
		const differences = calculatePriceDifferences(
			sampleBubbleData,
			[
				{ date: "2024-01-01", price: 95 },
				{ date: "2024-01-02", price: 100 },
				{ date: "2024-01-03", price: 125 },
			],
			new Date("2024-01-02T00:00:00.000Z"),
		);

		expect(differences).toEqual([
			{
				date: "2024-01-02T00:00:00.000Z",
				adjustedPrice: 110,
				regularPrice: 100,
				difference: 10,
				percentageDifference: 10,
			},
			{
				date: "2024-01-03T00:00:00.000Z",
				adjustedPrice: 130,
				regularPrice: 125,
				difference: 5,
				percentageDifference: 4,
			},
		]);
	});
});
