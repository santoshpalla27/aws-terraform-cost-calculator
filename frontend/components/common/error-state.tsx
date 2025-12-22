import { AlertCircle, RefreshCw } from 'lucide-react';
import { cn } from '@/lib/utils/cn';

interface ErrorStateProps {
    title?: string;
    message: string;
    onRetry?: () => void;
    className?: string;
}

export function ErrorState({
    title = 'Error',
    message,
    onRetry,
    className,
}: ErrorStateProps) {
    return (
        <div
            className={cn(
                'flex flex-col items-center justify-center gap-4 rounded-lg border border-red-200 bg-red-50 p-8',
                className
            )}
            role="alert"
        >
            <AlertCircle className="h-12 w-12 text-red-600" />
            <div className="text-center">
                <h3 className="text-lg font-semibold text-red-900">{title}</h3>
                <p className="mt-2 text-sm text-red-700">{message}</p>
            </div>
            {onRetry && (
                <button
                    onClick={onRetry}
                    className="mt-2 inline-flex items-center gap-2 rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
                >
                    <RefreshCw className="h-4 w-4" />
                    Retry
                </button>
            )}
        </div>
    );
}
