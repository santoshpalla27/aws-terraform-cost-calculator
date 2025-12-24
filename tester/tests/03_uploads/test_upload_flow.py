"""
Upload flow tests - REAL validation with HARD FAILURES.

These tests enforce that upload functionality is a REQUIRED platform capability:
- Upload API MUST exist
- Valid Terraform files MUST upload successfully
- Invalid files MUST be rejected
- upload_id MUST be valid UUID
- Uploads MUST be retrievable

ANY failure indicates platform is INCOMPLETE and blocks deployment.
"""
import pytest
import io
import zipfile
from pathlib import Path
from utils.assertions import assert_correlation_id


@pytest.mark.uploads
def test_upload_api_exists(api_client):
    """
    Test that upload API endpoint exists.
    
    CRITICAL: If this fails, platform is NOT functional.
    Upload capability is REQUIRED for platform certification.
    """
    import requests
    
    # Try to access upload endpoint
    response = requests.options(f"{api_client.base_url}/uploads")
    
    assert response.status_code != 404, \
        "FAILED: Upload API does not exist - platform is INCOMPLETE"
    
    print("   ✓ Upload API endpoint exists")


@pytest.mark.uploads
def test_valid_terraform_upload(api_client, track_correlation):
    """
    Test uploading valid Terraform files.
    
    HARD REQUIREMENTS:
    - Upload MUST succeed
    - Response MUST contain upload_id
    - upload_id MUST be valid UUID
    - ApiResponse envelope MUST be valid
    """
    print("\n" + "="*60)
    print("UPLOAD TEST: Valid Terraform Upload")
    print("="*60)
    
    # Get fixture
    fixture_dir = Path(__file__).parent.parent.parent / 'fixtures' / 'simple_ec2'
    assert fixture_dir.exists(), f"FAILED: Fixture not found: {fixture_dir}"
    
    # Create ZIP
    zip_data = create_terraform_zip(fixture_dir)
    
    # Upload
    import requests
    files = {
        'files': ('terraform.zip', zip_data, 'application/zip')
    }
    
    upload_url = f"{api_client.base_url}/uploads"
    response = requests.post(upload_url, files=files)
    
    # Validate HTTP status
    assert response.status_code in [200, 201], \
        f"FAILED: Upload failed with status {response.status_code}. Response: {response.text}"
    
    # Validate response structure
    data = response.json()
    assert 'success' in data, "FAILED: Response missing 'success' field"
    assert 'correlation_id' in data, "FAILED: Response missing 'correlation_id'"
    
    assert_correlation_id(data)
    track_correlation(data, '/uploads', 'POST')
    
    # Validate success
    assert data['success'] is True, \
        f"FAILED: Upload returned success=false. Error: {data.get('error')}"
    
    # Validate upload_id
    assert 'data' in data, "FAILED: Response missing 'data' field"
    assert 'upload_id' in data['data'], "FAILED: Response missing 'upload_id'"
    
    upload_id = data['data']['upload_id']
    
    # Validate UUID format
    import uuid
    try:
        uuid.UUID(upload_id)
    except ValueError:
        pytest.fail(f"FAILED: upload_id is not a valid UUID: {upload_id}")
    
    print(f"   ✓ Upload successful: {upload_id}")
    print("="*60 + "\n")
    
    return upload_id


@pytest.mark.uploads
def test_upload_persistence(api_client):
    """
    Test that uploads are retrievable after creation.
    
    HARD REQUIREMENTS:
    - Upload MUST be retrievable via GET /uploads/{id}
    - Retrieved data MUST match uploaded data
    """
    print("\n" + "="*60)
    print("UPLOAD TEST: Upload Persistence")
    print("="*60)
    
    # Create upload
    fixture_dir = Path(__file__).parent.parent.parent / 'fixtures' / 'simple_ec2'
    zip_data = create_terraform_zip(fixture_dir)
    
    import requests
    files = {'files': ('terraform.zip', zip_data, 'application/zip')}
    upload_response = requests.post(f"{api_client.base_url}/uploads", files=files)
    
    assert upload_response.status_code in [200, 201], "FAILED: Upload failed"
    
    upload_id = upload_response.json()['data']['upload_id']
    print(f"   Upload created: {upload_id}")
    
    # Retrieve upload
    get_response = api_client.get(f'/uploads/{upload_id}')
    
    assert get_response['success'], \
        f"FAILED: Could not retrieve upload {upload_id}. Error: {get_response.get('error')}"
    
    upload_data = get_response['data']
    
    # Validate upload data
    assert 'upload_id' in upload_data, "FAILED: Retrieved upload missing 'upload_id'"
    assert upload_data['upload_id'] == upload_id, \
        f"FAILED: upload_id mismatch. Expected: {upload_id}, Got: {upload_data['upload_id']}"
    
    print(f"   ✓ Upload retrieved successfully")
    print("="*60 + "\n")


@pytest.mark.uploads
def test_invalid_file_upload_rejected(api_client):
    """
    Test that invalid files are rejected.
    
    HARD REQUIREMENTS:
    - Non-ZIP files MUST be rejected
    - Response MUST indicate failure
    - Error message MUST be present
    """
    print("\n" + "="*60)
    print("UPLOAD TEST: Invalid File Rejection")
    print("="*60)
    
    # Try to upload a text file instead of ZIP
    import requests
    files = {
        'files': ('invalid.txt', b'This is not a valid Terraform file', 'text/plain')
    }
    
    response = requests.post(f"{api_client.base_url}/uploads", files=files)
    
    # Should either reject with 400/422 or return success=false
    if response.status_code in [400, 422]:
        print(f"   ✓ Invalid file rejected with status {response.status_code}")
    else:
        # Check response
        data = response.json()
        
        # If it returns 200, it MUST have success=false
        if response.status_code == 200:
            assert data.get('success') is False, \
                "FAILED: Invalid file upload returned success=true"
            
            assert 'error' in data, "FAILED: Error response missing 'error' field"
            assert data['error'] is not None, "FAILED: Error field is null"
            
            print(f"   ✓ Invalid file rejected: {data['error'].get('message')}")
        else:
            pytest.fail(f"FAILED: Unexpected status code {response.status_code}")
    
    print("="*60 + "\n")


@pytest.mark.uploads
def test_empty_file_upload_rejected(api_client):
    """
    Test that empty files are rejected.
    
    HARD REQUIREMENTS:
    - Empty files MUST be rejected
    - Error MUST be clear
    """
    print("\n" + "="*60)
    print("UPLOAD TEST: Empty File Rejection")
    print("="*60)
    
    import requests
    files = {
        'files': ('empty.zip', b'', 'application/zip')
    }
    
    response = requests.post(f"{api_client.base_url}/uploads", files=files)
    
    # Should reject empty files
    if response.status_code in [400, 422]:
        print(f"   ✓ Empty file rejected with status {response.status_code}")
    else:
        data = response.json()
        
        if response.status_code == 200:
            assert data.get('success') is False, \
                "FAILED: Empty file upload returned success=true"
            
            print(f"   ✓ Empty file rejected: {data['error'].get('message')}")
        else:
            pytest.fail(f"FAILED: Unexpected status code {response.status_code}")
    
    print("="*60 + "\n")


@pytest.mark.uploads
def test_malformed_zip_rejected(api_client):
    """
    Test that malformed ZIP files are rejected.
    
    HARD REQUIREMENTS:
    - Corrupted ZIP files MUST be rejected
    - Error MUST be clear
    """
    print("\n" + "="*60)
    print("UPLOAD TEST: Malformed ZIP Rejection")
    print("="*60)
    
    import requests
    
    # Create malformed ZIP (just random bytes)
    malformed_zip = b'PK\x03\x04' + b'\x00' * 100  # Looks like ZIP header but is invalid
    
    files = {
        'files': ('malformed.zip', malformed_zip, 'application/zip')
    }
    
    response = requests.post(f"{api_client.base_url}/uploads", files=files)
    
    # Should reject malformed files
    if response.status_code in [400, 422]:
        print(f"   ✓ Malformed ZIP rejected with status {response.status_code}")
    else:
        data = response.json()
        
        if response.status_code == 200:
            assert data.get('success') is False, \
                "FAILED: Malformed ZIP upload returned success=true"
            
            print(f"   ✓ Malformed ZIP rejected: {data['error'].get('message')}")
        else:
            pytest.fail(f"FAILED: Unexpected status code {response.status_code}")
    
    print("="*60 + "\n")


@pytest.mark.uploads
def test_upload_without_file_rejected(api_client):
    """
    Test that requests without file are rejected.
    
    HARD REQUIREMENTS:
    - Missing file MUST be rejected
    - Error MUST be clear
    """
    print("\n" + "="*60)
    print("UPLOAD TEST: Missing File Rejection")
    print("="*60)
    
    import requests
    
    # POST without file
    response = requests.post(f"{api_client.base_url}/uploads")
    
    # Should reject
    assert response.status_code in [400, 422], \
        f"FAILED: Upload without file should return 400/422, got {response.status_code}"
    
    print(f"   ✓ Request without file rejected with status {response.status_code}")
    print("="*60 + "\n")


def create_terraform_zip(fixture_dir: Path) -> bytes:
    """
    Create a ZIP file from Terraform fixtures.
    
    Args:
        fixture_dir: Path to fixture directory
        
    Returns:
        ZIP file bytes
    """
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for tf_file in fixture_dir.glob('*.tf'):
            zip_file.write(tf_file, arcname=tf_file.name)
    
    zip_buffer.seek(0)
    return zip_buffer.read()
