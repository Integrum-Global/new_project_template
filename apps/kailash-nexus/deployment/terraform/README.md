# Nexus Terraform Infrastructure

This directory contains Terraform code to provision the complete AWS infrastructure for the Kailash Nexus application.

## 🏗️ Architecture Overview

The infrastructure includes:

- **EKS Cluster**: Kubernetes cluster with auto-scaling node groups
- **RDS PostgreSQL**: Managed database with encryption and backups
- **ElastiCache Redis**: Managed cache with replication
- **Application Load Balancer**: High availability load balancing
- **Route53 & ACM**: DNS management and SSL certificates
- **S3 Buckets**: Backup storage and access logs
- **CloudWatch**: Monitoring, logging, and alerting
- **ECR Repository**: Container image registry
- **KMS**: Encryption key management
- **VPC**: Network isolation with public/private subnets

## 📋 Prerequisites

1. **AWS CLI**: Configured with appropriate permissions
2. **Terraform**: Version >= 1.5
3. **kubectl**: For Kubernetes management
4. **Domain**: Registered domain for SSL certificates

### Required AWS Permissions

Your AWS user/role needs permissions for:
- EKS (cluster and node group management)
- RDS (database creation and management)
- ElastiCache (Redis cluster management)
- EC2 (VPC, subnets, security groups, ALB)
- Route53 (DNS management)
- ACM (SSL certificate management)
- S3 (bucket creation and management)
- CloudWatch (monitoring and logging)
- ECR (container registry)
- KMS (key management)
- IAM (role creation)

## 🚀 Quick Start

### 1. Configure Variables

```bash
# Copy example configuration
cp terraform.tfvars.example terraform.tfvars

# Edit with your values
nano terraform.tfvars
```

Key variables to set:
```hcl
environment    = "production"
region        = "us-west-2"
domain_name   = "yourdomain.com"
subdomain     = "nexus"
alert_email   = "alerts@yourdomain.com"
```

### 2. Initialize Terraform

```bash
terraform init
```

### 3. Plan Deployment

```bash
terraform plan
```

### 4. Deploy Infrastructure

```bash
terraform apply
```

### 5. Configure kubectl

```bash
# Update kubeconfig
aws eks update-kubeconfig --region us-west-2 --name nexus-production

# Verify connection
kubectl get nodes
```

## 📁 File Structure

```
terraform/
├── main.tf                    # Core infrastructure resources
├── providers.tf              # Provider configurations
├── variables.tf               # Variable definitions
├── outputs.tf                # Output values
├── terraform.tfvars.example  # Example variable values
└── README.md                 # This file
```

## 🔧 Configuration Options

### Environment Sizing

**Development**:
```hcl
node_instance_type = "t3.micro"
min_node_count     = 1
max_node_count     = 3
db_instance_class  = "db.t3.micro"
redis_node_type    = "cache.t3.micro"
```

**Staging**:
```hcl
node_instance_type = "t3.small"
min_node_count     = 2
max_node_count     = 5
db_instance_class  = "db.t3.small"
redis_node_type    = "cache.t3.small"
```

**Production**:
```hcl
node_instance_type = "m5.large"
min_node_count     = 3
max_node_count     = 20
db_instance_class  = "db.r5.large"
redis_node_type    = "cache.r5.large"
```

### Security Configuration

```hcl
# Enable all security features
enable_encryption        = true
enable_waf              = true
enable_deletion_protection = true
enable_secrets_encryption = true

# Restrict network access
allowed_cidr_blocks = ["10.0.0.0/8", "your.office.ip/32"]
```

### Cost Optimization

```hcl
# Enable spot instances for non-production
enable_spot_instances = true
spot_max_price       = "0.05"

# Reduce backup retention
backup_retention_days = 7

# Disable expensive features
enable_container_insights = false
```

## 📊 Monitoring and Alerting

The infrastructure includes comprehensive monitoring:

### CloudWatch Dashboards
- EKS cluster metrics
- RDS PostgreSQL performance
- ElastiCache Redis metrics
- Application Load Balancer stats

### CloudWatch Alarms
- High CPU utilization
- High response times
- Database connection issues
- Redis memory usage

### SNS Notifications
Configure `alert_email` to receive notifications.

## 🔐 Security Features

### Encryption
- **At Rest**: RDS, ElastiCache, S3, EKS secrets
- **In Transit**: ALB, RDS, ElastiCache
- **KMS**: Customer-managed encryption keys

### Network Security
- **VPC**: Isolated network environment
- **Security Groups**: Restrictive access rules
- **Network Policies**: Kubernetes-level isolation
- **WAF**: Web application firewall (optional)

### Access Control
- **RBAC**: Kubernetes role-based access
- **IAM**: Fine-grained AWS permissions
- **Service Accounts**: Secure pod-level access

## 💾 Backup and Recovery

### Automated Backups
- **RDS**: 30-day retention, point-in-time recovery
- **Application**: Daily S3 backups via CronJobs
- **Redis**: Daily snapshots

### Disaster Recovery
- **Multi-AZ**: High availability across zones
- **Snapshot Restoration**: Automated recovery scripts
- **Cross-Region**: Optional backup replication

## 🔄 State Management

For production deployments, configure remote state:

1. **Create S3 Backend**:
```bash
# Create S3 bucket for state
aws s3 mb s3://your-terraform-state-bucket

# Create DynamoDB table for locking
aws dynamodb create-table \
  --table-name terraform-state-lock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5
```

2. **Configure Backend** in `providers.tf`:
```hcl
terraform {
  backend "s3" {
    bucket         = "your-terraform-state-bucket"
    key            = "nexus/terraform.tfstate"
    region         = "us-west-2"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}
```

## 📈 Scaling

### Horizontal Scaling
- **Auto Scaling Groups**: Automatic node scaling
- **HPA**: Horizontal Pod Autoscaler
- **Cluster Autoscaler**: Node provisioning

### Vertical Scaling
- **Instance Types**: Upgrade node instances
- **Database**: Scale RDS instance class
- **Cache**: Scale Redis node types

## 🔍 Troubleshooting

### Common Issues

**EKS Access Denied**:
```bash
# Update kubeconfig
aws eks update-kubeconfig --region us-west-2 --name nexus-production

# Check AWS identity
aws sts get-caller-identity
```

**DNS Resolution**:
```bash
# Verify Route53 zone
aws route53 list-hosted-zones

# Check certificate validation
aws acm list-certificates --region us-west-2
```

**Resource Limits**:
```bash
# Check service quotas
aws service-quotas get-service-quota --service-code eks --quota-code L-1194D53C
```

### Useful Commands

```bash
# View infrastructure
terraform show

# Get outputs
terraform output

# Destroy infrastructure (careful!)
terraform destroy

# View logs
kubectl logs -n nexus-production deployment/nexus-app

# Check resource usage
kubectl top nodes
kubectl top pods -n nexus-production
```

## 🎯 Next Steps

After infrastructure deployment:

1. **Deploy Nexus Application**: Use Kubernetes manifests
2. **Configure Monitoring**: Set up Grafana dashboards
3. **Test Backup/Recovery**: Validate disaster recovery
4. **Security Scan**: Run security assessments
5. **Performance Test**: Load test the application

## 🆘 Support

For issues with:
- **Terraform**: Check the official Terraform documentation
- **AWS Services**: Review AWS documentation and limits
- **Nexus Application**: See the main project documentation
- **Kubernetes**: Consult kubectl and EKS documentation

## 📚 References

- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [EKS Best Practices](https://aws.github.io/aws-eks-best-practices/)
- [VPC Design Patterns](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-getting-started.html)
- [RDS Security](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Overview.Encryption.html)
