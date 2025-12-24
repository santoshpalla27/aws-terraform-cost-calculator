import { useState, useEffect, useCallback } from 'react';
import { jobsApi } from '../api/jobs';
import { Job, JobStatus } from '../api/types';
import { JobStateMachine } from '../state/jobMachine';

/**
 * Hook for managing job state with polling and state machine validation
 */
export function useJob(jobId: string) {
    const [job, setJob] = useState<Job | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchJob = useCallback(async () => {
        try {
            const data = await jobsApi.get(jobId);

            // Validate state transition
            if (job && !JobStateMachine.validateTransition(job.status, data.status)) {
                console.warn(
                    `[useJob] Invalid state transition detected`,
                    `${job.status} → ${data.status}`
                );
            }

            setJob(data);
            setError(null);
            setIsLoading(false);

            // Stop polling if terminal state
            return JobStateMachine.isTerminal(data.status);
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Failed to fetch job';
            setError(errorMessage);
            setIsLoading(false);
            return true; // Stop polling on error
        }
    }, [jobId, job]);

    useEffect(() => {
        let isMounted = true;
        let intervalId: NodeJS.Timeout | null = null;

        const poll = async () => {
            if (!isMounted) return;

            const shouldStop = await fetchJob();

            if (shouldStop && intervalId) {
                clearInterval(intervalId);
                intervalId = null;
            }
        };

        // Initial fetch
        poll();

        // Poll every 2 seconds
        intervalId = setInterval(poll, 2000);

        return () => {
            isMounted = false;
            if (intervalId) {
                clearInterval(intervalId);
            }
        };
    }, [fetchJob]);

    return {
        job,
        isLoading,
        error,
        refresh: fetchJob
    };
}
