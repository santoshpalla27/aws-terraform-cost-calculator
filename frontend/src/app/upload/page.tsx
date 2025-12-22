'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { UploadForm } from '@/components/upload/UploadForm';
import { settingsService } from '@/services/settingsService';
import type { UsageProfile } from '@/types/usage';

export default function UploadPage() {
    const router = useRouter();
    const [profiles, setProfiles] = useState<UsageProfile[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchProfiles = async () => {
            try {
                const data = await settingsService.getUsageProfiles();
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
        return (
            <div className="flex items-center justify-center py-12">
                <div className="text-gray-600">Loading usage profiles...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="rounded-lg border border-red-200 bg-red-50 p-4">
                <p className="text-sm text-red-800">{error}</p>
            </div>
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
