'use client';

import { useState, useCallback } from 'react';
import { Upload, FileCode, CheckCircle, XCircle } from 'lucide-react';
import { apiClient } from '@/lib/api/api-client';
import { validateFiles } from '@/lib/utils/file-validator';
import { formatFileSize } from '@/lib/utils/format';
import type { CreateJobRequest, UploadProgress, UsageProfile } from '@/lib/types';
import { cn } from '@/lib/utils/cn';

interface UploadFormProps {
    usageProfiles: UsageProfile[];
    onSuccess: (jobId: string) => void;
}

export function UploadForm({ usageProfiles, onSuccess }: UploadFormProps) {
    const [files, setFiles] = useState<File[]>([]);
    const [jobName, setJobName] = useState('');
    const [selectedProfile, setSelectedProfile] = useState<string>('');
    const [isDragging, setIsDragging] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const [uploadProgress, setUploadProgress] = useState<UploadProgress | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState(false);

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    }, []);

    const handleDragLeave = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
    }, []);

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
        setError(null);

        const droppedFiles = Array.from(e.dataTransfer.files);
        const validation = validateFiles(droppedFiles);

        if (!validation.valid) {
            setError(validation.error || 'Invalid files');
            return;
        }

        setFiles(droppedFiles);
    }, []);

    const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        setError(null);
        const selectedFiles = e.target.files ? Array.from(e.target.files) : [];
        const validation = validateFiles(selectedFiles);

        if (!validation.valid) {
            setError(validation.error || 'Invalid files');
            return;
        }

        setFiles(selectedFiles);
    }, []);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        setSuccess(false);

        if (files.length === 0) {
            setError('Please select at least one file');
            return;
        }

        if (!jobName.trim()) {
            setError('Please enter a job name');
            return;
        }

        setIsUploading(true);

        try {
            const request: CreateJobRequest = {
                name: jobName.trim(),
                terraformFiles: files,
                usageProfileId: selectedProfile || undefined,
            };

            const job = await apiClient.createJob(request, (progress) => {
                setUploadProgress(progress);
            });

            setSuccess(true);
            setUploadProgress(null);

            // Reset form
            setTimeout(() => {
                onSuccess(job.id);
            }, 1000);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to upload files');
        } finally {
            setIsUploading(false);
        }
    };

    const removeFile = (index: number) => {
        setFiles((prev) => prev.filter((_, i) => i !== index));
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-6">
            {/* Job Name */}
            <div>
                <label htmlFor="jobName" className="block text-sm font-medium text-gray-700">
                    Job Name
                </label>
                <input
                    type="text"
                    id="jobName"
                    value={jobName}
                    onChange={(e) => setJobName(e.target.value)}
                    className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    placeholder="e.g., Production Infrastructure Cost Estimate"
                    disabled={isUploading}
                />
            </div>

            {/* Usage Profile */}
            <div>
                <label htmlFor="profile" className="block text-sm font-medium text-gray-700">
                    Usage Profile (Optional)
                </label>
                <select
                    id="profile"
                    value={selectedProfile}
                    onChange={(e) => setSelectedProfile(e.target.value)}
                    className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    disabled={isUploading}
                >
                    <option value="">Default Profile</option>
                    {usageProfiles.map((profile) => (
                        <option key={profile.id} value={profile.id}>
                            {profile.name} - {profile.description}
                        </option>
                    ))}
                </select>
            </div>

            {/* File Upload Area */}
            <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                    Terraform Files
                </label>
                <div
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                    className={cn(
                        'relative rounded-lg border-2 border-dashed p-8 text-center transition-colors',
                        isDragging
                            ? 'border-blue-500 bg-blue-50'
                            : 'border-gray-300 bg-gray-50 hover:border-gray-400',
                        isUploading && 'pointer-events-none opacity-50'
                    )}
                >
                    <input
                        type="file"
                        id="fileInput"
                        multiple
                        accept=".tf,.tfvars,.zip"
                        onChange={handleFileSelect}
                        className="hidden"
                        disabled={isUploading}
                    />
                    <Upload className="mx-auto h-12 w-12 text-gray-400" />
                    <p className="mt-2 text-sm text-gray-600">
                        Drag and drop your Terraform files here, or{' '}
                        <label
                            htmlFor="fileInput"
                            className="cursor-pointer font-medium text-blue-600 hover:text-blue-500"
                        >
                            browse
                        </label>
                    </p>
                    <p className="mt-1 text-xs text-gray-500">
                        Supported: .tf, .tfvars, .zip (max 50MB)
                    </p>
                </div>
            </div>

            {/* Selected Files */}
            {files.length > 0 && (
                <div className="space-y-2">
                    <p className="text-sm font-medium text-gray-700">Selected Files:</p>
                    {files.map((file, index) => (
                        <div
                            key={index}
                            className="flex items-center justify-between rounded-md border border-gray-200 bg-white px-4 py-2"
                        >
                            <div className="flex items-center gap-3">
                                <FileCode className="h-5 w-5 text-blue-600" />
                                <div>
                                    <p className="text-sm font-medium text-gray-900">{file.name}</p>
                                    <p className="text-xs text-gray-500">{formatFileSize(file.size)}</p>
                                </div>
                            </div>
                            {!isUploading && (
                                <button
                                    type="button"
                                    onClick={() => removeFile(index)}
                                    className="text-red-600 hover:text-red-800"
                                >
                                    <XCircle className="h-5 w-5" />
                                </button>
                            )}
                        </div>
                    ))}
                </div>
            )}

            {/* Upload Progress */}
            {uploadProgress && (
                <div className="space-y-2">
                    <div className="flex justify-between text-sm text-gray-600">
                        <span>Uploading...</span>
                        <span>{uploadProgress.percentage}%</span>
                    </div>
                    <div className="h-2 w-full overflow-hidden rounded-full bg-gray-200">
                        <div
                            className="h-full bg-blue-600 transition-all duration-300"
                            style={{ width: `${uploadProgress.percentage}%` }}
                        />
                    </div>
                </div>
            )}

            {/* Error Message */}
            {error && (
                <div className="rounded-md bg-red-50 border border-red-200 p-4">
                    <div className="flex items-center gap-2">
                        <XCircle className="h-5 w-5 text-red-600" />
                        <p className="text-sm text-red-800">{error}</p>
                    </div>
                </div>
            )}

            {/* Success Message */}
            {success && (
                <div className="rounded-md bg-green-50 border border-green-200 p-4">
                    <div className="flex items-center gap-2">
                        <CheckCircle className="h-5 w-5 text-green-600" />
                        <p className="text-sm text-green-800">
                            Job created successfully! Redirecting...
                        </p>
                    </div>
                </div>
            )}

            {/* Submit Button */}
            <button
                type="submit"
                disabled={isUploading || files.length === 0 || !jobName.trim()}
                className="w-full rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            >
                {isUploading ? 'Uploading...' : 'Create Cost Estimation Job'}
            </button>
        </form>
    );
}
