import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils/cn';

interface LoadingStateProps {
    message?: string;
    className?: string;
    size?: 'sm' | 'md' | 'lg';
}

export function LoadingState({
    message = 'Loading...',
    className,
    size = 'md',
}: LoadingStateProps) {
    const sizeClasses = {
        sm: 'h-4 w-4',
        md: 'h-8 w-8',
        lg: 'h-12 w-12',
    };

    return (
        <div
            className={cn(
                'flex flex-col items-center justify-center gap-4 py-12',
                className
            )}
        >
            <Loader2 className={cn('animate-spin text-blue-600', sizeClasses[size])} />
            {message && <p className="text-sm text-gray-600">{message}</p>}
        </div>
    );
}

/**
 * Skeleton loader for content placeholders
 */
interface SkeletonProps {
    className?: string;
}

export function Skeleton({ className }: SkeletonProps) {
    return (
        <div
            className={cn('animate-pulse rounded-md bg-gray-200', className)}
            aria-hidden="true"
        />
    );
}
