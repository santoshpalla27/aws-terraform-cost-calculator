import { useEffect, useRef, useCallback } from 'react';
import { jobsApi, ApiError } from '../api';
import { JobAction } from '../state/jobReducer';
import { JobStateMachine } from '../state/jobStateMachine';

/**
 * Polling configuration
 */
const POLLING_CONFIG = {
    // Exponential backoff delays (ms)
    delays: [1000, 2000, 4000, 8000, 16000, 30000],

    // Max polling attempts (~50 minutes with max delay)
    maxAttempts: 100,

    // Session storage key for persistence
    storageKey: 'job_polling_state'
};

/**
 * Calculate delay for next poll attempt
 */
function getPollingDelay(attempt: number): number {
    const index = Math.min(attempt, POLLING_CONFIG.delays.length - 1);
    return POLLING_CONFIG.delays[index];
}

/**
 * Polling state for persistence
 */
interface PollingState {
    jobId: string;
    attempt: number;
    startedAt: number;
}

/**
 * Save polling state to sessionStorage
 */
function savePollingState(state: PollingState): void {
    try {
        sessionStorage.setItem(POLLING_CONFIG.storageKey, JSON.stringify(state));
    } catch (error) {
        console.warn('[Polling] Failed to save state:', error);
    }
}

/**
 * Load polling state from sessionStorage
 */
function loadPollingState(jobId: string): PollingState | null {
    try {
        const stored = sessionStorage.getItem(POLLING_CONFIG.storageKey);
        if (!stored) return null;

        const state = JSON.parse(stored) as PollingState;

        // Only restore if same job
        if (state.jobId === jobId) {
            return state;
        }
    } catch (error) {
        console.warn('[Polling] Failed to load state:', error);
    }

    return null;
}

/**
 * Clear polling state
 */
function clearPollingState(): void {
    try {
        sessionStorage.removeItem(POLLING_CONFIG.storageKey);
    } catch (error) {
        console.warn('[Polling] Failed to clear state:', error);
    }
}

/**
 * Hook for job polling with exponential backoff
 * 
 * Features:
 * - Exponential backoff (1s → 30s)
 * - Max retry limit (100 attempts)
 * - Auto-stop on terminal states
 * - Resume after page refresh
 * - Cleanup on unmount
 */
export function useJobPolling(
    jobId: string,
    currentState: string,
    dispatch: React.Dispatch<JobAction>
) {
    const timeoutRef = useRef<NodeJS.Timeout | null>(null);
    const attemptRef = useRef(0);
    const isPollingRef = useRef(false);

    /**
     * Fetch job status and dispatch update
     */
    const pollJob = useCallback(async () => {
        try {
            console.log(`[Polling] Attempt ${attemptRef.current + 1}/${POLLING_CONFIG.maxAttempts}`);

            const job = await jobsApi.get(jobId);

            dispatch({
                type: 'JOB_UPDATED',
                payload: {
                    job,
                    correlationId: '' // Will be in response
                }
            });

            // Check if terminal state
            const mappedState = job.status;
            if (JobStateMachine.isTerminal(mappedState as any)) {
                console.log('[Polling] Terminal state reached, stopping');
                stopPolling();
                return true; // Stop polling
            }

            return false; // Continue polling
        } catch (error) {
            console.error('[Polling] Error fetching job:', error);

            // Increment attempt on error
            attemptRef.current++;

            // Stop if max attempts reached
            if (attemptRef.current >= POLLING_CONFIG.maxAttempts) {
                console.error('[Polling] Max attempts reached, stopping');
                dispatch({
                    type: 'JOB_FAILED',
                    error: 'Max polling attempts reached',
                    correlationId: (error as any).correlationId || 'unknown'
                });
                stopPolling();
                return true;
            }

            return false; // Continue polling
        }
    }, [jobId, dispatch]);

    /**
     * Schedule next poll
     */
    const scheduleNextPoll = useCallback(() => {
        if (!isPollingRef.current) return;

        const delay = getPollingDelay(attemptRef.current);

        console.log(`[Polling] Next poll in ${delay}ms`);

        timeoutRef.current = setTimeout(async () => {
            attemptRef.current++;

            dispatch({
                type: 'POLL_ATTEMPT',
                attempt: attemptRef.current
            });

            // Save state for resume
            savePollingState({
                jobId,
                attempt: attemptRef.current,
                startedAt: Date.now()
            });

            const shouldStop = await pollJob();

            if (!shouldStop && isPollingRef.current) {
                scheduleNextPoll();
            }
        }, delay);
    }, [jobId, pollJob, dispatch]);

    /**
     * Start polling
     */
    const startPolling = useCallback(() => {
        if (isPollingRef.current) {
            console.log('[Polling] Already polling');
            return;
        }

        console.log('[Polling] Starting');
        isPollingRef.current = true;

        dispatch({ type: 'POLLING_STARTED' });

        // Try to restore previous attempt count
        const savedState = loadPollingState(jobId);
        if (savedState) {
            attemptRef.current = savedState.attempt;
            console.log(`[Polling] Resumed from attempt ${attemptRef.current}`);
        }

        // Start polling immediately
        pollJob().then((shouldStop) => {
            if (!shouldStop) {
                scheduleNextPoll();
            }
        });
    }, [jobId, pollJob, scheduleNextPoll, dispatch]);

    /**
     * Stop polling
     */
    const stopPolling = useCallback(() => {
        console.log('[Polling] Stopping');
        isPollingRef.current = false;

        if (timeoutRef.current) {
            clearTimeout(timeoutRef.current);
            timeoutRef.current = null;
        }

        dispatch({ type: 'POLLING_STOPPED' });
        clearPollingState();
    }, [dispatch]);

    /**
     * Auto-start/stop based on state
     */
    useEffect(() => {
        const isTerminal = JobStateMachine.isTerminal(currentState as any);

        if (isTerminal) {
            stopPolling();
        } else if (!isPollingRef.current) {
            startPolling();
        }
    }, [currentState, startPolling, stopPolling]);

    /**
     * Cleanup on unmount
     */
    useEffect(() => {
        return () => {
            if (timeoutRef.current) {
                clearTimeout(timeoutRef.current);
            }
        };
    }, []);

    return {
        isPolling: isPollingRef.current,
        attempt: attemptRef.current,
        maxAttempts: POLLING_CONFIG.maxAttempts,
        startPolling,
        stopPolling
    };
}
