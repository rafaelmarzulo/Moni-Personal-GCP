# ============================================================================
# MONIPERSONAL - DEV ENVIRONMENT
# Infrastructure as Code for GCP + GKE
# ============================================================================

terraform {
  required_version = ">= 1.6.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }

  # Backend configuration - GCS
  backend "gcs" {
    bucket = "monipersonal-terraform-state-dev" # Create this bucket first!
    prefix = "terraform/state"
  }
}

# Provider configuration
provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "compute.googleapis.com",
    "container.googleapis.com",
    "servicenetworking.googleapis.com",
    "sqladmin.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "iam.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
  ])

  project = var.project_id
  service = each.value

  disable_on_destroy = false
}

# VPC Network
module "vpc_networking" {
  source = "../../modules/vpc-networking"

  project_id   = var.project_id
  project_name = var.project_name
  environment  = var.environment
  region       = var.region

  subnet_cidr    = "10.0.0.0/24"
  pods_cidr      = "10.1.0.0/16"
  services_cidr  = "10.2.0.0/16"

  depends_on = [google_project_service.required_apis]
}

# GKE Cluster
module "gke_cluster" {
  source = "../../modules/gke-cluster"

  project_id   = var.project_id
  project_name = var.project_name
  environment  = var.environment
  cluster_name = "${var.project_name}-${var.environment}"

  region   = var.region
  zone     = var.zone
  regional = false # Zonal for dev (cost saving)

  vpc_self_link    = module.vpc_networking.vpc_self_link
  subnet_self_link = module.vpc_networking.subnet_self_link
  pods_range_name    = module.vpc_networking.pods_range_name
  services_range_name = module.vpc_networking.services_range_name

  machine_type    = "e2-medium"      # 2 vCPU, 4GB RAM
  min_node_count  = 1
  max_node_count  = 3
  disk_size_gb    = 50
  preemptible     = true             # Cost saving for dev
  release_channel = "REGULAR"

  depends_on = [google_project_service.required_apis, module.vpc_networking]
}

# Private Service Connection (for Cloud SQL)
resource "google_compute_global_address" "private_ip_address" {
  name          = "${var.project_name}-${var.environment}-private-ip"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = module.vpc_networking.vpc_id
  project       = var.project_id

  depends_on = [google_project_service.required_apis]
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = module.vpc_networking.vpc_id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_address.name]

  depends_on = [google_project_service.required_apis]
}

# Cloud SQL
module "cloud_sql" {
  source = "../../modules/cloud-sql"

  project_id       = var.project_id
  instance_name    = var.project_name
  environment      = var.environment
  region           = var.region

  database_version = "POSTGRES_15"
  tier             = "db-f1-micro"     # Smallest tier for dev
  disk_size_gb     = 10
  high_availability = false             # Single zone for dev
  deletion_protection = false           # Allow deletion in dev

  vpc_self_link    = module.vpc_networking.vpc_self_link
  database_name    = "monipersonal"
  database_user    = "monipersonal_user"

  authorized_networks = []

  depends_on = [
    google_service_networking_connection.private_vpc_connection,
    module.vpc_networking
  ]
}
