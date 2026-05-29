output "invoke_arn" {
  value = aws_lambda_function.lambda_function.invoke_arn
}
output "aggregate_invoke_arn" {
  value = aws_lambda_function.lambda_aggregate.invoke_arn
}
output "preaggregate_invoke_arn" {
  value = aws_lambda_function.lambda_preaggregate.invoke_arn
}