# PostgreSQL для DSO-Shop у тому самому просторі імен, що й застосунок.
# Дані зберігаються в emptyDir: навчальне середовище, перезапуск поду очищає БД.

resource "kubernetes_deployment_v1" "postgres" {
  metadata {
    name      = "postgres"
    namespace = kubernetes_namespace.dso_shop.metadata[0].name
    labels = {
      "app.kubernetes.io/name"    = "postgres"
      "app.kubernetes.io/part-of" = "dso-shop"
    }
  }

  spec {
    replicas = 1

    strategy {
      type = "Recreate"
    }

    selector {
      match_labels = {
        "app.kubernetes.io/name" = "postgres"
      }
    }

    template {
      metadata {
        labels = {
          "app.kubernetes.io/name"    = "postgres"
          "app.kubernetes.io/part-of" = "dso-shop"
        }
      }

      spec {
        container {
          name  = "postgres"
          image = var.postgres_image

          port {
            name           = "postgres"
            container_port = 5432
          }

          env {
            name  = "POSTGRES_DB"
            value = "dso_shop"
          }
          env {
            name  = "POSTGRES_USER"
            value = "dso"
          }
          env {
            name = "POSTGRES_PASSWORD"
            value_from {
              secret_key_ref {
                name = kubernetes_secret_v1.db.metadata[0].name
                key  = "postgres-password"
              }
            }
          }
          env {
            name  = "PGDATA"
            value = "/var/lib/postgresql/data/pgdata"
          }

          volume_mount {
            name       = "data"
            mount_path = "/var/lib/postgresql/data"
          }

          readiness_probe {
            exec {
              command = ["pg_isready", "-U", "dso", "-d", "dso_shop"]
            }
            initial_delay_seconds = 5
            period_seconds        = 10
          }
        }

        volume {
          name = "data"
          empty_dir {}
        }
      }
    }
  }
}

resource "kubernetes_service_v1" "postgres" {
  metadata {
    name      = "postgres"
    namespace = kubernetes_namespace.dso_shop.metadata[0].name
  }

  spec {
    selector = {
      "app.kubernetes.io/name" = "postgres"
    }
    port {
      name        = "postgres"
      port        = 5432
      target_port = 5432
    }
    type = "ClusterIP"
  }
}
