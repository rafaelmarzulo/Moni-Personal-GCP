# ============================================================================
# GKE CLUSTER MODULE - OUTPUTS
# ============================================================================

output "cluster_id" {
  description = "GKE cluster ID"
  value       = google_container_cluster.primary.id
}

output "cluster_name" {
  description = "GKE cluster name"
  value       = google_container_cluster.primary.name
}

output "cluster_endpoint" {
  description = "GKE cluster endpoint"
  value       = google_container_cluster.primary.endpoint
  sensitive   = true
}

output "cluster_ca_certificate" {
  description = "GKE cluster CA certificate"
  value       = google_container_cluster.primary.master_auth[0].cluster_ca_certificate
  sensitive   = true
}

output "cluster_location" {
  description = "GKE cluster location"
  value       = google_container_cluster.primary.location
}

output "node_pool_name" {
  description = "Primary node pool name"
  value       = google_container_node_pool.primary_nodes.name
}

output "node_service_account_email" {
  description = "Service account email for GKE nodes"
  value       = google_service_account.gke_nodes.email
}
