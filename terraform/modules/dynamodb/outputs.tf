output "table_name" {
  value = aws_dynamodb_table.table.name
}
output "stream_arn" {
  value = aws_dynamodb_table.table.stream_arn
}