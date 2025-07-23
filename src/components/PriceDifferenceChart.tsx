import { useTheme } from "@/components/theme-provider";
import { Card, CardContent } from "@/components/ui/card";
import React, { useMemo } from "react";
import Plot from "react-plotly.js";
import type { PriceDifferenceDataPoint } from "../types/bubbleData";
import { LoadingSpinner } from "./LoadingSpinner";

interface PriceDifferenceChartProps {
	data: PriceDifferenceDataPoint[];
	title: string;
	loading?: boolean;
}

export const PriceDifferenceChart = React.memo(function PriceDifferenceChart({
	data,
	title,
	loading,
}: PriceDifferenceChartProps) {
	const { theme } = useTheme();

	const plotData = useMemo(() => {
		if (!data || data.length === 0) {
			return [];
		}

		const dates = data.map((d) => d.date);
		const adjustedPrices = data.map((d) => d.adjustedPrice);
		const regularPrices = data.map((d) => d.regularPrice);

		return [
			// Raw prices (regular prices) - blue line
			{
				x: dates,
				y: regularPrices,
				type: "scatter" as const,
				mode: "lines" as const,
				name: "Raw prices",
				line: {
					color: "#1f77b4", // Blue like in your image
					width: 2,
				},
				yaxis: "y",
				hovertemplate:
					"<b style='font-size: 14px; color: #1f77b4;'>📊 %{fullData.name}</b><br>" +
					"<span style='color: #6b7280;'>📅 Date:</span> <b>%{x|%B %d, %Y}</b><br>" +
					"<span style='color: #6b7280;'>💰 Price:</span> <b class='value' style='color: #1f77b4;'>%{y:.2f}</b><br>" +
					"<extra></extra>",
			},
			// Split-adjusted prices - orange line
			{
				x: dates,
				y: adjustedPrices,
				type: "scatter" as const,
				mode: "lines" as const,
				name: "Split-adjusted prices",
				line: {
					color: "#ff7f0e", // Orange like in your image
					width: 2,
				},
				yaxis: "y",
				hovertemplate:
					"<b style='font-size: 14px; color: #ff7f0e;'>📈 %{fullData.name}</b><br>" +
					"<span style='color: #6b7280;'>📅 Date:</span> <b>%{x|%B %d, %Y}</b><br>" +
					"<span style='color: #6b7280;'>💰 Price:</span> <b class='value' style='color: #ff7f0e;'>%{y:.2f}</b><br>" +
					"<extra></extra>",
			},
		];
	}, [data]);

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
				spikedash: "dot",
				spikemode: "across" as const,
			},
			yaxis: {
				title: {
					text: "Price",
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
				x: 0.5,
				xanchor: "center" as const,
				font: {
					color: theme === "dark" ? "#ffffff" : "#000000",
				},
			},
			margin: {
				l: 60,
				r: 80,
				t: 40,
				b: 80,
			},
		}),
		[theme],
	);

	if (loading) {
		return (
			<Card>
				<CardContent className="p-4">
					<div className="text-center mb-4">
						<h3 className="text-lg font-semibold mb-2">{title}</h3>
						<p className="text-sm text-muted-foreground">
							Comparison between raw prices and split-adjusted prices
						</p>
					</div>
					<LoadingSpinner
						message="Loading price difference data..."
						className="h-96"
						inline
					/>
				</CardContent>
			</Card>
		);
	}

	if (!data || data.length === 0) {
		return (
			<Card>
				<CardContent className="p-4">
					<div className="text-center mb-4">
						<h3 className="text-lg font-semibold mb-2">{title}</h3>
					</div>
					<div className="flex items-center justify-center h-96">
						<div className="text-muted-foreground">
							No price difference data available
						</div>
					</div>
				</CardContent>
			</Card>
		);
	}

	return (
		<Card>
			<CardContent className="p-4">
				{/* Chart Title */}
				<div className="text-center mb-4">
					<h3 className="text-lg font-semibold mb-2">{title}</h3>
					<p className="text-sm text-muted-foreground">
						Comparison between raw prices and split-adjusted prices
					</p>
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
								filename: "price_difference_chart",
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
