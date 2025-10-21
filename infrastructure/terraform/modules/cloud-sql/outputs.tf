# ============================================================================
# CLOUD SQL MODULE - OUTPUTS
# ============================================================================

output "instance_name" {
  description = "Cloud SQL instance name"
  value       = google_sql_database_instance.postgres.name
}

output "instance_connection_name" {
  description = "Cloud SQL instance connection name"
  value       = google_sql_database_instance.postgres.connection_name
}

output "connection_name" {
  description = "Cloud SQL connection name (alias)"
  value       = google_sql_database_instance.postgres.connection_name
}

output "private_ip_address" {
  description = "Private IP address"
  value       = google_sql_database_instance.postgres.private_ip_address
  sensitive   = true
}

output "database_name" {
  description = "Database name"
  value       = google_sql_database.database.name
}

output "database_user" {
  description = "Database user"
  value       = google_sql_user.user.name
}

output "password_secret_id" {
  description = "Secret Manager secret ID for password"
  value       = google_secret_manager_secret.db_password.secret_id
}

output "connection_string_secret_id" {
  description = "Secret Manager secret ID for connection string"
  value       = google_secret_manager_secret.db_connection_string.secret_id
}
