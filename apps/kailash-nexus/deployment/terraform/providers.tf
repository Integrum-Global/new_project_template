# Terraform Configuration
terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.20"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.10"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
  }

  # Backend Configuration (uncomment and configure for production)
  # backend "s3" {
  #   bucket  = "your-terraform-state-bucket"
  #   key     = "nexus/terraform.tfstate"
  #   region  = "us-west-2"
  #   encrypt = true
  #
  #   # DynamoDB table for state locking
  #   dynamodb_table = "terraform-state-lock"
  # }
}

# AWS Provider Configuration
provider "aws" {
  region = var.region

  # Default tags applied to all resources
  default_tags {
    tags = {
      Environment   = var.environment
      Project       = var.project_name
      ManagedBy     = "terraform"
      CreatedBy     = "nexus-infrastructure"
      Application   = "kailash-nexus"
      Repository    = "kailash_python_sdk"
    }
  }
}

# Kubernetes Provider Configuration
provider "kubernetes" {
  host                   = module.eks.cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)

  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "aws"
    args = ["eks", "get-token", "--cluster-name", module.eks.cluster_name]
  }
}

# Helm Provider Configuration
provider "helm" {
  kubernetes {
    host                   = module.eks.cluster_endpoint
    cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)

    exec {
      api_version = "client.authentication.k8s.io/v1beta1"
      command     = "aws"
      args = ["eks", "get-token", "--cluster-name", module.eks.cluster_name]
    }
  }
}

# Data Sources
data "aws_caller_identity" "current" {}

data "aws_availability_zones" "available" {
  state = "available"
}

# Route53 zone data source is defined in main.tf

# Local Values
locals {
  name_prefix = "${var.project_name}-${var.environment}"

  # Common tags for all resources
  common_tags = merge(
    {
      Environment   = var.environment
      Project       = var.project_name
      ManagedBy     = "terraform"
      CreatedBy     = "nexus-infrastructure"
      Application   = "kailash-nexus"
      Repository    = "kailash_python_sdk"
      Region        = var.region
      Cluster       = var.cluster_name
    },
    var.additional_tags
  )

  # Availability zones - use provided or default to first 3 in region
  azs = length(var.availability_zones) > 0 ? var.availability_zones : slice(data.aws_availability_zones.available.names, 0, 3)

  # Subnet CIDR calculations
  vpc_cidr = var.vpc_cidr
  newbits  = 8  # /16 becomes /24

  # Calculate subnet CIDRs dynamically
  private_subnet_cidrs = [
    for i in range(length(local.azs)) :
    cidrsubnet(local.vpc_cidr, local.newbits, i + 1)
  ]

  public_subnet_cidrs = [
    for i in range(length(local.azs)) :
    cidrsubnet(local.vpc_cidr, local.newbits, i + 101)
  ]

  # Application configuration
  app_name = "nexus"
  namespace = "nexus-${var.environment}"

  # DNS configuration
  domain_name = var.domain_name
  subdomain   = var.subdomain
  fqdn        = "${var.subdomain}.${var.domain_name}"

  # Security configuration
  enable_encryption = var.enable_encryption
  enable_waf       = var.enable_waf

  # Monitoring configuration
  enable_monitoring = var.enable_monitoring

  # Cost optimization
  enable_spot_instances = var.enable_spot_instances
}
