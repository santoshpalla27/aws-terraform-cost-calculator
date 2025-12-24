import React from 'react';
import { useJobMachine } from '../hooks/useJobMachine';
import { JobProgress } from '../components/JobProgress';
import { JobErrorPanel } from '../components/JobErrorPanel';
import { JobState } from '../state/jobStateMachine';

interface JobStatusPageProps {
    jobId: string;
}

/**
 * Example: Job Status Page Component
 * 
 * Demonstrates proper usage of useJobMachine hook
 * 
 * CRITICAL RULES ENFORCED:
 * - No direct state manipulation
 * - No optimistic updates
 * - Backend is source of truth
 * - Errors always show correlation_id
 */
export default function JobStatusPage({ jobId }: JobStatusPageProps) {
    const {
        state,
        progress,
        job,
        results,
        isLoading,
        isPolling,
        isCompleted,
        isFailed,
        error,
        correlationId,
        pollAttempt,
        maxAttempts,
        refresh,
        reset
    } = useJobMachine(jobId);

    // Loading state
    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                    <p className="mt-4 text-gray-600">Loading job...</p>
                </div>
            </div>
        );
    }

    // Failed state
    if (isFailed && error && correlationId) {
        return (
            <div className="max-w-2xl mx-auto p-6">
                <JobErrorPanel
                    error={error}
                    correlationId={correlationId}
                    onRetry={refresh}
                />
            </div>
        );
    }

    return (
        <div className="max-w-4xl mx-auto p-6">
            {/* Job Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900">
                    {job?.name || 'Cost Estimation Job'}
                </h1>
                <p className="mt-2 text-sm text-gray-500">
                    Job ID: <code className="bg-gray-100 px-2 py-1 rounded">{jobId}</code>
                </p>
            </div>

            {/* Progress Section */}
            <div className="bg-white rounded-lg shadow p-6 mb-6">
                <h2 className="text-lg font-semibold mb-4">Progress</h2>
                <JobProgress
                    state={state}
                    progress={progress}
                    isPolling={isPolling}
                    pollAttempt={pollAttempt}
                    maxAttempts={maxAttempts}
                />
            </div>

            {/* Results Section (only when COMPLETED) */}
            {isCompleted && results && (
                <div className="bg-white rounded-lg shadow p-6">
                    <h2 className="text-lg font-semibold mb-4">Cost Estimation Results</h2>

                    <div className="space-y-4">
                        {/* Total Cost */}
                        <div className="border-b pb-4">
                            <p className="text-sm text-gray-600">Total Monthly Cost</p>
                            <p className="text-3xl font-bold text-gray-900">
                                ${results.total_monthly_cost.toFixed(2)}
                                <span className="text-lg text-gray-500 ml-2">{results.currency}</span>
                            </p>
                        </div>

                        {/* Breakdown */}
                        <div>
                            <h3 className="text-sm font-medium text-gray-700 mb-2">
                                Cost Breakdown
                            </h3>
                            <div className="space-y-2">
                                {results.breakdown.map((item, index) => (
                                    <div
                                        key={index}
                                        className="flex justify-between items-center p-3 bg-gray-50 rounded"
                                    >
                                        <div>
                                            <p className="font-medium text-gray-900">
                                                {item.resource_name}
                                            </p>
                                            <p className="text-sm text-gray-500">
                                                {item.service} • {item.resource_type}
                                            </p>
                                        </div>
                                        <p className="font-semibold text-gray-900">
                                            ${item.monthly_cost.toFixed(2)}
                                        </p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Debug Info (development only) */}
            {process.env.NODE_ENV === 'development' && (
                <div className="mt-6 bg-gray-100 rounded p-4 text-xs font-mono">
                    <p><strong>State:</strong> {state}</p>
                    <p><strong>Progress:</strong> {progress}%</p>
                    <p><strong>Polling:</strong> {isPolling ? 'Yes' : 'No'}</p>
                    <p><strong>Attempt:</strong> {pollAttempt}/{maxAttempts}</p>
                    {correlationId && <p><strong>Correlation ID:</strong> {correlationId}</p>}
                </div>
            )}
        </div>
    );
}
