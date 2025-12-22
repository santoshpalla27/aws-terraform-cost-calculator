'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Clock, CheckCircle, XCircle, Loader2, ArrowRight } from 'lucide-react';
import { apiClient } from '@/lib/api/api-client';
import { formatRelativeTime } from '@/lib/utils/format';
import { LoadingState } from '../common/loading-state';
import { ErrorState } from '../common/error-state';
import { EmptyState } from '../common/empty-state';
import type { Job, JobStatus, JobListParams } from '@/lib/types';
import { cn } from '@/lib/utils/cn';

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
    const [jobs, setJobs] = useState<Job[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [filter, setFilter] = useState<JobStatus | 'ALL'>('ALL');
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);

    const fetchJobs = async () => {
        setIsLoading(true);
        setError(null);

        try {
            const params: JobListParams = {
                page,
                pageSize: 10,
                sortBy: 'createdAt',
                sortOrder: 'desc',
            };

            if (filter !== 'ALL') {
                params.status = filter as JobStatus;
            }

            const response = await apiClient.getJobs(params);
            setJobs(response.data);
            setTotalPages(response.totalPages);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to fetch jobs');
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchJobs();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [filter, page]);

    if (isLoading && jobs.length === 0) {
        return <LoadingState message="Loading jobs..." />;
    }

    if (error) {
        return <ErrorState message={error} onRetry={fetchJobs} />;
    }

    if (jobs.length === 0 && filter === 'ALL') {
        return (
            <EmptyState
                title="No jobs yet"
                description="Create your first cost estimation job to get started"
                action={{
                    label: 'Create Job',
                    onClick: () => (window.location.href = '/upload'),
                }}
            />
        );
    }

    return (
        <div className="space-y-6">
            {/* Filters */}
            <div className="flex items-center gap-2 overflow-x-auto pb-2">
                <button
                    onClick={() => setFilter('ALL')}
                    className={cn(
                        'rounded-md px-4 py-2 text-sm font-medium transition-colors',
                        filter === 'ALL'
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    )}
                >
                    All
                </button>
                {Object.entries(STATUS_CONFIG).map(([status, config]) => (
                    <button
                        key={status}
                        onClick={() => setFilter(status as JobStatus)}
                        className={cn(
                            'rounded-md px-4 py-2 text-sm font-medium transition-colors',
                            filter === status
                                ? 'bg-blue-600 text-white'
                                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        )}
                    >
                        {config.label}
                    </button>
                ))}
            </div>

            {/* Job List */}
            {jobs.length === 0 ? (
                <EmptyState
                    title={`No ${filter.toLowerCase()} jobs`}
                    description="Try adjusting your filters"
                />
            ) : (
                <div className="space-y-3">
                    {jobs.map((job) => {
                        const config = STATUS_CONFIG[job.status];
                        const Icon = config.icon;

                        return (
                            <Link
                                key={job.id}
                                href={`/jobs/${job.id}`}
                                onClick={(e) => {
                                    if (onJobClick) {
                                        e.preventDefault();
                                        onJobClick(job.id);
                                    }
                                }}
                                className="block rounded-lg border border-gray-200 bg-white p-4 transition-shadow hover:shadow-md"
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
                            </Link>
                        );
                    })}
                </div>
            )}

            {/* Pagination */}
            {totalPages > 1 && (
                <div className="flex items-center justify-center gap-2">
                    <button
                        onClick={() => setPage((p) => Math.max(1, p - 1))}
                        disabled={page === 1}
                        className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                        Previous
                    </button>
                    <span className="text-sm text-gray-600">
                        Page {page} of {totalPages}
                    </span>
                    <button
                        onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                        disabled={page === totalPages}
                        className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                        Next
                    </button>
                </div>
            )}
        </div>
    );
}
