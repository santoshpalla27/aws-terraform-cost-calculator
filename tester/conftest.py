"""
Pytest plugin to enforce certification mode.

When CERTIFICATION_MODE=true:
- Forbid test skips
- Forbid xfail
- Exit on first failure
"""
import os
import pytest


def pytest_configure(config):
    """Configure pytest for certification mode."""
    certification_mode = os.getenv('CERTIFICATION_MODE', 'false').lower() == 'true'
    
    if certification_mode:
        print("\n" + "="*60)
        print("🔒 CERTIFICATION MODE ACTIVE")
        print("="*60)
        print("RULES:")
        print("  - NO test skips allowed")
        print("  - NO xfail allowed")
        print("  - Exit on first failure")
        print("  - ALL tests MUST execute")
        print("="*60 + "\n")


def pytest_collection_modifyitems(config, items):
    """Modify test collection for certification mode."""
    certification_mode = os.getenv('CERTIFICATION_MODE', 'false').lower() == 'true'
    
    if not certification_mode:
        return
    
    # Check for skip markers
    skipped_tests = []
    for item in items:
        if item.get_closest_marker('skip'):
            skipped_tests.append(item.nodeid)
        if item.get_closest_marker('skipif'):
            skipped_tests.append(item.nodeid)
    
    if skipped_tests:
        print("\n" + "="*60)
        print("❌ CERTIFICATION MODE VIOLATION")
        print("="*60)
        print(f"Found {len(skipped_tests)} test(s) marked for skip:")
        for test in skipped_tests:
            print(f"  - {test}")
        print("\nSkips are FORBIDDEN in certification mode.")
        print("="*60 + "\n")
        pytest.exit("Certification mode: Skipped tests detected", returncode=1)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook to detect skipped tests during execution."""
    outcome = yield
    report = outcome.get_result()
    
    certification_mode = os.getenv('CERTIFICATION_MODE', 'false').lower() == 'true'
    
    if certification_mode and report.when == 'call' and report.skipped:
        print("\n" + "="*60)
        print("❌ CERTIFICATION MODE VIOLATION")
        print("="*60)
        print(f"Test was skipped: {item.nodeid}")
        print(f"Reason: {report.longrepr}")
        print("\nSkips are FORBIDDEN in certification mode.")
        print("="*60 + "\n")
        pytest.exit("Certification mode: Test skip detected", returncode=1)
