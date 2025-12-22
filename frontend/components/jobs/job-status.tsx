'use client';

import { useEffect, useState } from 'react';
import { Clock, CheckCircle, XCircle, Loader2, RefreshCw } from 'lucide-react';
import { wsService } from '@/lib/websocket/websocket-service';
import { apiClient } from '@/lib/api/api-client';
import { formatRelativeTime } from '@/lib/utils/format';
import type { Job, WebSocketMessage, WebSocketMessageType } from '@/lib/types';
import { cn } from '@/lib/utils/cn';

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
    jobId: string;
    initialJob?: Job;
    onRetry?: () => void;
}

export function JobStatus({ jobId, initialJob, onRetry }: JobStatusProps) {
    const [job, setJob] = useState<Job | null>(initialJob || null);
    const [isRetrying, setIsRetrying] = useState(false);

    useEffect(() => {
        // Fetch initial job data if not provided
        if (!initialJob) {
            apiClient.getJob(jobId).then(setJob).catch(console.error);
        }

        // Connect to WebSocket for real-time updates
        wsService.connect(jobId);

        // Subscribe to status updates
        const unsubscribeStatus = wsService.subscribe(
            'JOB_STATUS_UPDATE' as WebSocketMessageType,
            (message: WebSocketMessage) => {
                if (message.jobId === jobId) {
                    setJob((prev) => (prev ? { ...prev, ...message.payload } : null));
                }
            }
        );

        // Subscribe to progress updates
        const unsubscribeProgress = wsService.subscribe(
            'JOB_PROGRESS_UPDATE' as WebSocketMessageType,
            (message: WebSocketMessage) => {
                if (message.jobId === jobId) {
                    setJob((prev) =>
                        prev ? { ...prev, progress: message.payload.progress } : null
                    );
                }
            }
        );

        // Cleanup
        return () => {
            unsubscribeStatus();
            unsubscribeProgress();
            wsService.disconnect();
        };
    }, [jobId, initialJob]);

    const handleRetry = async () => {
        setIsRetrying(true);
        try {
            const retriedJob = await apiClient.retryJob(jobId);
            setJob(retriedJob);
            if (onRetry) {
                onRetry();
            }
        } catch (error) {
            console.error('Failed to retry job:', error);
        } finally {
            setIsRetrying(false);
        }
    };

    if (!job) {
        return (
            <div className="flex items-center justify-center py-8">
                <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
            </div>
        );
    }

    const config = STATUS_CONFIG[job.status];
    const Icon = config.icon;

    return (
        <div className="space-y-6">
            {/* Status Card */}
            <div className={cn('rounded-lg border-2 p-6', `border-${config.color.split('-')[1]}-200`)}>
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
                {job.status === 'FAILED' && (
                    <button
                        onClick={handleRetry}
                        disabled={isRetrying}
                        className="mt-4 inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                        <RefreshCw className={cn('h-4 w-4', isRetrying && 'animate-spin')} />
                        {isRetrying ? 'Retrying...' : 'Retry Job'}
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
