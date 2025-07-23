import { useTheme } from "@/components/theme-provider";
import { Card, CardContent } from "@/components/ui/card";
import React, { useMemo } from "react";
import { InlineMath } from "react-katex";
import Plot from "react-plotly.js";
import {
	type ChartDataPoint,
	type OptionType,
	TAU_COLORS,
} from "../types/bubbleData";
import { LoadingSpinner } from "./LoadingSpinner";

interface PlotlyBubbleChartProps {
	data: ChartDataPoint[];
	optionType: OptionType;
	title: string;
	mathExpression?: string;
	tauGroupsInfo: { mean: number }[];
	loading?: boolean;
}

export const PlotlyBubbleChart = React.memo(function PlotlyBubbleChart({
	data,
	optionType,
	title,
	mathExpression,
	tauGroupsInfo,
	loading,
}: PlotlyBubbleChartProps) {
	const { theme } = useTheme();
	const plotData = useMemo(() => {
		if (!data || data.length === 0) {
			return [];
		}

		const dates = data.map((d) => d.date);
		const stockPrices = data.map((d) => d.stockPrice);

		// Prepare bubble estimate data for each tau group
		const tau1Estimates = data.map((d) => d.tau1.mu);
		const tau2Estimates = data.map((d) => d.tau2.mu);
		const tau3Estimates = data.map((d) => d.tau3.mu);

		// Prepare confidence band data
		const tau1Upper = data.map((d) => d.tau1.ub);
		const tau1Lower = data.map((d) => d.tau1.lb);
		const tau2Upper = data.map((d) => d.tau2.ub);
		const tau2Lower = data.map((d) => d.tau2.lb);
		const tau3Upper = data.map((d) => d.tau3.ub);
		const tau3Lower = data.map((d) => d.tau3.lb);

		return [
			// Tau Group 1 confidence band (lower bound first, then upper with fill)
			{
				x: dates,
				y: tau1Lower,
				line: { color: "transparent" },
				name: "CI τ1 lower",
				showlegend: false,
				hoverinfo: "skip",
				yaxis: "y",
			},
			{
				x: dates,
				y: tau1Upper,
				fill: "tonexty",
				fillcolor: "rgba(31, 119, 180, 0.3)",
				line: { color: "transparent" },
				name: "CI τ1",
				showlegend: true,
				hoverinfo: "skip",
				yaxis: "y",
			},
			// Tau Group 2 confidence band (lower bound first, then upper with fill)
			{
				x: dates,
				y: tau2Lower,
				line: { color: "transparent" },
				name: "CI τ2 lower",
				showlegend: false,
				hoverinfo: "skip",
				yaxis: "y",
			},
			{
				x: dates,
				y: tau2Upper,
				fill: "tonexty",
				fillcolor: "rgba(44, 160, 44, 0.3)",
				line: { color: "transparent" },
				name: "CI τ2",
				showlegend: true,
				hoverinfo: "skip",
				yaxis: "y",
			},
			// Tau Group 3 confidence band (lower bound first, then upper with fill)
			{
				x: dates,
				y: tau3Lower,
				line: { color: "transparent" },
				name: "CI τ3 lower",
				showlegend: false,
				hoverinfo: "skip",
				yaxis: "y",
			},
			{
				x: dates,
				y: tau3Upper,
				fill: "tonexty",
				fillcolor: "rgba(255, 127, 14, 0.3)",
				line: { color: "transparent" },
				name: "CI τ3",
				showlegend: true,
				hoverinfo: "skip",
				yaxis: "y",
			},
			// Tau Group 1 main line
			{
				x: dates,
				y: tau1Estimates,
				type: "scatter" as const,
				mode: "lines" as const,
				name: `τ ∈ (${tauGroupsInfo[0]?.mean || 0.25}±0.1)`,
				line: {
					color: TAU_COLORS.tau1,
					width: 2,
				},
				yaxis: "y",
				customdata: data.map((d) => [d.tau1.lb, d.tau1.ub]),
				hovertemplate:
					"<b style='font-size: 14px; color: #3b82f6;'>🔵 %{fullData.name}</b><br>" +
					"<span style='color: #6b7280;'>📅 Date:</span> <b>%{x|%B %d, %Y}</b><br>" +
					"<span style='color: #6b7280;'>📊 Estimate:</span> <b class='value'>%{y:.4f}</b><br>" +
					"<span style='color: #6b7280;'>📏 Confidence Interval:</span><br>" +
					"<span style='margin-left: 8px; font-family: monospace;'>[%{customdata[0]:.4f}, %{customdata[1]:.4f}]</span><br>" +
					"<extra></extra>",
			},
			// Tau Group 2 main line
			{
				x: dates,
				y: tau2Estimates,
				type: "scatter" as const,
				mode: "lines" as const,
				name: `τ ∈ (${tauGroupsInfo[1]?.mean || 0.5}±0.15)`,
				line: {
					color: TAU_COLORS.tau2,
					width: 2,
					dash: "dash" as const,
				},
				yaxis: "y",
				customdata: data.map((d) => [d.tau2.lb, d.tau2.ub]),
				hovertemplate:
					"<b style='font-size: 14px; color: #10b981;'>🟢 %{fullData.name}</b><br>" +
					"<span style='color: #6b7280;'>📅 Date:</span> <b>%{x|%B %d, %Y}</b><br>" +
					"<span style='color: #6b7280;'>📊 Estimate:</span> <b class='value'>%{y:.4f}</b><br>" +
					"<span style='color: #6b7280;'>📏 Confidence Interval:</span><br>" +
					"<span style='margin-left: 8px; font-family: monospace;'>[%{customdata[0]:.4f}, %{customdata[1]:.4f}]</span><br>" +
					"<extra></extra>",
			},
			// Tau Group 3 main line
			{
				x: dates,
				y: tau3Estimates,
				type: "scatter" as const,
				mode: "lines" as const,
				name: `τ ∈ (${tauGroupsInfo[2]?.mean || 1.0}±0.25)`,
				line: {
					color: TAU_COLORS.tau3,
					width: 2,
					dash: "dashdot" as const,
				},
				yaxis: "y",
				customdata: data.map((d) => [d.tau3.lb, d.tau3.ub]),
				hovertemplate:
					"<b style='font-size: 14px; color: #f59e0b;'>🟡 %{fullData.name}</b><br>" +
					"<span style='color: #6b7280;'>📅 Date:</span> <b>%{x|%B %d, %Y}</b><br>" +
					"<span style='color: #6b7280;'>📊 Estimate:</span> <b class='value'>%{y:.4f}</b><br>" +
					"<span style='color: #6b7280;'>📏 Confidence Interval:</span><br>" +
					"<span style='margin-left: 8px; font-family: monospace;'>[%{customdata[0]:.4f}, %{customdata[1]:.4f}]</span><br>" +
					"<extra></extra>",
			},
			// Stock Price line
			{
				x: dates,
				y: stockPrices,
				type: "scatter" as const,
				mode: "lines" as const,
				name: "Adjusted Price",
				line: {
					color: TAU_COLORS.stockPrice,
					width: 2,
				},
				yaxis: "y2",
				hovertemplate:
					"<b style='font-size: 14px; color: #dc2626;'>💰 %{fullData.name}</b><br>" +
					"<span style='color: #6b7280;'>📅 Date:</span> <b>%{x|%B %d, %Y}</b><br>" +
					"<span style='color: #6b7280;'>💵 Stock Price:</span> <b class='value' style='color: #dc2626;'>%{y:.2f}</b><br>" +
					"<extra></extra>",
			},
		];
	}, [data, tauGroupsInfo]);

	const layout = useMemo(
		() => ({
			title: {
				text: "",
			},
			paper_bgcolor: "transparent",
			plot_bgcolor: "transparent",
			font: {
				color: theme === "dark" ? "#ffffff" : "#000000",
			},
			xaxis: {
				title: {
					text: "Date",
				},
				type: "date" as const,
				gridcolor: theme === "dark" ? "#404040" : "#e0e0e0",
				linecolor: theme === "dark" ? "#666666" : "#cccccc",
				tickcolor: theme === "dark" ? "#666666" : "#cccccc",
				titlefont: {
					color: theme === "dark" ? "#ffffff" : "#000000",
				},
				tickfont: {
					color: theme === "dark" ? "#ffffff" : "#000000",
				},
				showspikes: true,
				spikecolor: theme === "dark" ? "#666" : "#ccc",
				spikethickness: 1,
				spikedash: "dot" as const,
				spikemode: "across" as const,
			},
			yaxis: {
				title: {
					text: "Bubble Estimate",
				},
				side: "left" as const,
				gridcolor: theme === "dark" ? "#404040" : "#e0e0e0",
				linecolor: theme === "dark" ? "#666666" : "#cccccc",
				tickcolor: theme === "dark" ? "#666666" : "#cccccc",
				titlefont: {
					color: theme === "dark" ? "#ffffff" : "#000000",
				},
				tickfont: {
					color: theme === "dark" ? "#ffffff" : "#000000",
				},
			},
			yaxis2: {
				title: {
					text: "Adjusted Price",
				},
				side: "right" as const,
				overlaying: "y" as const,
				gridcolor: theme === "dark" ? "#404040" : "#e0e0e0",
				linecolor: theme === "dark" ? "#666666" : "#cccccc",
				tickcolor: theme === "dark" ? "#666666" : "#cccccc",
				titlefont: {
					color: theme === "dark" ? "#ffffff" : "#000000",
				},
				tickfont: {
					color: theme === "dark" ? "#ffffff" : "#000000",
				},
			},
			hovermode: "x unified" as const,
			hoverdistance: 50,
			spikedistance: 50,
			hoverlabel: {
				bgcolor:
					theme === "dark"
						? "rgba(15, 15, 15, 0.98)"
						: "rgba(255, 255, 255, 0.95)",
				bordercolor: theme === "dark" ? "#444" : "#ccc",
				font: {
					color: theme === "dark" ? "#f0f0f0" : "#333",
					family:
						"-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
					size: 13,
				},
				align: "left" as const,
				namelength: -1,
			},

			showlegend: true,
			legend: {
				orientation: "h" as const,
				y: -0.2,
				bgcolor: "transparent",
				font: {
					color: theme === "dark" ? "#ffffff" : "#000000",
				},
			},
			margin: {
				l: 60,
				r: 60,
				t: 40,
				b: 100,
			},
		}),
		[theme],
	);

	if (loading) {
		return (
			<Card>
				<CardContent className="p-4">
					{/* Chart Title with KaTeX */}
					<div className="text-center mb-4">
						<h3 className="text-lg font-semibold mb-2">
							{title}
							{mathExpression && (
								<span className="ml-2">
									<InlineMath math={mathExpression} />
								</span>
							)}
						</h3>
					</div>
					<LoadingSpinner
						message={`Loading ${optionType} options bubble estimates...`}
						className="h-96"
						inline
					/>
				</CardContent>
			</Card>
		);
	}

	return (
		<Card>
			<CardContent className="p-4">
				{/* Chart Title with KaTeX */}
				<div className="text-center mb-4">
					<h3 className="text-lg font-semibold mb-2">
						{title}
						{mathExpression && (
							<span className="ml-2">
								<InlineMath math={mathExpression} />
							</span>
						)}
					</h3>
				</div>

				<div className="plotly-chart-container">
					<Plot
						data={plotData}
						layout={layout}
						style={{ width: "100%", height: "500px" }}
						config={{
							responsive: true,
							displayModeBar: true,
							modeBarButtonsToRemove: ["lasso2d", "select2d"],
							modeBarButtonsToAdd: [],
							displaylogo: false,
							toImageButtonOptions: {
								format: "png",
								filename: "bubble_chart",
								height: 500,
								width: 1000,
								scale: 1,
							},
						}}
					/>
				</div>
			</CardContent>
		</Card>
	);
});
