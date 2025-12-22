'use client';

import { Clock, CheckCircle, XCircle, Loader2, RefreshCw } from 'lucide-react';
import { formatRelativeTime } from '@/utils/formatters';
import { cn } from '@/utils/formatters';
import type { Job } from '@/types/job';

const STATUS_CONFIG = {
    PENDING: {
        icon: Clock,
        color: 'text-yellow-600',
        bg: 'bg-yellow-100',
        label: 'Pending',
        description: 'Waiting to start...',
    },
    RUNNING: {
        icon: Loader2,
        color: 'text-blue-600',
        bg: 'bg-blue-100',
        label: 'Running',
        description: 'Processing your Terraform files...',
    },
    COMPLETED: {
        icon: CheckCircle,
        color: 'text-green-600',
        bg: 'bg-green-100',
        label: 'Completed',
        description: 'Cost estimation complete!',
    },
    FAILED: {
        icon: XCircle,
        color: 'text-red-600',
        bg: 'bg-red-100',
        label: 'Failed',
        description: 'An error occurred during processing',
    },
};

interface JobStatusProps {
    job: Job;
    onRetry?: () => void;
}

export function JobStatus({ job, onRetry }: JobStatusProps) {
    const config = STATUS_CONFIG[job.status];
    const Icon = config.icon;

    return (
        <div className="space-y-6">
            {/* Status Card */}
            <div className="rounded-lg border-2 border-gray-200 p-6">
                <div className="flex items-start gap-4">
                    <div className={cn('rounded-full p-3', config.bg)}>
                        <Icon
                            className={cn(
                                'h-8 w-8',
                                config.color,
                                job.status === 'RUNNING' && 'animate-spin'
                            )}
                        />
                    </div>
                    <div className="flex-1">
                        <h3 className="text-xl font-semibold text-gray-900">{job.name}</h3>
                        <p className="mt-1 text-sm text-gray-600">{config.description}</p>
                        <p className="mt-2 text-xs text-gray-500">
                            Created {formatRelativeTime(job.createdAt)}
                        </p>
                    </div>
                </div>

                {/* Progress Bar */}
                {job.progress !== undefined && job.status === 'RUNNING' && (
                    <div className="mt-4">
                        <div className="flex justify-between text-sm text-gray-600 mb-2">
                            <span>Progress</span>
                            <span>{job.progress}%</span>
                        </div>
                        <div className="h-2 w-full overflow-hidden rounded-full bg-gray-200">
                            <div
                                className="h-full bg-blue-600 transition-all duration-300"
                                style={{ width: `${job.progress}%` }}
                            />
                        </div>
                    </div>
                )}

                {/* Error Message */}
                {job.errorMessage && (
                    <div className="mt-4 rounded-md bg-red-50 border border-red-200 p-4">
                        <p className="text-sm text-red-800">{job.errorMessage}</p>
                    </div>
                )}

                {/* Retry Button */}
                {job.status === 'FAILED' && onRetry && (
                    <button
                        onClick={onRetry}
                        className="mt-4 inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                    >
                        <RefreshCw className="h-4 w-4" />
                        Retry Job
                    </button>
                )}
            </div>

            {/* Timeline */}
            <div className="space-y-3">
                <h4 className="text-sm font-medium text-gray-700">Timeline</h4>
                <div className="space-y-2">
                    <div className="flex items-center gap-3 text-sm">
                        <CheckCircle className="h-4 w-4 text-green-600" />
                        <span className="text-gray-600">Created</span>
                        <span className="text-gray-900">{formatRelativeTime(job.createdAt)}</span>
                    </div>
                    {job.updatedAt !== job.createdAt && (
                        <div className="flex items-center gap-3 text-sm">
                            <CheckCircle className="h-4 w-4 text-green-600" />
                            <span className="text-gray-600">Updated</span>
                            <span className="text-gray-900">{formatRelativeTime(job.updatedAt)}</span>
                        </div>
                    )}
                    {job.completedAt && (
                        <div className="flex items-center gap-3 text-sm">
                            <CheckCircle className="h-4 w-4 text-green-600" />
                            <span className="text-gray-600">Completed</span>
                            <span className="text-gray-900">{formatRelativeTime(job.completedAt)}</span>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
