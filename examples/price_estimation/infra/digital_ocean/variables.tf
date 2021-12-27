variable "domain" {
  description = "hosted zone name"
  default     = "price-oracle.co.uk"
}


variable "cluster_name" {
  description = "name of the cluster"
  default     = "price-estimation-cluster"
}
variable "deployment_region"{
    description = "region to deploy the cluster to."
    default = "lon1"
}

variable "ssh_fingerprint"{
    description = "fingerprint of the sshkey to be used to control the newly created workers."
    default = "12:31:25:bc:4e:d4:e8:e4:74:34:b1:9d:e2:f8:49:b2"
}
# variable "ssh_pub_key"{
#     description = "ssh public key path of the controlling key"
#     default ="${chomp(file("~/.config/digital-ocean/token"))}" 
# }
variable "cred_file"{
    description = "path of credentials for Digital Ocean"
    default = "../do_token"
}

variable "worker_count"{
    description = "Number of worker nodes to create for the cluster"
    default = "2"
}