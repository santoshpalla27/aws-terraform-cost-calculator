# Security Model

## Threat Model

### Assets

- **Terraform Configurations**: Untrusted user input
- **Execution Environment**: Container with limited resources
- **Plan JSON Output**: Sensitive infrastructure information

### Threats

1. **Arbitrary Code Execution**
   - Via `local-exec` provisioner
   - Via `external` provider
   - Via shell injection

2. **Data Exfiltration**
   - Via network requests
   - Via file writes
   - Via external providers

3. **Resource Exhaustion**
   - CPU consumption
   - Memory consumption
   - Disk space consumption
   - Infinite loops

4. **State Persistence**
   - Backend configuration
   - Remote state access
   - Credential leakage

5. **Path Traversal**
   - Directory traversal attacks
   - Symlink attacks
   - File overwrites

## Security Controls

### 1. Container Isolation

**Read-Only Filesystem**
- Root filesystem mounted read-only
- Only `/tmp` and `/home/tfuser/.terraform.d` writable (tmpfs)
- No persistence between executions
- Prevents file-based attacks

**Non-Root User**
- Runs as UID 1000 (tfuser)
- No sudo/privilege escalation
- Minimal capabilities
- Prevents privilege escalation

**Resource Limits**
- Memory: 512MB (hard limit)
- CPU: 1.0 core
- Execution timeout: 5 minutes
- Disk space: Limited by tmpfs size (256MB)

**Network Isolation** (configurable)
- Can disable network access
- Prevents data exfiltration
- Blocks external provider downloads (requires mirror)

### 2. Provider Filtering

**Blocked Providers:**
```
- local-exec (provisioner)
- remote-exec (provisioner)
- external (provider)
- null (when used with provisioners)
```

**Detection Method:**
- Regex pattern matching in .tf files
- Scans for provider blocks
- Scans for resource usage
- Scans for provisioner blocks

**Enforcement:**
- Pre-execution validation
- Fails before Terraform init
- Returns error to caller

### 3. Backend Blocking

**Blocked:**
- All backend configurations
- Remote state access
- State locking mechanisms

**Detection Method:**
- Regex pattern matching for `backend "..."` blocks
- Scans all .tf files

**Enforcement:**
- Pre-execution validation
- Forces `-backend=false` flag
- No state persistence

### 4. Timeout Enforcement

**Limits:**
- Per-command timeout: 5 minutes (default)
- Total execution timeout: 5 minutes
- Subprocess timeout via Python subprocess

**Enforcement:**
- `subprocess.run(timeout=...)`
- Returns TIMEOUT status
- Kills subprocess on timeout

### 5. Path Sanitization

**Sanitization:**
- Removes `..` sequences
- Removes null bytes
- Validates paths are within workspace

**Enforcement:**
- Applied to all file paths
- Prevents directory traversal
- Prevents symlink attacks

## Attack Surface Analysis

### Attack Vectors

1. **Malicious Terraform Configuration**
   - **Risk**: HIGH
   - **Mitigation**: Provider filtering, backend blocking, provisioner blocking
   - **Status**: ✅ Mitigated

2. **Resource Exhaustion**
   - **Risk**: MEDIUM
   - **Mitigation**: Resource limits, timeout enforcement
   - **Status**: ✅ Mitigated

3. **Container Escape**
   - **Risk**: LOW
   - **Mitigation**: Read-only filesystem, non-root user, minimal capabilities
   - **Status**: ✅ Mitigated

4. **Network-Based Attacks**
   - **Risk**: MEDIUM (if network enabled)
   - **Mitigation**: Network isolation (configurable)
   - **Status**: ⚠️ Partially mitigated (network required for provider downloads)

5. **Terraform Vulnerabilities**
   - **Risk**: LOW
   - **Mitigation**: Version pinning, regular updates
   - **Status**: ⚠️ Ongoing

## Residual Risks

### 1. Complex Terraform Configurations

**Risk**: Legitimate Terraform configurations may consume significant resources

**Mitigation**:
- Resource limits prevent complete exhaustion
- Timeout prevents infinite execution
- Monitoring alerts on high resource usage

**Recommendation**: Monitor execution metrics

### 2. Provider Downloads

**Risk**: Network access required for provider downloads

**Mitigation**:
- Use provider mirror in production
- Pre-download allowed providers
- Mount as read-only volume

**Recommendation**: Implement provider mirror

### 3. Terraform Bugs

**Risk**: Terraform CLI may have vulnerabilities

**Mitigation**:
- Pin Terraform version
- Regular security updates
- Monitor Terraform security advisories

**Recommendation**: Establish update process

## Security Best Practices

### Production Deployment

1. **Disable Network Access**
   ```yaml
   environment:
     - ALLOW_NETWORK=false
   ```

2. **Use Provider Mirror**
   ```bash
   # Pre-download providers
   terraform providers mirror /mirror
   
   # Mount as read-only
   volumes:
     - ./mirror:/mirror:ro
   ```

3. **Enable Audit Logging**
   ```yaml
   environment:
     - LOG_LEVEL=INFO
     - LOG_FORMAT=json
   ```

4. **Monitor Resources**
   ```bash
   docker stats terraform-executor
   ```

5. **Regular Updates**
   - Update Terraform version monthly
   - Update base image weekly
   - Update Python dependencies weekly

### Incident Response

**If Suspicious Activity Detected:**

1. Stop container immediately
2. Review execution logs
3. Analyze Terraform configuration
4. Check for data exfiltration
5. Update security controls

**Indicators of Compromise:**
- Unexpected network connections
- High resource usage
- Long execution times
- Unusual Terraform output
- Failed security validations

## Compliance

### Security Standards

- **OWASP**: Follows OWASP container security guidelines
- **CIS**: Aligns with CIS Docker benchmarks
- **Least Privilege**: Runs with minimal permissions
- **Defense in Depth**: Multiple layers of security

### Audit Trail

All executions logged with:
- Job ID
- Upload ID
- Execution time
- Status (SUCCESS/FAILED/TIMEOUT)
- Error messages
- Terraform output (debug mode)

## Security Testing

### Test Cases

1. **Blocked Provider Test**
   ```hcl
   resource "null_resource" "test" {
     provisioner "local-exec" {
       command = "echo test"
     }
   }
   ```
   Expected: Execution blocked

2. **Backend Test**
   ```hcl
   terraform {
     backend "s3" {
       bucket = "test"
     }
   }
   ```
   Expected: Execution blocked

3. **Timeout Test**
   ```hcl
   # Configuration that takes > 5 minutes
   ```
   Expected: Timeout after 5 minutes

4. **Resource Limit Test**
   ```hcl
   # Configuration that requires > 512MB RAM
   ```
   Expected: Container killed by OOM

## Conclusion

This service implements defense-in-depth security with multiple layers:
1. Container isolation
2. Provider filtering
3. Backend blocking
4. Resource limits
5. Timeout enforcement

While no system is 100% secure, these controls significantly reduce the attack surface and mitigate known threats.
