output "kubeconfig_path" {
  description = "Шлях до kubeconfig створеного кластера"
  value       = kind_cluster.this.kubeconfig_path
}

output "namespace" {
  description = "Простір імен застосунку"
  value       = kubernetes_namespace.dso_shop.metadata[0].name
}

output "api_server_endpoint" {
  description = "Адреса API-сервера кластера"
  value       = kind_cluster.this.endpoint
}
