/**
 * Domain API Layer
 * 
 * CRITICAL: This is the ONLY place where API endpoints are defined
 * NO raw URLs outside this file
 */

import { api, ApiError } from './client';
import { Job, UsageProfile, CostResult } from './types';

/**
 * Jobs API
 */
export const jobsApi = {
    /**
     * Create a new job
     */
    async create(params: {
        name: string;
        upload_id: string;
        usage_profile?: string;
    }): Promise<Job> {
        return api.post<Job>('/jobs', {
            name: params.name,
            upload_id: params.upload_id,
            usage_profile: params.usage_profile || 'prod'
        });
    },

    /**
     * Get job by ID
     */
    async get(jobId: string): Promise<Job> {
        return api.get<Job>(`/jobs/${jobId}`);
    },

    /**
     * List all jobs
     */
    async list(params?: {
        status?: string;
        page?: number;
        page_size?: number;
    }): Promise<Job[]> {
        const query = new URLSearchParams();
        if (params?.status) query.set('status', params.status);
        if (params?.page) query.set('page', params.page.toString());
        if (params?.page_size) query.set('page_size', params.page_size.toString());

        const endpoint = `/jobs${query.toString() ? '?' + query.toString() : ''}`;
        return api.get<Job[]>(endpoint);
    },

    /**
     * Get job results
     */
    async getResults(jobId: string): Promise<CostResult> {
        return api.get<CostResult>(`/jobs/${jobId}/results`);
    },

    /**
     * Delete job
     */
    async delete(jobId: string): Promise<void> {
        return api.delete<void>(`/jobs/${jobId}`);
    }
};

/**
 * Usage Profiles API
 */
export const usageProfilesApi = {
    /**
     * Get all usage profiles
     */
    async list(): Promise<UsageProfile[]> {
        return api.get<UsageProfile[]>('/usage-profiles');
    },

    /**
     * Validate a usage profile
     */
    async validate(profileId: string): Promise<{ valid: boolean }> {
        return api.post<{ valid: boolean }>('/usage-profiles/validate', {
            profile_id: profileId
        });
    }
};

/**
 * Re-export ApiError for error handling
 */
export { ApiError };
