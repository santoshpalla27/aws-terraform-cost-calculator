'use client';

import { AlertCircle, Info } from 'lucide-react';
import { formatCurrency } from '@/lib/utils/format';
import type { ResourceCost } from '@/lib/types';
import { cn } from '@/lib/utils/cn';

interface ResourceBreakdownProps {
    resources: ResourceCost[];
    currency: string;
}

export function ResourceBreakdown({ resources, currency }: ResourceBreakdownProps) {
    return (
        <div className="rounded-lg border border-gray-200 bg-white overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
                <h3 className="text-lg font-semibold text-gray-900">Resource Breakdown</h3>
                <p className="text-sm text-gray-600 mt-1">
                    Detailed cost breakdown for each resource
                </p>
            </div>

            <div className="overflow-x-auto">
                <table className="w-full">
                    <thead className="bg-gray-50 border-b border-gray-200">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Resource
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Type
                            </th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Monthly Cost
                            </th>
                            <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Confidence
                            </th>
                            <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Details
                            </th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                        {resources.map((resource) => {
                            const confidenceColor =
                                resource.confidence >= 80
                                    ? 'text-green-600 bg-green-100'
                                    : resource.confidence >= 60
                                        ? 'text-yellow-600 bg-yellow-100'
                                        : 'text-red-600 bg-red-100';

                            return (
                                <tr key={resource.resourceId} className="hover:bg-gray-50">
                                    <td className="px-6 py-4">
                                        <div className="flex items-start gap-2">
                                            <div>
                                                <p className="text-sm font-medium text-gray-900">
                                                    {resource.resourceName}
                                                </p>
                                                <p className="text-xs text-gray-500">{resource.resourceId}</p>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className="inline-flex items-center rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-800">
                                            {resource.resourceType}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-right">
                                        <p className="text-sm font-semibold text-gray-900">
                                            {formatCurrency(resource.monthlyCost, currency)}
                                        </p>
                                    </td>
                                    <td className="px-6 py-4 text-center">
                                        <span
                                            className={cn(
                                                'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
                                                confidenceColor
                                            )}
                                        >
                                            {resource.confidence}%
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-center">
                                        <ResourceDetailsPopover resource={resource} currency={currency} />
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

/**
 * Popover component for resource details
 */
function ResourceDetailsPopover({
    resource,
    currency,
}: {
    resource: ResourceCost;
    currency: string;
}) {
    const [isOpen, setIsOpen] = React.useState(false);

    return (
        <div className="relative inline-block">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="text-blue-600 hover:text-blue-800"
            >
                <Info className="h-5 w-5" />
            </button>

            {isOpen && (
                <>
                    <div
                        className="fixed inset-0 z-10"
                        onClick={() => setIsOpen(false)}
                    />
                    <div className="absolute right-0 z-20 mt-2 w-80 rounded-lg border border-gray-200 bg-white p-4 shadow-lg">
                        {/* Cost Components */}
                        <div className="mb-4">
                            <h4 className="text-sm font-semibold text-gray-900 mb-2">
                                Cost Components
                            </h4>
                            <div className="space-y-2">
                                {resource.breakdown.map((component, index) => (
                                    <div key={index} className="text-xs">
                                        <div className="flex justify-between">
                                            <span className="text-gray-600">{component.name}</span>
                                            <span className="font-medium text-gray-900">
                                                {formatCurrency(component.totalCost, currency)}
                                            </span>
                                        </div>
                                        <p className="text-gray-500">
                                            {component.amount} {component.unit} × {formatCurrency(component.unitPrice, currency)}
                                        </p>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Assumptions */}
                        {resource.assumptions.length > 0 && (
                            <div className="mb-4">
                                <h4 className="text-sm font-semibold text-gray-900 mb-2">
                                    Assumptions
                                </h4>
                                <ul className="space-y-1">
                                    {resource.assumptions.map((assumption, index) => (
                                        <li key={index} className="text-xs text-gray-600">
                                            • {assumption}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}

                        {/* Warnings */}
                        {resource.warnings.length > 0 && (
                            <div>
                                <h4 className="text-sm font-semibold text-yellow-900 mb-2 flex items-center gap-1">
                                    <AlertCircle className="h-4 w-4" />
                                    Warnings
                                </h4>
                                <ul className="space-y-1">
                                    {resource.warnings.map((warning, index) => (
                                        <li key={index} className="text-xs text-yellow-800">
                                            • {warning}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </div>
                </>
            )}
        </div>
    );
}

// Add React import for useState
import React from 'react';
