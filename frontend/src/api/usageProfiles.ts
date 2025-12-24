import { api } from './client';
import { UsageProfile } from './types';

/**
 * Usage Profiles API
 * Typed methods for usage profile management
 */
export const usageProfilesApi = {
    /**
     * Get all usage profiles
     */
    async list(): Promise<UsageProfile[]> {
        return await api.get<UsageProfile[]>('/usage-profiles');
    },

    /**
     * Get a specific usage profile by ID
     */
    async get(profileId: string): Promise<UsageProfile> {
        return await api.get<UsageProfile>(`/usage-profiles/${profileId}`);
    },

    /**
     * Validate a usage profile
     */
    async validate(profile: UsageProfile): Promise<{ valid: boolean; errors?: string[] }> {
        return await api.post<{ valid: boolean; errors?: string[] }>('/usage-profiles/validate', profile);
    }
};
