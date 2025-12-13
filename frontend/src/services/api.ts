/**
 * API service for backend integration
 */

import axios from 'axios';
import type { CostEstimate, Job, Resource, ServiceCost, RegionCost } from './types';

const api = axios.create({
    baseURL: '/api/v1',
    headers: {
        'Content-Type': 'application/json'
    }
});

export class CostEstimationAPI {
    /**
     * Upload and parse Terraform plan
     */
    async parsePlan(file: File): Promise<{ nrg: any }> {
        const formData = new FormData();
        formData.append('file', file);

        const response = await axios.post('/api/v1/parse', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });

        return response.data;
    }

    /**
     * Enrich resources with AWS metadata
     */
    async enrichResources(nrg: any): Promise<{ enriched_nrg: any }> {
        const response = await api.post('/enrich', { nrg });
        return response.data;
    }

    /**
     * Generate usage scenarios
     */
    async generateScenarios(
        resource: any,
        profile: string,
        overrides?: Record<string, any>
    ): Promise<any> {
        const response = await api.post('/scenarios', {
            resource,
            profile,
            overrides
        });
        return response.data;
    }

    /**
     * Calculate costs
     */
    async calculateCosts(
        resources: any[],
        pricing: any[],
        usage: any[]
    ): Promise<CostEstimate> {
        const response = await api.post('/estimate', {
            resources,
            pricing_data: pricing,
            usage_data: usage
        });
        return response.data;
    }

    /**
     * Store results
     */
    async storeResults(
        estimate: CostEstimate,
        userId?: string
    ): Promise<{ job_id: string }> {
        const response = await api.post('/store', {
            estimate,
            user_id: userId
        });
        return response.data;
    }

    /**
     * Get job by ID
     */
    async getJob(jobId: string): Promise<Job> {
        const response = await api.get(`/jobs/${jobId}`);
        return response.data;
    }

    /**
     * List recent jobs
     */
    async listJobs(userId?: string, limit: number = 10): Promise<Job[]> {
        const params = new URLSearchParams();
        if (userId) params.append('user_id', userId);
        params.append('limit', limit.toString());

        const response = await api.get(`/jobs?${params}`);
        return response.data;
    }

    /**
     * Get job resources
     */
    async getJobResources(jobId: string): Promise<Resource[]> {
        const response = await api.get(`/jobs/${jobId}/resources`);
        return response.data;
    }

    /**
     * Get job services
     */
    async getJobServices(jobId: string): Promise<ServiceCost[]> {
        const response = await api.get(`/jobs/${jobId}/services`);
        return response.data;
    }

    /**
     * Get job regions
     */
    async getJobRegions(jobId: string): Promise<RegionCost[]> {
        const response = await api.get(`/jobs/${jobId}/regions`);
        return response.data;
    }

    /**
     * Compare two jobs
     */
    async compareJobs(jobId1: string, jobId2: string): Promise<any> {
        const response = await api.get(`/compare?job_id_1=${jobId1}&job_id_2=${jobId2}`);
        return response.data;
    }
}

export const costAPI = new CostEstimationAPI();
