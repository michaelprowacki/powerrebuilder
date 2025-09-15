# PowerRebuilder Security Documentation

## Overview

PowerRebuilder implements comprehensive security measures to protect against common vulnerabilities and attacks. This document details the security features, best practices, and configuration options.

## Security Principles

1. **Defense in Depth**: Multiple layers of security controls
2. **Least Privilege**: Minimal permissions for operations
3. **Fail Secure**: Safe defaults and graceful failure
4. **Input Validation**: Strict validation of all inputs
5. **Resource Limits**: Prevention of resource exhaustion

## Security Features

### 1. Path Traversal Protection

PowerRebuilder prevents path traversal attacks through multiple mechanisms:

#### Path Validation

```python
from src.extract.security.path_validator import PathValidator

# Create validator with base directory
validator = PathValidator("/safe/output")

# Validate user-provided paths
try:
    safe_path = validator.validate_path(user_input)
except ValueError as e:
    # Path traversal attempt detected
    log_security_event(e)
```

#### Protection Mechanisms

- **Canonical Path Resolution**: Resolves symlinks and relative paths
- **Boundary Checking**: Ensures paths stay within allowed directories
- **Character Filtering**: Blocks special characters and escape sequences
- **Null Byte Protection**: Prevents null byte injection attacks

#### Examples of Blocked Patterns

```
../../../etc/passwd          # Unix path traversal
..\..\windows\system32       # Windows path traversal
/etc/passwd                  # Absolute path escape
C:\Windows\System32          # Windows absolute path
../../${HOME}/.ssh           # Environment variable injection
file.txt\x00.jpg            # Null byte injection
```

### 2. Resource Limiting

Prevents denial of service through resource exhaustion:

#### Memory Limits

```python
from src.extract.security.resource_limiter import ResourceLimiter

limiter = ResourceLimiter(
    max_memory=512 * 1024 * 1024,  # 512MB
    max_file_size=100 * 1024 * 1024,  # 100MB
    max_files=1000,
    timeout=300  # 5 minutes
)

# Check before allocation
limiter.check_memory(requested_size)
limiter.track_file("output.txt")
```

#### CPU Limits

- Operation timeouts
- CPU time quotas
- Parallel worker limits
- Priority-based scheduling

#### I/O Limits

- Maximum file size restrictions
- File count limitations
- Disk quota enforcement
- I/O throttling

### 3. Input Validation

Comprehensive validation of all user inputs:

#### Filename Sanitization

```python
from src.extract.security.input_validator import InputValidator

validator = InputValidator()

# Sanitize filenames
safe_name = validator.sanitize_filename(user_filename)
# Removes: ../, ..\, |, >, <, :, ", ?, *, null bytes

# Validate file types
if not validator.is_allowed_type(filename, ['.pbl', '.pbd']):
    raise ValueError("Invalid file type")
```

#### Content Validation

- File signature verification
- Size validation
- Character encoding checks
- Format compliance verification

### 4. Zip Bomb Protection

Protection against decompression attacks:

```python
from src.extract.security.decompression_guard import DecompressionGuard

guard = DecompressionGuard(
    max_ratio=100,  # Max 100:1 compression ratio
    max_depth=5,    # Max 5 levels of nesting
    max_total_size=1024 * 1024 * 1024  # 1GB total
)

# Check before decompression
guard.check_compression_ratio(compressed_size, uncompressed_size)
guard.enter_archive("nested.zip")
```

### 5. SQL Injection Prevention

For generated SQL code:

```python
from src.generate.security.sql_sanitizer import SQLSanitizer

sanitizer = SQLSanitizer()

# Parameterized queries
query = sanitizer.prepare_query(
    "SELECT * FROM users WHERE id = ?",
    [user_id]
)

# Input sanitization
safe_value = sanitizer.sanitize_value(user_input)
```

### 6. Template Injection Prevention

For code generation templates:

```python
from src.generate.security.template_sanitizer import TemplateSanitizer

sanitizer = TemplateSanitizer()

# Escape template syntax
safe_content = sanitizer.sanitize_template(user_content)
# Escapes: {{, }}, {%, %}, ${, }
```

## Security Configuration

### Default Security Settings

```yaml
# config/security.yaml
security:
  # Path traversal protection
  path_validation:
    enabled: true
    allowed_paths:
      - "${OUTPUT_DIR}"
    blocked_patterns:
      - ".."
      - "~"
      - "$"

  # Resource limits
  resource_limits:
    max_file_size: 104857600  # 100MB
    max_files: 1000
    max_memory: 536870912     # 512MB
    max_cpu_seconds: 300
    timeout: 600              # 10 minutes

  # Input validation
  input_validation:
    enabled: true
    allowed_extensions:
      - .pbl
      - .pbd
      - .srw
      - .srd
      - .sru
    max_filename_length: 255

  # Decompression protection
  decompression:
    max_ratio: 100
    max_nested_depth: 5
    max_extracted_size: 1073741824  # 1GB

  # Audit logging
  audit:
    enabled: true
    log_file: "security_audit.log"
    log_level: "WARNING"
    include_stacktrace: false
```

### Environment-Specific Settings

#### Development

```yaml
security:
  path_validation:
    enabled: true
    strict_mode: false  # Allow more flexibility
  resource_limits:
    max_file_size: 1073741824  # 1GB for testing
  audit:
    log_level: "DEBUG"
    include_stacktrace: true
```

#### Production

```yaml
security:
  path_validation:
    enabled: true
    strict_mode: true
    jail_mode: true  # Strict sandboxing
  resource_limits:
    max_file_size: 52428800  # 50MB
    max_memory: 268435456    # 256MB
  audit:
    enabled: true
    remote_logging: true
    alert_on_violation: true
```

## Security Best Practices

### 1. Deployment Security

- **Run with minimal privileges**: Use dedicated user account
- **File system permissions**: Restrict write access
- **Network isolation**: Limit network access if not needed
- **Container security**: Use read-only containers where possible

### 2. Configuration Security

- **Secure defaults**: Always fail closed
- **Environment variables**: Use for sensitive configuration
- **Secret management**: Never hardcode credentials
- **Configuration validation**: Verify settings at startup

### 3. Operational Security

- **Regular updates**: Keep dependencies updated
- **Security scanning**: Regular vulnerability scans
- **Audit log review**: Monitor for suspicious activity
- **Incident response**: Have a plan for security events

### 4. Input Handling

```python
# Always validate and sanitize inputs
def process_file(filename):
    # Validate filename
    if not is_valid_filename(filename):
        raise SecurityError("Invalid filename")

    # Resolve to absolute path
    abs_path = os.path.abspath(filename)

    # Check within allowed directory
    if not abs_path.startswith(ALLOWED_DIR):
        raise SecurityError("Path traversal detected")

    # Check file exists and is regular file
    if not os.path.isfile(abs_path):
        raise SecurityError("Invalid file")

    # Proceed with processing
    process_safe_file(abs_path)
```

## Security Monitoring

### Audit Events

The following events are logged for security monitoring:

1. **Path Traversal Attempts**
   ```
   [SECURITY] Path traversal attempt: ../../../etc/passwd from IP 192.168.1.100
   ```

2. **Resource Limit Violations**
   ```
   [SECURITY] Resource limit exceeded: memory usage 1.2GB exceeds 1GB limit
   ```

3. **Invalid Input Detection**
   ```
   [SECURITY] Invalid input detected: SQL injection pattern in field 'username'
   ```

4. **Authentication Failures** (if applicable)
   ```
   [SECURITY] Authentication failed for user 'admin' from IP 192.168.1.100
   ```

### Security Metrics

Monitor these metrics for security health:

- Path validation failures per hour
- Resource limit violations per day
- Invalid input attempts per hour
- Circuit breaker trips per hour
- Average resource usage percentages

### Alert Thresholds

```yaml
alerts:
  path_traversal:
    threshold: 10  # per hour
    action: "email"
  resource_exhaustion:
    threshold: 5   # per hour
    action: "page"
  repeated_failures:
    threshold: 100 # per hour
    action: "block_ip"
```

## Vulnerability Response

### Reporting Security Issues

Report security vulnerabilities to: security@powerrebuilder.example.com

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Security Update Process

1. **Vulnerability reported**
2. **Triage and verify** (24 hours)
3. **Develop fix** (depends on severity)
4. **Test fix** (comprehensive testing)
5. **Release update** (with security advisory)
6. **Notify users** (email and changelog)

## Security Checklist

Before deployment, ensure:

- [ ] All security features enabled
- [ ] Resource limits configured appropriately
- [ ] Audit logging enabled and monitored
- [ ] File permissions properly set
- [ ] Latest security updates applied
- [ ] Security configuration reviewed
- [ ] Incident response plan in place
- [ ] Monitoring alerts configured
- [ ] Backup and recovery tested
- [ ] Security training completed

## Common Attack Scenarios

### 1. Path Traversal Attack

**Attack**: `../../../etc/passwd`
**Defense**: Path validator rejects traversal patterns
**Result**: `ValueError: Path traversal attempt detected`

### 2. Resource Exhaustion Attack

**Attack**: Upload 10GB file
**Defense**: File size limit enforced
**Result**: `ValueError: File size exceeds maximum allowed`

### 3. Zip Bomb Attack

**Attack**: 42.zip (4.5PB when extracted)
**Defense**: Compression ratio check
**Result**: `ValueError: Suspicious compression ratio detected`

### 4. Memory Exhaustion Attack

**Attack**: Trigger infinite memory allocation
**Defense**: Memory limits and timeouts
**Result**: `MemoryError: Memory limit exceeded`

## Compliance

PowerRebuilder's security features help meet common compliance requirements:

- **OWASP Top 10**: Addresses common web vulnerabilities
- **CWE/SANS Top 25**: Prevents dangerous software errors
- **GDPR**: Supports data protection requirements
- **SOC 2**: Enables security controls for compliance

## Additional Resources

- [OWASP Secure Coding Practices](https://owasp.org/www-project-secure-coding-practices-quick-reference-guide/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [Security Configuration Baseline](./config/security-baseline.yaml)
- [Incident Response Playbook](./docs/INCIDENT_RESPONSE.md)
