# ============================================================================
# ENVIRONMENT OUTPUTS - DEV
# ============================================================================

output "vpc_name" {
  description = "VPC network name"
  value       = module.vpc_networking.vpc_name
}

output "gke_cluster_name" {
  description = "GKE cluster name"
  value       = module.gke_cluster.cluster_name
}

output "gke_cluster_endpoint" {
  description = "GKE cluster endpoint"
  value       = module.gke_cluster.cluster_endpoint
  sensitive   = true
}

output "gke_cluster_location" {
  description = "GKE cluster location"
  value       = module.gke_cluster.cluster_location
}

output "cloudsql_instance_name" {
  description = "Cloud SQL instance name"
  value       = module.cloud_sql.instance_name
}

output "cloudsql_connection_name" {
  description = "Cloud SQL connection name"
  value       = module.cloud_sql.connection_name
}

output "cloudsql_private_ip" {
  description = "Cloud SQL private IP"
  value       = module.cloud_sql.private_ip_address
  sensitive   = true
}

output "database_name" {
  description = "Database name"
  value       = module.cloud_sql.database_name
}

output "kubectl_connection_command" {
  description = "Command to configure kubectl"
  value       = "gcloud container clusters get-credentials ${module.gke_cluster.cluster_name} --zone ${var.zone} --project ${var.project_id}"
}
