import { Card, CardContent } from "@/components/ui/card";
import { Loader2 } from "lucide-react";

interface LoadingSpinnerProps {
	message?: string;
	className?: string;
}

export function LoadingSpinner({ 
	message = "Loading chart...", 
	className = "h-96" 
}: LoadingSpinnerProps) {
	return (
		<Card className={className}>
			<CardContent className="h-full flex flex-col items-center justify-center">
				<Loader2 className="h-8 w-8 animate-spin text-primary mb-4" />
				<p className="text-muted-foreground text-sm">{message}</p>
			</CardContent>
		</Card>
	);
}
