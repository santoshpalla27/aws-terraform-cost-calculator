// ============================================================================
// Cost-related Types
// ============================================================================

export interface CostComponent {
    name: string;
    amount: number;
    unit: string;
    unitPrice: number;
    totalCost: number;
}

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

export interface ServiceCost {
    serviceName: string;
    totalCost: number;
    resourceCount: number;
    resources: ResourceCost[];
}

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

export interface CostDiff {
    before: CostEstimationResult;
    after: CostEstimationResult;
    delta: number;
    percentageChange: number;
    changedResources: ResourceCost[];
    newResources: ResourceCost[];
    removedResources: ResourceCost[];
}
