import React from "react";
import Plot from "react-plotly.js";
import type { ChartDataPoint, OptionType } from "../types/bubbleData";
import { TAU_COLORS } from "../types/bubbleData";

interface BubbleChartPlotlyProps {
	data: ChartDataPoint[];
	optionType: OptionType;
	title: string;
	tauGroupsInfo: { mean: number }[];
	loading?: boolean;
}

export function BubbleChartPlotly({ data, title, tauGroupsInfo }: BubbleChartPlotlyProps) {
	if (!data || data.length === 0) {
		return (
			<div className="flex h-96 items-center justify-center">
				<p className="text-muted-foreground">No data available</p>
			</div>
		);
	}

	// Prepare data for Plotly
	const dates = data.map((d) => d.date);
	const stockPrices = data.map((d) => d.stockPrice);

	// Tau estimates
	const tau1Estimates = data.map((d) => d.tau1.mu);
	const tau2Estimates = data.map((d) => d.tau2.mu);
	const tau3Estimates = data.map((d) => d.tau3.mu);

	// Confidence intervals
	const tau1Upper = data.map((d) => d.tau1.ub);
	const tau1Lower = data.map((d) => d.tau1.lb);
	const tau2Upper = data.map((d) => d.tau2.ub);
	const tau2Lower = data.map((d) => d.tau2.lb);
	const tau3Upper = data.map((d) => d.tau3.ub);
	const tau3Lower = data.map((d) => d.tau3.lb);

	const traces = [
		// Tau 1 confidence band
		{
			x: dates,
			y: tau1Upper,
			fill: "tonexty",
			fillcolor: "rgba(31, 119, 180, 0.3)",
			line: { color: "transparent" },
			mode: "lines" as const,
			name: "CI τ1",
			showlegend: true,
			legendgroup: "tau1",
			hoverinfo: "skip" as const,
			yaxis: "y",
		},
		{
			x: dates,
			y: tau1Lower,
			fill: "none",
			line: { color: "transparent" },
			mode: "lines" as const,
			name: "CI τ1 lower",
			showlegend: false,
			legendgroup: "tau1",
			hoverinfo: "skip" as const,
			yaxis: "y",
		},
		// Tau 2 confidence band
		{
			x: dates,
			y: tau2Upper,
			fill: "tonexty",
			fillcolor: "rgba(44, 160, 44, 0.3)",
			line: { color: "transparent" },
			mode: "lines" as const,
			name: "CI τ2",
			showlegend: true,
			legendgroup: "tau2",
			hoverinfo: "skip" as const,
			yaxis: "y",
		},
		{
			x: dates,
			y: tau2Lower,
			fill: "none",
			line: { color: "transparent" },
			mode: "lines" as const,
			name: "CI τ2 lower",
			showlegend: false,
			legendgroup: "tau2",
			hoverinfo: "skip" as const,
			yaxis: "y",
		},
		// Tau 3 confidence band
		{
			x: dates,
			y: tau3Upper,
			fill: "tonexty",
			fillcolor: "rgba(255, 127, 14, 0.3)",
			line: { color: "transparent" },
			mode: "lines" as const,
			name: "CI τ3",
			showlegend: true,
			legendgroup: "tau3",
			hoverinfo: "skip" as const,
			yaxis: "y",
		},
		{
			x: dates,
			y: tau3Lower,
			fill: "none",
			line: { color: "transparent" },
			mode: "lines" as const,
			name: "CI τ3 lower",
			showlegend: false,
			legendgroup: "tau3",
			hoverinfo: "skip" as const,
			yaxis: "y",
		},
		// Tau estimate lines
		{
			x: dates,
			y: tau1Estimates,
			mode: "lines" as const,
			name: `τ ∈ (${tauGroupsInfo[0]?.mean || 0.25}±0.1)`,
			line: { color: TAU_COLORS.tau1, width: 2 },
			yaxis: "y",
		},
		{
			x: dates,
			y: tau2Estimates,
			mode: "lines" as const,
			name: `τ ∈ (${tauGroupsInfo[1]?.mean || 0.5}±0.15)`,
			line: { color: TAU_COLORS.tau2, width: 2, dash: "dash" },
			yaxis: "y",
		},
		{
			x: dates,
			y: tau3Estimates,
			mode: "lines" as const,
			name: `τ ∈ (${tauGroupsInfo[2]?.mean || 1.0}±0.25)`,
			line: { color: TAU_COLORS.tau3, width: 2, dash: "dashdot" },
			yaxis: "y",
		},
		// Stock price
		{
			x: dates,
			y: stockPrices,
			mode: "lines" as const,
			name: "Stock Price",
			line: { color: TAU_COLORS.stockPrice, width: 2 },
			yaxis: "y2",
		},
	];

	const layout = {
		title: {
			text: title,
			font: { size: 16 },
		},
		xaxis: {
			title: "Date",
			type: "date" as const,
		},
		yaxis: {
			title: "Bubble Estimate",
			side: "left" as const,
			autorange: true,
		},
		yaxis2: {
			title: "Stock Price ($)",
			side: "right" as const,
			overlaying: "y",
		},
		legend: {
			x: 0.02,
			y: 0.98,
			bgcolor: "rgba(255, 255, 255, 0.8)",
			bordercolor: "rgba(0, 0, 0, 0.2)",
			borderwidth: 1,
		},
		hovermode: "x unified" as const,
		margin: { l: 60, r: 60, t: 60, b: 60 },
		height: 500,
	};

	const config = {
		responsive: true,
		displayModeBar: true,
		modeBarButtonsToRemove: ["lasso2d", "select2d"],
		displaylogo: false,
	};

	return (
		<div className="w-full">
			<Plot
				data={traces}
				layout={layout}
				config={config}
				style={{ width: "100%", height: "500px" }}
			/>
		</div>
	);
}
