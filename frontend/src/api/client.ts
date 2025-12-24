import { ApiResponse, isApiResponse } from './types';

/**
 * SINGLE API ENTRY POINT
 * 
 * CRITICAL RULES:
 * - ALL backend communication goes through this client
 * - NO fetch() calls outside this file
 * - Runtime validation on EVERY response
 * - Errors include correlation_id
 */

// Use relative path - proxied by nginx
const API_BASE_URL = '/api';

/**
 * Enhanced error with correlation_id
 */
export class ApiError extends Error {
    constructor(
        message: string,
        public correlationId: string,
        public errorCode?: string,
        public details?: any
    ) {
        super(message);
        this.name = 'ApiError';
    }
}

/**
 * HTTP request options
 */
interface RequestOptions {
    method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
    body?: any;
    headers?: Record<string, string>;
}

/**
 * Core API client
 * 
 * This is the ONLY function that calls fetch()
 */
async function apiRequest<T>(
    endpoint: string,
    options: RequestOptions = {}
): Promise<T> {
    const { method = 'GET', body, headers = {} } = options;

    // Build request
    const url = `${API_BASE_URL}${endpoint}`;
    const requestHeaders: Record<string, string> = {
        'Content-Type': 'application/json',
        ...headers
    };

    // Add auth token if available
    if (typeof window !== 'undefined') {
        const token = localStorage.getItem('auth_token');
        if (token) {
            requestHeaders['Authorization'] = `Bearer ${token}`;
        }
    }

    try {
        console.log(`[API] ${method} ${endpoint}`);

        const response = await fetch(url, {
            method,
            headers: requestHeaders,
            body: body ? JSON.stringify(body) : undefined
        });

        // Parse response
        const data = await response.json();

        // CRITICAL: Runtime validation
        if (!isApiResponse<T>(data)) {
            console.error('[API] Contract violation:', data);
            throw new Error('API response does not match contract');
        }

        // Check success flag
        if (!data.success) {
            const error = data.error || { code: 'UNKNOWN', message: 'Request failed' };

            console.error('[API] Request failed:', {
                endpoint,
                error,
                correlationId: data.correlation_id
            });

            throw new ApiError(
                error.message,
                data.correlation_id,
                error.code,
                error.details
            );
        }

        // Return data payload
        if (data.data === null) {
            throw new ApiError(
                'Response data is null',
                data.correlation_id
            );
        }

        return data.data;

    } catch (error) {
        // Network or parsing errors
        if (error instanceof ApiError) {
            throw error;
        }

        console.error('[API] Request error:', error);
        throw new ApiError(
            error instanceof Error ? error.message : 'Network error',
            'unknown'
        );
    }
}

/**
 * Public API methods
 * These are the ONLY exported functions
 */
export const api = {
    /**
     * GET request
     */
    get<T>(endpoint: string): Promise<T> {
        return apiRequest<T>(endpoint, { method: 'GET' });
    },

    /**
     * POST request
     */
    post<T>(endpoint: string, body?: any): Promise<T> {
        return apiRequest<T>(endpoint, { method: 'POST', body });
    },

    /**
     * PUT request
     */
    put<T>(endpoint: string, body?: any): Promise<T> {
        return apiRequest<T>(endpoint, { method: 'PUT', body });
    },

    /**
     * DELETE request
     */
    delete<T>(endpoint: string): Promise<T> {
        return apiRequest<T>(endpoint, { method: 'DELETE' });
    }
};

