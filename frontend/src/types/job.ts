// ============================================================================
// Job-related Types
// ============================================================================

export enum JobStatus {
    PENDING = 'PENDING',
    RUNNING = 'RUNNING',
    COMPLETED = 'COMPLETED',
    FAILED = 'FAILED',
}

export interface Job {
    id: string;
    name: string;
    status: JobStatus;
    createdAt: string;
    updatedAt: string;
    completedAt?: string;
    errorMessage?: string;
    progress?: number; // 0-100
}

export interface JobListParams {
    page?: number;
    pageSize?: number;
    status?: JobStatus;
    sortBy?: 'createdAt' | 'updatedAt' | 'name';
    sortOrder?: 'asc' | 'desc';
}

export interface JobTimeline {
    timestamp: string;
    event: string;
    description: string;
}

export interface JobLogs {
    timestamp: string;
    level: 'info' | 'warn' | 'error';
    message: string;
}

export interface JobStatusData {
    job_id: string;
    status: JobStatus;
    progress: number;
    updated_at: string;
}
