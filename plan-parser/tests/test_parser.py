"""Tests for Terraform Plan Parser."""

import pytest
import json
from pathlib import Path

from app.parser import TerraformPlanParser
from app.schema import NRG


@pytest.fixture
def parser():
    """Parser fixture."""
    return TerraformPlanParser()


@pytest.fixture
def simple_plan():
    """Load simple plan example."""
    path = Path(__file__).parent.parent / "examples" / "input" / "simple.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def count_plan():
    """Load count plan example."""
    path = Path(__file__).parent.parent / "examples" / "input" / "count.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def foreach_plan():
    """Load for_each plan example."""
    path = Path(__file__).parent.parent / "examples" / "input" / "for_each.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def module_plan():
    """Load module plan example."""
    path = Path(__file__).parent.parent / "examples" / "input" / "module.json"
    with open(path) as f:
        return json.load(f)


def test_parse_simple_plan(parser, simple_plan):
    """Test parsing simple plan."""
    nrg = parser.parse(simple_plan)
    
    assert isinstance(nrg, NRG)
    assert len(nrg.resources) == 2
    assert nrg.terraform_version == "1.6.6"
    assert nrg.format_version == "1.2"
    
    # Check first resource
    resource = nrg.resources[0]
    assert resource.resource_id == "aws_instance.web"
    assert resource.resource_type == "aws_instance"
    assert resource.provider == "aws"
    assert resource.region == "us-east-1"
    assert resource.quantity == 1
    assert resource.module_path == ["root"]
    assert "ami" in resource.attributes
    assert "instance_type" in resource.attributes
    assert "id" in resource.computed_attributes
    assert 0.0 <= resource.confidence <= 1.0


def test_parse_count_plan(parser, count_plan):
    """Test parsing plan with count."""
    nrg = parser.parse(count_plan)
    
    assert len(nrg.resources) == 3
    
    # Check resource IDs
    resource_ids = [r.resource_id for r in nrg.resources]
    assert "aws_instance.servers[0]" in resource_ids
    assert "aws_instance.servers[1]" in resource_ids
    assert "aws_instance.servers[2]" in resource_ids
    
    # All should have same attributes
    for resource in nrg.resources:
        assert resource.resource_type == "aws_instance"
        assert resource.provider == "aws"
        assert resource.quantity == 1


def test_parse_foreach_plan(parser, foreach_plan):
    """Test parsing plan with for_each."""
    nrg = parser.parse(foreach_plan)
    
    assert len(nrg.resources) == 3
    
    # Check resource IDs
    resource_ids = [r.resource_id for r in nrg.resources]
    assert 'aws_instance.servers["web"]' in resource_ids
    assert 'aws_instance.servers["api"]' in resource_ids
    assert 'aws_instance.servers["worker"]' in resource_ids


def test_parse_module_plan(parser, module_plan):
    """Test parsing plan with modules."""
    nrg = parser.parse(module_plan)
    
    assert len(nrg.resources) == 2
    
    # Check module paths
    resource1 = next(r for r in nrg.resources if "aws_instance" in r.resource_id)
    assert resource1.module_path == ["root", "web_servers"]
    
    resource2 = next(r for r in nrg.resources if "aws_lb" in r.resource_id)
    assert resource2.module_path == ["root", "web_servers", "load_balancer"]


def test_metadata_generation(parser, simple_plan):
    """Test metadata generation."""
    nrg = parser.parse(simple_plan)
    
    assert nrg.metadata.total_resources == 2
    assert "aws" in nrg.metadata.providers
    assert "us-east-1" in nrg.metadata.regions
    assert "root" in nrg.metadata.modules
    assert nrg.metadata.resource_types["aws_instance"] == 1
    assert nrg.metadata.resource_types["aws_s3_bucket"] == 1


def test_confidence_calculation(parser, simple_plan):
    """Test confidence calculation."""
    nrg = parser.parse(simple_plan)
    
    for resource in nrg.resources:
        # Confidence should be between 0 and 1
        assert 0.0 <= resource.confidence <= 1.0
        
        # Resources with more computed attributes should have lower confidence
        if len(resource.computed_attributes) > 0:
            assert resource.confidence < 1.0
