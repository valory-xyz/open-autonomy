provider "ct" {}

terraform {
  required_providers {
    ct = {
      source  = "poseidon/ct"
      version = "0.9.0"
    }
    aws = {
      source = "hashicorp/aws"
      version = "3.48.0"
    }
  }
}


module "aws_cluster" {
  source = "git::https://github.com/poseidon/typhoon//aws/flatcar-linux/kubernetes?ref=v1.22.4"

  # AWS
  cluster_name = var.cluster_name
  dns_zone     = var.hosted_zone
  dns_zone_id  = var.hosted_zone_id

  # configuration
  ssh_authorized_key = chomp(file(var.ssh_pub_key_path))

  # optional
  worker_count = var.worker_count
  worker_type  = var.worker_type
  controller_count = var.controller_count
  controller_type  = var.controller_type
}


resource "aws_route53_record" "app-1" {
  zone_id = var.hosted_zone_id

  name = format("*.%s.%s", var.cluster_name, var.hosted_zone)
  type = "A"
  alias {
    name                   = module.aws_cluster.ingress_dns_name
    zone_id                = module.aws_cluster.ingress_zone_id
    evaluate_target_health = false
  }  # DNS zone name
  # DNS record
}


resource "local_file" "kubeconfig" {
  content  = module.aws_cluster.kubeconfig-admin
  filename = "kubefiles/kubeconfig"
}
