variable "dynamodb_table_name" {
  description = "table name for dynamodb"
  type = string
}
variable "stream_arn" {
  description = "stream ARN for dyanmoDB grid updates"
  type = string
}