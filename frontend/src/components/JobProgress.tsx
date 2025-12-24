import React from 'react';
import { JobState } from '../state/jobStateMachine';

interface JobProgressProps {
    state: JobState;
    progress: number;
    isPolling: boolean;
    pollAttempt?: number;
    maxAttempts?: number;
}

/**
 * Job Progress Display Component
 * 
 * Shows current job state and progress bar
 */
export function JobProgress({
    state,
    progress,
    isPolling,
    pollAttempt = 0,
    maxAttempts = 100
}: JobProgressProps) {
    const getStateLabel = (state: JobState): string => {
        const labels: Record<JobState, string> = {
            [JobState.UPLOADED]: 'Uploaded',
            [JobState.PLANNING]: 'Planning Infrastructure',
            [JobState.PARSING]: 'Parsing Configuration',
            [JobState.ENRICHING]: 'Enriching Metadata',
            [JobState.PRICING]: 'Calculating Prices',
            [JobState.COSTING]: 'Aggregating Costs',
            [JobState.COMPLETED]: 'Completed',
            [JobState.FAILED]: 'Failed'
        };

        return labels[state] || state;
    };

    const getStateColor = (state: JobState): string => {
        if (state === JobState.COMPLETED) return 'bg-green-500';
        if (state === JobState.FAILED) return 'bg-red-500';
        return 'bg-blue-500';
    };

    return (
        <div className="space-y-2">
            {/* State Label */}
            <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">
                    {getStateLabel(state)}
                </span>
                <span className="text-sm text-gray-500">
                    {progress}%
                </span>
            </div>

            {/* Progress Bar */}
            <div className="w-full bg-gray-200 rounded-full h-2.5">
                <div
                    className={`h-2.5 rounded-full transition-all duration-500 ${getStateColor(state)}`}
                    style={{ width: `${progress}%` }}
                />
            </div>

            {/* Polling Status */}
            {isPolling && (
                <div className="flex items-center justify-between text-xs text-gray-500">
                    <span className="flex items-center">
                        <span className="animate-pulse mr-2">●</span>
                        Polling for updates...
                    </span>
                    <span>
                        {pollAttempt}/{maxAttempts}
                    </span>
                </div>
            )}
        </div>
    );
}
