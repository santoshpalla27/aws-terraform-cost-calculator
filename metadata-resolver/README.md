# AWS Metadata Resolver

Enriches Terraform resources with AWS-derived metadata using read-only AWS SDK calls.

## Overview

This service resolves metadata that Terraform doesn't expose by default, enabling more accurate cost estimation:
- **EC2**: Default EBS volumes from AMI, instance specs (vCPU, memory), networking
- **ALB/NLB**: LCU/NLCU capacity factors, cross-zone behavior
- **NAT Gateway**: Bandwidth limits, data processing characteristics
- **EKS**: Control plane costs, configuration details

## Features

### Metadata Resolution

**EC2 Instances:**
- Root volume size/type/IOPS from AMI
- vCPU, memory, network performance
- EBS optimization support
- Instance storage

**ALB/NLB:**
- LCU factors (connections, bytes, rules)
- NLCU factors (connections, bytes)
- Cross-zone load balancing defaults
- IP address type

**NAT Gateway:**
- Bandwidth (up to 45 Gbps)
- Data processing charges
- Connectivity type (public/private)

**EKS:**
- Control plane hourly cost ($0.10/hour)
- Multi-AZ high availability
- Logging and encryption configuration

### Caching Strategy

Aggressive caching to minimize AWS API calls:
- **AMI metadata**: 1 hour TTL
- **Instance types**: 24 hours TTL
- **ELB metadata**: 5 minutes TTL
- **EKS metadata**: 15 minutes TTL

Cache statistics available via `/health` endpoint.

### Graceful Degradation

If AWS metadata is unavailable:
- Returns original resource with `metadata_status.degraded: true`
- Cost estimation can proceed with reduced accuracy
- Logs warning for monitoring

## IAM Policy

Read-only permissions required:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:DescribeInstanceTypes",
        "ec2:DescribeImages",
        "elasticloadbalancing:DescribeLoadBalancers",
        "eks:DescribeCluster",
        "pricing:GetProducts"
      ],
      "Resource": "*"
    }
  ]
}
```

See [iam-policy.json](file:///d:/good%20projects/aws-terraform-cost-calculator/metadata-resolver/iam-policy.json) for complete policy.

## API Endpoints

### Enrich NRG

```http
POST /api/v1/enrich
Content-Type: application/json

{
  "nrg": {
    "resources": [...],
    "metadata": {...},
    "terraform_version": "1.6.6",
    "format_version": "1.2"
  }
}
```

**Response:**
```json
{
  "resources": [
    {
      "resource_id": "aws_instance.web",
      "resource_type": "aws_instance",
      "attributes": {...},
      "enriched_metadata": {
        "root_volume_size": 8,
        "root_volume_type": "gp3",
        "vcpu": 2,
        "memory_mb": 4096,
        "network_performance": "Up to 5 Gigabit"
      },
      "metadata_status": {
        "enriched": true,
        "degraded": false
      }
    }
  ],
  ...
}
```

### Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "cache_stats": {
    "hits": 150,
    "misses": 50,
    "total_requests": 200,
    "hit_rate_percent": 75.0
  }
}
```

### Clear Cache

```http
POST /api/v1/cache/clear?cache_type=ami
```

## Quick Start

### Local Development

```bash
cd metadata-resolver
pip install -r requirements.txt

# Set AWS credentials
export AWS_PROFILE=your-profile
# or
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...

python -m app.main
```

Service available at: http://localhost:8003

### Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `AWS_REGION` | us-east-1 | Default AWS region |
| `AWS_PROFILE` | None | AWS profile name |
| `CACHE_TTL_AMI` | 3600 | AMI cache TTL (seconds) |
| `CACHE_TTL_INSTANCE_TYPE` | 86400 | Instance type cache TTL |
| `CACHE_TTL_ELB` | 300 | ELB cache TTL |
| `CACHE_TTL_EKS` | 900 | EKS cache TTL |
| `ENABLE_GRACEFUL_DEGRADATION` | true | Enable graceful degradation |

## Architecture

```
┌─────────────────────┐
│ Plan Parser (NRG)   │
└──────────┬──────────┘
           │ NRG
           │
┌──────────▼──────────────────┐
│ Metadata Resolver           │
│                             │
│  ┌──────────────────────┐   │
│  │ Enricher             │   │
│  └──────┬───────────────┘   │
│         │                   │
│  ┌──────▼───────────────┐   │
│  │ Resolvers            │   │
│  │ - EC2Resolver        │   │
│  │ - ELBResolver        │   │
│  │ - NATResolver        │   │
│  │ - EKSResolver        │   │
│  └──────┬───────────────┘   │
│         │                   │
│  ┌──────▼───────────────┐   │
│  │ AWS Client + Cache   │   │
│  └──────────────────────┘   │
└──────────┬──────────────────┘
           │ Enriched NRG
           │
┌──────────▼──────────────┐
│ Pricing Engine          │
└─────────────────────────┘
```

## Example: EC2 Enrichment

### Input

```json
{
  "resource_id": "aws_instance.web",
  "resource_type": "aws_instance",
  "provider": "aws",
  "region": "us-east-1",
  "attributes": {
    "ami": "ami-0c55b159cbfafe1f0",
    "instance_type": "t3.medium"
  }
}
```

### AWS SDK Calls

```python
# 1. Get AMI details (cached for 1 hour)
ec2.describe_images(ImageIds=["ami-0c55b159cbfafe1f0"])

# 2. Get instance type details (cached for 24 hours)
ec2.describe_instance_types(InstanceTypes=["t3.medium"])
```

### Output

```json
{
  "resource_id": "aws_instance.web",
  "resource_type": "aws_instance",
  "attributes": {...},
  "enriched_metadata": {
    "root_volume_size": 8,
    "root_volume_type": "gp3",
    "vcpu": 2,
    "memory_mb": 4096,
    "network_performance": "Up to 5 Gigabit",
    "ebs_optimized_support": "default"
  },
  "metadata_status": {
    "enriched": true,
    "degraded": false
  }
}
```

## Security

### Read-Only Operations

- Only Describe/List AWS API calls
- No resource mutation
- No cross-account writes
- Credentials from environment or IAM role

### Best Practices

1. Use IAM role with least privilege
2. Enable CloudTrail for audit logging
3. Monitor API call costs
4. Set appropriate cache TTLs
5. Enable graceful degradation in production

## Performance

### Caching Benefits

With 1000 resources:
- **Without cache**: ~1000 AWS API calls
- **With cache (75% hit rate)**: ~250 AWS API calls
- **Cost savings**: ~75% reduction in API costs

### Optimization Tips

1. Increase cache TTLs for stable metadata
2. Batch similar resources together
3. Use regional endpoints
4. Monitor cache hit rates

## Troubleshooting

### AWS API Errors

**Issue**: `AccessDenied` errors

**Solution**: Verify IAM policy includes required permissions

### Cache Issues

**Issue**: Stale metadata

**Solution**: Clear cache via `/api/v1/cache/clear`

### Graceful Degradation

**Issue**: All resources degraded

**Solution**: Check AWS credentials and network connectivity

## License

[Your License]
