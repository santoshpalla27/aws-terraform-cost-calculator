"""Tests for job repository."""

import pytest
from app.models.domain import Job, JobStatus


def test_create_job(job_repository):
    """Test job creation."""
    job = Job(
        job_id="job_123",
        upload_id="upload_456",
        region="us-east-1",
        status=JobStatus.PENDING
    )
    
    created_job = job_repository.create(job)
    
    assert created_job.job_id == "job_123"
    assert created_job.upload_id == "upload_456"
    assert created_job.status == JobStatus.PENDING


def test_get_job(job_repository):
    """Test getting a job."""
    job = Job(
        job_id="job_123",
        upload_id="upload_456",
        region="us-east-1",
        status=JobStatus.PENDING
    )
    job_repository.create(job)
    
    retrieved_job = job_repository.get("job_123")
    
    assert retrieved_job is not None
    assert retrieved_job.job_id == "job_123"


def test_idempotent_creation(job_repository):
    """Test idempotent job creation."""
    job1 = Job(
        job_id="job_123",
        upload_id="upload_456",
        region="us-east-1",
        status=JobStatus.PENDING,
        idempotency_key="key_abc"
    )
    
    job2 = Job(
        job_id="job_789",
        upload_id="upload_456",
        region="us-east-1",
        status=JobStatus.PENDING,
        idempotency_key="key_abc"
    )
    
    created_job1 = job_repository.create(job1)
    created_job2 = job_repository.create(job2)
    
    # Should return the same job
    assert created_job1.job_id == created_job2.job_id
    assert created_job1.job_id == "job_123"


def test_list_jobs(job_repository):
    """Test listing jobs."""
    for i in range(15):
        job = Job(
            job_id=f"job_{i}",
            upload_id=f"upload_{i}",
            region="us-east-1",
            status=JobStatus.PENDING
        )
        job_repository.create(job)
    
    # Get first page
    jobs = job_repository.list(skip=0, limit=10)
    assert len(jobs) == 10
    
    # Get second page
    jobs = job_repository.list(skip=10, limit=10)
    assert len(jobs) == 5


def test_delete_job(job_repository):
    """Test deleting a job."""
    job = Job(
        job_id="job_123",
        upload_id="upload_456",
        region="us-east-1",
        status=JobStatus.PENDING
    )
    job_repository.create(job)
    
    deleted = job_repository.delete("job_123")
    assert deleted is True
    
    retrieved_job = job_repository.get("job_123")
    assert retrieved_job is None
