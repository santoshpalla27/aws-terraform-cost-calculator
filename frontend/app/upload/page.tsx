'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { UploadForm } from '@/components/upload/upload-form';
import { apiClient } from '@/lib/api/api-client';
import { LoadingState } from '@/components/common/loading-state';
import { ErrorState } from '@/components/common/error-state';
import type { UsageProfile } from '@/lib/types';

export default function UploadPage() {
    const router = useRouter();
    const [profiles, setProfiles] = useState<UsageProfile[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchProfiles = async () => {
            try {
                const data = await apiClient.getUsageProfiles();
                setProfiles(data);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to load profiles');
            } finally {
                setIsLoading(false);
            }
        };

        fetchProfiles();
    }, []);

    const handleSuccess = (jobId: string) => {
        router.push(`/jobs/${jobId}`);
    };

    if (isLoading) {
        return <LoadingState message="Loading usage profiles..." />;
    }

    if (error) {
        return (
            <ErrorState
                message={error}
                onRetry={() => window.location.reload()}
            />
        );
    }

    return (
        <div className="mx-auto max-w-3xl">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900">Upload Terraform Files</h1>
                <p className="mt-2 text-gray-600">
                    Upload your Terraform configuration files to estimate AWS infrastructure costs
                </p>
            </div>

            <div className="rounded-lg border border-gray-200 bg-white p-8 shadow-sm">
                <UploadForm usageProfiles={profiles} onSuccess={handleSuccess} />
            </div>
        </div>
    );
}
