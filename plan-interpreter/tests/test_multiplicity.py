"""
Tests for resource multiplicity resolution.
"""
import pytest
from app.interpreter.multiplicity import (
    build_terraform_address,
    resolve_multiplicity,
    extract_module_path,
    calculate_module_depth
)


class TestMultiplicity:
    """Test multiplicity resolution."""
    
    def test_build_address_no_index(self):
        """Test address building without index."""
        address = build_terraform_address("aws_instance.web")
        assert address == "aws_instance.web"
    
    def test_build_address_count_index(self):
        """Test address building with count index."""
        address = build_terraform_address("aws_instance.web", 0)
        assert address == "aws_instance.web[0]"
        
        address = build_terraform_address("aws_instance.web", 5)
        assert address == "aws_instance.web[5]"
    
    def test_build_address_for_each_key(self):
        """Test address building with for_each key."""
        address = build_terraform_address("aws_instance.web", "prod")
        assert address == 'aws_instance.web["prod"]'
        
        address = build_terraform_address("aws_instance.web", "us-east-1")
        assert address == 'aws_instance.web["us-east-1"]'
    
    def test_resolve_single_resource(self):
        """Test resolving single resource (no count/for_each)."""
        resource = {
            'address': 'aws_instance.web',
            'type': 'aws_instance',
            'mode': 'managed',
            'values': {'instance_type': 't3.micro'}
        }
        
        instances = resolve_multiplicity(resource)
        
        assert len(instances) == 1
        assert instances[0]['full_address'] == 'aws_instance.web'
        assert instances[0]['index'] is None
    
    def test_resolve_count_resource(self):
        """Test resolving resource with count."""
        resource = {
            'address': 'aws_instance.web',
            'index': 2,
            'type': 'aws_instance',
            'mode': 'managed',
            'values': {'instance_type': 't3.micro'}
        }
        
        instances = resolve_multiplicity(resource)
        
        assert len(instances) == 1
        assert instances[0]['full_address'] == 'aws_instance.web[2]'
        assert instances[0]['index'] == 2
    
    def test_resolve_for_each_resource(self):
        """Test resolving resource with for_each."""
        resource = {
            'address': 'aws_instance.web',
            'index': 'prod',
            'type': 'aws_instance',
            'mode': 'managed',
            'values': {'instance_type': 't3.micro'}
        }
        
        instances = resolve_multiplicity(resource)
        
        assert len(instances) == 1
        assert instances[0]['full_address'] == 'aws_instance.web["prod"]'
        assert instances[0]['index'] == 'prod'
    
    def test_extract_module_path_root(self):
        """Test extracting module path from root resource."""
        path = extract_module_path("aws_instance.web")
        assert path == []
    
    def test_extract_module_path_single_module(self):
        """Test extracting module path with single module."""
        path = extract_module_path("module.vpc.aws_vpc.main")
        assert path == ["module.vpc"]
    
    def test_extract_module_path_nested_modules(self):
        """Test extracting module path with nested modules."""
        path = extract_module_path("module.vpc.module.subnets.aws_subnet.private[0]")
        assert path == ["module.vpc", "module.subnets"]
    
    def test_calculate_module_depth(self):
        """Test calculating module depth."""
        assert calculate_module_depth([]) == 0
        assert calculate_module_depth(["module.vpc"]) == 1
        assert calculate_module_depth(["module.vpc", "module.subnets"]) == 2
