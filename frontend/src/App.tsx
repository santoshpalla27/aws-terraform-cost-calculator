import React, { useState } from 'react';
import { FileUpload } from './components/FileUpload/FileUpload';
import { JobProgress } from './components/JobProgress/JobProgress';
import { CostDashboard } from './components/CostDashboard/CostDashboard';
import { costAPI } from './services/api';
import type { CostEstimate, JobStage } from './services/types';
import './App.css';

function App() {
    const [stage, setStage] = useState<JobStage | null>(null);
    const [progress, setProgress] = useState(0);
    const [estimate, setEstimate] = useState<CostEstimate | null>(null);
    const [error, setError] = useState<string | null>(null);

    const handleFileUpload = async (file: File) => {
        try {
            setError(null);
            setStage('parsing');
            setProgress(20);

            // Parse plan
            const { nrg } = await costAPI.parsePlan(file);

            setStage('enriching');
            setProgress(40);

            // Enrich resources
            const { enriched_nrg } = await costAPI.enrichResources(nrg);

            setStage('modeling');
            setProgress(60);

            // For demo: simulate usage modeling
            // In production, this would call the usage modeling API

            setStage('calculating');
            setProgress(80);

            // For demo: simulate cost calculation
            // In production, this would call the cost aggregation API

            setStage('complete');
            setProgress(100);

            // For demo: create mock estimate
            const mockEstimate: CostEstimate = {
                total_monthly_cost: 1234.56,
                confidence_score: 0.85,
                profile: 'prod',
                by_resource: [],
                by_service: [
                    { service: 'EC2', total_cost: 500, resource_count: 5 },
                    { service: 'S3', total_cost: 234.56, resource_count: 3 },
                    { service: 'RDS', total_cost: 500, resource_count: 2 }
                ],
                by_region: [
                    { region: 'us-east-1', total_cost: 800, resource_count: 7, services: {} },
                    { region: 'eu-west-1', total_cost: 434.56, resource_count: 3, services: {} }
                ],
                timestamp: new Date().toISOString()
            };

            setEstimate(mockEstimate);

        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred');
            setStage(null);
            setProgress(0);
        }
    };

    return (
        <div className="app">
            <header className="app-header">
                <h1>Terraform Cost Estimator</h1>
                <p>Upload your Terraform plan to estimate AWS costs</p>
            </header>

            <main className="app-main">
                {!stage && !estimate && (
                    <FileUpload onUpload={handleFileUpload} loading={false} />
                )}

                {stage && stage !== 'complete' && (
                    <JobProgress stage={stage} progress={progress} />
                )}

                {estimate && (
                    <CostDashboard estimate={estimate} />
                )}

                {error && (
                    <div className="error-message" role="alert">
                        <strong>Error:</strong> {error}
                    </div>
                )}
            </main>
        </div>
    );
}

export default App;
