provider "digitalocean" {
  token = "${chomp(file(var.cred_file))}"
}