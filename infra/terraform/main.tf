# Локальна інфраструктура DSO-Shop: кластер kind, простір імен, PostgreSQL.
# Застосунок розгортається окремо: kubectl apply -f deploy/k8s/ або Helm-чарт deploy/helm/dso-shop.

provider "kind" {}

resource "kind_cluster" "this" {
  name           = var.cluster_name
  node_image     = var.node_image
  wait_for_ready = true

  kind_config {
    kind        = "Cluster"
    api_version = "kind.x-k8s.io/v1alpha4"

    networking {
      api_server_address = "127.0.0.1"
    }

    node {
      role = "control-plane"
    }
  }
}

provider "kubernetes" {
  host                   = kind_cluster.this.endpoint
  client_certificate     = kind_cluster.this.client_certificate
  client_key             = kind_cluster.this.client_key
  cluster_ca_certificate = kind_cluster.this.cluster_ca_certificate
}

resource "kubernetes_namespace" "dso_shop" {
  metadata {
    name = var.namespace
    labels = {
      "app.kubernetes.io/part-of" = "dso-shop"
    }
  }
}

resource "random_password" "db" {
  length  = 32
  special = false
}

resource "kubernetes_secret_v1" "db" {
  metadata {
    name      = "dso-shop-db"
    namespace = kubernetes_namespace.dso_shop.metadata[0].name
  }

  data = {
    "postgres-password" = random_password.db.result
    "database-url"      = "postgresql://dso:${random_password.db.result}@postgres:5432/dso_shop"
  }
}
