/**
 * Deterministic Job State Machine
 * 
 * CRITICAL RULES:
 * - All state transitions must be explicit
 * - Invalid transitions throw errors
 * - Backend is source of truth
 * - No optimistic updates
 */

/**
 * Canonical job state enumeration
 * Maps to backend JobStatus but uses frontend naming
 */
export enum JobState {
    UPLOADED = 'UPLOADED',
    PLANNING = 'PLANNING',
    PARSING = 'PARSING',
    ENRICHING = 'ENRICHING',
    PRICING = 'PRICING',
    COSTING = 'COSTING',
    COMPLETED = 'COMPLETED',
    FAILED = 'FAILED'
}

/**
 * Valid state transitions
 * Any state can transition to FAILED
 */
const VALID_TRANSITIONS: Record<JobState, JobState[]> = {
    [JobState.UPLOADED]: [JobState.PLANNING, JobState.FAILED],
    [JobState.PLANNING]: [JobState.PARSING, JobState.FAILED],
    [JobState.PARSING]: [JobState.ENRICHING, JobState.FAILED],
    [JobState.ENRICHING]: [JobState.PRICING, JobState.FAILED],
    [JobState.PRICING]: [JobState.COSTING, JobState.FAILED],
    [JobState.COSTING]: [JobState.COMPLETED, JobState.FAILED],
    [JobState.COMPLETED]: [], // Terminal state
    [JobState.FAILED]: []      // Terminal state
};

/**
 * Progress percentage for each state
 * Used for UI progress bars
 */
const STATE_PROGRESS: Record<JobState, number> = {
    [JobState.UPLOADED]: 10,
    [JobState.PLANNING]: 20,
    [JobState.PARSING]: 40,
    [JobState.ENRICHING]: 60,
    [JobState.PRICING]: 75,
    [JobState.COSTING]: 90,
    [JobState.COMPLETED]: 100,
    [JobState.FAILED]: 0
};

/**
 * Map backend JobStatus to frontend JobState
 */
export function mapBackendStatus(backendStatus: string): JobState {
    // Backend uses: IDLE, UPLOADING, CREATED, PLANNING, PARSING, ENRICHING, COSTING, COMPLETED, FAILED
    // Frontend uses: UPLOADED, PLANNING, PARSING, ENRICHING, PRICING, COSTING, COMPLETED, FAILED

    const mapping: Record<string, JobState> = {
        'IDLE': JobState.UPLOADED,
        'UPLOADING': JobState.UPLOADED,
        'CREATED': JobState.UPLOADED,
        'PLANNING': JobState.PLANNING,
        'PARSING': JobState.PARSING,
        'ENRICHING': JobState.ENRICHING,
        'COSTING': JobState.PRICING, // Backend "COSTING" maps to our "PRICING"
        'PRICING': JobState.PRICING,
        'COMPLETED': JobState.COMPLETED,
        'FAILED': JobState.FAILED
    };

    const mapped = mapping[backendStatus];
    if (!mapped) {
        console.error(`[State Machine] Unknown backend status: ${backendStatus}`);
        return JobState.UPLOADED; // Safe fallback
    }

    return mapped;
}

/**
 * State Machine API
 */
export const JobStateMachine = {
    /**
     * Validate if transition from one state to another is allowed
     */
    canTransition(from: JobState, to: JobState): boolean {
        const validNextStates = VALID_TRANSITIONS[from];
        return validNextStates.includes(to);
    },

    /**
     * Check if state is terminal (no further transitions possible)
     */
    isTerminal(state: JobState): boolean {
        return state === JobState.COMPLETED || state === JobState.FAILED;
    },

    /**
     * Get progress percentage for a state
     */
    getProgress(state: JobState): number {
        return STATE_PROGRESS[state];
    },

    /**
     * Get valid next states from current state
     */
    getNextStates(state: JobState): JobState[] {
        return VALID_TRANSITIONS[state] || [];
    },

    /**
     * Validate and enforce state transition
     * Throws if transition is invalid
     */
    transition(from: JobState, to: JobState): JobState {
        // Allow staying in same state (idempotent)
        if (from === to) {
            return to;
        }

        // Validate transition
        if (!this.canTransition(from, to)) {
            const error = new Error(
                `[State Machine] Invalid transition: ${from} → ${to}. ` +
                `Valid transitions: ${this.getNextStates(from).join(', ')}`
            );
            console.error(error.message);
            throw error;
        }

        console.log(`[State Machine] Transition: ${from} → ${to} (${this.getProgress(to)}%)`);
        return to;
    },

    /**
     * Validate progress is monotonic (never decreases)
     */
    validateProgress(oldState: JobState, newState: JobState): boolean {
        const oldProgress = this.getProgress(oldState);
        const newProgress = this.getProgress(newState);

        // FAILED state is exception (progress goes to 0)
        if (newState === JobState.FAILED) {
            return true;
        }

        // Progress must not decrease
        if (newProgress < oldProgress) {
            console.warn(
                `[State Machine] Progress decreased: ${oldState} (${oldProgress}%) → ` +
                `${newState} (${newProgress}%)`
            );
            return false;
        }

        return true;
    }
};
