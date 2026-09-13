variable "service_name" {
  description = "Service / resource name prefix"
  type        = string
  default     = "url-shortener"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "image_tag" {
  description = "Docker image tag to deploy"
  type        = string
  default     = "latest"
}
