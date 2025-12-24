"""
End-to-end test - REAL execution with HARD FAILURES.

This test executes the COMPLETE user flow with NO soft assertions:
1. Upload real Terraform files
2. Create real job
3. Poll until terminal state
4. Fetch real results
5. Verify immutability

ANY failure blocks deployment.
"""
import pytest
import os
from pathlib import Path
from utils.polling import poll_until_sync
from utils.assertions import (
    assert_valid_state_transition,
    assert_terminal_state,
    assert_monotonic_progress,
    assert_immutable_result
)


@pytest.mark.e2e
@pytest.mark.slow
def test_full_user_flow_real_execution(api_client, track_correlation):
    """
    REAL end-to-end test - NO SKIPS, NO MOCKS.
    
    This test MUST pass for platform to be production-ready.
    Any failure indicates platform is NOT functional.
    """
    print("\n" + "="*80)
    print("E2E TEST: FULL USER FLOW - REAL EXECUTION")
    print("="*80)
    
    # ========================================================================
    # STEP 1: Get usage profiles
    # ========================================================================
    print("\n[1/6] Fetching usage profiles...")
    profiles_response = api_client.get('/usage-profiles', validate_schema='UsageProfile')
    track_correlation(profiles_response, '/usage-profiles', 'GET')
    
    assert profiles_response['success'], \
        f"FAILED: Could not fetch usage profiles. correlation_id={profiles_response.get('correlation_id')}"
    
    profiles = profiles_response['data']
    assert isinstance(profiles, list), "Usage profiles must be a list"
    assert len(profiles) > 0, "FAILED: No usage profiles available"
    
    # Use first profile
    profile = profiles[0]
    profile_id = profile.get('id')
    assert profile_id is not None, "FAILED: Usage profile missing 'id' field"
    
    print(f"   ✓ Using profile: {profile.get('name', profile_id)}")
    
    # ========================================================================
    # STEP 2: Upload Terraform files
    # ========================================================================
    print("\n[2/6] Uploading Terraform files...")
    
    # Get fixture path
    fixture_dir = Path(__file__).parent.parent.parent / 'fixtures' / 'simple_ec2'
    assert fixture_dir.exists(), f"FAILED: Fixture directory not found: {fixture_dir}"
    
    main_tf = fixture_dir / 'main.tf'
    providers_tf = fixture_dir / 'providers.tf'
    
    assert main_tf.exists(), f"FAILED: main.tf not found: {main_tf}"
    assert providers_tf.exists(), f"FAILED: providers.tf not found: {providers_tf}"
    
    # Upload using PlatformClient (enforces contract)
    upload_response = api_client.upload_terraform_fixture(fixture_dir)
    track_correlation(upload_response, '/uploads', 'POST')
    
    # Extract upload_id (already validated by client)
    upload_id = upload_response['data']['upload_id']
    
    print(f"   ✓ Upload successful: {upload_id}")

    
    # ========================================================================
    # STEP 3: Create job
    # ========================================================================
    print("\n[3/6] Creating job...")
    
    job_payload = {
        'name': 'E2E Test Job - Real Execution',
        'upload_id': upload_id,
        'usage_profile': profile_id
    }
    
    job_response = api_client.post('/jobs', json=job_payload, validate_schema='Job')
    track_correlation(job_response, '/jobs', 'POST')
    
    assert job_response['success'], \
        f"FAILED: Job creation failed. Error: {job_response.get('error')}"
    
    job_data = job_response['data']
    job_id = job_data.get('job_id')
    assert job_id is not None, "FAILED: Job response missing 'job_id'"
    
    print(f"   ✓ Job created: {job_id}")
    print(f"   Initial status: {job_data.get('status')}")
    
    # ========================================================================
    # STEP 4: Poll job status until terminal
    # ========================================================================
    print("\n[4/6] Polling job status...")
    
    previous_state = None
    previous_progress = 0
    poll_count = 0
    max_polls = 60
    
    def check_job_status():
        nonlocal previous_state, previous_progress, poll_count
        poll_count += 1
        
        status_response = api_client.get(f'/jobs/{job_id}/status')
        assert status_response['success'], \
            f"FAILED: Status check failed at poll {poll_count}"
        
        status_data = status_response['data']
        current_state = status_data.get('status')
        current_progress = status_data.get('progress', 0)
        
        # Validate state transition
        if previous_state is not None and previous_state != current_state:
            assert_valid_state_transition(previous_state, current_state)
        
        # Validate monotonic progress
        if current_state not in ['FAILED']:
            assert_monotonic_progress(previous_progress, current_progress)
        
        previous_state = current_state
        previous_progress = current_progress
        
        print(f"   Poll {poll_count}: {current_state} ({current_progress}%)")
        
        return status_data
    
    def is_terminal(status_data):
        state = status_data.get('status')
        return state in ['COMPLETED', 'FAILED']
    
    try:
        final_status = poll_until_sync(
            check_fn=check_job_status,
            condition_fn=is_terminal,
            max_attempts=max_polls,
            initial_delay=2.0,
            max_delay=10.0,
            timeout=300
        )
    except TimeoutError as e:
        pytest.fail(f"FAILED: Job did not reach terminal state within timeout. Last state: {previous_state}")
    
    final_state = final_status.get('status')
    assert_terminal_state(final_state)
    
    # MUST be COMPLETED, not FAILED
    assert final_state == 'COMPLETED', \
        f"FAILED: Job ended in FAILED state. Error: {final_status.get('error_message')}"
    
    print(f"   ✓ Job completed successfully after {poll_count} polls")
    
    # ========================================================================
    # STEP 5: Fetch results
    # ========================================================================
    print("\n[5/6] Fetching cost results...")
    
    results_response = api_client.get(f'/jobs/{job_id}/results', validate_schema='CostResult')
    track_correlation(results_response, f'/jobs/{job_id}/results', 'GET')
    
    assert results_response['success'], \
        f"FAILED: Could not fetch results. Error: {results_response.get('error')}"
    
    results = results_response['data']
    
    # Validate results structure
    assert 'total_monthly_cost' in results, "FAILED: Results missing 'total_monthly_cost'"
    assert 'currency' in results, "FAILED: Results missing 'currency'"
    assert 'breakdown' in results, "FAILED: Results missing 'breakdown'"
    
    total_cost = results['total_monthly_cost']
    currency = results['currency']
    breakdown = results['breakdown']
    
    assert isinstance(total_cost, (int, float)), "FAILED: total_monthly_cost must be numeric"
    assert total_cost >= 0, "FAILED: total_monthly_cost cannot be negative"
    assert isinstance(breakdown, list), "FAILED: breakdown must be a list"
    assert len(breakdown) > 0, "FAILED: breakdown cannot be empty"
    
    print(f"   ✓ Results fetched successfully")
    print(f"   Total cost: {currency} {total_cost:.2f}/month")
    print(f"   Resources: {len(breakdown)}")
    
    # ========================================================================
    # STEP 6: Verify immutability
    # ========================================================================
    print("\n[6/6] Verifying result immutability...")
    
    # Fetch results again
    results_response_2 = api_client.get(f'/jobs/{job_id}/results')
    results_2 = results_response_2['data']
    
    # Results MUST be identical
    assert_immutable_result(job_id, results, results_2)
    
    print(f"   ✓ Results are immutable")
    
    # ========================================================================
    # SUCCESS
    # ========================================================================
    print("\n" + "="*80)
    print("✅ E2E TEST PASSED - PLATFORM IS PRODUCTION-READY")
    print("="*80)
    print(f"Job ID: {job_id}")
    print(f"Total Cost: {currency} {total_cost:.2f}/month")
    print(f"Resources Analyzed: {len(breakdown)}")
    print(f"Polls Required: {poll_count}")
    print("="*80 + "\n")


def create_terraform_zip(fixture_dir: Path) -> bytes:
    """
    Create a ZIP file from Terraform fixtures.
    
    Args:
        fixture_dir: Path to fixture directory
        
    Returns:
        ZIP file bytes
    """
    import io
    import zipfile
    
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for tf_file in fixture_dir.glob('*.tf'):
            zip_file.write(tf_file, arcname=tf_file.name)
    
    zip_buffer.seek(0)
    return zip_buffer.read()
