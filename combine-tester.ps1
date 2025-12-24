# PowerShell Script to Combine Tester Files
# Processes only the tester directory

param(
    [string]$OutputFile = "tester-combined.txt",
    [string]$RootPath = ".\tester"
)

# Directories to exclude
$ExcludeDirs = @(
    '__pycache__',
    '.pytest_cache',
    'venv',
    'env',
    '.venv',
    '.git',
    'logs',
    'tmp',
    'temp',
    '.coverage',
    'htmlcov',
    'dist',
    'build',
    '*.egg-info'
)

# File extensions to exclude
$ExcludeExtensions = @(
    '.pyc',
    '.pyo',
    '.pyd',
    '.so',
    '.dll',
    '.exe',
    '.zip',
    '.tar',
    '.gz',
    '.log',
    '.coverage'
)

Write-Host "Starting Tester file combination..." -ForegroundColor Green
Write-Host "Output file: $OutputFile" -ForegroundColor Cyan

# Remove existing output file if it exists
if (Test-Path $OutputFile) {
    Remove-Item $OutputFile
    Write-Host "Removed existing output file" -ForegroundColor Yellow
}

# Initialize counters
$fileCount = 0
$totalSize = 0

# Create output file with header
$header = @"
================================================================================
PLATFORM TESTER - COMBINED FILES
Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
Root Path: $(Resolve-Path $RootPath)
================================================================================

TABLE OF CONTENTS
================================================================================
1. Configuration Files (Dockerfile, requirements.txt, pytest.ini, etc.)
2. JSON Schema Contracts (ApiResponse, Job, UsageProfile, CostResult)
3. Utility Modules (api_client, polling, assertions, correlation)
4. Test Files (health, contracts, api_gateway, e2e, etc.)
5. Documentation (README.md)
================================================================================

"@

Add-Content -Path $OutputFile -Value $header -Encoding UTF8

# Get all files recursively, excluding specified directories
$files = Get-ChildItem -Path $RootPath -Recurse -File | Where-Object {
    $file = $_
    $exclude = $false
    
    # Check if file is in excluded directory
    foreach ($dir in $ExcludeDirs) {
        if ($file.FullName -like "*\$dir\*") {
            $exclude = $true
            break
        }
    }
    
    # Check if file has excluded extension
    if (-not $exclude) {
        foreach ($ext in $ExcludeExtensions) {
            if ($file.Extension -eq $ext) {
                $exclude = $true
                break
            }
        }
    }
    
    # Exclude the output file itself
    if ($file.Name -eq $OutputFile) {
        $exclude = $true
    }
    
    -not $exclude
}

Write-Host "Found $($files.Count) files to process" -ForegroundColor Cyan

# Sort files by category for better organization
$sortedFiles = $files | Sort-Object {
    $path = $_.FullName
    switch -Regex ($path) {
        'Dockerfile|requirements\.txt|pytest\.ini|entrypoint\.sh|\.yaml$' { 1 }
        'contracts.*\.json$' { 2 }
        'utils.*\.py$' { 3 }
        'tests.*\.py$' { 4 }
        'README\.md$' { 5 }
        default { 6 }
    }
}, Name

# Process each file
foreach ($file in $sortedFiles) {
    try {
        $relativePath = $file.FullName.Substring((Resolve-Path $RootPath).Path.Length + 1)
        
        # Determine file type for better categorization
        $fileType = switch -Regex ($relativePath) {
            '^Dockerfile$' { "Docker Configuration" }
            '^requirements\.txt$' { "Python Dependencies" }
            '^pytest\.ini$' { "Pytest Configuration" }
            '^entrypoint\.sh$' { "Entrypoint Script" }
            '\.yaml$' { "YAML Configuration" }
            'contracts.*\.json$' { "JSON Schema Contract" }
            'utils.*\.py$' { "Utility Module" }
            'conftest\.py$' { "Pytest Fixtures" }
            'tests.*test_.*\.py$' { "Test Suite" }
            '\.md$' { "Documentation" }
            default { "Other" }
        }
        
        # File header
        $fileHeader = @"

================================================================================
FILE: $relativePath
TYPE: $fileType
SIZE: $($file.Length) bytes
MODIFIED: $($file.LastWriteTime)
================================================================================

"@
        
        Add-Content -Path $OutputFile -Value $fileHeader -Encoding UTF8
        
        # Try to read file content
        try {
            $content = Get-Content -Path $file.FullName -Raw -ErrorAction Stop
            Add-Content -Path $OutputFile -Value $content -Encoding UTF8
        }
        catch {
            $errorMsg = "[ERROR: Could not read file - possibly binary or locked]"
            Add-Content -Path $OutputFile -Value $errorMsg -Encoding UTF8
        }
        
        # Add separator
        Add-Content -Path $OutputFile -Value "`n`n" -Encoding UTF8
        
        $fileCount++
        $totalSize += $file.Length
        
        # Progress indicator
        if ($fileCount % 5 -eq 0) {
            Write-Host "Processed $fileCount files..." -ForegroundColor Gray
        }
    }
    catch {
        Write-Host "Error processing file: $($file.FullName)" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
    }
}

# Add footer with statistics
$footer = @"

================================================================================
SUMMARY
================================================================================
Total Files Processed: $fileCount
Total Size: $([math]::Round($totalSize / 1KB, 2)) KB
Output File: $OutputFile
Completed: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

FILE BREAKDOWN:
- Configuration Files: $(($sortedFiles | Where-Object { $_.Name -match 'Dockerfile|requirements|pytest|entrypoint|\.yaml$' }).Count)
- JSON Schemas: $(($sortedFiles | Where-Object { $_.FullName -match 'contracts.*\.json$' }).Count)
- Utility Modules: $(($sortedFiles | Where-Object { $_.FullName -match 'utils.*\.py$' }).Count)
- Test Files: $(($sortedFiles | Where-Object { $_.FullName -match 'tests.*test_.*\.py$' }).Count)
- Documentation: $(($sortedFiles | Where-Object { $_.Extension -eq '.md' }).Count)
================================================================================
"@

Add-Content -Path $OutputFile -Value $footer -Encoding UTF8

# Display summary
Write-Host "`n" -NoNewline
Write-Host "================================================================================" -ForegroundColor Green
Write-Host "TESTER FILE COMBINATION COMPLETE!" -ForegroundColor Green
Write-Host "================================================================================" -ForegroundColor Green
Write-Host "Files processed: $fileCount" -ForegroundColor Cyan
Write-Host "Total size: $([math]::Round($totalSize / 1KB, 2)) KB" -ForegroundColor Cyan
Write-Host "Output file: $OutputFile" -ForegroundColor Cyan
Write-Host "Output size: $([math]::Round((Get-Item $OutputFile).Length / 1KB, 2)) KB" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "File breakdown:" -ForegroundColor Yellow
Write-Host "  Configuration: $(($sortedFiles | Where-Object { $_.Name -match 'Dockerfile|requirements|pytest|entrypoint|\.yaml$' }).Count) files" -ForegroundColor Gray
Write-Host "  JSON Schemas: $(($sortedFiles | Where-Object { $_.FullName -match 'contracts.*\.json$' }).Count) files" -ForegroundColor Gray
Write-Host "  Utilities: $(($sortedFiles | Where-Object { $_.FullName -match 'utils.*\.py$' }).Count) files" -ForegroundColor Gray
Write-Host "  Tests: $(($sortedFiles | Where-Object { $_.FullName -match 'tests.*test_.*\.py$' }).Count) files" -ForegroundColor Gray
Write-Host "  Documentation: $(($sortedFiles | Where-Object { $_.Extension -eq '.md' }).Count) files" -ForegroundColor Gray
Write-Host "================================================================================" -ForegroundColor Green
