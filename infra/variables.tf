variable "project_name" {
  description = "Project name used to prefix all resources"
  type        = string
}

variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

variable "tf_state_bucket" {
  description = "S3 bucket for Terraform state (injected by platform)"
  type        = string
  default     = ""
}

variable "db_password" {
  description = "Password for the local PostgreSQL database"
  type        = string
  sensitive   = true
}

variable "secret_key" {
  description = "Django SECRET_KEY"
  type        = string
  sensitive   = true
  default     = ""
}

variable "allowed_hosts" {
  description = "Comma-separated ALLOWED_HOSTS for Django"
  type        = string
  default     = "*"
}

variable "ssh_public_key" {
  description = "SSH public key for the EC2 key pair (injected by platform)"
  type        = string
  default     = ""
}
