'use client';

import { useState, useEffect } from 'react';
import { jobsService } from '@/services/jobsService';
import { CostSummary } from './CostSummary';
import { ResourceBreakdown } from './ResourceBreakdown';
import type { CostEstimationResult } from '@/types/cost';

interface CostResultsProps {
    jobId: string;
}

export function CostResults({ jobId }: CostResultsProps) {
    const [result, setResult] = useState<CostEstimationResult | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchResults = async () => {
            try {
                const data = await jobsService.getJobResults(jobId);
                setResult(data);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to load results');
            } finally {
                setIsLoading(false);
            }
        };

        fetchResults();
    }, [jobId]);

    if (isLoading) {
        return (
            <div className="flex items-center justify-center py-12">
                <div className="text-gray-600">Loading cost results...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="rounded-lg border border-red-200 bg-red-50 p-4">
                <p className="text-sm text-red-800">{error}</p>
            </div>
        );
    }

    if (!result) {
        return null;
    }

    return (
        <div className="space-y-6">
            <div className="border-t border-gray-200 pt-6">
                <h2 className="text-2xl font-bold text-gray-900 mb-6">
                    Cost Estimation Results
                </h2>
                <CostSummary result={result} />
            </div>

            <div className="border-t border-gray-200 pt-6">
                <h2 className="text-2xl font-bold text-gray-900 mb-6">
                    Resource Details
                </h2>
                <ResourceBreakdown
                    resources={result.services.flatMap((s) => s.resources)}
                    currency={result.currency}
                />
            </div>
        </div>
    );
}
