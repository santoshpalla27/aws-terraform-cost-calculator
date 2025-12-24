import { apiClient } from './client';
import { Job, CostResult, JobStatus } from './types';

/**
 * Jobs API
 * Typed methods for job management
 * NO business logic - pure API communication
 */
export const jobsApi = {
    /**
     * Create a new cost estimation job
     */
    async create(params: {
        name: string;
        upload_id: string;
        usage_profile?: string;
    }): Promise<Job> {
        const response = await apiClient.post<Job>('/api/jobs', {
            name: params.name,
            upload_id: params.upload_id,
            usage_profile: params.usage_profile || 'prod'
        });

        if (!response.data) {
            throw new Error(response.error?.message || 'Failed to create job');
        }

        return response.data;
    },

    /**
     * Get job details by ID
     */
    async get(jobId: string): Promise<Job> {
        const response = await apiClient.get<Job>(`/api/jobs/${jobId}`);

        if (!response.data) {
            throw new Error(response.error?.message || 'Failed to fetch job');
        }

        return response.data;
    },

    /**
     * List jobs with pagination
     */
    async list(params?: {
        status?: JobStatus;
        page?: number;
        page_size?: number;
    }): Promise<{ jobs: Job[]; pagination: any }> {
        const response = await apiClient.get<Job[]>('/api/jobs', params);

        if (!response.data) {
            throw new Error(response.error?.message || 'Failed to list jobs');
        }

        return {
            jobs: response.data,
            pagination: response.meta.pagination || null
        };
    },

    /**
     * Get job status (lightweight for polling)
     */
    async getStatus(jobId: string): Promise<{
        job_id: string;
        status: JobStatus;
        progress: number;
        updated_at: string;
    }> {
        const response = await apiClient.get<any>(`/api/jobs/${jobId}/status`);

        if (!response.data) {
            throw new Error(response.error?.message || 'Failed to fetch job status');
        }

        return response.data;
    },

    /**
     * Get cost estimation results for completed job
     */
    async getResults(jobId: string): Promise<CostResult> {
        const response = await apiClient.get<CostResult>(`/api/jobs/${jobId}/results`);

        if (!response.data) {
            throw new Error(response.error?.message || 'Failed to fetch results');
        }

        return response.data;
    },

    /**
     * Delete a job
     */
    async delete(jobId: string): Promise<void> {
        await apiClient.delete(`/api/jobs/${jobId}`);
    }
};
