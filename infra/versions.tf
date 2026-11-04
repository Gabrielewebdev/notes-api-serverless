terraform {
  required_version = ">= 1.10, < 2.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  backend "s3" {
    bucket       = "notes-api-tfstate-726862573245"
    key          = "notes-api-serverless/terraform.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true
  }
}

provider "aws" {
  region              = "us-east-1"
  allowed_account_ids = ["726862573245"]

  default_tags {
    tags = {
      Project     = local.function_name
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}
