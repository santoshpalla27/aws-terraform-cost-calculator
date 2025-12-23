import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig, AxiosResponse } from 'axios';

/**
 * Centralized API Client
 * All backend communication goes through this client
 * NO business logic - pure HTTP communication
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
                // Add auth token if available
                if (typeof window !== 'undefined') {
                    const token = localStorage.getItem('auth_token');
                    if (token && config.headers) {
                        config.headers.Authorization = `Bearer ${token}`;
                    }
                }
                return config;
            },
            (error: AxiosError) => {
                return Promise.reject(error);
            }
        );

        // Response interceptor
        this.client.interceptors.response.use(
            (response: AxiosResponse) => response,
            async (error: AxiosError) => {
                if (error.response) {
                    const status = error.response.status;

                    if (status === 401) {
                        // Unauthorized - clear token and redirect to login if needed
                        if (typeof window !== 'undefined') {
                            localStorage.removeItem('auth_token');
                        }
                    } else if (status === 403) {
                        console.error('Forbidden access');
                    } else if (status >= 500) {
                        console.error('Server error');
                    }
                } else if (error.request) {
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
            const responseData = error.response?.data;
            const errorMessage = responseData?.error?.message || error.message || 'An unexpected error occurred';
            const correlationId = responseData?.correlation_id;

            const enhancedError = new Error(errorMessage);
            (enhancedError as any).correlationId = correlationId;
            (enhancedError as any).errorCode = responseData?.error?.code;

            console.error('[API Error]', {
                message: errorMessage,
                code: responseData?.error?.code,
                correlationId,
                url: error.config?.url,
                status: error.response?.status
            });

            throw enhancedError;
        }
        throw error;
    }

    /**
     * GET request
     */
    async get<T>(url: string, params?: any): Promise<T> {
        try {
            const response = await this.client.get<T>(url, { params });
            return response.data;
        } catch (error) {
            this.handleError(error);
        }
    }

    /**
     * POST request
     */
    async post<T>(url: string, data?: any, config?: any): Promise<T> {
        try {
            const response = await this.client.post<T>(url, data, config);
            return response.data;
        } catch (error) {
            this.handleError(error);
        }
    }

    /**
     * PUT request
     */
    async put<T>(url: string, data?: any): Promise<T> {
        try {
            const response = await this.client.put<T>(url, data);
            return response.data;
        } catch (error) {
            this.handleError(error);
        }
    }

    /**
     * DELETE request
     */
    async delete<T>(url: string): Promise<T> {
        try {
            const response = await this.client.delete<T>(url);
            return response.data;
        } catch (error) {
            this.handleError(error);
        }
    }

    /**
     * Health check
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
