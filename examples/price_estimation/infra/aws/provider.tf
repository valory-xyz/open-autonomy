provider "aws" {
  region                  = var.deployment_region
  shared_credentials_file = var.aws_cred_file
}

