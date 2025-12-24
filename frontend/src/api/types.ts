// ============================================================================
// Generated TypeScript Types from OpenAPI Contract
// DO NOT EDIT - Generated from api-contract/openapi.yaml
// ============================================================================

/**
 * Canonical job status enumeration
 * State transitions: IDLE → UPLOADING → CREATED → PLANNING → PARSING → ENRICHING → COSTING → COMPLETED/FAILED
 */
export enum JobStatus {
    IDLE = 'IDLE',
    UPLOADING = 'UPLOADING',
    CREATED = 'CREATED',
    PLANNING = 'PLANNING',
    PARSING = 'PARSING',
    ENRICHING = 'ENRICHING',
    COSTING = 'COSTING',
    COMPLETED = 'COMPLETED',
    FAILED = 'FAILED'
}

/**
 * Canonical API Response envelope
 * All endpoints MUST return this structure
 */
export interface ApiResponse<T> {
    success: boolean;
    data: T | null;
    error: ApiError | null;
    correlation_id: string;
}

/**
 * Error object
 */
export interface ApiError {
    code: string;
    message: string;
    details?: any;
}

/**
 * Job model
 */
export interface Job {
    job_id: string;
    upload_id: string;
    user_id: string;
    name: string;
    status: JobStatus;
    progress: number; // 0-100
    current_stage: string | null;
    created_at: string;
    updated_at: string;
    completed_at: string | null;
    errors: string[];
    error_message: string | null;
}

/**
 * Usage Profile model
 */
export interface UsageProfile {
    id: string;
    name: string;
    description: string;
    is_default: boolean;
    assumptions?: {
        hours_per_day?: number;
        days_per_month?: number;
        availability_zone_count?: number;
        [key: string]: any;
    };
}

/**
 * Cost Result model
 */
export interface CostResult {
    job_id: string;
    total_monthly_cost: number;
    currency: string;
    breakdown: ResourceCost[];
    confidence: number; // 0-1
    metadata?: {
        terraform_version?: string;
        resource_count?: number;
        estimated_at?: string;
    };
}

/**
 * Resource Cost model
 */
export interface ResourceCost {
    resource_name: string;
    resource_type: string;
    service: string;
    monthly_cost: number;
    details?: any;
}

/**
 * Runtime validation helper
 */
export function isApiResponse<T>(obj: any): obj is ApiResponse<T> {
    return (
        obj !== null &&
        typeof obj === 'object' &&
        'success' in obj &&
        'data' in obj &&
        'error' in obj &&
        'correlation_id' in obj &&
        typeof obj.success === 'boolean' &&
        typeof obj.correlation_id === 'string'
    );
}

/**
 * Validate job status is valid
 */
export function isValidJobStatus(status: string): status is JobStatus {
    return Object.values(JobStatus).includes(status as JobStatus);
}
