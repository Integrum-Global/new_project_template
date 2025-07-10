# Core Infrastructure Variables
variable "environment" {
  description = "Environment name (production, staging, development)"
  type        = string
  default     = "production"
  validation {
    condition = contains(["production", "staging", "development"], var.environment)
    error_message = "Environment must be one of: production, staging, development."
  }
}

variable "region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-west-2"
}

variable "project_name" {
  description = "Project name for resource naming and tagging"
  type        = string
  default     = "nexus"
}

# Networking Variables
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = []  # Will use first 3 AZs in region if empty
}

# EKS Cluster Variables
variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
  default     = "nexus-production"
}

variable "cluster_version" {
  description = "Kubernetes version for EKS cluster"
  type        = string
  default     = "1.27"
}

variable "node_instance_type" {
  description = "EC2 instance type for worker nodes"
  type        = string
  default     = "t3.medium"
  validation {
    condition = can(regex("^[a-z][0-9][a-z]*\\.[a-z0-9]+$", var.node_instance_type))
    error_message = "Node instance type must be a valid EC2 instance type."
  }
}

variable "min_node_count" {
  description = "Minimum number of worker nodes"
  type        = number
  default     = 3
  validation {
    condition = var.min_node_count >= 1 && var.min_node_count <= 100
    error_message = "Minimum node count must be between 1 and 100."
  }
}

variable "max_node_count" {
  description = "Maximum number of worker nodes"
  type        = number
  default     = 10
  validation {
    condition = var.max_node_count >= 1 && var.max_node_count <= 100
    error_message = "Maximum node count must be between 1 and 100."
  }
}

variable "desired_node_count" {
  description = "Desired number of worker nodes"
  type        = number
  default     = 3
  validation {
    condition = var.desired_node_count >= 1 && var.desired_node_count <= 100
    error_message = "Desired node count must be between 1 and 100."
  }
}

# Database Variables
variable "db_name" {
  description = "Database name for Nexus"
  type        = string
  default     = "nexus_prod"
}

variable "db_username" {
  description = "Database username for Nexus"
  type        = string
  default     = "nexus"
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.medium"
}

variable "db_allocated_storage" {
  description = "Initial allocated storage for RDS instance (GB)"
  type        = number
  default     = 100
}

variable "db_max_allocated_storage" {
  description = "Maximum allocated storage for RDS instance (GB)"
  type        = number
  default     = 1000
}

variable "db_backup_retention_period" {
  description = "Number of days to retain database backups"
  type        = number
  default     = 30
}

# Cache Variables
variable "redis_node_type" {
  description = "ElastiCache Redis node type"
  type        = string
  default     = "cache.t3.medium"
}

variable "redis_num_cache_clusters" {
  description = "Number of cache clusters in Redis replication group"
  type        = number
  default     = 3
}

# Domain and SSL Variables
variable "domain_name" {
  description = "Domain name for Nexus application"
  type        = string
  default     = "example.com"
}

variable "subdomain" {
  description = "Subdomain for Nexus application"
  type        = string
  default     = "nexus"
}

# Monitoring and Alerting Variables
variable "enable_monitoring" {
  description = "Enable CloudWatch monitoring and alerting"
  type        = bool
  default     = true
}

variable "alert_email" {
  description = "Email address for CloudWatch alerts"
  type        = string
  default     = ""
}

variable "cpu_alarm_threshold" {
  description = "CPU utilization threshold for alarms (percentage)"
  type        = number
  default     = 80
  validation {
    condition = var.cpu_alarm_threshold >= 1 && var.cpu_alarm_threshold <= 100
    error_message = "CPU alarm threshold must be between 1 and 100."
  }
}

variable "response_time_threshold" {
  description = "Response time threshold for ALB alarms (seconds)"
  type        = number
  default     = 2
}

# Backup and Storage Variables
variable "backup_retention_days" {
  description = "Number of days to retain S3 backups"
  type        = number
  default     = 30
  validation {
    condition = var.backup_retention_days >= 1 && var.backup_retention_days <= 365
    error_message = "Backup retention days must be between 1 and 365."
  }
}

variable "enable_deletion_protection" {
  description = "Enable deletion protection for critical resources"
  type        = bool
  default     = true
}

# Security Variables
variable "allowed_cidr_blocks" {
  description = "CIDR blocks allowed to access the load balancer"
  type        = list(string)
  default     = ["0.0.0.0/0"]  # Restrict this in production
}

variable "enable_waf" {
  description = "Enable AWS WAF for the load balancer"
  type        = bool
  default     = true
}

variable "enable_encryption" {
  description = "Enable encryption at rest and in transit"
  type        = bool
  default     = true
}

# Cost Optimization Variables
variable "enable_spot_instances" {
  description = "Enable spot instances for cost optimization"
  type        = bool
  default     = false
}

variable "spot_max_price" {
  description = "Maximum price for spot instances"
  type        = string
  default     = ""
}

# Tagging Variables
variable "additional_tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}

# Feature Flags
variable "enable_container_insights" {
  description = "Enable EKS Container Insights"
  type        = bool
  default     = true
}

variable "enable_secrets_encryption" {
  description = "Enable EKS secrets encryption"
  type        = bool
  default     = true
}

variable "enable_irsa" {
  description = "Enable IAM Roles for Service Accounts (IRSA)"
  type        = bool
  default     = true
}
