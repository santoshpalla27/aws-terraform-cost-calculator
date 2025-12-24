import { useState, useEffect } from 'react';
import { usageProfilesApi, ApiError } from '../api';
import { UsageProfile } from '../api/types';

/**
 * Hook for fetching usage profiles
 * 
 * NO direct API calls in components
 */
export function useUsageProfiles() {
    const [profiles, setProfiles] = useState<UsageProfile[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [correlationId, setCorrelationId] = useState<string | null>(null);

    useEffect(() => {
        const fetchProfiles = async () => {
            try {
                const data = await usageProfilesApi.list();
                setProfiles(data);
                setError(null);
            } catch (err) {
                const apiError = err as ApiError;
                setError(apiError.message);
                setCorrelationId(apiError.correlationId);
            } finally {
                setIsLoading(false);
            }
        };

        fetchProfiles();
    }, []);

    return {
        profiles,
        isLoading,
        error,
        correlationId
    };
}
