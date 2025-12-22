import axios, {
    AxiosInstance,
    AxiosError,
    InternalAxiosRequestConfig,
    AxiosResponse,
} from 'axios';
import type {
    Job,
    JobListParams,
    PaginatedResponse,
    ApiResponse,
    UsageProfile,
    CostEstimationResult,
    CreateJobRequest,
    UploadProgress,
} from '../types';

/**
 * Centralized API Client for AWS Cost Calculator
 * Handles all HTTP communication with the API Gateway
 */
class ApiClient {
    private client: AxiosInstance;
    private baseURL: string;

    constructor() {
        this.baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

        this.client = axios.create({
            baseURL: this.baseURL,
            timeout: 30000,
            headers: {
                'Content-Type': 'application/json',
            },
        });

        this.setupInterceptors();
    }

    /**
     * Setup request and response interceptors
     */
    private setupInterceptors() {
        // Request interceptor
        this.client.interceptors.request.use(
            (config: InternalAxiosRequestConfig) => {
                // Add any auth tokens here if needed
                // const token = localStorage.getItem('token');
                // if (token) {
                //   config.headers.Authorization = `Bearer ${token}`;
                // }
                return config;
            },
            (error: AxiosError) => {
                return Promise.reject(error);
            }
        );

        // Response interceptor
        this.client.interceptors.response.use(
            (response: AxiosResponse) => {
                return response;
            },
            async (error: AxiosError) => {
                if (error.response) {
                    // Server responded with error status
                    const status = error.response.status;

                    if (status === 401) {
                        // Handle unauthorized - redirect to login if needed
                        console.error('Unauthorized access');
                    } else if (status === 403) {
                        console.error('Forbidden access');
                    } else if (status >= 500) {
                        console.error('Server error');
                    }
                } else if (error.request) {
                    // Request made but no response
                    console.error('Network error - no response from server');
                }

                return Promise.reject(error);
            }
        );
    }

    /**
     * Generic error handler
     */
    private handleError(error: unknown): never {
        if (axios.isAxiosError(error)) {
            const message =
                error.response?.data?.error?.message ||
                error.message ||
                'An unexpected error occurred';
            throw new Error(message);
        }
        throw error;
    }

    // ========================================================================
    // Job Management APIs
    // ========================================================================

    /**
     * Create a new cost estimation job
     */
    async createJob(
        request: CreateJobRequest,
        onProgress?: (progress: UploadProgress) => void
    ): Promise<Job> {
        try {
            const formData = new FormData();
            formData.append('name', request.name);

            if (request.usageProfileId) {
                formData.append('usageProfileId', request.usageProfileId);
            }

            if (request.usageOverrides) {
                formData.append('usageOverrides', JSON.stringify(request.usageOverrides));
            }

            request.terraformFiles.forEach((file) => {
                formData.append('files', file);
            });

            const response = await this.client.post<ApiResponse<Job>>('/api/jobs', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
                onUploadProgress: (progressEvent) => {
                    if (onProgress && progressEvent.total) {
                        const percentage = Math.round(
                            (progressEvent.loaded * 100) / progressEvent.total
                        );
                        onProgress({
                            loaded: progressEvent.loaded,
                            total: progressEvent.total,
                            percentage,
                        });
                    }
                },
            });

            if (!response.data.success || !response.data.data) {
                throw new Error(response.data.error?.message || 'Failed to create job');
            }

            return response.data.data;
        } catch (error) {
            this.handleError(error);
        }
    }

    /**
     * Get list of jobs with pagination and filtering
     */
    async getJobs(params?: JobListParams): Promise<PaginatedResponse<Job>> {
        try {
            const response = await this.client.get<ApiResponse<PaginatedResponse<Job>>>(
                '/api/jobs',
                { params }
            );

            if (!response.data.success || !response.data.data) {
                throw new Error(response.data.error?.message || 'Failed to fetch jobs');
            }

            return response.data.data;
        } catch (error) {
            this.handleError(error);
        }
    }

    /**
     * Get a specific job by ID
     */
    async getJob(jobId: string): Promise<Job> {
        try {
            const response = await this.client.get<ApiResponse<Job>>(`/api/jobs/${jobId}`);

            if (!response.data.success || !response.data.data) {
                throw new Error(response.data.error?.message || 'Failed to fetch job');
            }

            return response.data.data;
        } catch (error) {
            this.handleError(error);
        }
    }

    /**
     * Get cost estimation results for a job
     */
    async getJobResults(jobId: string): Promise<CostEstimationResult> {
        try {
            const response = await this.client.get<ApiResponse<CostEstimationResult>>(
                `/api/jobs/${jobId}/results`
            );

            if (!response.data.success || !response.data.data) {
                throw new Error(response.data.error?.message || 'Failed to fetch results');
            }

            return response.data.data;
        } catch (error) {
            this.handleError(error);
        }
    }

    /**
     * Retry a failed job
     */
    async retryJob(jobId: string): Promise<Job> {
        try {
            const response = await this.client.post<ApiResponse<Job>>(
                `/api/jobs/${jobId}/retry`
            );

            if (!response.data.success || !response.data.data) {
                throw new Error(response.data.error?.message || 'Failed to retry job');
            }

            return response.data.data;
        } catch (error) {
            this.handleError(error);
        }
    }

    // ========================================================================
    // Usage Profile APIs
    // ========================================================================

    /**
     * Get available usage profiles
     */
    async getUsageProfiles(): Promise<UsageProfile[]> {
        try {
            const response = await this.client.get<ApiResponse<UsageProfile[]>>(
                '/api/usage-profiles'
            );

            if (!response.data.success || !response.data.data) {
                throw new Error(response.data.error?.message || 'Failed to fetch profiles');
            }

            return response.data.data;
        } catch (error) {
            this.handleError(error);
        }
    }

    /**
     * Get a specific usage profile
     */
    async getUsageProfile(profileId: string): Promise<UsageProfile> {
        try {
            const response = await this.client.get<ApiResponse<UsageProfile>>(
                `/api/usage-profiles/${profileId}`
            );

            if (!response.data.success || !response.data.data) {
                throw new Error(response.data.error?.message || 'Failed to fetch profile');
            }

            return response.data.data;
        } catch (error) {
            this.handleError(error);
        }
    }

    // ========================================================================
    // Health Check
    // ========================================================================

    /**
     * Check API health
     */
    async healthCheck(): Promise<boolean> {
        try {
            const response = await this.client.get('/health');
            return response.status === 200;
        } catch (error) {
            return false;
        }
    }
}

// Export singleton instance
export const apiClient = new ApiClient();
