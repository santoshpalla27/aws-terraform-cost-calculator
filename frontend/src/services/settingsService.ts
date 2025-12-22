import { apiClient } from './apiClient';
import type { ApiResponse } from '../types/api';
import type { UsageProfile } from '../types/usage';

/**
 * Settings Service
 * Handles usage profiles and application settings
 * NO business logic - pure API communication
 */

export const settingsService = {
    /**
     * Get all available usage profiles
     */
    async getUsageProfiles(): Promise<UsageProfile[]> {
        const response = await apiClient.get<ApiResponse<UsageProfile[]>>(
            '/api/usage-profiles'
        );

        if (!response.success || !response.data) {
            throw new Error(response.error?.message || 'Failed to fetch profiles');
        }

        return response.data;
    },

    /**
     * Get a specific usage profile by ID
     */
    async getUsageProfile(profileId: string): Promise<UsageProfile> {
        const response = await apiClient.get<ApiResponse<UsageProfile>>(
            `/api/usage-profiles/${profileId}`
        );

        if (!response.success || !response.data) {
            throw new Error(response.error?.message || 'Failed to fetch profile');
        }

        return response.data;
    },
};
