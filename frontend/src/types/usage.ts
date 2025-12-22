// ============================================================================
// Usage Profile Types
// ============================================================================

export interface UsageProfile {
    id: string;
    name: string;
    description: string;
    isDefault: boolean;
    assumptions: Record<string, any>;
}

export interface UsageOverride {
    resourceType: string;
    parameter: string;
    value: any;
}

export interface UsageAssumptions {
    profileId?: string;
    overrides?: UsageOverride[];
}
