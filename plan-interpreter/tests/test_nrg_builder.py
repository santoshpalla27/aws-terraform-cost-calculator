"""
Tests for NRG builder.
"""
import pytest
from app.interpreter.nrg_builder import NRGBuilder, interpret_plan
from app.schemas.nrg import ConfidenceLevel


class TestNRGBuilder:
    """Test NRG builder."""
    
    def test_simple_plan(self):
        """Test building NRG from simple plan."""
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
                                'ami': 'ami-12345678',
                                'availability_zone': 'us-east-1a'
                            }
                        }
                    ]
                }
            }
        }
        
        nrg = interpret_plan(plan_json)
        
        assert len(nrg.nodes) == 1
        assert nrg.nodes[0].terraform_address == 'aws_instance.web'
        assert nrg.nodes[0].resource_type == 'aws_instance'
        assert nrg.nodes[0].provider == 'aws'
        assert nrg.nodes[0].quantity == 1
        assert nrg.nodes[0].attributes['instance_type'] == 't3.micro'
        assert nrg.metadata.total_resources == 1
    
    def test_count_resources(self):
        """Test building NRG with count resources."""
        plan_json = {
            'planned_values': {
                'root_module': {
                    'resources': [
                        {
                            'address': 'aws_instance.web',
                            'index': 0,
                            'type': 'aws_instance',
                            'mode': 'managed',
                            'values': {'instance_type': 't3.micro'}
                        },
                        {
                            'address': 'aws_instance.web',
                            'index': 1,
                            'type': 'aws_instance',
                            'mode': 'managed',
                            'values': {'instance_type': 't3.micro'}
                        }
                    ]
                }
            }
        }
        
        nrg = interpret_plan(plan_json)
        
        assert len(nrg.nodes) == 2
        assert nrg.nodes[0].terraform_address == 'aws_instance.web[0]'
        assert nrg.nodes[1].terraform_address == 'aws_instance.web[1]'
        assert nrg.metadata.total_resources == 2
    
    def test_for_each_resources(self):
        """Test building NRG with for_each resources."""
        plan_json = {
            'planned_values': {
                'root_module': {
                    'resources': [
                        {
                            'address': 'aws_instance.web',
                            'index': 'prod',
                            'type': 'aws_instance',
                            'mode': 'managed',
                            'values': {'instance_type': 't3.large'}
                        },
                        {
                            'address': 'aws_instance.web',
                            'index': 'dev',
                            'type': 'aws_instance',
                            'mode': 'managed',
                            'values': {'instance_type': 't3.micro'}
                        }
                    ]
                }
            }
        }
        
        nrg = interpret_plan(plan_json)
        
        assert len(nrg.nodes) == 2
        assert nrg.nodes[0].terraform_address == 'aws_instance.web["prod"]'
        assert nrg.nodes[1].terraform_address == 'aws_instance.web["dev"]'
    
    def test_module_resources(self):
        """Test building NRG with module resources."""
        plan_json = {
            'planned_values': {
                'root_module': {
                    'resources': [],
                    'child_modules': [
                        {
                            'address': 'module.vpc',
                            'resources': [
                                {
                                    'address': 'module.vpc.aws_vpc.main',
                                    'type': 'aws_vpc',
                                    'mode': 'managed',
                                    'values': {'cidr_block': '10.0.0.0/16'}
                                }
                            ]
                        }
                    ]
                }
            }
        }
        
        nrg = interpret_plan(plan_json)
        
        assert len(nrg.nodes) == 1
        assert nrg.nodes[0].terraform_address == 'module.vpc.aws_vpc.main'
        assert nrg.nodes[0].module_path == ['module.vpc']
        assert nrg.metadata.module_depth == 1
    
    def test_nested_modules(self):
        """Test building NRG with nested modules."""
        plan_json = {
            'planned_values': {
                'root_module': {
                    'resources': [],
                    'child_modules': [
                        {
                            'address': 'module.vpc',
                            'resources': [],
                            'child_modules': [
                                {
                                    'address': 'module.vpc.module.subnets',
                                    'resources': [
                                        {
                                            'address': 'module.vpc.module.subnets.aws_subnet.private',
                                            'index': 0,
                                            'type': 'aws_subnet',
                                            'mode': 'managed',
                                            'values': {'cidr_block': '10.0.1.0/24'}
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            }
        }
        
        nrg = interpret_plan(plan_json)
        
        assert len(nrg.nodes) == 1
        assert nrg.nodes[0].module_path == ['module.vpc', 'module.subnets']
        assert nrg.metadata.module_depth == 2
    
    def test_unknown_values(self):
        """Test handling unknown/computed values."""
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
                                'id': None,  # Unknown
                                'public_ip': None  # Unknown
                            }
                        }
                    ]
                }
            }
        }
        
        nrg = interpret_plan(plan_json)
        
        assert len(nrg.nodes) == 1
        assert 'instance_type' in nrg.nodes[0].attributes
        assert 'id' in nrg.nodes[0].unknown_attributes
        assert 'public_ip' in nrg.nodes[0].unknown_attributes
        assert nrg.metadata.unknown_value_count == 2
    
    def test_confidence_levels(self):
        """Test confidence level calculation."""
        # High confidence (>90% known)
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
                                'ami': 'ami-12345',
                                'availability_zone': 'us-east-1a',
                                'id': None  # Only 1 unknown out of 4
                            }
                        }
                    ]
                }
            }
        }
        
        nrg = interpret_plan(plan_json)
        assert nrg.nodes[0].confidence_level == ConfidenceLevel.HIGH
    
    def test_determinism(self):
        """Test that interpretation is deterministic."""
        plan_json = {
            'planned_values': {
                'root_module': {
                    'resources': [
                        {
                            'address': 'aws_instance.web',
                            'type': 'aws_instance',
                            'mode': 'managed',
                            'values': {'instance_type': 't3.micro'}
                        }
                    ]
                }
            }
        }
        
        # Run twice
        nrg1 = interpret_plan(plan_json)
        nrg2 = interpret_plan(plan_json)
        
        # Should produce identical results
        assert nrg1.nodes[0].resource_id == nrg2.nodes[0].resource_id
        assert nrg1.metadata.plan_hash == nrg2.metadata.plan_hash
    
    def test_resources_by_type(self):
        """Test resources_by_type metadata."""
        plan_json = {
            'planned_values': {
                'root_module': {
                    'resources': [
                        {
                            'address': 'aws_instance.web1',
                            'type': 'aws_instance',
                            'mode': 'managed',
                            'values': {}
                        },
                        {
                            'address': 'aws_instance.web2',
                            'type': 'aws_instance',
                            'mode': 'managed',
                            'values': {}
                        },
                        {
                            'address': 'aws_s3_bucket.data',
                            'type': 'aws_s3_bucket',
                            'mode': 'managed',
                            'values': {}
                        }
                    ]
                }
            }
        }
        
        nrg = interpret_plan(plan_json)
        
        assert nrg.metadata.resources_by_type['aws_instance'] == 2
        assert nrg.metadata.resources_by_type['aws_s3_bucket'] == 1
    
    def test_dependencies(self):
        """Test dependency extraction and resolution."""
        plan_json = {
            'planned_values': {
                'root_module': {
                    'resources': [
                        {
                            'address': 'aws_vpc.main',
                            'type': 'aws_vpc',
                            'mode': 'managed',
                            'values': {'cidr_block': '10.0.0.0/16'}
                        },
                        {
                            'address': 'aws_subnet.private',
                            'type': 'aws_subnet',
                            'mode': 'managed',
                            'values': {'cidr_block': '10.0.1.0/24'}
                        },
                        {
                            'address': 'aws_instance.web',
                            'type': 'aws_instance',
                            'mode': 'managed',
                            'values': {'instance_type': 't3.micro'}
                        }
                    ]
                }
            },
            'resource_changes': [
                {
                    'address': 'aws_subnet.private',
                    'change': {
                        'after_depends_on': ['aws_vpc.main']
                    }
                },
                {
                    'address': 'aws_instance.web',
                    'change': {
                        'after_depends_on': ['aws_vpc.main', 'aws_subnet.private']
                    }
                }
            ]
        }
        
        nrg = interpret_plan(plan_json)
        
        # Find nodes by address
        vpc_node = next(n for n in nrg.nodes if n.terraform_address == 'aws_vpc.main')
        subnet_node = next(n for n in nrg.nodes if n.terraform_address == 'aws_subnet.private')
        instance_node = next(n for n in nrg.nodes if n.terraform_address == 'aws_instance.web')
        
        # VPC has no dependencies
        assert len(vpc_node.dependencies) == 0
        
        # Subnet depends on VPC
        assert len(subnet_node.dependencies) == 1
        assert vpc_node.resource_id in subnet_node.dependencies
        
        # Instance depends on VPC and Subnet
        assert len(instance_node.dependencies) == 2
        assert vpc_node.resource_id in instance_node.dependencies
        assert subnet_node.resource_id in instance_node.dependencies
