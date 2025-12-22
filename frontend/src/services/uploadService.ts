import { apiClient } from './apiClient';
import type { ApiResponse } from '../types/api';
import type { Job } from '../types/job';
import type { UploadProgress } from '../types/api';

/**
 * Upload Service
 * Handles file uploads to API Gateway
 * NO business logic - pure API communication
 */

export interface UploadRequest {
    name: string;
    files: File[];
    usageProfileId?: string;
    usageOverrides?: Record<string, any>;
}

export const uploadService = {
    /**
     * Upload Terraform files and create a new job
     */
    async uploadFiles(
        request: UploadRequest,
        onProgress?: (progress: UploadProgress) => void
    ): Promise<Job> {
        const formData = new FormData();
        formData.append('name', request.name);

        if (request.usageProfileId) {
            formData.append('usageProfileId', request.usageProfileId);
        }

        if (request.usageOverrides) {
            formData.append('usageOverrides', JSON.stringify(request.usageOverrides));
        }

        request.files.forEach((file) => {
            formData.append('files', file);
        });

        const response = await apiClient.post<ApiResponse<Job>>(
            '/api/jobs',
            formData,
            {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
                onUploadProgress: (progressEvent: any) => {
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
            }
        );

        if (!response.success || !response.data) {
            throw new Error(response.error?.message || 'Failed to upload files');
        }

        return response.data;
    },
};
