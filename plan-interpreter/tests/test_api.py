"""
Tests for API endpoints.
"""
import pytest
import json
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestAPI:
    """Test API endpoints."""
    
    def test_root_endpoint(self):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data['service'] == 'terraform-plan-interpreter'
        assert data['status'] == 'operational'
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/internal/health")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
    
    def test_interpret_valid_plan(self):
        """Test interpretation with valid plan reference."""
        plan_json = {
            'planned_values': {
                'root_module': {
                    'resources': [
                        {
                            'address': 'aws_instance.web',
                            'type': 'aws_instance',
                            'mode': 'managed',
                            'values': {
                                'instance_type': 't3.micro',
                                'ami': 'ami-12345678'
                            }
                        }
                    ]
                }
            },
            'resource_changes': []
        }
        
        # Create temporary plan file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(plan_json, f)
            temp_path = f.name
        
        try:
            response = client.post(
                "/internal/interpret",
                json={'plan_json_reference': f'file://{temp_path}'}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert 'normalized_resource_graph' in data
            assert 'interpretation_metadata' in data
            assert len(data['normalized_resource_graph']) == 1
            assert data['interpretation_metadata']['total_resources'] == 1
        finally:
            Path(temp_path).unlink()
    
    def test_interpret_invalid_reference(self):
        """Test interpretation with invalid reference."""
        response = client.post(
            "/internal/interpret",
            json={'plan_json_reference': 'file:///nonexistent/plan.json'}
        )
        
        assert response.status_code == 400
        assert 'not found' in response.json()['detail'].lower()
    
    def test_interpret_invalid_plan_structure(self):
        """Test interpretation with invalid plan structure."""
        plan_json = {'invalid': 'structure'}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(plan_json, f)
            temp_path = f.name
        
        try:
            response = client.post(
                "/internal/interpret",
                json={'plan_json_reference': f'file://{temp_path}'}
            )
            
            assert response.status_code == 400
        finally:
            Path(temp_path).unlink()
    
    def test_interpret_empty_plan(self):
        """Test interpretation with empty plan."""
        plan_json = {
            'planned_values': {
                'root_module': {
                    'resources': []
                }
            },
            'resource_changes': []
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(plan_json, f)
            temp_path = f.name
        
        try:
            response = client.post(
                "/internal/interpret",
                json={'plan_json_reference': f'file://{temp_path}'}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data['normalized_resource_graph']) == 0
            assert data['interpretation_metadata']['total_resources'] == 0
        finally:
            Path(temp_path).unlink()
