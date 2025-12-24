import { api } from './client';
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
        return await api.post<Job>('/jobs', {
            name: params.name,
            upload_id: params.upload_id,
            usage_profile: params.usage_profile || 'prod'
        });
    },

    /**
     * Get job details by ID
     */
    async get(jobId: string): Promise<Job> {
        return await api.get<Job>(`/jobs/${jobId}`);
    },

    /**
     * List jobs with pagination
     */
    async list(params?: {
        status?: JobStatus;
        page?: number;
        page_size?: number;
    }): Promise<{ jobs: Job[]; pagination: any }> {
        let endpoint = '/jobs';
        if (params) {
            const queryParams = new URLSearchParams();
            if (params.status) queryParams.append('status', params.status);
            if (params.page) queryParams.append('page', params.page.toString());
            if (params.page_size) queryParams.append('page_size', params.page_size.toString());
            const queryString = queryParams.toString();
            if (queryString) endpoint += `?${queryString}`;
        }

        const jobs = await api.get<Job[]>(endpoint);
        return {
            jobs,
            pagination: null // TODO: Extract from response
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
        return await api.get<any>(`/jobs/${jobId}/status`);
    },

    /**
     * Get cost estimation results for completed job
     */
    async getResults(jobId: string): Promise<CostResult> {
        return await api.get<CostResult>(`/jobs/${jobId}/results`);
    },

    /**
     * Delete a job
     */
    async delete(jobId: string): Promise<void> {
        await api.delete(`/jobs/${jobId}`);
    }
};
