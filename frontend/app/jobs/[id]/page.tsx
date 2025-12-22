'use client';

import { use, useEffect, useState } from 'react';
import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';
import { apiClient } from '@/lib/api/api-client';
import { JobStatus } from '@/components/jobs/job-status';
import { CostSummary } from '@/components/cost/cost-summary';
import { ResourceBreakdown } from '@/components/cost/resource-breakdown';
import { LoadingState } from '@/components/common/loading-state';
import { ErrorState } from '@/components/common/error-state';
import type { Job, CostEstimationResult } from '@/lib/types';

export default function JobDetailPage({
    params,
}: {
    params: Promise<{ id: string }>;
}) {
    const { id } = use(params);
    const [job, setJob] = useState<Job | null>(null);
    const [result, setResult] = useState<CostEstimationResult | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchJobData = async () => {
        setIsLoading(true);
        setError(null);

        try {
            const jobData = await apiClient.getJob(id);
            setJob(jobData);

            // Fetch results if job is completed
            if (jobData.status === 'COMPLETED') {
                const resultData = await apiClient.getJobResults(id);
                setResult(resultData);
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to fetch job');
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchJobData();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [id]);

    if (isLoading) {
        return <LoadingState message="Loading job details..." />;
    }

    if (error) {
        return <ErrorState message={error} onRetry={fetchJobData} />;
    }

    if (!job) {
        return <ErrorState message="Job not found" />;
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
            <JobStatus jobId={id} initialJob={job} onRetry={fetchJobData} />

            {/* Cost Results */}
            {result && (
                <>
                    <div className="border-t border-gray-200 pt-6">
                        <h2 className="text-2xl font-bold text-gray-900 mb-6">
                            Cost Estimation Results
                        </h2>
                        <CostSummary result={result} />
                    </div>

                    <div className="border-t border-gray-200 pt-6">
                        <h2 className="text-2xl font-bold text-gray-900 mb-6">
                            Resource Details
                        </h2>
                        <ResourceBreakdown
                            resources={result.services.flatMap((s) => s.resources)}
                            currency={result.currency}
                        />
                    </div>
                </>
            )}
        </div>
    );
}
