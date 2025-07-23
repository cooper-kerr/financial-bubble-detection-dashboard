import { useTheme } from "@/components/theme-provider";
import { Card, CardContent } from "@/components/ui/card";
import ReactECharts from "echarts-for-react";
import { Hand, Info, Move, Square, ZoomIn, ZoomOut } from "lucide-react";
import React, { useMemo, useRef } from "react";
import {
	type ChartDataPoint,
	type OptionType,
	TAU_COLORS,
} from "../types/bubbleData";
import { formatTooltipData } from "../utils/dataLoader";
import { LoadingSpinner } from "./LoadingSpinner";
import "../styles/tooltip.css";

interface BubbleChartProps {
	data: ChartDataPoint[];
	optionType: OptionType;
	title: string;
	tauGroupsInfo: { mean: number }[];
	loading?: boolean;
}

export const BubbleChart = React.memo(function BubbleChart({
	data,
	title,
	tauGroupsInfo,
	loading,
}: BubbleChartProps) {
	const { theme } = useTheme();
	const chartRef = useRef<ReactECharts>(null);

	// Memoize ECharts option configuration
	const chartOption = useMemo(() => {
		if (!data || data.length === 0) {
			return null;
		}
		// Prepare data for ECharts
		const dates = data.map((d) => new Date(d.date).toLocaleDateString());
		const stockPrices = data.map((d) => d.stockPrice);

		// Prepare bubble estimate data for each tau group
		const tau1Estimates = data.map((d) => d.tau1.mu);
		const tau2Estimates = data.map((d) => d.tau2.mu);
		const tau3Estimates = data.map((d) => d.tau3.mu);

		// Prepare confidence band data for area charts
		const tau1Upper = data.map((d) => d.tau1.ub);
		const tau1Lower = data.map((d) => d.tau1.lb);
		const tau2Upper = data.map((d) => d.tau2.ub);
		const tau2Lower = data.map((d) => d.tau2.lb);
		const tau3Upper = data.map((d) => d.tau3.ub);
		const tau3Lower = data.map((d) => d.tau3.lb);

		return {
			backgroundColor: "transparent",
			title: {
				text: title,
				left: "center",
				textStyle: {
					fontSize: 16,
				},
			},
			tooltip: {
				trigger: "axis",
				axisPointer: {
					type: "cross",
				},
				className: "bubble-chart-tooltip",
				formatter: (params: unknown) => {
					const paramsArray = params as Array<{ dataIndex: number }>;
					if (!paramsArray || paramsArray.length === 0) return "";

					const dataIndex = paramsArray[0].dataIndex;
					const point = data[dataIndex];
					const formatted = formatTooltipData(point, tauGroupsInfo);

					return `
						<div class="bubble-chart-tooltip-content">
							<div class="tooltip-header">
								<div class="tooltip-date">${formatted.date}</div>
								<div class="tooltip-stock-price">💰 ${formatted.stockPrice}</div>
							</div>

							<div class="tooltip-tau-groups">
								<div class="tau-group tau-1">
									<div class="tau-indicator">🔵</div>
									<div class="tau-info">
										<div class="tau-name">${formatted.tau1.name}</div>
										<div class="tau-values">
											<span class="tau-estimate">${formatted.tau1.estimate}</span>
											<span class="tau-range">[${formatted.tau1.lowerBound}, ${formatted.tau1.upperBound}]</span>
										</div>
									</div>
								</div>

								<div class="tau-group tau-2">
									<div class="tau-indicator">🟢</div>
									<div class="tau-info">
										<div class="tau-name">${formatted.tau2.name}</div>
										<div class="tau-values">
											<span class="tau-estimate">${formatted.tau2.estimate}</span>
											<span class="tau-range">[${formatted.tau2.lowerBound}, ${formatted.tau2.upperBound}]</span>
										</div>
									</div>
								</div>

								<div class="tau-group tau-3">
									<div class="tau-indicator">🟡</div>
									<div class="tau-info">
										<div class="tau-name">${formatted.tau3.name}</div>
										<div class="tau-values">
											<span class="tau-estimate">${formatted.tau3.estimate}</span>
											<span class="tau-range">[${formatted.tau3.lowerBound}, ${formatted.tau3.upperBound}]</span>
										</div>
									</div>
								</div>
							</div>
						</div>
					`;
				},
			},
			legend: {
				data: [
					`τ ∈ (${tauGroupsInfo[0]?.mean || 0.25}±0.1)`,
					`τ ∈ (${tauGroupsInfo[1]?.mean || 0.5}±0.15)`,
					`τ ∈ (${tauGroupsInfo[2]?.mean || 1.0}±0.25)`,
					"Stock Price",
				],
				bottom: "9%",
			},
			toolbox: {
				show: true,
				orient: "vertical",
				right: "2%",
				top: "center",
				feature: {
					dataZoom: {
						yAxisIndex: "none",
						title: {
							zoom: "Area Zoom",
						},
						show: true,
						filterMode: "none",
					},
					restore: {
						show: true,
						title: "Reset Timeline View",
					},
					saveAsImage: {
						title: "Save as Image",
						pixelRatio: 2,
					},
				},
				iconStyle: {
					borderColor: theme === "dark" ? "#ffffff" : "#333333",
				},
				emphasis: {
					iconStyle: {
						borderColor: "#3b82f6",
					},
				},
			},
			grid: {
				left: "10%",
				right: "15%",
				bottom: "20%",
				top: "15%",
				containLabel: true,
			},
			dataZoom: [
				{
					type: "slider",
					show: true,
					xAxisIndex: [0],
					start: 0,
					end: 100,
					startValue: 0,
					endValue: data.length - 1,
					minSpan: 1,
					maxSpan: 100,
					bottom: "2%",
					height: "5%",
					handleSize: "100%",
					handleStyle: {
						color: "#fff",
						shadowBlur: 3,
						shadowColor: "rgba(0, 0, 0, 0.6)",
						shadowOffsetX: 2,
						shadowOffsetY: 2,
					},
					textStyle: {
						color: theme === "dark" ? "#ffffff" : "#333333",
					},
					borderColor: theme === "dark" ? "#404040" : "#ccc",
					fillerColor: "rgba(135, 175, 274, 0.2)",
					backgroundColor: theme === "dark" ? "#2a2a2a" : "#fafafa",
				},
				{
					type: "inside",
					xAxisIndex: [0],
					start: 0,
					end: 100,
					startValue: 0,
					endValue: data.length - 1,
					minSpan: 1,
					maxSpan: 100,
				},
			],
			xAxis: {
				type: "category",
				data: dates,
				name: "Date",
				nameLocation: "middle",
				nameGap: 30,
			},
			yAxis: [
				{
					type: "value",
					name: "Bubble Estimate",
					position: "left",
				},
				{
					type: "value",
					name: "Stock Price ($)",
					position: "right",
				},
			],
			series: [
				// Tau Group 1 confidence band - upper bound
				{
					name: "CI τ1",
					type: "line",
					data: tau1Upper,
					lineStyle: {
						opacity: 0,
					},
					areaStyle: {
						color: "rgba(31, 119, 180, 0.3)",
					},
					stack: "tau1",
					symbol: "none",
					yAxisIndex: 0,
					z: 1,
				},
				// Tau Group 1 confidence band - lower bound
				{
					name: "CI τ1 lower",
					type: "line",
					data: tau1Lower,
					lineStyle: {
						opacity: 0,
					},
					areaStyle: {
						color: "rgba(255, 255, 255, 0)",
					},
					stack: "tau1",
					symbol: "none",
					yAxisIndex: 0,
					showInLegend: false,
					z: 1,
				},
				// Tau Group 1 main line
				{
					name: `τ ∈ (${tauGroupsInfo[0]?.mean || 0.25}±0.1)`,
					type: "line",
					data: tau1Estimates,
					smooth: true,
					lineStyle: {
						color: TAU_COLORS.tau1,
						width: 2,
					},
					symbol: "circle",
					symbolSize: 8,
					showSymbol: false,
					itemStyle: {
						color: TAU_COLORS.tau1,
						borderColor: "#ffffff",
						borderWidth: 2,
						shadowColor: "rgba(0, 0, 0, 0.3)",
						shadowBlur: 4,
						shadowOffsetX: 1,
						shadowOffsetY: 1,
					},
					yAxisIndex: 0,
					z: 3,
				},

				// Tau Group 2 confidence band - upper bound
				{
					name: "CI τ2",
					type: "line",
					data: tau2Upper,
					lineStyle: {
						opacity: 0,
					},
					areaStyle: {
						color: "rgba(44, 160, 44, 0.3)",
					},
					stack: "tau2",
					symbol: "none",
					yAxisIndex: 0,
					z: 1,
				},
				// Tau Group 2 confidence band - lower bound
				{
					name: "CI τ2 lower",
					type: "line",
					data: tau2Lower,
					lineStyle: {
						opacity: 0,
					},
					areaStyle: {
						color: "rgba(255, 255, 255, 0)",
					},
					stack: "tau2",
					symbol: "none",
					yAxisIndex: 0,
					showInLegend: false,
					z: 1,
				},
				// Tau Group 2 main line
				{
					name: `τ ∈ (${tauGroupsInfo[1]?.mean || 0.5}±0.15)`,
					type: "line",
					data: tau2Estimates,
					smooth: true,
					lineStyle: {
						color: TAU_COLORS.tau2,
						width: 2,
						type: "dashed",
					},
					symbol: "circle",
					symbolSize: 8,
					showSymbol: false,
					itemStyle: {
						color: TAU_COLORS.tau2,
						borderColor: "#ffffff",
						borderWidth: 2,
						shadowColor: "rgba(0, 0, 0, 0.3)",
						shadowBlur: 4,
						shadowOffsetX: 1,
						shadowOffsetY: 1,
					},
					yAxisIndex: 0,
					z: 3,
				},

				// Tau Group 3 confidence band - upper bound
				{
					name: "CI τ3",
					type: "line",
					data: tau3Upper,
					lineStyle: {
						opacity: 0,
					},
					areaStyle: {
						color: "rgba(255, 127, 14, 0.3)",
					},
					stack: "tau3",
					symbol: "none",
					yAxisIndex: 0,
					z: 1,
				},
				// Tau Group 3 confidence band - lower bound
				{
					name: "CI τ3 lower",
					type: "line",
					data: tau3Lower,
					lineStyle: {
						opacity: 0,
					},
					areaStyle: {
						color: "rgba(255, 255, 255, 0)",
					},
					stack: "tau3",
					symbol: "none",
					yAxisIndex: 0,
					showInLegend: false,
					z: 1,
				},
				// Tau Group 3 main line
				{
					name: `τ ∈ (${tauGroupsInfo[2]?.mean || 1.0}±0.25)`,
					type: "line",
					data: tau3Estimates,
					smooth: true,
					lineStyle: {
						color: TAU_COLORS.tau3,
						width: 2,
						type: "dashdot",
					},
					symbol: "circle",
					symbolSize: 8,
					showSymbol: false,
					itemStyle: {
						color: TAU_COLORS.tau3,
						borderColor: "#ffffff",
						borderWidth: 2,
						shadowColor: "rgba(0, 0, 0, 0.3)",
						shadowBlur: 4,
						shadowOffsetX: 1,
						shadowOffsetY: 1,
					},
					yAxisIndex: 0,
					z: 3,
				},
				// Stock Price line
				{
					name: "Stock Price",
					type: "line",
					data: stockPrices,
					smooth: true,
					lineStyle: {
						color: TAU_COLORS.stockPrice,
						width: 2,
					},
					symbol: "circle",
					symbolSize: 8,
					showSymbol: false,
					itemStyle: {
						color: TAU_COLORS.stockPrice,
						borderColor: "#ffffff",
						borderWidth: 2,
						shadowColor: "rgba(0, 0, 0, 0.3)",
						shadowBlur: 4,
						shadowOffsetX: 1,
						shadowOffsetY: 1,
					},
					yAxisIndex: 1,
				},
			],
		};
	}, [data, tauGroupsInfo, title, theme]);

	// Handle restore button click to reset zoom
	const handleRestore = () => {
		if (chartRef.current) {
			const echartsInstance = chartRef.current.getEchartsInstance();
			echartsInstance.dispatchAction({
				type: "dataZoom",
				start: 0,
				end: 100,
			});
		}
	};

	// Handle loading state
	if (loading) {
		return <LoadingSpinner message="Loading chart data..." />;
	}

	// Handle no data state
	if (!data || data.length === 0 || !chartOption) {
		return (
			<Card>
				<CardContent className="h-96 flex items-center justify-center">
					<div className="text-muted-foreground">No data available</div>
				</CardContent>
			</Card>
		);
	}

	return (
		<Card>
			<CardContent className="p-4">
				{/* Instructions Panel */}
				<div className="mb-4 p-4 bg-muted/50 rounded-lg border">
					<h4 className="font-semibold mb-3 flex items-center gap-2">
						<Info className="h-4 w-4" />
						Chart Navigation Guide
					</h4>
					<div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
						<div className="space-y-2">
							<div className="flex items-center gap-2">
								<Move className="h-4 w-4 text-blue-500" />
								<span>
									<strong>Mouse Wheel:</strong> Scroll to zoom in/out
								</span>
							</div>
							<div className="flex items-center gap-2">
								<Hand className="h-4 w-4 text-green-500" />
								<span>
									<strong>Click & Drag:</strong> Pan around when zoomed
								</span>
							</div>
							<div className="flex items-center gap-2">
								<ZoomIn className="h-4 w-4 text-purple-500" />
								<span>
									<strong>Slider:</strong> Drag handles to select time range
								</span>
							</div>
						</div>
						<div className="space-y-2">
							<div className="flex items-center gap-2">
								<Square className="h-4 w-4 text-cyan-500" />
								<span>
									<strong>Area Zoom:</strong> Use the zoom tool in the toolbox
									(right side) to select and zoom into regions
								</span>
							</div>
							<div className="flex items-center gap-2">
								<ZoomOut className="h-4 w-4 text-orange-500" />
								<span>
									<strong>Undo Zoom:</strong> Use the back button (↩️) to undo
									the last area selection
								</span>
							</div>
							<div className="flex items-center gap-2">
								<ZoomOut className="h-4 w-4 text-red-500" />
								<span>
									<strong>Reset Timeline:</strong> Use "Reset Timeline View"
									(🔄) to return to full timeline
								</span>
							</div>
							<div className="text-muted-foreground">
								<strong>Tip:</strong> Hover over data points to see detailed
								bubble estimates and confidence intervals.
							</div>
						</div>
					</div>
				</div>

				<ReactECharts
					ref={chartRef}
					option={chartOption}
					style={{ height: "450px", width: "100%" }}
					theme={theme === "dark" ? "dark" : undefined}
					opts={{ renderer: "svg" }}
					onEvents={{
						restore: handleRestore,
					}}
				/>
			</CardContent>
		</Card>
	);
});
