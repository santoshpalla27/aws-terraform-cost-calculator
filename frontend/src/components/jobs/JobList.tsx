'use client';

import { useJobs } from '@/hooks/useJobs';
import { Clock, CheckCircle, XCircle, Loader2, ArrowRight } from 'lucide-react';
import { formatRelativeTime } from '@/utils/formatters';
import { cn } from '@/utils/formatters';
import type { JobStatus as JobStatusType } from '@/types/job';

const STATUS_CONFIG = {
    PENDING: {
        icon: Clock,
        color: 'text-yellow-600',
        bg: 'bg-yellow-100',
        label: 'Pending',
    },
    RUNNING: {
        icon: Loader2,
        color: 'text-blue-600',
        bg: 'bg-blue-100',
        label: 'Running',
    },
    COMPLETED: {
        icon: CheckCircle,
        color: 'text-green-600',
        bg: 'bg-green-100',
        label: 'Completed',
    },
    FAILED: {
        icon: XCircle,
        color: 'text-red-600',
        bg: 'bg-red-100',
        label: 'Failed',
    },
};

interface JobListProps {
    onJobClick?: (jobId: string) => void;
}

export function JobList({ onJobClick }: JobListProps) {
    const { jobs, isLoading, error, params, updateParams, pagination } = useJobs();

    if (isLoading && jobs.length === 0) {
        return (
            <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
            </div>
        );
    }

    if (error) {
        return (
            <div className="rounded-lg border border-red-200 bg-red-50 p-4">
                <p className="text-sm text-red-800">{error}</p>
            </div>
        );
    }

    if (jobs.length === 0) {
        return (
            <div className="rounded-lg border-2 border-dashed border-gray-300 bg-gray-50 p-12 text-center">
                <p className="text-gray-600">No jobs yet. Create your first cost estimation job!</p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Filters */}
            <div className="flex items-center gap-2 overflow-x-auto pb-2">
                <button
                    onClick={() => updateParams({ status: undefined })}
                    className={cn(
                        'rounded-md px-4 py-2 text-sm font-medium transition-colors',
                        !params.status
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    )}
                >
                    All
                </button>
                {Object.entries(STATUS_CONFIG).map(([status, config]) => (
                    <button
                        key={status}
                        onClick={() => updateParams({ status: status as JobStatusType })}
                        className={cn(
                            'rounded-md px-4 py-2 text-sm font-medium transition-colors',
                            params.status === status
                                ? 'bg-blue-600 text-white'
                                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        )}
                    >
                        {config.label}
                    </button>
                ))}
            </div>

            {/* Job List */}
            <div className="space-y-3">
                {jobs.map((job) => {
                    const config = STATUS_CONFIG[job.status];
                    const Icon = config.icon;

                    return (
                        <div
                            key={job.id}
                            onClick={() => onJobClick?.(job.id)}
                            className="block rounded-lg border border-gray-200 bg-white p-4 transition-shadow hover:shadow-md cursor-pointer"
                        >
                            <div className="flex items-start justify-between">
                                <div className="flex-1">
                                    <div className="flex items-center gap-3">
                                        <div className={cn('rounded-full p-2', config.bg)}>
                                            <Icon
                                                className={cn(
                                                    'h-5 w-5',
                                                    config.color,
                                                    job.status === 'RUNNING' && 'animate-spin'
                                                )}
                                            />
                                        </div>
                                        <div>
                                            <h3 className="font-semibold text-gray-900">{job.name}</h3>
                                            <p className="text-sm text-gray-500">
                                                {formatRelativeTime(job.createdAt)}
                                            </p>
                                        </div>
                                    </div>
                                    {job.errorMessage && (
                                        <p className="mt-2 text-sm text-red-600">{job.errorMessage}</p>
                                    )}
                                    {job.progress !== undefined && job.status === 'RUNNING' && (
                                        <div className="mt-3">
                                            <div className="flex justify-between text-xs text-gray-600 mb-1">
                                                <span>Progress</span>
                                                <span>{job.progress}%</span>
                                            </div>
                                            <div className="h-1.5 w-full overflow-hidden rounded-full bg-gray-200">
                                                <div
                                                    className="h-full bg-blue-600 transition-all duration-300"
                                                    style={{ width: `${job.progress}%` }}
                                                />
                                            </div>
                                        </div>
                                    )}
                                </div>
                                <ArrowRight className="h-5 w-5 text-gray-400" />
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Pagination */}
            {pagination.totalPages > 1 && (
                <div className="flex items-center justify-center gap-2">
                    <button
                        onClick={() => updateParams({ page: Math.max(1, pagination.page - 1) })}
                        disabled={pagination.page === 1}
                        className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                        Previous
                    </button>
                    <span className="text-sm text-gray-600">
                        Page {pagination.page} of {pagination.totalPages}
                    </span>
                    <button
                        onClick={() =>
                            updateParams({ page: Math.min(pagination.totalPages, pagination.page + 1) })
                        }
                        disabled={pagination.page === pagination.totalPages}
                        className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                        Next
                    </button>
                </div>
            )}
        </div>
    );
}
