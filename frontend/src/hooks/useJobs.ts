import { useState, useEffect, useCallback } from 'react';
import { jobsService } from '../services/jobsService';
import type { Job, JobListParams } from '../types/job';
import type { PaginatedResponse } from '../types/api';

/**
 * Custom hook for jobs list management
 * Handles fetching, filtering, and pagination
 */
export function useJobs(initialParams?: JobListParams) {
    const [jobs, setJobs] = useState<Job[]>([]);
    const [pagination, setPagination] = useState<Omit<PaginatedResponse<Job>, 'data'>>({
        total: 0,
        page: 1,
        pageSize: 10,
        totalPages: 0,
    });
    const [params, setParams] = useState<JobListParams>(initialParams || {});
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchJobs = useCallback(async () => {
        setIsLoading(true);
        setError(null);

        try {
            const response = await jobsService.getJobs(params);
            setJobs(response.data);
            setPagination({
                total: response.total,
                page: response.page,
                pageSize: response.pageSize,
                totalPages: response.totalPages,
            });
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Failed to fetch jobs';
            setError(errorMessage);
        } finally {
            setIsLoading(false);
        }
    }, [params]);

    useEffect(() => {
        fetchJobs();
    }, [fetchJobs]);

    const updateParams = useCallback((newParams: Partial<JobListParams>) => {
        setParams((prev) => ({ ...prev, ...newParams }));
    }, []);

    const refresh = useCallback(() => {
        fetchJobs();
    }, [fetchJobs]);

    return {
        jobs,
        pagination,
        params,
        updateParams,
        isLoading,
        error,
        refresh,
    };
}
