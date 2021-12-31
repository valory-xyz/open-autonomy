provider "ct" {}

terraform {
  required_providers {
    ct = {
      source  = "poseidon/ct"
      version = "0.9.0"
    }
    digitalocean = {
      source = "digitalocean/digitalocean"
      version = "1.22.1"
    }
  }
}

data "digitalocean_image" "flatcar-stable-2303" {
  name = "flatcar-stable-2303.4.0"
}

resource "digitalocean_domain" "zone-for-clusters" {
  name       = var.domain
  ip_address = "8.8.8.8"
}

module "nemo" {
  source = "git::https://github.com/poseidon/typhoon//digital-ocean/flatcar-linux/kubernetes?ref=v1.22.3"

  # Digital Ocean
  cluster_name = var.cluster_name
  region       = var.deployment_region
  dns_zone     = var.domain

  # configuration
  os_image         = data.digitalocean_image.flatcar-stable-2303.id
  ssh_fingerprints = [var.ssh_fingerprint]

  # optional
  worker_count = var.worker_count
}

resource "local_file" "kubeconfig-nemo" {
  content  = module.nemo.kubeconfig-admin
  filename = "kubefiles/kubeconfig"
}
