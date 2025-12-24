import { useState, useEffect } from 'react';
import { jobsApi, ApiError } from '../api';
import { CostResult } from '../api/types';

/**
 * Hook for fetching job results with caching.
 * 
 * CRITICAL: Results are immutable, so we cache them forever.
 * Once loaded, they never change.
 */
export function useJobResults(jobId: string) {
    const [results, setResults] = useState<CostResult | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [correlationId, setCorrelationId] = useState<string | null>(null);

    useEffect(() => {
        const fetchResults = async () => {
            try {
                // Try cache first (results are immutable)
                const cacheKey = `results:${jobId}`;
                const cached = localStorage.getItem(cacheKey);

                if (cached) {
                    setResults(JSON.parse(cached));
                    setIsLoading(false);
                    return;
                }

                // Fetch from API
                const data = await jobsApi.getResults(jobId);
                setResults(data);

                // Cache forever (immutable)
                localStorage.setItem(cacheKey, JSON.stringify(data));
                setError(null);
            } catch (err) {
                const apiError = err as ApiError;
                setError(apiError.message);
                setCorrelationId(apiError.correlationId);
            } finally {
                setIsLoading(false);
            }
        };

        fetchResults();
    }, [jobId]);

    return {
        results,
        isLoading,
        error,
        correlationId
    };
}
