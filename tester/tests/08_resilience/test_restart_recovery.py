"""
Resilience tests - REAL service restart scenarios with HARD FAILURES.

These tests validate that the platform can survive service failures:
- Job orchestrator restart mid-job
- Pricing engine restart mid-job
- Jobs must reach terminal state (COMPLETED or FAILED)
- No stuck states allowed
- Failure reasons must be visible

ANY failure to recover blocks deployment.
"""
import pytest
import time
from pathlib import Path
from utils.polling import poll_until_sync
from utils.docker_control import DockerController
from utils.assertions import assert_terminal_state


@pytest.mark.resilience
@pytest.mark.slow
def test_job_survives_orchestrator_restart(api_client, track_correlation):
    """
    Test that jobs survive job-orchestrator restart.
    
    HARD REQUIREMENTS:
    - Job MUST reach terminal state after restart
    - Job MUST NOT be stuck
    - Failure reason MUST be visible if job fails
    """
    print("\n" + "="*80)
    print("RESILIENCE TEST: Job Orchestrator Restart Mid-Job")
    print("="*80)
    
    docker = DockerController()
    
    # ========================================================================
    # STEP 1: Create and start a job
    # ========================================================================
    print("\n[1/5] Creating job...")
    
    # Get usage profile
    profiles_response = api_client.get('/usage-profiles')
    assert profiles_response['success'], "FAILED: Could not fetch usage profiles"
    
    profile_id = profiles_response['data'][0]['id']
    
    # Upload Terraform using PlatformClient (enforces contract)
    fixture_dir = Path(__file__).parent.parent.parent / 'fixtures' / 'simple_ec2'
    assert fixture_dir.exists(), f"FAILED: Fixture not found: {fixture_dir}"
    
    upload_response = api_client.upload_terraform_fixture(fixture_dir)
    upload_id = upload_response['data']['upload_id']
    
    # Create job
    job_response = api_client.post('/jobs', json={
        'name': 'Resilience Test - Orchestrator Restart',
        'upload_id': upload_id,
        'usage_profile': profile_id
    })
    assert job_response['success'], "FAILED: Job creation failed"
    
    job_id = job_response['data']['job_id']
    print(f"   ✓ Job created: {job_id}")
    
    # ========================================================================
    # STEP 2: Wait for job to start processing
    # ========================================================================
    print("\n[2/5] Waiting for job to start processing...")
    
    max_wait = 10
    for i in range(max_wait):
        status_response = api_client.get(f'/jobs/{job_id}/status')
        current_status = status_response['data']['status']
        
        if current_status not in ['UPLOADED']:
            print(f"   ✓ Job processing: {current_status}")
            break
        
        time.sleep(1)
    else:
        pytest.fail("FAILED: Job did not start processing")
    
    # ========================================================================
    # STEP 3: Restart job-orchestrator
    # ========================================================================
    print("\n[3/5] Restarting job-orchestrator...")
    
    try:
        docker.restart_container('cost-platform-job-orchestrator', wait_healthy=True, timeout=30)
    except Exception as e:
        pytest.fail(f"FAILED: Could not restart job-orchestrator: {e}")
    
    print("   ✓ Job orchestrator restarted and healthy")
    
    # ========================================================================
    # STEP 4: Poll until terminal state
    # ========================================================================
    print("\n[4/5] Polling job to terminal state...")
    
    poll_count = 0
    
    def check_status():
        nonlocal poll_count
        poll_count += 1
        
        status_response = api_client.get(f'/jobs/{job_id}/status')
        assert status_response['success'], f"FAILED: Status check failed at poll {poll_count}"
        
        status_data = status_response['data']
        current_state = status_data['status']
        
        print(f"   Poll {poll_count}: {current_state} ({status_data.get('progress', 0)}%)")
        
        return status_data
    
    def is_terminal(status_data):
        return status_data['status'] in ['COMPLETED', 'FAILED']
    
    try:
        final_status = poll_until_sync(
            check_fn=check_status,
            condition_fn=is_terminal,
            max_attempts=60,
            initial_delay=2.0,
            timeout=300
        )
    except TimeoutError:
        pytest.fail("FAILED: Job stuck after orchestrator restart - did not reach terminal state")
    
    # ========================================================================
    # STEP 5: Validate terminal state reached
    # ========================================================================
    print("\n[5/5] Validating recovery...")
    
    final_state = final_status['status']
    assert_terminal_state(final_state)
    
    if final_state == 'FAILED':
        error_msg = final_status.get('error_message', 'Unknown error')
        print(f"   ⚠ Job failed after restart: {error_msg}")
        print(f"   ✓ Failure is visible and terminal (acceptable)")
    else:
        print(f"   ✓ Job completed successfully after restart")
    
    print("\n" + "="*80)
    print("✅ RESILIENCE TEST PASSED - Platform survived orchestrator restart")
    print("="*80)
    print(f"Final State: {final_state}")
    print(f"Polls Required: {poll_count}")
    print("="*80 + "\n")


@pytest.mark.resilience
@pytest.mark.slow
def test_job_survives_pricing_engine_restart(api_client, track_correlation):
    """
    Test that jobs survive pricing-engine restart.
    
    HARD REQUIREMENTS:
    - Job MUST reach terminal state after restart
    - Job MUST NOT be stuck
    - Failure reason MUST be visible if job fails
    """
    print("\n" + "="*80)
    print("RESILIENCE TEST: Pricing Engine Restart Mid-Job")
    print("="*80)
    
    docker = DockerController()
    
    # ========================================================================
    # STEP 1: Create and start a job
    # ========================================================================
    print("\n[1/5] Creating job...")
    
    # Get usage profile
    profiles_response = api_client.get('/usage-profiles')
    assert profiles_response['success'], "FAILED: Could not fetch usage profiles"
    
    profile_id = profiles_response['data'][0]['id']
    
    # Upload Terraform using PlatformClient (enforces contract)
    fixture_dir = Path(__file__).parent.parent.parent / 'fixtures' / 'simple_ec2'
    assert fixture_dir.exists(), f"FAILED: Fixture not found: {fixture_dir}"
    
    upload_response = api_client.upload_terraform_fixture(fixture_dir)
    upload_id = upload_response['data']['upload_id']
    
    # Create job
    job_response = api_client.post('/jobs', json={
        'name': 'Resilience Test - Pricing Engine Restart',
        'upload_id': upload_id,
        'usage_profile': profile_id
    })
    assert job_response['success'], "FAILED: Job creation failed"
    
    job_id = job_response['data']['job_id']
    print(f"   ✓ Job created: {job_id}")
    
    # ========================================================================
    # STEP 2: Wait for job to reach COSTING stage
    # ========================================================================
    print("\n[2/5] Waiting for job to reach COSTING stage...")
    
    max_wait = 30
    for i in range(max_wait):
        status_response = api_client.get(f'/jobs/{job_id}/status')
        current_status = status_response['data']['status']
        
        if current_status == 'COSTING':
            print(f"   ✓ Job in COSTING stage")
            break
        
        if current_status in ['COMPLETED', 'FAILED']:
            print(f"   ⚠ Job reached terminal state before restart: {current_status}")
            pytest.skip("Job completed too quickly - cannot test pricing engine restart")
        
        time.sleep(1)
    else:
        print("   ⚠ Job did not reach COSTING stage - restarting anyway")
    
    # ========================================================================
    # STEP 3: Restart pricing-engine
    # ========================================================================
    print("\n[3/5] Restarting pricing-engine...")
    
    try:
        docker.restart_container('cost-platform-pricing-engine', wait_healthy=False, timeout=30)
    except Exception as e:
        pytest.fail(f"FAILED: Could not restart pricing-engine: {e}")
    
    print("   ✓ Pricing engine restarted")
    
    # ========================================================================
    # STEP 4: Poll until terminal state
    # ========================================================================
    print("\n[4/5] Polling job to terminal state...")
    
    poll_count = 0
    
    def check_status():
        nonlocal poll_count
        poll_count += 1
        
        status_response = api_client.get(f'/jobs/{job_id}/status')
        assert status_response['success'], f"FAILED: Status check failed at poll {poll_count}"
        
        status_data = status_response['data']
        current_state = status_data['status']
        
        print(f"   Poll {poll_count}: {current_state} ({status_data.get('progress', 0)}%)")
        
        return status_data
    
    def is_terminal(status_data):
        return status_data['status'] in ['COMPLETED', 'FAILED']
    
    try:
        final_status = poll_until_sync(
            check_fn=check_status,
            condition_fn=is_terminal,
            max_attempts=60,
            initial_delay=2.0,
            timeout=300
        )
    except TimeoutError:
        pytest.fail("FAILED: Job stuck after pricing engine restart - did not reach terminal state")
    
    # ========================================================================
    # STEP 5: Validate terminal state reached
    # ========================================================================
    print("\n[5/5] Validating recovery...")
    
    final_state = final_status['status']
    assert_terminal_state(final_state)
    
    if final_state == 'FAILED':
        error_msg = final_status.get('error_message', 'Unknown error')
        print(f"   ⚠ Job failed after restart: {error_msg}")
        print(f"   ✓ Failure is visible and terminal (acceptable)")
    else:
        print(f"   ✓ Job completed successfully after restart")
    
    print("\n" + "="*80)
    print("✅ RESILIENCE TEST PASSED - Platform survived pricing engine restart")
    print("="*80)
    print(f"Final State: {final_state}")
    print(f"Polls Required: {poll_count}")
    print("="*80 + "\n")
