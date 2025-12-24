```typescript
import { useReducer, useEffect, useCallback, useRef } from 'react';
import { jobsApi, ApiError } from '../api';
import { JobState, JobStateMachine } from '../state/jobStateMachine';
import { jobReducer, initialJobState, JobMachineState } from '../state/jobReducer';
import { useJobPolling } from './useJobPolling';

/**
 * Main hook for job state machine
 * 
 * Features:
 * - Loads job from API on mount
 * - Starts polling automatically
 * - Fetches results when COMPLETED
 * - Handles errors with correlation_id
 * - Survives page refresh
 * 
 * CRITICAL: This is the ONLY way to manage job state
 */
export function useJobMachine(jobId: string) {
    const [state, dispatch] = useReducer(jobReducer, initialJobState);
    const hasLoadedRef = useRef(false);
    const hasLoadedResultsRef = useRef(false);

    /**
     * Initialize: Load job from API
     */
    const loadJob = useCallback(async () => {
        if (hasLoadedRef.current) return;

        try {
            console.log(`[Job Machine] Loading job ${ jobId } `);

            const job = await jobsApi.get(jobId);

            dispatch({
                type: 'INITIALIZE',
                payload: {
                    job,
                    correlationId: 'loaded' // From API
                }
            });

            hasLoadedRef.current = true;
        } catch (error) {
            console.error('[Job Machine] Failed to load job:', error);

            const apiError = error as ApiError;
            dispatch({
                type: 'JOB_FAILED',
                error: apiError.message,
                correlationId: apiError.correlationId
            });
        }
    }, [jobId]);

    /**
     * Load results when job completes
     */
    const loadResults = useCallback(async () => {
        if (hasLoadedResultsRef.current) return;
        if (state.state !== JobState.COMPLETED) return;
        
        try {
            console.log('[Job Machine] Loading results');
            
            const results = await jobsApi.getResults(jobId);
            
            dispatch({
                type: 'RESULTS_LOADED',
                payload: results
            });
            
            hasLoadedResultsRef.current = true;
        } catch (error) {
            console.error('[Job Machine] Failed to load results:', error);
            
            const apiError = error as ApiError;
            dispatch({
                type: 'JOB_FAILED',
                error: 'Failed to load results',
                correlationId: apiError.correlationId
            });
        }
    }, [jobId, state.state]);

    /**
     * Initialize on mount
     */
    useEffect(() => {
        loadJob();
    }, [loadJob]);

    /**
     * Load results when COMPLETED
     */
    useEffect(() => {
        if (state.state === JobState.COMPLETED) {
            loadResults();
        }
    }, [state.state, loadResults]);

    /**
     * Start polling (managed by useJobPolling)
     */
    const polling = useJobPolling(jobId, state.state, dispatch);

    /**
     * Reset function for cleanup
     */
    const reset = useCallback(() => {
        dispatch({ type: 'RESET' });
        hasLoadedRef.current = false;
        hasLoadedResultsRef.current = false;
        polling.stopPolling();
    }, [polling]);

    return {
        // State
        state: state.state,
        progress: state.progress,
        job: state.job,
        results: state.results,

        // Status flags
        isLoading: state.isLoading,
        isPolling: polling.isPolling,
        isCompleted: state.state === JobState.COMPLETED,
        isFailed: state.state === JobState.FAILED,
        isTerminal: JobStateMachine.isTerminal(state.state),

        // Error info
        error: state.error,
        correlationId: state.correlationId,

        // Polling info
        pollAttempt: polling.attempt,
        maxAttempts: polling.maxAttempts,

        // Actions
        refresh: loadJob,
        reset
    };
}
