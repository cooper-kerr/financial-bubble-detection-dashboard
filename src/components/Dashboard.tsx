import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { AlertTriangle } from "lucide-react";
import { useDashboardData } from "../hooks/useDashboardData";
import { DashboardControls } from "./DashboardControls";
import { PlotlyBubbleChart } from "./PlotlyBubbleChart";
import { PriceDifferenceChart } from "./PriceDifferenceChart";

export function Dashboard() {
	const {
		selectedStock,
		startDate,
		endDate,
		bubbleData,
		loading,
		error,
		setSelectedStock,
		setDateRange,
		resetDateRange,
		getChartData,
		getPriceDifferenceData,
		getAvailableDateRange,
	} = useDashboardData();

	if (error) {
		return (
			<div className="min-h-screen bg-background flex items-center justify-center p-4">
				<Card className="max-w-md w-full">
					<CardContent className="p-8 text-center">
						<AlertTriangle className="h-12 w-12 text-destructive mx-auto mb-4" />
						<h2 className="text-xl font-semibold mb-2">Error Loading Data</h2>
						<p className="text-muted-foreground mb-4">{error}</p>
						<Button onClick={() => window.location.reload()}>Retry</Button>
					</CardContent>
				</Card>
			</div>
		);
	}

	const availableDateRange = getAvailableDateRange();
	const tauGroupsInfo = bubbleData?.metadata.tau_groups_info || [];

	return (
		<div className="min-h-screen bg-background">
			<div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
				<DashboardControls
					selectedStock={selectedStock}
					startDate={startDate}
					endDate={endDate}
					onStockChange={setSelectedStock}
					onDateRangeChange={setDateRange}
					onResetDateRange={resetDateRange}
					availableDateRange={availableDateRange}
					loading={loading}
				/>

				{/* Charts Grid */}
				<div className="space-y-6">
					{/* Put Options Chart */}
					<PlotlyBubbleChart
						data={getChartData("put")}
						optionType="put"
						title="Put Options Bubble Estimates"
						mathExpression="\hat{\Pi}_p(\tau)"
						tauGroupsInfo={tauGroupsInfo}
						loading={loading}
					/>

					{/* Call Options Chart */}
					<PlotlyBubbleChart
						data={getChartData("call")}
						optionType="call"
						title="Call Options Bubble Estimates"
						mathExpression="\hat{\Pi}_c(\tau)"
						tauGroupsInfo={tauGroupsInfo}
						loading={loading}
					/>

					{/* Combined Options Chart */}
					<PlotlyBubbleChart
						data={getChartData("combined")}
						optionType="combined"
						title="Combined Options Bubble Estimates"
						mathExpression="\hat{\Pi}_{cp}(\tau)"
						tauGroupsInfo={tauGroupsInfo}
						loading={loading}
					/>

					{/* Price Difference Chart */}
					<PriceDifferenceChart
						data={getPriceDifferenceData()}
						title={`${selectedStock} - Price Comparison`}
						loading={loading}
					/>
				</div>

				{/* Footer */}
				<div className="mt-12 text-center text-muted-foreground text-sm">
					<p>Financial Bubble Detection Dashboard</p>
					<p>
						Data covers {availableDateRange?.min.getFullYear()} -{" "}
						{availableDateRange?.max.getFullYear()}
					</p>
				</div>
			</div>
		</div>
	);
}
