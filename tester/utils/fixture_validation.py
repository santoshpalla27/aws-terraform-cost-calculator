"""
Fixture validation utilities - CERTIFIED INPUT enforcement.

Ensures Terraform fixtures are locked and validated before use.
"""
import hashlib
from pathlib import Path
from typing import Dict, List


# CERTIFIED FIXTURE HASHES - These are the ONLY valid fixtures
CERTIFIED_FIXTURES = {
    'simple_ec2': {
        'main.tf': '760bf3dd6d7da90029bdfe6ebee16c63f11ba4ff2cb3c378952f943f670f110da86898',
        'providers.tf': '8080cf6f5ab295ce9408d76df05f5f884702fa5bce76373a6fdd0e5b9f0e4e5a',
        'expected_resources': 1,  # Number of resources in plan
        'forbidden_features': [
            'external',  # No external data sources
            'local-exec',  # No local-exec provisioners
            'remote-exec',  # No remote-exec provisioners
        ]
    }
}


def compute_file_hash(file_path: Path) -> str:
    """
    Compute SHA256 hash of file.
    
    Args:
        file_path: Path to file
        
    Returns:
        Hex digest of SHA256 hash
    """
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()


def validate_fixture_hashes(fixture_dir: Path, fixture_name: str) -> Dict[str, str]:
    """
    Validate fixture file hashes against certified values.
    
    Args:
        fixture_dir: Path to fixture directory
        fixture_name: Name of fixture (e.g., 'simple_ec2')
        
    Returns:
        Dictionary of file -> hash
        
    Raises:
        AssertionError: If hashes don't match or files missing
    """
    if fixture_name not in CERTIFIED_FIXTURES:
        raise AssertionError(f"Unknown fixture: {fixture_name}. Not certified.")
    
    certified = CERTIFIED_FIXTURES[fixture_name]
    actual_hashes = {}
    
    # Compute actual hashes
    for filename in certified.keys():
        if filename.startswith('expected_') or filename == 'forbidden_features':
            continue
        
        file_path = fixture_dir / filename
        if not file_path.exists():
            raise AssertionError(f"FIXTURE VIOLATION: Missing file {filename}")
        
        actual_hash = compute_file_hash(file_path)
        actual_hashes[filename] = actual_hash
        
        # For initial setup, print hashes to update CERTIFIED_FIXTURES
        if certified[filename] == f'PLACEHOLDER_HASH_{filename.upper().replace(".", "_")}':
            print(f"   [SETUP] {filename}: {actual_hash}")
            continue
        
        # Validate hash
        expected_hash = certified[filename]
        if actual_hash != expected_hash:
            raise AssertionError(
                f"FIXTURE VIOLATION: {filename} hash mismatch.\n"
                f"Expected: {expected_hash}\n"
                f"Actual:   {actual_hash}\n"
                f"Fixture has been modified!"
            )
    
    return actual_hashes


def validate_terraform_content(fixture_dir: Path, fixture_name: str):
    """
    Validate Terraform content for forbidden features.
    
    Args:
        fixture_dir: Path to fixture directory
        fixture_name: Name of fixture
        
    Raises:
        AssertionError: If forbidden features detected
    """
    if fixture_name not in CERTIFIED_FIXTURES:
        return
    
    certified = CERTIFIED_FIXTURES[fixture_name]
    forbidden = certified.get('forbidden_features', [])
    
    # Read all .tf files
    all_content = []
    for tf_file in fixture_dir.glob('*.tf'):
        with open(tf_file, 'r') as f:
            all_content.append(f.read())
    
    combined_content = '\n'.join(all_content).lower()
    
    # Check for forbidden features
    violations = []
    for feature in forbidden:
        if feature.lower() in combined_content:
            violations.append(feature)
    
    if violations:
        raise AssertionError(
            f"FIXTURE VIOLATION: Forbidden Terraform features detected: {violations}\n"
            f"Certified fixtures must not use: {forbidden}"
        )


def assert_fixture_certified(fixture_dir: Path, fixture_name: str = 'simple_ec2'):
    """
    Assert fixture is certified and unmodified.
    
    This is the main entry point for fixture validation.
    
    Args:
        fixture_dir: Path to fixture directory
        fixture_name: Name of fixture to validate
        
    Raises:
        AssertionError: If fixture is not certified
    """
    print(f"\n   [CERTIFICATION] Validating fixture: {fixture_name}")
    
    # Validate hashes
    actual_hashes = validate_fixture_hashes(fixture_dir, fixture_name)
    print(f"   ✓ File hashes validated: {len(actual_hashes)} files")
    
    # Validate content
    validate_terraform_content(fixture_dir, fixture_name)
    print(f"   ✓ Terraform content validated (no forbidden features)")
    
    print(f"   ✓ Fixture certified: {fixture_name}")
