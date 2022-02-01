variable "hosted_zone" {
  description = "hosted zone name"
  default     = "mas-oracle.uk"
}

variable "hosted_zone_id" {
  description = "hosted zone id"
  default     = "Z02078622JD3XU3S087EM"
}

variable "cluster_name" {
  description = "name of the cluster"
  default     = "price-estimation"
}
variable "deployment_region"{
    description = "region to deploy the cluster to."
    default = "eu-west-1"
}

variable "ssh_pub_key_path"{
    description = "ssh public key path of the controlling key"
#   default = file("${path.module}/.txt")
    default = "~/.ssh/id_rsa.pub"
}
variable "aws_cred_file"{
    description = "path of credentials for aws"
    default = "../aws_creds"
}

variable "worker_type"{
    description = "Type of ec2 to be used for the worker nodes."
    default     = "m5.large"
}