'use client';

import { useState, useEffect } from 'react';
import { settingsService } from '@/services/settingsService';
import type { UsageProfile } from '@/types/usage';

export default function SettingsPage() {
    const [profiles, setProfiles] = useState<UsageProfile[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchProfiles = async () => {
            try {
                const data = await settingsService.getUsageProfiles();
                setProfiles(data);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to load profiles');
            } finally {
                setIsLoading(false);
            }
        };

        fetchProfiles();
    }, []);

    if (isLoading) {
        return (
            <div className="flex items-center justify-center py-12">
                <div className="text-gray-600">Loading settings...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="rounded-lg border border-red-200 bg-red-50 p-4">
                <p className="text-sm text-red-800">{error}</p>
            </div>
        );
    }

    return (
        <div className="space-y-8">
            <div>
                <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
                <p className="mt-2 text-gray-600">
                    Manage usage profiles and application configuration
                </p>
            </div>

            {/* Usage Profiles */}
            <div className="rounded-lg border border-gray-200 bg-white p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Usage Profiles</h2>
                <div className="space-y-4">
                    {profiles.map((profile) => (
                        <div
                            key={profile.id}
                            className="rounded-lg border border-gray-200 p-4 hover:border-blue-300"
                        >
                            <div className="flex items-start justify-between">
                                <div>
                                    <h3 className="font-semibold text-gray-900">{profile.name}</h3>
                                    <p className="text-sm text-gray-600 mt-1">{profile.description}</p>
                                    {profile.isDefault && (
                                        <span className="mt-2 inline-flex items-center rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-800">
                                            Default
                                        </span>
                                    )}
                                </div>
                            </div>
                            {Object.keys(profile.assumptions).length > 0 && (
                                <details className="mt-4">
                                    <summary className="cursor-pointer text-sm font-medium text-gray-700">
                                        View Assumptions
                                    </summary>
                                    <pre className="mt-2 rounded bg-gray-50 p-3 text-xs text-gray-800 overflow-auto">
                                        {JSON.stringify(profile.assumptions, null, 2)}
                                    </pre>
                                </details>
                            )}
                        </div>
                    ))}
                </div>
            </div>

            {/* API Configuration */}
            <div className="rounded-lg border border-gray-200 bg-white p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">API Configuration</h2>
                <div className="space-y-3 text-sm">
                    <div>
                        <span className="font-medium text-gray-700">API URL:</span>
                        <span className="ml-2 text-gray-600">
                            {process.env.NEXT_PUBLIC_API_URL || 'Not configured'}
                        </span>
                    </div>
                    <div>
                        <span className="font-medium text-gray-700">WebSocket URL:</span>
                        <span className="ml-2 text-gray-600">
                            {process.env.NEXT_PUBLIC_WS_URL || 'Not configured'}
                        </span>
                    </div>
                    <div>
                        <span className="font-medium text-gray-700">Max File Size:</span>
                        <span className="ml-2 text-gray-600">
                            {process.env.NEXT_PUBLIC_MAX_FILE_SIZE
                                ? `${parseInt(process.env.NEXT_PUBLIC_MAX_FILE_SIZE) / 1024 / 1024} MB`
                                : 'Not configured'}
                        </span>
                    </div>
                </div>
            </div>
        </div>
    );
}
