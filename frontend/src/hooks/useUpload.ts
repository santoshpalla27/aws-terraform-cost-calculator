import { useState, useCallback } from 'react';
import { uploadService, type UploadRequest } from '../services/uploadService';
import type { Job } from '../types/job';
import type { UploadProgress } from '../types/api';

/**
 * Custom hook for file upload functionality
 * Manages upload state, progress, and error handling
 */
export function useUpload() {
    const [isUploading, setIsUploading] = useState(false);
    const [progress, setProgress] = useState<UploadProgress | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [uploadedJob, setUploadedJob] = useState<Job | null>(null);

    const upload = useCallback(async (request: UploadRequest) => {
        setIsUploading(true);
        setError(null);
        setProgress(null);
        setUploadedJob(null);

        try {
            const job = await uploadService.uploadFiles(request, (prog) => {
                setProgress(prog);
            });

            setUploadedJob(job);
            return job;
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Upload failed';
            setError(errorMessage);
            throw err;
        } finally {
            setIsUploading(false);
            setProgress(null);
        }
    }, []);

    const reset = useCallback(() => {
        setIsUploading(false);
        setProgress(null);
        setError(null);
        setUploadedJob(null);
    }, []);

    return {
        upload,
        reset,
        isUploading,
        progress,
        error,
        uploadedJob,
    };
}
