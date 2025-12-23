import { apiClient } from './apiClient';
import type { ApiResponse, PaginatedResponse } from '../types/api';
import type { Job, JobListParams, JobLogs, JobTimeline } from '../types/job';
import type { CostEstimationResult } from '../types/cost';

/**
 * Jobs Service
 * Handles job management operations
 * NO business logic - pure API communication
 */

export const jobsService = {
    /**
     * Get list of jobs with pagination and filtering
     */
    async getJobs(params?: JobListParams): Promise<PaginatedResponse<Job>> {
        const response = await apiClient.get<any>(
            '/api/jobs',
            params
        );

        if (!response.success) {
            throw new Error(response.error?.message || 'Failed to fetch jobs');
        }

        // Backend returns flattened structure with pagination at top level
        return {
            data: response.data || [],
            total: response.total || 0,
            page: response.page || 1,
            pageSize: response.pageSize || 10,
            totalPages: response.totalPages || 0,
        };
    },

    /**
     * Get a specific job by ID
     */
    async getJob(jobId: string): Promise<Job> {
        const response = await apiClient.get<ApiResponse<Job>>(`/api/jobs/${jobId}`);

        if (!response.success || !response.data) {
            throw new Error(response.error?.message || 'Failed to fetch job');
        }

        return response.data;
    },

    /**
     * Get cost estimation results for a completed job
     */
    async getJobResults(jobId: string): Promise<CostEstimationResult> {
        const response = await apiClient.get<ApiResponse<CostEstimationResult>>(
            `/api/jobs/${jobId}/results`
        );

        if (!response.success || !response.data) {
            throw new Error(response.error?.message || 'Failed to fetch results');
        }

        return response.data;
    },

    /**
     * Retry a failed job
     */
    async retryJob(jobId: string): Promise<Job> {
        const response = await apiClient.post<ApiResponse<Job>>(
            `/api/jobs/${jobId}/retry`
        );

        if (!response.success || !response.data) {
            throw new Error(response.error?.message || 'Failed to retry job');
        }

        return response.data;
    },

    /**
     * Get job timeline (if provided by backend)
     */
    async getJobTimeline(jobId: string): Promise<JobTimeline[]> {
        try {
            const response = await apiClient.get<ApiResponse<JobTimeline[]>>(
                `/api/jobs/${jobId}/timeline`
            );

            if (!response.success || !response.data) {
                return [];
            }

            return response.data;
        } catch (error) {
            // Timeline is optional, return empty array if not available
            return [];
        }
    },

    /**
     * Get job logs (if provided by backend)
     */
    async getJobLogs(jobId: string): Promise<JobLogs[]> {
        try {
            const response = await apiClient.get<ApiResponse<JobLogs[]>>(
                `/api/jobs/${jobId}/logs`
            );

            if (!response.success || !response.data) {
                return [];
            }

            return response.data;
        } catch (error) {
            // Logs are optional, return empty array if not available
            return [];
        }
    },
};
