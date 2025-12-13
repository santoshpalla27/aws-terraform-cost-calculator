import React, { useState, useRef } from 'react';
import './FileUpload.css';

interface FileUploadProps {
    onUpload: (file: File) => void;
    loading: boolean;
}

export const FileUpload: React.FC<FileUploadProps> = ({ onUpload, loading }) => {
    const [isDragging, setIsDragging] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);

        const file = e.dataTransfer.files[0];
        if (file && file.name.endsWith('.json')) {
            onUpload(file);
        } else {
            alert('Please upload a JSON file');
        }
    };

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            onUpload(file);
        }
    };

    const handleClick = () => {
        fileInputRef.current?.click();
    };

    return (
        <div
            className={`upload-zone ${isDragging ? 'dragging' : ''} ${loading ? 'loading' : ''}`}
            onDrop={handleDrop}
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
            onDragLeave={() => setIsDragging(false)}
            onClick={handleClick}
            role="button"
            aria-label="Upload Terraform plan JSON file"
            tabIndex={0}
            onKeyDown={(e) => e.key === 'Enter' && handleClick()}
        >
            <input
                ref={fileInputRef}
                type="file"
                accept=".json"
                onChange={handleFileSelect}
                style={{ display: 'none' }}
                aria-label="Select Terraform plan file"
            />

            <div className="upload-icon">📁</div>
            <h3>Upload Terraform Plan</h3>
            <p>Drop your plan JSON here or click to browse</p>
            {loading && <div className="spinner">Loading...</div>}
        </div>
    );
};
