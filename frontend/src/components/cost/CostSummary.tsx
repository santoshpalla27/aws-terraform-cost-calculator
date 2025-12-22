'use client';

import { DollarSign, AlertTriangle } from 'lucide-react';
import { formatCurrency, formatPercentage } from '@/utils/formatters';
import { cn } from '@/utils/formatters';
import type { CostEstimationResult } from '@/types/cost';

interface CostSummaryProps {
    result: CostEstimationResult;
}

export function CostSummary({ result }: CostSummaryProps) {
    const confidenceColor =
        result.overallConfidence >= 80
            ? 'text-green-600'
            : result.overallConfidence >= 60
                ? 'text-yellow-600'
                : 'text-red-600';

    return (
        <div className="space-y-6">
            {/* Total Cost Card */}
            <div className="rounded-lg border-2 border-blue-200 bg-gradient-to-br from-blue-50 to-white p-8">
                <div className="flex items-center justify-between">
                    <div>
                        <p className="text-sm font-medium text-gray-600">Estimated Monthly Cost</p>
                        <p className="mt-2 text-4xl font-bold text-gray-900">
                            {formatCurrency(result.totalMonthlyCost, result.currency)}
                        </p>
                        <p className="mt-2 text-sm text-gray-500">
                            Based on {result.metadata.resourceCount} resources
                        </p>
                    </div>
                    <div className="rounded-full bg-blue-100 p-4">
                        <DollarSign className="h-12 w-12 text-blue-600" />
                    </div>
                </div>
            </div>

            {/* Confidence Score */}
            <div className="rounded-lg border border-gray-200 bg-white p-6">
                <div className="flex items-center justify-between">
                    <div>
                        <p className="text-sm font-medium text-gray-700">Confidence Score</p>
                        <p className={cn('mt-1 text-2xl font-bold', confidenceColor)}>
                            {formatPercentage(result.overallConfidence, 0)}
                        </p>
                    </div>
                </div>
            </div>

            {/* Warnings */}
            {result.warnings.length > 0 && (
                <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-6">
                    <div className="flex items-start gap-3">
                        <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
                        <div className="flex-1">
                            <h4 className="font-semibold text-yellow-900">Warnings</h4>
                            <ul className="mt-2 space-y-1">
                                {result.warnings.map((warning, index) => (
                                    <li key={index} className="text-sm text-yellow-800">
                                        • {warning}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    </div>
                </div>
            )}

            {/* Service Breakdown */}
            <div className="rounded-lg border border-gray-200 bg-white p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Cost by Service</h3>
                <div className="space-y-3">
                    {result.services
                        .sort((a, b) => b.totalCost - a.totalCost)
                        .map((service) => {
                            const percentage = (service.totalCost / result.totalMonthlyCost) * 100;
                            return (
                                <div key={service.serviceName}>
                                    <div className="flex items-center justify-between text-sm mb-1">
                                        <span className="font-medium text-gray-700">
                                            {service.serviceName}
                                        </span>
                                        <span className="text-gray-900">
                                            {formatCurrency(service.totalCost, result.currency)}
                                        </span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                                            <div
                                                className="h-full bg-blue-600"
                                                style={{ width: `${percentage}%` }}
                                            />
                                        </div>
                                        <span className="text-xs text-gray-500 w-12 text-right">
                                            {formatPercentage(percentage, 1)}
                                        </span>
                                    </div>
                                    <p className="mt-1 text-xs text-gray-500">
                                        {service.resourceCount} resource{service.resourceCount !== 1 ? 's' : ''}
                                    </p>
                                </div>
                            );
                        })}
                </div>
            </div>
        </div>
    );
}
