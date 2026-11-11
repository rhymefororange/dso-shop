variable "cluster_name" {
  description = "Назва локального кластера kind"
  type        = string
  default     = "dso-shop"
}

variable "node_image" {
  description = "Образ вузла kind (версія Kubernetes)"
  type        = string
  default     = "kindest/node:v1.37.0"
}

variable "namespace" {
  description = "Простір імен застосунку"
  type        = string
  default     = "dso-shop"
}

variable "postgres_image" {
  description = "Образ PostgreSQL"
  type        = string
  default     = "postgres:17"
}
