import { useState, useEffect, useCallback } from 'react';
import { jobsService } from '../services/jobsService';
import { useWebSocket } from './useWebSocket';
import type { Job, JobLogs, JobTimeline } from '../types/job';
import type { WebSocketMessageType } from '../types/api';

/**
 * Custom hook for tracking individual job status
 * Supports real-time updates via WebSocket
 */
export function useJobStatus(jobId: string) {
    const [job, setJob] = useState<Job | null>(null);
    const [timeline, setTimeline] = useState<JobTimeline[]>([]);
    const [logs, setLogs] = useState<JobLogs[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // WebSocket for real-time updates
    const { subscribe, connect, disconnect } = useWebSocket(jobId);

    const fetchJob = useCallback(async () => {
        setIsLoading(true);
        setError(null);

        try {
            const jobData = await jobsService.getJob(jobId);
            setJob(jobData);

            // Fetch timeline and logs if available
            const [timelineData, logsData] = await Promise.all([
                jobsService.getJobTimeline(jobId),
                jobsService.getJobLogs(jobId),
            ]);

            setTimeline(timelineData);
            setLogs(logsData);
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Failed to fetch job';
            setError(errorMessage);
        } finally {
            setIsLoading(false);
        }
    }, [jobId]);

    useEffect(() => {
        fetchJob();
    }, [fetchJob]);

    useEffect(() => {
        // Connect to WebSocket for real-time updates
        connect();

        // Subscribe to status updates
        const unsubscribeStatus = subscribe(
            'JOB_STATUS_UPDATE' as WebSocketMessageType,
            (message) => {
                if (message.jobId === jobId) {
                    setJob((prev) => (prev ? { ...prev, ...message.payload } : null));
                }
            }
        );

        // Subscribe to progress updates
        const unsubscribeProgress = subscribe(
            'JOB_PROGRESS_UPDATE' as WebSocketMessageType,
            (message) => {
                if (message.jobId === jobId) {
                    setJob((prev) =>
                        prev ? { ...prev, progress: message.payload.progress } : null
                    );
                }
            }
        );

        // Subscribe to log updates
        const unsubscribeLogs = subscribe(
            'JOB_LOG' as WebSocketMessageType,
            (message) => {
                if (message.jobId === jobId) {
                    setLogs((prev) => [...prev, message.payload]);
                }
            }
        );

        return () => {
            unsubscribeStatus();
            unsubscribeProgress();
            unsubscribeLogs();
            disconnect();
        };
    }, [jobId, subscribe, connect, disconnect]);

    const retry = useCallback(async () => {
        try {
            const retriedJob = await jobsService.retryJob(jobId);
            setJob(retriedJob);
            return retriedJob;
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Failed to retry job';
            setError(errorMessage);
            throw err;
        }
    }, [jobId]);

    return {
        job,
        timeline,
        logs,
        isLoading,
        error,
        retry,
        refresh: fetchJob,
    };
}
