'use client';

import { formatCurrency } from '@/utils/formatters';
import { cn } from '@/utils/formatters';
import type { ResourceCost } from '@/types/cost';

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
                                        <div>
                                            <p className="text-sm font-medium text-gray-900">
                                                {resource.resourceName}
                                            </p>
                                            <p className="text-xs text-gray-500">{resource.resourceId}</p>
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
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
