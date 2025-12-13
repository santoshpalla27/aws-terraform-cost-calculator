import React from 'react';
import './ConfidenceIndicator.css';

interface ConfidenceIndicatorProps {
    score: number; // 0.0 - 1.0
}

export const ConfidenceIndicator: React.FC<ConfidenceIndicatorProps> = ({ score }) => {
    const getColor = (score: number): string => {
        if (score >= 0.8) return '#4CAF50'; // Green
        if (score >= 0.6) return '#FFC107'; // Yellow
        return '#F44336'; // Red
    };

    const getLabel = (score: number): string => {
        if (score >= 0.8) return 'High Confidence';
        if (score >= 0.6) return 'Medium Confidence';
        return 'Low Confidence';
    };

    const percentage = Math.round(score * 100);

    return (
        <div className="confidence-indicator" role="status" aria-label={`Confidence: ${getLabel(score)}`}>
            <div className="confidence-bar">
                <div
                    className="confidence-fill"
                    style={{
                        width: `${percentage}%`,
                        backgroundColor: getColor(score)
                    }}
                />
            </div>
            <div className="confidence-label" style={{ color: getColor(score) }}>
                {getLabel(score)} ({percentage}%)
            </div>
        </div>
    );
};
