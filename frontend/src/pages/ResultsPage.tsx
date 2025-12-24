import React from 'react';
import { useJobResults } from '../hooks/useJobResults';
import { JobErrorPanel } from '../components/JobErrorPanel';

interface ResultsPageProps {
    jobId: string;
}

/**
 * Results page component (READ-ONLY).
 * 
 * CRITICAL: Results are immutable and cannot be modified.
 * No edit/update/delete buttons.
 */
export function ResultsPage({ jobId }: ResultsPageProps) {
    const { results, isLoading, error, correlationId } = useJobResults(jobId);

    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                    <p className="mt-4 text-gray-600">Loading results...</p>
                </div>
            </div>
        );
    }

    if (error && correlationId) {
        return (
            <div className="max-w-4xl mx-auto p-6">
                <JobErrorPanel error={error} correlationId={correlationId} />
            </div>
        );
    }

    if (!results) {
        return (
            <div className="max-w-4xl mx-auto p-6">
                <div className="bg-yellow-50 border-2 border-yellow-200 rounded-lg p-6">
                    <p className="text-yellow-800">
                        No results available for this job yet.
                    </p>
                </div>
            </div>
        );
    }

    return (
        <div className="max-w-6xl mx-auto p-6">
            {/* Header with immutability notice */}
            <div className="mb-6">
                <h1 className="text-3xl font-bold text-gray-900">
                    Cost Estimation Results
                </h1>
                <div className="mt-2 flex items-center text-sm text-gray-500">
                    <svg className="h-4 w-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
                    </svg>
                    <span>Results are immutable and cannot be modified</span>
                </div>
            </div>

            {/* Total Cost Card */}
            <div className="bg-white rounded-lg shadow-lg p-8 mb-6">
                <div className="border-b pb-4 mb-4">
                    <p className="text-sm text-gray-600">Total Monthly Cost</p>
                    <p className="text-4xl font-bold text-gray-900">
                        ${results.total_monthly_cost.toFixed(2)}
                        <span className="text-lg text-gray-500 ml-2">{results.currency}</span>
                    </p>
                </div>

                {/* Metadata */}
                <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                        <p className="text-gray-600">Usage Profile</p>
                        <p className="font-medium text-gray-900">{results.usage_profile || 'N/A'}</p>
                    </div>
                    <div>
                        <p className="text-gray-600">Confidence</p>
                        <p className="font-medium text-gray-900">{results.confidence}</p>
                    </div>
                    <div>
                        <p className="text-gray-600">Created At</p>
                        <p className="font-medium text-gray-900">
                            {new Date(results.created_at).toLocaleString()}
                        </p>
                    </div>
                    <div>
                        <p className="text-gray-600">Result ID</p>
                        <p className="font-mono text-xs text-gray-700">{results.result_id}</p>
                    </div>
                </div>
            </div>

            {/* Cost Breakdown */}
            <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-xl font-semibold mb-4">Cost Breakdown</h2>

                {results.breakdown && results.breakdown.length > 0 ? (
                    <div className="space-y-3">
                        {results.breakdown.map((item, index) => (
                            <div
                                key={index}
                                className="flex justify-between items-center p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                            >
                                <div className="flex-1">
                                    <p className="font-medium text-gray-900">
                                        {item.resource_name}
                                    </p>
                                    <p className="text-sm text-gray-500">
                                        {item.service} • {item.resource_type} • {item.region}
                                    </p>
                                </div>
                                <div className="text-right">
                                    <p className="font-semibold text-gray-900">
                                        ${item.monthly_cost.toFixed(2)}
                                    </p>
                                    {item.quantity && item.pricing_unit && (
                                        <p className="text-sm text-gray-500">
                                            {item.quantity} {item.pricing_unit}
                                        </p>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <p className="text-gray-500">No breakdown available</p>
                )}
            </div>

            {/* Footer notice */}
            <div className="mt-6 text-center text-sm text-gray-500">
                <p>
                    To generate new results, create a new cost estimation job.
                </p>
            </div>
        </div>
    );
}
