import React from 'react';

interface JobErrorPanelProps {
    error: string;
    correlationId: string;
    onRetry?: () => void;
}

/**
 * Job Error Display Component
 * 
 * Shows error message with correlation ID for debugging
 * CRITICAL: Always display correlation_id for support
 */
export function JobErrorPanel({
    error,
    correlationId,
    onRetry
}: JobErrorPanelProps) {
    const copyCorrelationId = () => {
        navigator.clipboard.writeText(correlationId);
    };

    return (
        <div className="rounded-lg border-2 border-red-200 bg-red-50 p-6">
            {/* Error Icon */}
            <div className="flex items-start">
                <div className="flex-shrink-0">
                    <svg
                        className="h-6 w-6 text-red-600"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                    >
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                        />
                    </svg>
                </div>

                <div className="ml-3 flex-1">
                    {/* Error Title */}
                    <h3 className="text-lg font-medium text-red-800">
                        Job Failed
                    </h3>

                    {/* Error Message */}
                    <div className="mt-2 text-sm text-red-700">
                        <p>{error}</p>
                    </div>

                    {/* Correlation ID */}
                    <div className="mt-4">
                        <p className="text-xs text-red-600 font-medium mb-1">
                            Correlation ID (for support):
                        </p>
                        <div className="flex items-center space-x-2">
                            <code className="text-xs bg-red-100 px-2 py-1 rounded font-mono text-red-800">
                                {correlationId}
                            </code>
                            <button
                                onClick={copyCorrelationId}
                                className="text-xs text-red-600 hover:text-red-800 underline"
                            >
                                Copy
                            </button>
                        </div>
                    </div>

                    {/* Retry Button */}
                    {onRetry && (
                        <div className="mt-4">
                            <button
                                onClick={onRetry}
                                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                            >
                                Retry
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
