/**
 * File validation utilities for Terraform file uploads
 */

const ALLOWED_EXTENSIONS = ['.tf', '.tfvars', '.zip'];
const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB default

export interface ValidationResult {
    valid: boolean;
    error?: string;
}

/**
 * Validate file extension
 */
export function validateFileExtension(file: File): ValidationResult {
    const fileName = file.name.toLowerCase();
    const hasValidExtension = ALLOWED_EXTENSIONS.some((ext) =>
        fileName.endsWith(ext)
    );

    if (!hasValidExtension) {
        return {
            valid: false,
            error: `Invalid file type. Allowed types: ${ALLOWED_EXTENSIONS.join(', ')}`,
        };
    }

    return { valid: true };
}

/**
 * Validate file size
 */
export function validateFileSize(
    file: File,
    maxSize: number = MAX_FILE_SIZE
): ValidationResult {
    if (file.size > maxSize) {
        return {
            valid: false,
            error: `File size exceeds maximum allowed size of ${formatBytes(maxSize)}`,
        };
    }

    return { valid: true };
}

/**
 * Validate multiple files
 */
export function validateFiles(files: File[]): ValidationResult {
    if (files.length === 0) {
        return {
            valid: false,
            error: 'No files selected',
        };
    }

    for (const file of files) {
        const extensionResult = validateFileExtension(file);
        if (!extensionResult.valid) {
            return extensionResult;
        }

        const sizeResult = validateFileSize(file);
        if (!sizeResult.valid) {
            return sizeResult;
        }
    }

    return { valid: true };
}

/**
 * Check if file is a ZIP file
 */
export function isZipFile(file: File): boolean {
    return file.name.toLowerCase().endsWith('.zip');
}

/**
 * Format bytes to human-readable string
 */
function formatBytes(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
}
