'use client';

import { use } from 'react';
import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';
import { useJobStatus } from '@/hooks/useJobStatus';
import { JobStatus } from '@/components/jobs/JobStatus';
import { CostResults } from '@/components/cost/CostResults';

export default function JobDetailPage({
    params,
}: {
    params: Promise<{ jobId: string }>;
}) {
    const { jobId } = use(params);
    const { job, isLoading, error, retry } = useJobStatus(jobId);

    if (isLoading) {
        return (
            <div className="flex items-center justify-center py-12">
                <div className="text-gray-600">Loading job details...</div>
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

    if (!job) {
        return (
            <div className="rounded-lg border border-gray-200 bg-gray-50 p-8 text-center">
                <p className="text-gray-600">Job not found</p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Back Button */}
            <Link
                href="/jobs"
                className="inline-flex items-center gap-2 text-sm font-medium text-gray-600 hover:text-gray-900"
            >
                <ArrowLeft className="h-4 w-4" />
                Back to Jobs
            </Link>

            {/* Job Status */}
            <JobStatus job={job} onRetry={retry} />

            {/* Cost Results */}
            {job.status === 'COMPLETED' && <CostResults jobId={jobId} />}
        </div>
    );
}
