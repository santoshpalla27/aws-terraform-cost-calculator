import React from 'react';
import { ServiceChart } from './ServiceChart';
import { RegionChart } from './RegionChart';
import { ResourceList } from './ResourceList';
import { ConfidenceIndicator } from '../ConfidenceIndicator/ConfidenceIndicator';
import type { CostEstimate } from '../../services/types';
import './CostDashboard.css';

interface CostDashboardProps {
    estimate: CostEstimate;
}

export const CostDashboard: React.FC<CostDashboardProps> = ({ estimate }) => {
    return (
        <div className="dashboard">
            <div className="summary-card">
                <h2>Total Monthly Cost</h2>
                <div className="cost-value" aria-label={`Total cost: $${estimate.total_monthly_cost.toFixed(2)}`}>
                    ${estimate.total_monthly_cost.toFixed(2)}
                </div>
                <div className="resource-count">
                    {estimate.by_resource.length} resources analyzed
                </div>
                <ConfidenceIndicator score={estimate.confidence_score} />
            </div>

            <div className="charts-grid">
                <ServiceChart data={estimate.by_service} />
                <RegionChart data={estimate.by_region} />
            </div>

            <ResourceList resources={estimate.by_resource} />
        </div>
    );
};
