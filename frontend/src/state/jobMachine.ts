import { JobStatus } from '../api/types';

/**
 * Job State Machine
 * Enforces valid state transitions based on canonical JobStatus enum
 */

type JobState = JobStatus;

/**
 * Valid state transitions
 */
const STATE_TRANSITIONS: Record<JobState, JobState[]> = {
    [JobStatus.IDLE]: [JobStatus.UPLOADING],
    [JobStatus.UPLOADING]: [JobStatus.CREATED, JobStatus.FAILED],
    [JobStatus.CREATED]: [JobStatus.PLANNING, JobStatus.FAILED],
    [JobStatus.PLANNING]: [JobStatus.PARSING, JobStatus.FAILED],
    [JobStatus.PARSING]: [JobStatus.ENRICHING, JobStatus.FAILED],
    [JobStatus.ENRICHING]: [JobStatus.COSTING, JobStatus.FAILED],
    [JobStatus.COSTING]: [JobStatus.COMPLETED, JobStatus.FAILED],
    [JobStatus.COMPLETED]: [],
    [JobStatus.FAILED]: []
};

/**
 * Progress percentage for each state
 */
const STATE_PROGRESS: Record<JobState, number> = {
    [JobStatus.IDLE]: 0,
    [JobStatus.UPLOADING]: 10,
    [JobStatus.CREATED]: 20,
    [JobStatus.PLANNING]: 30,
    [JobStatus.PARSING]: 50,
    [JobStatus.ENRICHING]: 70,
    [JobStatus.COSTING]: 90,
    [JobStatus.COMPLETED]: 100,
    [JobStatus.FAILED]: 0
};

/**
 * Job State Machine
 */
export const JobStateMachine = {
    /**
     * Check if transition from one state to another is valid
     */
    canTransition(from: JobState, to: JobState): boolean {
        const validTransitions = STATE_TRANSITIONS[from];
        return validTransitions ? validTransitions.includes(to) : false;
    },

    /**
     * Check if state is terminal (no further transitions)
     */
    isTerminal(state: JobState): boolean {
        return state === JobStatus.COMPLETED || state === JobStatus.FAILED;
    },

    /**
     * Get expected progress percentage for a state
     */
    getProgressPercentage(state: JobState): number {
        return STATE_PROGRESS[state] || 0;
    },

    /**
     * Get next possible states
     */
    getNextStates(state: JobState): JobState[] {
        return STATE_TRANSITIONS[state] || [];
    },

    /**
     * Validate state transition and log warning if invalid
     */
    validateTransition(from: JobState, to: JobState): boolean {
        const valid = this.canTransition(from, to);

        if (!valid) {
            console.warn(
                `[State Machine] Invalid transition: ${from} → ${to}`,
                `Valid transitions from ${from}:`,
                this.getNextStates(from)
            );
        }

        return valid;
    }
};
