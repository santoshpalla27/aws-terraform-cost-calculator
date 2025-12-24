import { Job, CostResult } from '../api/types';
import { JobState, JobStateMachine, mapBackendStatus } from './jobStateMachine';

/**
 * Job Machine State
 */
export interface JobMachineState {
    // Current state
    state: JobState;
    progress: number;

    // Job data
    job: Job | null;
    results: CostResult | null;

    // Status flags
    isLoading: boolean;
    isPolling: boolean;

    // Error handling
    error: string | null;
    correlationId: string | null;

    // Polling metadata
    pollAttempt: number;
    lastUpdated: number;
}

/**
 * Job Machine Actions
 */
export type JobAction =
    | { type: 'INITIALIZE'; payload: { job: Job; correlationId: string } }
    | { type: 'JOB_UPDATED'; payload: { job: Job; correlationId: string } }
    | { type: 'JOB_FAILED'; error: string; correlationId: string }
    | { type: 'RESULTS_LOADED'; payload: CostResult }
    | { type: 'POLL_ATTEMPT'; attempt: number }
    | { type: 'POLLING_STARTED' }
    | { type: 'POLLING_STOPPED' }
    | { type: 'RESET' };

/**
 * Initial state
 */
export const initialJobState: JobMachineState = {
    state: JobState.UPLOADED,
    progress: 0,
    job: null,
    results: null,
    isLoading: true,
    isPolling: false,
    error: null,
    correlationId: null,
    pollAttempt: 0,
    lastUpdated: Date.now()
};

/**
 * Job Reducer
 * 
 * CRITICAL: All state transitions go through state machine validation
 */
export function jobReducer(
    state: JobMachineState,
    action: JobAction
): JobMachineState {
    switch (action.type) {
        case 'INITIALIZE': {
            const newState = mapBackendStatus(action.payload.job.status);

            return {
                ...state,
                state: newState,
                progress: JobStateMachine.getProgress(newState),
                job: action.payload.job,
                correlationId: action.payload.correlationId,
                isLoading: false,
                lastUpdated: Date.now()
            };
        }

        case 'JOB_UPDATED': {
            const currentState = state.state;
            const newState = mapBackendStatus(action.payload.job.status);

            // Validate transition
            try {
                JobStateMachine.transition(currentState, newState);
            } catch (error) {
                console.error('[Reducer] Invalid state transition, keeping current state', error);
                return state;
            }

            // Validate progress is monotonic
            if (!JobStateMachine.validateProgress(currentState, newState)) {
                console.warn('[Reducer] Progress decreased, keeping current state');
                return state;
            }

            return {
                ...state,
                state: newState,
                progress: JobStateMachine.getProgress(newState),
                job: action.payload.job,
                correlationId: action.payload.correlationId,
                error: action.payload.job.error_message || null,
                lastUpdated: Date.now()
            };
        }

        case 'JOB_FAILED': {
            return {
                ...state,
                state: JobState.FAILED,
                progress: 0,
                error: action.error,
                correlationId: action.correlationId,
                isPolling: false,
                lastUpdated: Date.now()
            };
        }

        case 'RESULTS_LOADED': {
            return {
                ...state,
                results: action.payload,
                lastUpdated: Date.now()
            };
        }

        case 'POLL_ATTEMPT': {
            return {
                ...state,
                pollAttempt: action.attempt
            };
        }

        case 'POLLING_STARTED': {
            return {
                ...state,
                isPolling: true
            };
        }

        case 'POLLING_STOPPED': {
            return {
                ...state,
                isPolling: false
            };
        }

        case 'RESET': {
            return initialJobState;
        }

        default:
            return state;
    }
}
