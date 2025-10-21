# ============================================================================
# GKE CLUSTER MODULE
# Cria cluster GKE com node pool gerenciado e configurações de segurança
# ============================================================================

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

# Service Account for GKE nodes
resource "google_service_account" "gke_nodes" {
  account_id   = "${var.cluster_name}-node-sa"
  display_name = "GKE Node Service Account for ${var.cluster_name}"
  project      = var.project_id
}

# IAM roles for node service account
resource "google_project_iam_member" "gke_node_roles" {
  for_each = toset([
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/monitoring.viewer",
    "roles/stackdriver.resourceMetadata.writer"
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.gke_nodes.email}"
}

# GKE Cluster
resource "google_container_cluster" "primary" {
  name     = var.cluster_name
  location = var.regional ? var.region : var.zone
  project  = var.project_id

  # We can't create a cluster with no node pool defined, but we want to only use
  # separately managed node pools. So we create the smallest possible default
  # node pool and immediately delete it.
  remove_default_node_pool = true
  initial_node_count       = 1

  # Network configuration
  network    = var.vpc_self_link
  subnetwork = var.subnet_self_link

  # IP allocation policy for pods and services
  ip_allocation_policy {
    cluster_secondary_range_name  = var.pods_range_name
    services_secondary_range_name = var.services_range_name
  }

  # Private cluster configuration
  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false # Allow public access to control plane
    master_ipv4_cidr_block  = "172.16.0.0/28"
  }

  # Master authorized networks (limit access to control plane)
  master_authorized_networks_config {
    cidr_blocks {
      cidr_block   = "0.0.0.0/0" # TODO: Restrict to specific IPs in production
      display_name = "All networks (temporary)"
    }
  }

  # Workload Identity
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  # Add-ons configuration
  addons_config {
    http_load_balancing {
      disabled = false
    }

    horizontal_pod_autoscaling {
      disabled = false
    }

    network_policy_config {
      disabled = false
    }

    gcp_filestore_csi_driver_config {
      enabled = false
    }

    gce_persistent_disk_csi_driver_config {
      enabled = true
    }
  }

  # Enable network policy
  network_policy {
    enabled  = true
    provider = "CALICO"
  }

  # Dataplane V2 (advanced networking)
  datapath_provider = "ADVANCED_DATAPATH"

  # Maintenance window
  maintenance_policy {
    daily_maintenance_window {
      start_time = "03:00" # 3 AM UTC
    }
  }

  # Release channel (REGULAR for production, RAPID for dev)
  release_channel {
    channel = var.release_channel
  }

  # Monitoring and logging
  monitoring_config {
    enable_components = ["SYSTEM_COMPONENTS", "WORKLOADS"]

    managed_prometheus {
      enabled = true
    }
  }

  logging_config {
    enable_components = ["SYSTEM_COMPONENTS", "WORKLOADS"]
  }

  # Security settings
  binary_authorization {
    evaluation_mode = "PROJECT_SINGLETON_POLICY_ENFORCE"
  }

  # Enable shielded nodes
  enable_shielded_nodes = true

  # Resource labels
  resource_labels = {
    environment = var.environment
    managed_by  = "terraform"
    project     = var.project_name
  }

  lifecycle {
    ignore_changes = [
      # Ignore changes to initial_node_count since we remove default pool
      initial_node_count,
    ]
  }
}

# Primary Node Pool
resource "google_container_node_pool" "primary_nodes" {
  name       = "${var.cluster_name}-node-pool"
  location   = var.regional ? var.region : var.zone
  cluster    = google_container_cluster.primary.name
  project    = var.project_id

  # Node count configuration
  initial_node_count = var.min_node_count

  autoscaling {
    min_node_count = var.min_node_count
    max_node_count = var.max_node_count
  }

  # Node management
  management {
    auto_repair  = true
    auto_upgrade = true
  }

  # Upgrade settings
  upgrade_settings {
    max_surge       = 1
    max_unavailable = 0
  }

  # Node configuration
  node_config {
    preemptible  = var.preemptible
    machine_type = var.machine_type
    disk_size_gb = var.disk_size_gb
    disk_type    = "pd-standard"

    # Service account
    service_account = google_service_account.gke_nodes.email

    # OAuth scopes
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    # Metadata
    metadata = {
      disable-legacy-endpoints = "true"
    }

    # Network tags
    tags = ["gke-node", "${var.cluster_name}-node"]

    # Labels
    labels = {
      environment = var.environment
      node_pool   = "primary"
    }

    # Shielded instance config
    shielded_instance_config {
      enable_secure_boot          = true
      enable_integrity_monitoring = true
    }

    # Workload metadata config
    workload_metadata_config {
      mode = "GKE_METADATA"
    }

    # GCE instance metadata
    gcfs_config {
      enabled = true
    }

    gvnic {
      enabled = true
    }
  }

  lifecycle {
    create_before_destroy = true
  }
}
