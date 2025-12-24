"""
Determinism test - MATHEMATICAL EXACTNESS enforced.

This test validates that the platform is DETERMINISTIC:
- Same Terraform input → EXACT same cost output
- No floating point drift
- No random variation
- No timestamp-based differences

ANY delta between runs → FAIL
"""
import pytest
from pathlib import Path


@pytest.mark.e2e
@pytest.mark.slow
def test_deterministic_cost_calculation(api_client, track_correlation):
    """
    Test that identical Terraform produces IDENTICAL costs.
    
    HARD REQUIREMENTS:
    - Same fixture uploaded twice
    - Two separate jobs created
    - Results MUST be EXACTLY equal (no tolerance)
    - total_monthly_cost MUST match
    - breakdown MUST match
    - currency MUST match
    
    ANY difference → FAIL
    """
    print("\n" + "="*80)
    print("DETERMINISM TEST: Mathematical Exactness")
    print("="*80)
    
    # Get usage profile
    profiles_response = api_client.get('/usage-profiles')
    assert profiles_response['success'], "FAILED: Could not fetch usage profiles"
    profile_id = profiles_response['data'][0]['id']
    
    # Get fixture
    fixture_dir = Path(__file__).parent.parent.parent / 'fixtures' / 'simple_ec2'
    assert fixture_dir.exists(), f"FAILED: Fixture not found: {fixture_dir}"
    
    results = []
    job_ids = []
    
    # ========================================================================
    # RUN 1: First execution
    # ========================================================================
    print("\n[RUN 1] First execution...")
    
    upload_response_1 = api_client.upload_terraform_fixture(fixture_dir)
    upload_id_1 = upload_response_1['data']['upload_id']
    print(f"   Upload 1: {upload_id_1}")
    
    job_response_1 = api_client.post('/jobs', json={
        'name': 'Determinism Test - Run 1',
        'upload_id': upload_id_1,
        'usage_profile': profile_id
    })
    assert job_response_1['success'], "FAILED: Job 1 creation failed"
    
    job_id_1 = job_response_1['data']['job_id']
    job_ids.append(job_id_1)
    print(f"   Job 1: {job_id_1}")
    
    # Wait for completion
    from utils.polling import poll_until_sync
    
    def check_status_1():
        status = api_client.get(f'/jobs/{job_id_1}/status')
        return status['data']
    
    def is_terminal(data):
        return data['status'] in ['COMPLETED', 'FAILED']
    
    final_status_1 = poll_until_sync(
        check_fn=check_status_1,
        condition_fn=is_terminal,
        max_attempts=60,
        timeout=300
    )
    
    assert final_status_1['status'] == 'COMPLETED', \
        f"FAILED: Job 1 failed: {final_status_1.get('error_message')}"
    
    # Get results
    results_response_1 = api_client.get(f'/jobs/{job_id_1}/results')
    assert results_response_1['success'], "FAILED: Could not fetch results 1"
    results.append(results_response_1['data'])
    
    print(f"   ✓ Job 1 completed: {results[0]['currency']} {results[0]['total_monthly_cost']:.2f}")
    
    # ========================================================================
    # RUN 2: Second execution (IDENTICAL input)
    # ========================================================================
    print("\n[RUN 2] Second execution (identical input)...")
    
    upload_response_2 = api_client.upload_terraform_fixture(fixture_dir)
    upload_id_2 = upload_response_2['data']['upload_id']
    print(f"   Upload 2: {upload_id_2}")
    
    job_response_2 = api_client.post('/jobs', json={
        'name': 'Determinism Test - Run 2',
        'upload_id': upload_id_2,
        'usage_profile': profile_id
    })
    assert job_response_2['success'], "FAILED: Job 2 creation failed"
    
    job_id_2 = job_response_2['data']['job_id']
    job_ids.append(job_id_2)
    print(f"   Job 2: {job_id_2}")
    
    # Wait for completion
    def check_status_2():
        status = api_client.get(f'/jobs/{job_id_2}/status')
        return status['data']
    
    final_status_2 = poll_until_sync(
        check_fn=check_status_2,
        condition_fn=is_terminal,
        max_attempts=60,
        timeout=300
    )
    
    assert final_status_2['status'] == 'COMPLETED', \
        f"FAILED: Job 2 failed: {final_status_2.get('error_message')}"
    
    # Get results
    results_response_2 = api_client.get(f'/jobs/{job_id_2}/results')
    assert results_response_2['success'], "FAILED: Could not fetch results 2"
    results.append(results_response_2['data'])
    
    print(f"   ✓ Job 2 completed: {results[1]['currency']} {results[1]['total_monthly_cost']:.2f}")
    
    # ========================================================================
    # VALIDATE: EXACT EQUALITY
    # ========================================================================
    print("\n[VALIDATION] Enforcing mathematical determinism...")
    
    result_1 = results[0]
    result_2 = results[1]
    
    # ENFORCE: Currency must match
    assert result_1['currency'] == result_2['currency'], \
        f"DETERMINISM VIOLATION: Currency mismatch. " \
        f"Job 1: {result_1['currency']}, Job 2: {result_2['currency']}"
    
    # ENFORCE: Total cost must be EXACTLY equal
    cost_1 = result_1['total_monthly_cost']
    cost_2 = result_2['total_monthly_cost']
    
    if cost_1 != cost_2:
        delta = abs(cost_1 - cost_2)
        print(f"\n   ❌ DETERMINISM VIOLATION DETECTED")
        print(f"   Job 1 ({job_id_1}): {cost_1}")
        print(f"   Job 2 ({job_id_2}): {cost_2}")
        print(f"   Delta: {delta}")
        pytest.fail(
            f"DETERMINISM VIOLATION: Total costs differ. "
            f"Job 1: {cost_1}, Job 2: {cost_2}, Delta: {delta}"
        )
    
    print(f"   ✓ Total cost identical: {result_1['currency']} {cost_1}")
    
    # ENFORCE: Breakdown must be EXACTLY equal
    breakdown_1 = sorted(result_1['breakdown'], key=lambda x: x.get('resource_name', ''))
    breakdown_2 = sorted(result_2['breakdown'], key=lambda x: x.get('resource_name', ''))
    
    assert len(breakdown_1) == len(breakdown_2), \
        f"DETERMINISM VIOLATION: Breakdown count mismatch. " \
        f"Job 1: {len(breakdown_1)}, Job 2: {len(breakdown_2)}"
    
    # Compare each resource
    for i, (res_1, res_2) in enumerate(zip(breakdown_1, breakdown_2)):
        resource_name = res_1.get('resource_name', f'resource_{i}')
        
        # Resource name must match
        assert res_1.get('resource_name') == res_2.get('resource_name'), \
            f"DETERMINISM VIOLATION: Resource name mismatch at index {i}"
        
        # Resource type must match
        assert res_1.get('resource_type') == res_2.get('resource_type'), \
            f"DETERMINISM VIOLATION: Resource type mismatch for {resource_name}"
        
        # Cost must be EXACTLY equal
        cost_1_res = res_1.get('monthly_cost', 0)
        cost_2_res = res_2.get('monthly_cost', 0)
        
        if cost_1_res != cost_2_res:
            delta_res = abs(cost_1_res - cost_2_res)
            print(f"\n   ❌ DETERMINISM VIOLATION in {resource_name}")
            print(f"   Job 1 cost: {cost_1_res}")
            print(f"   Job 2 cost: {cost_2_res}")
            print(f"   Delta: {delta_res}")
            pytest.fail(
                f"DETERMINISM VIOLATION: Cost mismatch for {resource_name}. "
                f"Job 1: {cost_1_res}, Job 2: {cost_2_res}, Delta: {delta_res}"
            )
    
    print(f"   ✓ Breakdown identical: {len(breakdown_1)} resources")
    
    # ========================================================================
    # SUCCESS
    # ========================================================================
    print("\n" + "="*80)
    print("✅ DETERMINISM TEST PASSED - Platform is mathematically deterministic")
    print("="*80)
    print(f"Job 1: {job_id_1}")
    print(f"Job 2: {job_id_2}")
    print(f"Total Cost: {result_1['currency']} {cost_1}")
    print(f"Resources: {len(breakdown_1)}")
    print(f"Delta: 0 (EXACT MATCH)")
    print("="*80 + "\n")
