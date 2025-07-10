# Core Infrastructure Outputs
output "cluster_endpoint" {
  description = "Endpoint for EKS control plane"
  value       = module.eks.cluster_endpoint
}

output "cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "cluster_arn" {
  description = "EKS cluster ARN"
  value       = module.eks.cluster_arn
}

output "cluster_security_group_id" {
  description = "Security group ID attached to the EKS cluster"
  value       = module.eks.cluster_security_group_id
}

output "cluster_certificate_authority_data" {
  description = "Base64 encoded certificate data required to communicate with the cluster"
  value       = module.eks.cluster_certificate_authority_data
}

# VPC and Networking Outputs
output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "vpc_cidr_block" {
  description = "VPC CIDR block"
  value       = module.vpc.vpc_cidr_block
}

output "private_subnet_ids" {
  description = "List of private subnet IDs"
  value       = module.vpc.private_subnets
}

output "public_subnet_ids" {
  description = "List of public subnet IDs"
  value       = module.vpc.public_subnets
}

output "nat_gateway_ids" {
  description = "List of NAT Gateway IDs"
  value       = module.vpc.natgw_ids
}

# Database Outputs
output "postgres_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = aws_db_instance.postgres.endpoint
  sensitive   = true
}

output "postgres_port" {
  description = "RDS PostgreSQL port"
  value       = aws_db_instance.postgres.port
}

output "postgres_database_name" {
  description = "RDS PostgreSQL database name"
  value       = aws_db_instance.postgres.db_name
}

output "postgres_username" {
  description = "RDS PostgreSQL username"
  value       = aws_db_instance.postgres.username
  sensitive   = true
}

output "postgres_security_group_id" {
  description = "Security group ID for PostgreSQL"
  value       = aws_security_group.postgres.id
}

# Cache Outputs
output "redis_endpoint" {
  description = "ElastiCache Redis primary endpoint"
  value       = aws_elasticache_replication_group.redis.primary_endpoint_address
  sensitive   = true
}

output "redis_port" {
  description = "ElastiCache Redis port"
  value       = aws_elasticache_replication_group.redis.port
}

output "redis_reader_endpoint" {
  description = "ElastiCache Redis reader endpoint"
  value       = aws_elasticache_replication_group.redis.reader_endpoint_address
  sensitive   = true
}

output "redis_security_group_id" {
  description = "Security group ID for Redis"
  value       = aws_security_group.redis.id
}

# Load Balancer Outputs
output "load_balancer_dns" {
  description = "Load balancer DNS name"
  value       = aws_lb.main.dns_name
}

output "load_balancer_arn" {
  description = "Load balancer ARN"
  value       = aws_lb.main.arn
}

output "load_balancer_zone_id" {
  description = "Load balancer zone ID"
  value       = aws_lb.main.zone_id
}

output "nexus_api_target_group_arn" {
  description = "Target group ARN for Nexus API"
  value       = aws_lb_target_group.nexus_api.arn
}

output "nexus_mcp_target_group_arn" {
  description = "Target group ARN for Nexus MCP"
  value       = aws_lb_target_group.nexus_mcp.arn
}

# DNS and SSL Outputs
output "nexus_url" {
  description = "Nexus application URL"
  value       = "https://${var.subdomain}.${var.domain_name}"
}

output "route53_zone_id" {
  description = "Route53 hosted zone ID"
  value       = data.aws_route53_zone.main.zone_id
}

output "ssl_certificate_arn" {
  description = "ACM SSL certificate ARN"
  value       = aws_acm_certificate.nexus.arn
}

# Security Outputs
output "kms_key_id" {
  description = "KMS key ID for encryption"
  value       = aws_kms_key.nexus.key_id
}

output "kms_key_arn" {
  description = "KMS key ARN for encryption"
  value       = aws_kms_key.nexus.arn
}

output "kms_alias_name" {
  description = "KMS key alias name"
  value       = aws_kms_alias.nexus.name
}

# Storage Outputs
output "s3_backup_bucket" {
  description = "S3 bucket name for backups"
  value       = aws_s3_bucket.backups.id
}

output "s3_backup_bucket_arn" {
  description = "S3 bucket ARN for backups"
  value       = aws_s3_bucket.backups.arn
}

output "s3_alb_logs_bucket" {
  description = "S3 bucket name for ALB access logs"
  value       = aws_s3_bucket.alb_logs.id
}

output "ecr_repository_url" {
  description = "ECR repository URL for Nexus images"
  value       = aws_ecr_repository.nexus.repository_url
}

# Monitoring Outputs
output "sns_alerts_topic_arn" {
  description = "SNS topic ARN for alerts"
  value       = var.enable_monitoring ? aws_sns_topic.alerts[0].arn : null
}

output "cloudwatch_dashboard_url" {
  description = "CloudWatch dashboard URL"
  value       = var.enable_monitoring ? "https://${var.region}.console.aws.amazon.com/cloudwatch/home?region=${var.region}#dashboards:name=${local.name_prefix}-dashboard" : null
}

output "cloudwatch_log_groups" {
  description = "CloudWatch log group names"
  value = {
    nexus_app = aws_cloudwatch_log_group.nexus_app.name
    nexus_mcp = aws_cloudwatch_log_group.nexus_mcp.name
    postgres  = aws_cloudwatch_log_group.postgres.name
  }
}

# IAM Outputs
output "rds_monitoring_role_arn" {
  description = "IAM role ARN for RDS enhanced monitoring"
  value       = aws_iam_role.rds_enhanced_monitoring.arn
}

# Connection Information for Applications
output "database_connection_info" {
  description = "Database connection information for applications"
  value = {
    host     = aws_db_instance.postgres.endpoint
    port     = aws_db_instance.postgres.port
    database = aws_db_instance.postgres.db_name
    username = aws_db_instance.postgres.username
  }
  sensitive = true
}

output "redis_connection_info" {
  description = "Redis connection information for applications"
  value = {
    primary_endpoint = aws_elasticache_replication_group.redis.primary_endpoint_address
    reader_endpoint  = aws_elasticache_replication_group.redis.reader_endpoint_address
    port            = aws_elasticache_replication_group.redis.port
  }
  sensitive = true
}

# Kubernetes Configuration
output "kubectl_config" {
  description = "kubectl configuration command"
  value       = "aws eks update-kubeconfig --region ${var.region} --name ${module.eks.cluster_name}"
}

# Environment Information
output "environment_info" {
  description = "Environment configuration information"
  value = {
    environment = var.environment
    region      = var.region
    project     = var.project_name
    created_at  = timestamp()
  }
}

# Cost Tracking Tags
output "resource_tags" {
  description = "Common tags applied to all resources"
  value       = local.common_tags
}

# Security Configuration
output "security_configuration" {
  description = "Security configuration summary"
  value = {
    encryption_enabled     = var.enable_encryption
    deletion_protection    = var.enable_deletion_protection
    waf_enabled           = var.enable_waf
    secrets_encryption    = var.enable_secrets_encryption
    container_insights    = var.enable_container_insights
  }
}

# Network Configuration
output "network_configuration" {
  description = "Network configuration summary"
  value = {
    vpc_cidr             = module.vpc.vpc_cidr_block
    availability_zones   = module.vpc.azs
    private_subnet_cidrs = module.vpc.private_subnets_cidr_blocks
    public_subnet_cidrs  = module.vpc.public_subnets_cidr_blocks
    nat_gateway_count    = length(module.vpc.natgw_ids)
  }
}
