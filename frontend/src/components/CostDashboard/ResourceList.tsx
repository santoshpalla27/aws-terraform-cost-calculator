import React, { useState } from 'react';
import type { Resource } from '../../services/types';
import './ResourceList.css';

interface ResourceListProps {
    resources: Resource[];
}

export const ResourceList: React.FC<ResourceListProps> = ({ resources }) => {
    const [sortBy, setSortBy] = useState<'cost' | 'confidence'>('cost');

    const sortedResources = [...resources].sort((a, b) => {
        if (sortBy === 'cost') {
            return b.total_monthly_cost - a.total_monthly_cost;
        }
        return b.confidence_score - a.confidence_score;
    });

    return (
        <div className="resource-list">
            <div className="list-header">
                <h3>Resources</h3>
                <div className="sort-controls">
                    <label htmlFor="sort-select">Sort by:</label>
                    <select
                        id="sort-select"
                        value={sortBy}
                        onChange={(e) => setSortBy(e.target.value as 'cost' | 'confidence')}
                        aria-label="Sort resources by"
                    >
                        <option value="cost">Cost (High to Low)</option>
                        <option value="confidence">Confidence (High to Low)</option>
                    </select>
                </div>
            </div>

            <div className="resource-table">
                <table>
                    <thead>
                        <tr>
                            <th>Resource ID</th>
                            <th>Service</th>
                            <th>Region</th>
                            <th>Monthly Cost</th>
                            <th>Confidence</th>
                        </tr>
                    </thead>
                    <tbody>
                        {sortedResources.map((resource, index) => (
                            <tr key={`${resource.resource_id}-${index}`}>
                                <td className="resource-id">{resource.resource_id}</td>
                                <td>{resource.service}</td>
                                <td>{resource.region}</td>
                                <td className="cost">${resource.total_monthly_cost.toFixed(2)}</td>
                                <td className="confidence">
                                    <span className={`confidence-badge ${getConfidenceClass(resource.confidence_score)}`}>
                                        {(resource.confidence_score * 100).toFixed(0)}%
                                    </span>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

function getConfidenceClass(score: number): string {
    if (score >= 0.8) return 'high';
    if (score >= 0.6) return 'medium';
    return 'low';
}
