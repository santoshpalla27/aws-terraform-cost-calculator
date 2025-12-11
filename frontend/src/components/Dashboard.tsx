import React, { useState } from 'react';
import Upload from './Upload';
import CostTable from './CostTable';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { Pie } from 'react-chartjs-2';

ChartJS.register(ArcElement, Tooltip, Legend);

const Dashboard: React.FC = () => {
    const [data, setData] = useState<any>(null);
    const [loading, setLoading] = useState(false);

    // Prepare chart data
    const chartData = data ? {
        labels: data.resources.map((r: any) => r.type),
        datasets: [
            {
                label: 'Monthly Cost',
                data: data.resources.map((r: any) => r.total_monthly_cost),
                backgroundColor: [
                    'rgba(56, 189, 248, 0.8)',
                    'rgba(34, 197, 94, 0.8)',
                    'rgba(239, 68, 68, 0.8)',
                    'rgba(168, 85, 247, 0.8)',
                ],
                borderColor: [
                    'rgba(56, 189, 248, 1)',
                    'rgba(34, 197, 94, 1)',
                    'rgba(239, 68, 68, 1)',
                    'rgba(168, 85, 247, 1)',
                ],
                borderWidth: 1,
            },
        ],
    } : null;

    return (
        <div className="container">
            <header style={{ marginBottom: '3rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                    <h1 style={{ fontSize: '2rem', background: 'linear-gradient(to right, #38bdf8, #818cf8)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                        CloudCost.
                    </h1>
                    <p style={{ color: 'var(--text-secondary)' }}>Terraform Cost Estimation Engine</p>
                </div>
                {data && <button className="btn-primary" onClick={() => setData(null)}>New Scan</button>}
            </header>

            {loading && (
                <div style={{ textAlign: 'center', padding: '4rem' }}>
                    <div className="spinner" style={{ fontSize: '2rem' }}>⚡ Parsing & Estimating...</div>
                </div>
            )}

            {!data && !loading && (
                <div style={{ maxWidth: '600px', margin: '0 auto' }}>
                    <Upload onUploadSuccess={setData} onLoading={setLoading} />
                </div>
            )}

            {data && !loading && (
                <div style={{ animation: 'fadeIn 0.5s ease-out' }}>
                    <div className="card" style={{ marginBottom: '2rem', display: 'flex', justifyContent: 'space-around', alignItems: 'center' }}>
                        <div style={{ textAlign: 'center' }}>
                            <h3 style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>TOTAL MONTHLY</h3>
                            <div style={{ fontSize: '2.5rem', fontWeight: 'bold' }}>
                                ${data.total_monthly_cost.toFixed(2)}
                            </div>
                        </div>
                        <div style={{ textAlign: 'center' }}>
                            <h3 style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>TOTAL HOURLY</h3>
                            <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>
                                ${data.total_hourly_cost.toFixed(4)}
                            </div>
                        </div>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '2rem' }}>
                        <div className="card">
                            <h3>Distribution</h3>
                            {chartData && <Pie data={chartData} />}
                        </div>

                        <CostTable resources={data.resources} currency={data.currency} />
                    </div>
                </div>
            )}
        </div>
    );
};

export default Dashboard;
