import { apiClient } from './apiClient';
import type { ApiResponse, PaginatedResponse } from '../types/api';
import type { Job, JobListParams, JobLogs, JobTimeline, JobStatusData } from '../types/job';
import type { CostEstimationResult } from '../types/cost';

/**
 * Jobs Service
 * Handles job management operations
 * NO business logic - pure API communication
 */

/**
 * Transform backend job data to frontend Job type
 * Backend uses snake_case (job_id, created_at), frontend uses camelCase (id, createdAt)
 */
function transformJob(backendJob: any): Job {
    return {
        id: backendJob.job_id,
        name: backendJob.name,
        status: backendJob.status,
        createdAt: backendJob.created_at,
        updatedAt: backendJob.updated_at,
        completedAt: backendJob.completed_at,
        errorMessage: backendJob.error_message,
        progress: backendJob.progress,
    };
}

export const jobsService = {
    /**
     * Get list of jobs with pagination and filtering
     */
    async getJobs(params?: JobListParams): Promise<PaginatedResponse<Job>> {
        const response = await apiClient.get<any>(
            '/jobs',
            params
        );

        if (!response.success) {
            throw new Error(response.error?.message || 'Failed to fetch jobs');
        }

        // Backend returns flattened structure with pagination at top level
        // Transform backend jobs to frontend Job type
        return {
            data: (response.data || []).map(transformJob),
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
        const response = await apiClient.get<any>(`/jobs/${jobId}`);

        if (!response.success || !response.data) {
            throw new Error(response.error?.message || 'Failed to fetch job');
        }

        // Backend returns job directly in data field
        return transformJob(response.data);
    },

    /**
     * Get cost estimation results for a completed job
     */
    async getJobResults(jobId: string): Promise<CostEstimationResult> {
        const response = await apiClient.get<ApiResponse<CostEstimationResult>>(
            `/jobs/${jobId}/results`
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
            `/jobs/${jobId}/retry`
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
                `/jobs/${jobId}/timeline`
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
                `/jobs/${jobId}/logs`
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

    /**
     * Get job status for polling (lightweight)
     */
    async getJobStatus(jobId: string): Promise<JobStatusData> {
        const response = await apiClient.get<ApiResponse<JobStatusData>>(
            `/jobs/${jobId}/status`
        );

        if (!response.success || !response.data) {
            throw new Error(response.error?.message || 'Failed to fetch job status');
        }

        return response.data;
    },
};

