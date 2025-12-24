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

interface UploadResponseData {
    upload: {
        upload_id: string;
        user_id: string;
        filename: string;
        file_count: number;
        total_size: number;
        created_at: string;
    };
    message: string;
}

export const uploadService = {
    /**
     * Upload Terraform files and create a new job
     * Two-step process:
     * 1. Upload files to /api/uploads
     * 2. Create job with /api/jobs using upload_id
     */
    async uploadFiles(
        request: UploadRequest,
        onProgress?: (progress: UploadProgress) => void
    ): Promise<Job> {
        // Step 1: Upload files
        const formData = new FormData();
        request.files.forEach((file) => {
            formData.append('files', file);
        });

        const uploadResponse = await apiClient.post<UploadResponseData>(
            '/uploads',
            formData,
            {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
                onUploadProgress: (progressEvent: any) => {
                    if (onProgress && progressEvent.total) {
                        // Show 0-80% for file upload
                        const percentage = Math.round(
                            (progressEvent.loaded * 80) / progressEvent.total
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

        if (!uploadResponse || !uploadResponse.upload) {
            throw new Error('Failed to upload files - invalid response');
        }

        const uploadId = uploadResponse.upload.upload_id;

        // Step 2: Create job with upload_id
        if (onProgress) {
            onProgress({ loaded: 80, total: 100, percentage: 80 });
        }

        const jobResponse = await apiClient.post<ApiResponse<Job>>(
            '/jobs',
            {
                upload_id: uploadId,
                name: request.name,
                usage_profile_id: request.usageProfileId || null,
            }
        );

        if (!jobResponse.success || !jobResponse.data) {
            throw new Error(jobResponse.error?.message || 'Failed to create job');
        }

        if (onProgress) {
            onProgress({ loaded: 100, total: 100, percentage: 100 });
        }

        return jobResponse.data;
    },
};
