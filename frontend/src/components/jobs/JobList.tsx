'use client';

import { useJobs } from '@/hooks/useJobs';
import { Clock, CheckCircle, XCircle, Loader2, ArrowRight } from 'lucide-react';
import { formatRelativeTime } from '@/utils/formatters';
import { cn } from '@/utils/formatters';

const STATUS_CONFIG: Record<string, any> = {
    UPLOADED: {
        icon: Clock,
        color: 'text-yellow-600',
        bg: 'bg-yellow-100',
        label: 'Uploaded',
    },
    PLANNING: {
        icon: Loader2,
        color: 'text-blue-600',
        bg: 'bg-blue-100',
        label: 'Planning',
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
    const { jobs, isLoading, error, correlationId, refresh } = useJobs();

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
                {correlationId && (
                    <p className="text-xs text-red-600 mt-1">ID: {correlationId}</p>
                )}
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
            <div className="space-y-3">
                {jobs.map((job) => {
                    const config = STATUS_CONFIG[job.status] || STATUS_CONFIG.UPLOADED;
                    const Icon = config.icon;

                    return (
                        <div
                            key={job.job_id}
                            onClick={() => onJobClick?.(job.job_id)}
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
                                                    (job.status === 'PLANNING' || job.status === 'PARSING') && 'animate-spin'
                                                )}
                                            />
                                        </div>
                                        <div>
                                            <h3 className="font-semibold text-gray-900">{job.name || 'Unnamed Job'}</h3>
                                            <p className="text-sm text-gray-500">
                                                {formatRelativeTime(job.created_at)}
                                            </p>
                                        </div>
                                    </div>
                                    {job.error_message && (
                                        <p className="mt-2 text-sm text-red-600">{job.error_message}</p>
                                    )}
                                    {job.progress !== undefined && job.progress > 0 && (
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
        </div>
    );
}
