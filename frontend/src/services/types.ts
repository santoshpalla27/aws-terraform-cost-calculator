/**
 * Type definitions for the Terraform Cost Estimator
 */

export interface Resource {
    resource_id: string;
    resource_type: string;
    service: string;
    region: string;
    total_monthly_cost: number;
    compute_cost: number;
    storage_cost: number;
    network_cost: number;
    other_cost: number;
    confidence_score: number;
    usage_profile: string;
    cost_drivers?: CostDriver[];
    assumptions?: Assumption[];
}

export interface CostDriver {
    component: string;
    cost: number;
    percentage: number;
    description: string;
}

export interface Assumption {
    parameter: string;
    value: number | string;
    source: string;
    description: string;
}

export interface ServiceCost {
    service: string;
    total_cost: number;
    resource_count: number;
}

export interface RegionCost {
    region: string;
    total_cost: number;
    resource_count: number;
    services: Record<string, number>;
}

export interface CostEstimate {
    total_monthly_cost: number;
    confidence_score: number;
    profile: string;
    by_resource: Resource[];
    by_service: ServiceCost[];
    by_region: RegionCost[];
    timestamp: string;
}

export interface Job {
    job_id: string;
    created_at: string;
    profile: string;
    total_monthly_cost: number;
    confidence_score: number;
    resource_count: number;
    status: string;
}

export type JobStage = 'parsing' | 'enriching' | 'modeling' | 'calculating' | 'complete';

export interface UsageOverrides {
    uptime_hours_per_month?: number;
    network_out_gb?: number;
    storage_gb?: number;
    [key: string]: number | undefined;
}
