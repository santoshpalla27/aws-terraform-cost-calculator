'use client';

import { JobList } from '@/components/jobs/JobList';
import { useRouter } from 'next/navigation';

export default function JobsPage() {
    const router = useRouter();

    const handleJobClick = (jobId: string) => {
        router.push(`/jobs/${jobId}`);
    };

    return (
        <div>
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900">Cost Estimation Jobs</h1>
                <p className="mt-2 text-gray-600">
                    View and manage your cost estimation jobs
                </p>
            </div>

            <JobList onJobClick={handleJobClick} />
        </div>
    );
}
