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
import { STOCK_LIST, type StockCode } from "../types/bubbleData";

interface DashboardControlsProps {
	selectedStock: StockCode;
	startDate: Date | null;
	endDate: Date | null;
	onStockChange: (stock: StockCode) => void;
	onDateRangeChange: (startDate: Date | null, endDate: Date | null) => void;
	onResetDateRange: () => void;
	availableDateRange: { min: Date; max: Date } | null;
	loading?: boolean;
}

export const DashboardControls = React.memo(function DashboardControls({
	selectedStock,
	startDate,
	endDate,
	onStockChange,
	onDateRangeChange,
	onResetDateRange,
	availableDateRange,
	loading,
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
				<div className="flex flex-wrap items-end gap-4">
					{/* Stock Selector */}
					<div className="flex flex-col space-y-2">
						<label htmlFor="stock-select" className="text-sm font-medium">
							Stock Symbol
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

					{/* Loading Indicator */}
					{loading && (
						<div className="flex items-center text-muted-foreground">
							<div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2" />
							Loading...
						</div>
					)}
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
