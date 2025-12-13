import React from 'react';
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import type { ServiceCost } from '../../services/types';

interface ServiceChartProps {
    data: ServiceCost[];
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82ca9d'];

export const ServiceChart: React.FC<ServiceChartProps> = ({ data }) => {
    const chartData = data.map(s => ({
        name: s.service,
        value: s.total_cost,
        count: s.resource_count
    }));

    return (
        <div className="chart-container">
            <h3>Cost by Service</h3>
            <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                    <Pie
                        data={chartData}
                        dataKey="value"
                        nameKey="name"
                        cx="50%"
                        cy="50%"
                        label={(entry) => `${entry.name}: $${entry.value.toFixed(2)}`}
                        labelLine={false}
                    >
                        {chartData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                    </Pie>
                    <Tooltip formatter={(value: number) => `$${value.toFixed(2)}`} />
                    <Legend />
                </PieChart>
            </ResponsiveContainer>
        </div>
    );
};
