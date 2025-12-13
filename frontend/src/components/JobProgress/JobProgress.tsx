import React from 'react';
import type { JobStage } from '../../services/types';
import './JobProgress.css';

interface JobProgressProps {
    stage: JobStage;
    progress: number;
}

const STAGES = [
    { key: 'parsing' as JobStage, label: 'Parsing Plan', icon: '📄' },
    { key: 'enriching' as JobStage, label: 'Enriching Resources', icon: '🔍' },
    { key: 'modeling' as JobStage, label: 'Modeling Usage', icon: '📊' },
    { key: 'calculating' as JobStage, label: 'Calculating Costs', icon: '💰' },
    { key: 'complete' as JobStage, label: 'Complete', icon: '✅' }
];

export const JobProgress: React.FC<JobProgressProps> = ({ stage, progress }) => {
    const currentIndex = STAGES.findIndex(s => s.key === stage);

    return (
        <div className="progress-container" role="progressbar" aria-valuenow={progress} aria-valuemin={0} aria-valuemax={100}>
            <div className="stages">
                {STAGES.map((s, i) => (
                    <div
                        key={s.key}
                        className={`stage ${i <= currentIndex ? 'active' : ''} ${i === currentIndex ? 'current' : ''}`}
                    >
                        <div className="stage-icon">{s.icon}</div>
                        <div className="stage-label">{s.label}</div>
                    </div>
                ))}
            </div>

            <div className="progress-bar">
                <div className="progress-fill" style={{ width: `${progress}%` }} />
            </div>

            <div className="progress-text">{progress}% Complete</div>
        </div>
    );
};
