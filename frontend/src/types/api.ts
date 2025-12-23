// ============================================================================
// API Contract Types
// ============================================================================

export interface ApiResponse<T> {
    success: boolean;
    data: T | null;
    error: {
        code: string;
        message: string;
        details?: any;
    } | null;
    correlation_id: string;
}

export interface PaginatedResponse<T> {
    data: T[];
    total: number;
    page: number;
    pageSize: number;
    totalPages: number;
}

export interface UploadProgress {
    loaded: number;
    total: number;
    percentage: number;
}

export enum WebSocketMessageType {
    JOB_STATUS_UPDATE = 'JOB_STATUS_UPDATE',
    JOB_PROGRESS_UPDATE = 'JOB_PROGRESS_UPDATE',
    JOB_LOG = 'JOB_LOG',
    ERROR = 'ERROR',
}

export interface WebSocketMessage {
    type: WebSocketMessageType;
    jobId: string;
    payload: any;
    timestamp: string;
}
