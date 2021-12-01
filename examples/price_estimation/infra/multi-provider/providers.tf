provider "aws" {
  region                  = "eu-central-1"
 # shared_credentials_file = "${chomp(file("~/.aws/config_valory"))}"
}

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
  cluster_name = "kraken"
  dns_zone     = "mas-oracle.uk"
  dns_zone_id  = "Z02078622JD3XU3S087EM"

  # configuration
  ssh_authorized_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDUeszMdmFkdibX8PsyVPlIN3shhLRonfeDfKMCeDmZP9ElczCji7TN04TusB2oP3MfxLjj4KWz7IMipLHxsOnHLNwUangjlvEmkOlN7ZHt5MVcD1jn/X9NIjTT9t/6pIOOA1vZWqZC0pN6xkdB/m+tITaFSCG28eodAkcAu9QjKajSCuSexpKgPiXhidxmSCruOJRM8eBRqc5NOGgCrHFRCiEtPfO65emu9Z2LDLA7TkHhvKHgX8HkGfVRLEqoC1bjBB2oLZ9oPGE99d6HOQqNEJVjgf2vyV9jyglg+D+1n2ipYwlxMoWNiuRRj9XcIzuVzlBAJDw0+vE9ttTVF8MaO/DN2bkknc8FsIci4ZNIcTbB4iAbu7d9NcXxt5cvo16oG9b/kF3XMMx9hIJq4KlP/JDePbWPgBH1v8llUH6GT6Mi378kY+WRV+k6gG1u6JC+Wg7nrNg9kWoq2LH8dLS0/Sbei1kXWIxqyxaHa9M5SUGiFh7VcVJBFElRa8sXip/w8aY72R/E76RGH/yMUlzQoczdh5fnPDVGpxcAKln5APW+4Ni8+IgzSEoAIHqAw/OmRgSOfREcx4+nlQZhIBCf3LT6c4nl2jtBKeSNCQPWnT6CrZy88BFKFHOSUdNr6opMc62j8rAZcHiz1HaC3CJqEEuXJ8fV/6uRNTG3Vh5aYw== tomrae030@hotmail.com"

  # optional
  worker_count = 2
  worker_type  = "t3.small"
}


resource "local_file" "kubeconfig-tempest" {
  content  = module.aws_cluster.kubeconfig-admin
  filename = "kubefiles/kraken"
}

