import { apiClient } from './client';
import { UsageProfile } from './types';

/**
 * Usage Profiles API
 * Typed methods for usage profile management
 */
export const usageProfilesApi = {
    /**
     * Get all available usage profiles
     */
    async list(): Promise<UsageProfile[]> {
        const response = await apiClient.get<UsageProfile[]>('/api/usage-profiles');

        if (!response.data) {
            throw new Error(response.error?.message || 'Failed to fetch usage profiles');
        }

        return response.data;
    },

    /**
     * Validate a usage profile
     */
    async validate(profileId: string): Promise<{ valid: boolean }> {
        const response = await apiClient.post<{ valid: boolean }>(
            '/api/usage-profiles/validate',
            { profile_id: profileId }
        );

        if (!response.data) {
            throw new Error(response.error?.message || 'Failed to validate profile');
        }

        return response.data;
    }
};
