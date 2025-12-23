"""
Tests for dependency extraction.
"""
import pytest
from app.interpreter.dependencies import DependencyExtractor, build_dependency_graph


class TestDependencyExtraction:
    """Test dependency extraction from plan JSON."""
    
    def test_no_dependencies(self):
        """Test resources with no dependencies."""
        plan_json = {
            'resource_changes': [
                {
                    'address': 'aws_instance.web',
                    'change': {}
                }
            ]
        }
        
        address_to_id = {'aws_instance.web': 'res_001'}
        
        dep_graph = build_dependency_graph(plan_json, address_to_id)
        
        assert len(dep_graph) == 0
    
    def test_single_dependency(self):
        """Test resource with single dependency."""
        plan_json = {
            'resource_changes': [
                {
                    'address': 'aws_instance.web',
                    'change': {
                        'after_depends_on': ['aws_vpc.main']
                    }
                }
            ]
        }
        
        address_to_id = {
            'aws_instance.web': 'res_001',
            'aws_vpc.main': 'res_002'
        }
        
        dep_graph = build_dependency_graph(plan_json, address_to_id)
        
        assert 'res_001' in dep_graph
        assert dep_graph['res_001'] == ['res_002']
    
    def test_multiple_dependencies(self):
        """Test resource with multiple dependencies."""
        plan_json = {
            'resource_changes': [
                {
                    'address': 'aws_instance.web',
                    'change': {
                        'after_depends_on': [
                            'aws_vpc.main',
                            'aws_subnet.private',
                            'aws_security_group.web'
                        ]
                    }
                }
            ]
        }
        
        address_to_id = {
            'aws_instance.web': 'res_001',
            'aws_vpc.main': 'res_002',
            'aws_subnet.private': 'res_003',
            'aws_security_group.web': 'res_004'
        }
        
        dep_graph = build_dependency_graph(plan_json, address_to_id)
        
        assert 'res_001' in dep_graph
        assert len(dep_graph['res_001']) == 3
        assert 'res_002' in dep_graph['res_001']
        assert 'res_003' in dep_graph['res_001']
        assert 'res_004' in dep_graph['res_001']
    
    def test_cross_module_dependencies(self):
        """Test dependencies across modules."""
        plan_json = {
            'resource_changes': [
                {
                    'address': 'module.app.aws_instance.web',
                    'change': {
                        'after_depends_on': ['module.vpc.aws_vpc.main']
                    }
                }
            ]
        }
        
        address_to_id = {
            'module.app.aws_instance.web': 'res_001',
            'module.vpc.aws_vpc.main': 'res_002'
        }
        
        dep_graph = build_dependency_graph(plan_json, address_to_id)
        
        assert 'res_001' in dep_graph
        assert dep_graph['res_001'] == ['res_002']
    
    def test_count_dependencies(self):
        """Test dependencies with count resources."""
        plan_json = {
            'resource_changes': [
                {
                    'address': 'aws_instance.web[0]',
                    'change': {
                        'after_depends_on': ['aws_vpc.main']
                    }
                },
                {
                    'address': 'aws_instance.web[1]',
                    'change': {
                        'after_depends_on': ['aws_vpc.main']
                    }
                }
            ]
        }
        
        address_to_id = {
            'aws_instance.web[0]': 'res_001',
            'aws_instance.web[1]': 'res_002',
            'aws_vpc.main': 'res_003'
        }
        
        dep_graph = build_dependency_graph(plan_json, address_to_id)
        
        assert 'res_001' in dep_graph
        assert 'res_002' in dep_graph
        assert dep_graph['res_001'] == ['res_003']
        assert dep_graph['res_002'] == ['res_003']
    
    def test_for_each_dependencies(self):
        """Test dependencies with for_each resources."""
        plan_json = {
            'resource_changes': [
                {
                    'address': 'aws_instance.web["prod"]',
                    'change': {
                        'after_depends_on': ['aws_vpc.main']
                    }
                }
            ]
        }
        
        address_to_id = {
            'aws_instance.web["prod"]': 'res_001',
            'aws_vpc.main': 'res_002'
        }
        
        dep_graph = build_dependency_graph(plan_json, address_to_id)
        
        assert 'res_001' in dep_graph
        assert dep_graph['res_001'] == ['res_002']
    
    def test_circular_dependencies(self):
        """Test circular dependencies are preserved."""
        plan_json = {
            'resource_changes': [
                {
                    'address': 'aws_resource.a',
                    'change': {
                        'after_depends_on': ['aws_resource.b']
                    }
                },
                {
                    'address': 'aws_resource.b',
                    'change': {
                        'after_depends_on': ['aws_resource.a']
                    }
                }
            ]
        }
        
        address_to_id = {
            'aws_resource.a': 'res_001',
            'aws_resource.b': 'res_002'
        }
        
        dep_graph = build_dependency_graph(plan_json, address_to_id)
        
        # Circular dependencies should be preserved
        assert 'res_001' in dep_graph
        assert 'res_002' in dep_graph
        assert dep_graph['res_001'] == ['res_002']
        assert dep_graph['res_002'] == ['res_001']
    
    def test_missing_dependency_reference(self):
        """Test graceful handling of missing dependency references."""
        plan_json = {
            'resource_changes': [
                {
                    'address': 'aws_instance.web',
                    'change': {
                        'after_depends_on': [
                            'aws_vpc.main',
                            'aws_subnet.missing'  # This doesn't exist
                        ]
                    }
                }
            ]
        }
        
        address_to_id = {
            'aws_instance.web': 'res_001',
            'aws_vpc.main': 'res_002'
            # aws_subnet.missing is not in the map
        }
        
        dep_graph = build_dependency_graph(plan_json, address_to_id)
        
        # Should only include the found dependency
        assert 'res_001' in dep_graph
        assert dep_graph['res_001'] == ['res_002']
        assert len(dep_graph['res_001']) == 1
    
    def test_before_depends_on_fallback(self):
        """Test fallback to before_depends_on if after_depends_on is missing."""
        plan_json = {
            'resource_changes': [
                {
                    'address': 'aws_instance.web',
                    'change': {
                        'before_depends_on': ['aws_vpc.main']
                    }
                }
            ]
        }
        
        address_to_id = {
            'aws_instance.web': 'res_001',
            'aws_vpc.main': 'res_002'
        }
        
        dep_graph = build_dependency_graph(plan_json, address_to_id)
        
        assert 'res_001' in dep_graph
        assert dep_graph['res_001'] == ['res_002']
