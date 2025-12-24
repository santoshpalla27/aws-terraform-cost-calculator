"""
API Client for platform testing.

Provides a wrapper around requests with automatic schema validation,
correlation_id tracking, and error handling.
"""
import os
import json
from typing import Any, Dict, Optional
from pathlib import Path

import requests
from jsonschema import validate, ValidationError


class PlatformClient:
    """HTTP client for platform API with contract validation."""
    
    def __init__(self, base_url: str = None):
        """
        Initialize client.
        
        Args:
            base_url: Base URL for API (defaults to env var API_BASE)
        """
        self.base_url = base_url or os.getenv('API_BASE', 'http://nginx/api')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        # Load schemas
        self.schemas = self._load_schemas()
    
    def _load_schemas(self) -> Dict[str, dict]:
        """Load JSON schemas from contracts directory."""
        schemas = {}
        contracts_dir = Path(__file__).parent.parent / 'config' / 'contracts'
        
        for schema_file in contracts_dir.glob('*.json'):
            with open(schema_file) as f:
                schemas[schema_file.stem] = json.load(f)
        
        return schemas
    
    def _validate_response(self, data: dict):
        """
        Validate response against ApiResponse schema.
        
        Args:
            data: Response JSON
            
        Raises:
            ValidationError: If response doesn't match schema
            AssertionError: If correlation_id missing
        """
        try:
            validate(instance=data, schema=self.schemas['ApiResponse'])
        except ValidationError as e:
            raise AssertionError(f"Response schema validation failed: {e.message}")
        
        # Additional validation
        assert 'correlation_id' in data, "Missing correlation_id"
        assert isinstance(data['success'], bool), "success must be boolean"
        
        if data['success']:
            assert data['data'] is not None, "data must not be null on success"
            assert data['error'] is None, "error must be null on success"
        else:
            assert data['error'] is not None, "error must not be null on failure"
            assert 'message' in data['error'], "error.message required"
            assert 'code' in data['error'], "error.code required"
    
    def request(
        self,
        method: str,
        endpoint: str,
        validate_schema: str = None,
        **kwargs
    ) -> dict:
        """
        Make HTTP request with automatic validation.
        
        Args:
            method: HTTP method
            endpoint: API endpoint (relative to base_url)
            validate_schema: Optional schema name to validate data against
            **kwargs: Additional arguments for requests
            
        Returns:
            Response JSON
            
        Raises:
            AssertionError: If validation fails
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
        except requests.RequestException as e:
            raise AssertionError(f"Request failed: {e}")
        
        try:
            data = response.json()
        except json.JSONDecodeError:
            raise AssertionError(f"Invalid JSON response: {response.text}")
        
        # Validate ApiResponse envelope
        self._validate_response(data)
        
        # Validate data against specific schema if requested
        if validate_schema and data['success']:
            if validate_schema in self.schemas:
                try:
                    validate(instance=data['data'], schema=self.schemas[validate_schema])
                except ValidationError as e:
                    raise AssertionError(f"{validate_schema} validation failed: {e.message}")
        
        return data
    
    def get(self, endpoint: str, validate_schema: str = None, **kwargs) -> dict:
        """GET request."""
        return self.request('GET', endpoint, validate_schema=validate_schema, **kwargs)
    
    def post(self, endpoint: str, validate_schema: str = None, **kwargs) -> dict:
        """POST request."""
        return self.request('POST', endpoint, validate_schema=validate_schema, **kwargs)
    
    def put(self, endpoint: str, validate_schema: str = None, **kwargs) -> dict:
        """PUT request."""
        return self.request('PUT', endpoint, validate_schema=validate_schema, **kwargs)
    
    def delete(self, endpoint: str, **kwargs) -> dict:
        """DELETE request."""
        return self.request('DELETE', endpoint, **kwargs)
    
    def upload_terraform_fixture(self, fixture_path) -> dict:
        """
        Upload Terraform fixture with FULL contract validation.
        
        This method enforces:
        - ApiResponse schema validation
        - correlation_id presence and UUID format
        - success=true requirement
        
        Args:
            fixture_path: Path to fixture directory or ZIP file
            
        Returns:
            Validated API response with upload_id
            
        Raises:
            AssertionError: If contract violated
        """
        from pathlib import Path
        import io
        import zipfile
        
        fixture_path = Path(fixture_path)
        
        # Create ZIP if directory provided
        if fixture_path.is_dir():
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for tf_file in fixture_path.glob('*.tf'):
                    zip_file.write(tf_file, arcname=tf_file.name)
            zip_buffer.seek(0)
            zip_data = zip_buffer.read()
        else:
            # Read ZIP file
            with open(fixture_path, 'rb') as f:
                zip_data = f.read()
        
        # Prepare multipart upload
        files = {
            'files': ('terraform.zip', zip_data, 'application/zip')
        }
        
        url = f"{self.base_url}/uploads"
        
        # Make upload request
        try:
            response = self.session.post(url, files=files)
            response.raise_for_status()
        except requests.RequestException as e:
            raise AssertionError(f"Upload request failed: {e}")
        
        # Parse JSON
        try:
            data = response.json()
        except json.JSONDecodeError:
            raise AssertionError(f"Upload returned invalid JSON: {response.text}")
        
        # ENFORCE ApiResponse contract
        self._validate_response(data)
        
        # ENFORCE success=true
        assert data['success'] is True, \
            f"Upload failed: {data.get('error', {}).get('message', 'Unknown error')}"
        
        # ENFORCE upload_id presence
        assert 'data' in data, "Upload response missing 'data' field"
        assert 'upload_id' in data['data'], "Upload response missing 'upload_id'"
        
        upload_id = data['data']['upload_id']
        
        # ENFORCE UUID format
        import uuid
        try:
            uuid.UUID(upload_id)
        except ValueError:
            raise AssertionError(f"upload_id is not a valid UUID: {upload_id}")
        
        return data
    
    def get_correlation_id(self, response: dict) -> str:
        """Extract correlation_id from response."""
        return response.get('correlation_id', 'MISSING')

