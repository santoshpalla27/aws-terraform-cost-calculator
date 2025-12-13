import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import type { RegionCost } from '../../services/types';

interface RegionChartProps {
    data: RegionCost[];
}

export const RegionChart: React.FC<RegionChartProps> = ({ data }) => {
    const chartData = data.map(r => ({
        region: r.region,
        cost: r.total_cost,
        resources: r.resource_count
    }));

    return (
        <div className="chart-container">
            <h3>Cost by Region</h3>
            <ResponsiveContainer width="100%" height={300}>
                <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="region" />
                    <YAxis />
                    <Tooltip formatter={(value: number) => `$${value.toFixed(2)}`} />
                    <Bar dataKey="cost" fill="#8884d8" />
                </BarChart>
            </ResponsiveContainer>
        </div>
    );
};
