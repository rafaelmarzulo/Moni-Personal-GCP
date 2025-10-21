# ============================================================================
# VPC NETWORKING MODULE - OUTPUTS
# ============================================================================

output "vpc_id" {
  description = "VPC network ID"
  value       = google_compute_network.vpc.id
}

output "vpc_name" {
  description = "VPC network name"
  value       = google_compute_network.vpc.name
}

output "vpc_self_link" {
  description = "VPC network self link"
  value       = google_compute_network.vpc.self_link
}

output "subnet_id" {
  description = "GKE subnet ID"
  value       = google_compute_subnetwork.gke_subnet.id
}

output "subnet_name" {
  description = "GKE subnet name"
  value       = google_compute_subnetwork.gke_subnet.name
}

output "subnet_self_link" {
  description = "GKE subnet self link"
  value       = google_compute_subnetwork.gke_subnet.self_link
}

output "pods_range_name" {
  description = "Secondary range name for pods"
  value       = "gke-pods"
}

output "services_range_name" {
  description = "Secondary range name for services"
  value       = "gke-services"
}

output "router_name" {
  description = "Cloud Router name"
  value       = google_compute_router.router.name
}

output "nat_name" {
  description = "Cloud NAT name"
  value       = google_compute_router_nat.nat.name
}
