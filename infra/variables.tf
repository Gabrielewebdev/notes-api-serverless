variable "project_name" {
  description = "Prefisso dei nomi delle risorse"
  type        = string
  default     = "notes-api"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,29}$", var.project_name))
    error_message = "Usa da 3 a 30 caratteri: lettere minuscole, numeri e trattini; inizia con una lettera."
  }
}

variable "environment" {
  description = "Ambiente identificato nei tag delle risorse"
  type        = string
  default     = "lab"

  validation {
    condition     = contains(["lab", "dev", "prod"], var.environment)
    error_message = "L'ambiente deve essere lab, dev oppure prod."
  }
}

locals {
  function_name = "${var.project_name}-serverless"
}
