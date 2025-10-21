# ============================================================================
# ENVIRONMENT VARIABLES - DEV
# ============================================================================

variable "project_id" {
  description = "GCP Project ID"
  type        = string
  # Set via: export TF_VAR_project_id="your-project-id"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "monipersonal"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "GCP Zone"
  type        = string
  default     = "us-central1-a"
}
