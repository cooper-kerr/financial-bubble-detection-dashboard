import { DatePicker } from "@/components/date-picker";
import { ThemeSwitcher } from "@/components/theme-switcher";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
	Select,
	SelectContent,
	SelectItem,
	SelectTrigger,
	SelectValue,
} from "@/components/ui/select";
import { RotateCcw } from "lucide-react";
import React from "react";
import {
	CONFIDENCE_LEVELS,
	STOCK_LIST,
	type ConfidenceLevel,
	type DataSource,
	type StockCode,
} from "../types/bubbleData";
import type { ChartKey } from "./Dashboard";

const CHART_TOGGLE_CONFIG: {
	key: ChartKey;
	label: string;
	activeClass: string;
}[] = [
	{
		key: "put",
		label: "Put Options",
		activeClass:
			"bg-blue-500 text-white border-blue-500 hover:bg-blue-600 hover:border-blue-600",
	},
	{
		key: "call",
		label: "Call Options",
		activeClass:
			"bg-green-500 text-white border-green-500 hover:bg-green-600 hover:border-green-600",
	},
	{
		key: "combined",
		label: "Combined",
		activeClass:
			"bg-amber-500 text-white border-amber-500 hover:bg-amber-600 hover:border-amber-600",
	},
	{
		key: "price",
		label: "Price Comparison",
		activeClass:
			"bg-red-500 text-white border-red-500 hover:bg-red-600 hover:border-red-600",
	},
];

interface DashboardControlsProps {
	selectedStock: StockCode;
	dataSource: DataSource;
	startDate: Date | null;
	endDate: Date | null;
	onStockChange: (stock: StockCode) => void;
	onDataSourceChange: (dataSource: DataSource) => void;
	onDateRangeChange: (startDate: Date | null, endDate: Date | null) => void;
	onResetDateRange: () => void;
	availableDateRange: { min: Date; max: Date } | null;
	loading?: boolean;
	visibleCharts: Set<ChartKey>;
	onToggleChart: (key: ChartKey) => void;
	confidenceLevel: ConfidenceLevel;
	onConfidenceLevelChange: (level: ConfidenceLevel) => void;
	/** True when the loaded JSON contains se values (post-pipeline-update).
	 *  When false, the CI selector renders but is disabled with an explanatory badge. */
	hasSeData: boolean;
}

export const DashboardControls = React.memo(function DashboardControls({
	selectedStock,
	dataSource,
	startDate,
	endDate,
	onStockChange,
	onDataSourceChange,
	onDateRangeChange,
	onResetDateRange,
	availableDateRange,
	loading,
	visibleCharts,
	onToggleChart,
	confidenceLevel,
	onConfidenceLevelChange,
	hasSeData,
}: DashboardControlsProps) {
	return (
		<Card className="mb-6">
			<CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
				<CardTitle className="text-2xl font-bold">
					📊 Financial Bubble Detection Dashboard
				</CardTitle>
				<ThemeSwitcher />
			</CardHeader>
			<CardContent>
				{/* ── Row 1: Stock / Source / Dates / Reset ── */}
				<div className="flex flex-wrap items-end gap-4">
					{/* Stock Selector */}
					<div className="flex flex-col space-y-2">
						<label htmlFor="stock-select" className="text-sm font-medium">
							Stock
						</label>
						<Select
							value={selectedStock}
							onValueChange={onStockChange}
							disabled={loading}
						>
							<SelectTrigger id="stock-select" className="w-[180px]">
								<SelectValue placeholder="Select stock" />
							</SelectTrigger>
							<SelectContent>
								{STOCK_LIST.map((stock) => (
									<SelectItem key={stock} value={stock}>
										{stock}
									</SelectItem>
								))}
							</SelectContent>
						</Select>
					</div>

					{/* Data Source Selector */}
					<div className="flex flex-col space-y-2">
						<label htmlFor="data-source-select" className="text-sm font-medium">
							Data Source
						</label>
						<Select
							value={dataSource}
							onValueChange={onDataSourceChange}
							disabled={loading}
						>
							<SelectTrigger id="data-source-select" className="w-[180px]">
								<SelectValue placeholder="Select data source" />
							</SelectTrigger>
							<SelectContent>
								<SelectItem value="WRDS">WRDS</SelectItem>
								<SelectItem value="Yahoo Finance">Yahoo Finance</SelectItem>
							</SelectContent>
						</Select>
					</div>

					{/* Date Range Picker */}
					<div className="flex flex-col space-y-2">
						<span className="text-sm font-medium">Start Date</span>
						<DatePicker
							date={startDate || undefined}
							onSelect={(date) => onDateRangeChange(date || null, endDate)}
							minDate={availableDateRange?.min}
							maxDate={availableDateRange?.max}
							disabled={loading}
							placeholder="Select start date"
						/>
					</div>

					<div className="flex flex-col space-y-2">
						<span className="text-sm font-medium">End Date</span>
						<DatePicker
							date={endDate || undefined}
							onSelect={(date) => onDateRangeChange(startDate, date || null)}
							minDate={startDate || availableDateRange?.min}
							maxDate={availableDateRange?.max}
							disabled={loading}
							placeholder="Select end date"
						/>
					</div>

					{/* Reset Button */}
					<div className="flex flex-col justify-end">
						<Button
							type="button"
							variant="outline"
							onClick={onResetDateRange}
							disabled={loading}
							className="w-full"
						>
							<RotateCcw className="mr-2 h-4 w-4" />
							Reset Range
						</Button>
					</div>
				</div>

				{/* ── Row 2: Visible Charts toggles ── */}
				<div className="mt-5 flex flex-wrap items-center gap-3">
					<span className="text-sm font-medium text-muted-foreground shrink-0">
						Visible charts:
					</span>
					{CHART_TOGGLE_CONFIG.map(({ key, label, activeClass }) => {
						const isActive = visibleCharts.has(key);
						const isLastActive = visibleCharts.size === 1 && isActive;
						return (
							<button
								key={key}
								type="button"
								onClick={() => onToggleChart(key)}
								disabled={isLastActive}
								title={
									isLastActive
										? "At least one chart must remain visible"
										: `${isActive ? "Hide" : "Show"} ${label}`
								}
								className={[
									"inline-flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-sm font-medium transition-all duration-150",
									"focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
									"disabled:pointer-events-none disabled:opacity-50",
									isActive
										? activeClass
										: "border-input bg-background text-muted-foreground hover:bg-accent hover:text-accent-foreground",
								].join(" ")}
							>
								<span
									className={[
										"h-2 w-2 rounded-full",
										isActive ? "bg-white/80" : "bg-muted-foreground/40",
									].join(" ")}
								/>
								{label}
							</button>
						);
					})}
				</div>

				{/* ── Row 3: Confidence level selector ── */}
				<div className="mt-4 flex flex-wrap items-center gap-3">
					<span
						className="text-sm font-medium text-muted-foreground shrink-0"
						title={
							!hasSeData
								? "Confidence level selection requires re-running the Python pipeline with se emission enabled."
								: undefined
						}
					>
						Confidence level:
						{!hasSeData && (
							<span className="ml-1.5 rounded bg-muted px-1.5 py-0.5 text-xs text-muted-foreground">
								Requires SE in JSON
							</span>
						)}
					</span>
					{CONFIDENCE_LEVELS.map((level) => {
						const isActive = confidenceLevel === level;
						return (
							<button
								key={level}
								type="button"
								onClick={() => onConfidenceLevelChange(level)}
								disabled={!hasSeData || loading}
								title={
									!hasSeData
										? "Re-run pipeline to add standard errors to JSON"
										: `Show ${(level * 100).toFixed(0)}% confidence intervals`
								}
								className={[
									"inline-flex items-center rounded-md border px-3 py-1.5 text-sm font-medium",
									"transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
									"disabled:pointer-events-none disabled:opacity-40",
									isActive
										? "bg-primary text-primary-foreground border-primary shadow-sm"
										: "border-input bg-background text-muted-foreground hover:bg-accent hover:text-accent-foreground",
								].join(" ")}
							>
								{(level * 100).toFixed(0)}%
							</button>
						);
					})}
				</div>

				{/* Date Range Display */}
				{startDate && endDate && (
					<div className="mt-4 text-sm text-muted-foreground">
						Showing data from {startDate.toLocaleDateString()} to{" "}
						{endDate.toLocaleDateString()}
					</div>
				)}
			</CardContent>
		</Card>
	);
});
