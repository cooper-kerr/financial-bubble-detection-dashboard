import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { Loader2 } from "lucide-react";

interface LoadingSpinnerProps {
	message?: string;
	className?: string;
	/** If true, renders without Card wrapper (for use inside existing Cards) */
	inline?: boolean;
}

export function LoadingSpinner({
	message = "Loading chart...",
	className = "h-96",
	inline = false,
}: LoadingSpinnerProps) {
	const content = (
		<div
			className={cn(
				"flex flex-col items-center justify-center",
				inline ? className : "h-full",
			)}
		>
			<Loader2 className="h-8 w-8 animate-spin text-primary mb-4" />
			<p className="text-muted-foreground text-sm">{message}</p>
		</div>
	);

	if (inline) {
		return content;
	}

	return (
		<Card className={className}>
			<CardContent className="h-full flex flex-col items-center justify-center">
				<Loader2 className="h-8 w-8 animate-spin text-primary mb-4" />
				<p className="text-muted-foreground text-sm">{message}</p>
			</CardContent>
		</Card>
	);
}
