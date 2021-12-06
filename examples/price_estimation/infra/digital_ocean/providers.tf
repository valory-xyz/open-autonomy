provider "digitalocean" {
  token = "${chomp(file("~/.config/digital-ocean/token"))}"
}

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

# Declare a DigitalOcean record to also create a zone file
resource "digitalocean_domain" "zone-for-clusters" {
  name       = "price-oracle.co.uk"
  ip_address = "8.8.8.8"
}

module "nemo" {
  source = "git::https://github.com/poseidon/typhoon//digital-ocean/flatcar-linux/kubernetes?ref=v1.22.3"

  # Digital Ocean
  cluster_name = "price-estimation"
  region       = "nyc3"
  dns_zone     = "price-oracle.co.uk"

  # configuration
  os_image         = data.digitalocean_image.flatcar-stable-2303.id
  ssh_fingerprints = ["12:31:25:bc:4e:d4:e8:e4:74:34:b1:9d:e2:f8:49:b2"]
  # ssh_fingerprints = ["d7:9d:79:ae:56:32:73:79:95:88:e3:a2:ab:5d:45:e7"]

  # optional
  worker_count = 2
}


resource "local_file" "kubeconfig-nemo" {
  content  = module.nemo.kubeconfig-admin
  filename = "kubefiles/nemo"
}
