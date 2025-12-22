// ============================================================================
// Type Definitions for AWS Cost Calculator Frontend
// ============================================================================

// Job Status Enum
export enum JobStatus {
  PENDING = 'PENDING',
  RUNNING = 'RUNNING',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
}

// Job Model
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

// Usage Profile
export interface UsageProfile {
  id: string;
  name: string;
  description: string;
  isDefault: boolean;
  assumptions: Record<string, any>;
}

// Resource Cost
export interface ResourceCost {
  resourceId: string;
  resourceType: string;
  resourceName: string;
  monthlyCost: number;
  confidence: number; // 0-100
  assumptions: string[];
  warnings: string[];
  breakdown: CostComponent[];
}

// Cost Component (e.g., compute, storage, data transfer)
export interface CostComponent {
  name: string;
  amount: number;
  unit: string;
  unitPrice: number;
  totalCost: number;
}

// Service Cost Breakdown
export interface ServiceCost {
  serviceName: string;
  totalCost: number;
  resourceCount: number;
  resources: ResourceCost[];
}

// Cost Estimation Result
export interface CostEstimationResult {
  jobId: string;
  totalMonthlyCost: number;
  overallConfidence: number;
  currency: string;
  services: ServiceCost[];
  warnings: string[];
  metadata: {
    terraformVersion?: string;
    resourceCount: number;
    estimatedAt: string;
  };
}

// Cost Diff (Before vs After)
export interface CostDiff {
  before: CostEstimationResult;
  after: CostEstimationResult;
  delta: number;
  percentageChange: number;
  changedResources: ResourceCost[];
  newResources: ResourceCost[];
  removedResources: ResourceCost[];
}

// API Request Types
export interface CreateJobRequest {
  name: string;
  terraformFiles: File[];
  usageProfileId?: string;
  usageOverrides?: Record<string, any>;
}

export interface JobListParams {
  page?: number;
  pageSize?: number;
  status?: JobStatus;
  sortBy?: 'createdAt' | 'updatedAt' | 'name';
  sortOrder?: 'asc' | 'desc';
}

// API Response Types
export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
}

// WebSocket Message Types
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

// Upload Progress
export interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}
