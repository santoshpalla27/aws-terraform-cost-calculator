import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';

interface UploadProps {
    onUploadSuccess: (data: any) => void;
    onLoading: (isLoading: boolean) => void;
}

const Upload: React.FC<UploadProps> = ({ onUploadSuccess, onLoading }) => {
    const onDrop = useCallback(async (acceptedFiles: File[]) => {
        if (acceptedFiles.length === 0) return;

        const file = acceptedFiles[0];
        const formData = new FormData();
        formData.append('file', file);

        onLoading(true);
        try {
            const response = await axios.post('/scan', formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
            });
            onUploadSuccess(response.data);
        } catch (error) {
            console.error('Upload failed', error);
            alert('Upload failed. Check backend connection.');
        } finally {
            onLoading(false);
        }
    }, [onUploadSuccess, onLoading]);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: { 'application/zip': ['.zip'] },
        multiple: false
    });

    return (
        <div
            {...getRootProps()}
            className="card"
            style={{
                border: '2px dashed var(--border)',
                textAlign: 'center',
                padding: '4rem 2rem',
                cursor: 'pointer',
                background: isDragActive ? '#1e293b' : 'transparent'
            }}
        >
            <input {...getInputProps()} />
            {isDragActive ? (
                <p style={{ color: 'var(--accent)' }}>Drop the Zip file here ...</p>
            ) : (
                <div>
                    <h3 style={{ marginBottom: '0.5rem' }}>Drag & drop Terraform Zip here</h3>
                    <p style={{ color: 'var(--text-secondary)' }}>or click to select file</p>
                </div>
            )}
        </div>
    );
};

export default Upload;
