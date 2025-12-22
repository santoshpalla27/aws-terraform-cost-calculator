import { FileQuestion } from 'lucide-react';
import { cn } from '@/lib/utils/cn';

interface EmptyStateProps {
    title: string;
    description?: string;
    action?: {
        label: string;
        onClick: () => void;
    };
    className?: string;
}

export function EmptyState({
    title,
    description,
    action,
    className,
}: EmptyStateProps) {
    return (
        <div
            className={cn(
                'flex flex-col items-center justify-center gap-4 rounded-lg border-2 border-dashed border-gray-300 bg-gray-50 p-12',
                className
            )}
        >
            <FileQuestion className="h-16 w-16 text-gray-400" />
            <div className="text-center">
                <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
                {description && (
                    <p className="mt-2 text-sm text-gray-600">{description}</p>
                )}
            </div>
            {action && (
                <button
                    onClick={action.onClick}
                    className="mt-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                >
                    {action.label}
                </button>
            )}
        </div>
    );
}
