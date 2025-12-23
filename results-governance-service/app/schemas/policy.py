"""
Policy schemas for API.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum
from uuid import UUID


class PolicyStatus(str, Enum):
    """Policy evaluation status."""
    PASS = "PASS"
    FAIL = "FAIL"


class PolicyRule(BaseModel):
    """Policy rule definition."""
    
    rule_id: str = Field(..., description="Rule identifier")
    rule_type: str = Field(..., description="Rule type (threshold, confidence, delta)")
    description: str = Field(..., description="Human-readable description")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Rule parameters")


class PolicyViolation(BaseModel):
    """Policy violation details."""
    
    rule_id: str
    description: str
    actual_value: Any
    expected_value: Any
    severity: str = Field(default="error", description="Severity (error/warning)")


class PolicyEvaluation(BaseModel):
    """Policy evaluation result."""
    
    status: PolicyStatus
    violations: List[PolicyViolation] = Field(default_factory=list)
    passed_rules: List[str] = Field(default_factory=list)
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "PASS",
                "violations": [],
                "passed_rules": ["budget_threshold", "confidence_check"]
            }
        }


class GateRequest(BaseModel):
    """CI/CD gate evaluation request."""
    
    result_id: Optional[UUID] = Field(None, description="Result ID to evaluate")
    fcm: Optional[Dict[str, Any]] = Field(None, description="FCM to evaluate (if not stored)")
    baseline_result_id: Optional[UUID] = Field(None, description="Baseline for comparison")
    
    class Config:
        json_schema_extra = {
            "example": {
                "result_id": "550e8400-e29b-41d4-a716-446655440000",
                "baseline_result_id": "550e8400-e29b-41d4-a716-446655440001"
            }
        }


class GateResponse(BaseModel):
    """CI/CD gate evaluation response."""
    
    status: PolicyStatus = Field(..., description="Gate status (PASS/FAIL)")
    policy_evaluation: PolicyEvaluation = Field(..., description="Policy evaluation results")
    cost_delta: Optional[Dict[str, Any]] = Field(None, description="Cost delta vs baseline")
    exit_code: int = Field(..., description="Exit code for CI (0=PASS, 1=FAIL)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "PASS",
                "policy_evaluation": {},
                "cost_delta": None,
                "exit_code": 0
            }
        }
