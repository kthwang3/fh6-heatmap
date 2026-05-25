variable "lambda_invoke_arn"{
  description = "Invoke ARN of the position ingest Lambda function"
  type = string
}
variable "lambda_aggregate_invoke_arn" {
  description = "Invoke ARN of the heatmap ingest Lambda function"
  type = string
}