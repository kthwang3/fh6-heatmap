resource "aws_iam_role" "lambda_role"{
  name = "fh6-lambda-role"
  assume_role_policy = jsonencode(
     {
      "Version": "2012-10-17",
      "Statement": [{
        "Action": "sts:AssumeRole",
        "Effect": "Allow",
        "Principal": { "Service": "lambda.amazonaws.com" }
      }]
    }
  )
}
resource "aws_iam_role_policy_attachment" "lambda_policy" {
  role = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}
resource "aws_iam_role_policy_attachment" "dynamodb_policy" {
  role = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"
}
resource "aws_iam_role_policy_attachment" "s3_policy" {
  role = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_lambda_function" "lambda_function" {
  function_name = "fh6-lambda"
  runtime = "python3.12"
  handler = "main.handler"
  filename = "../lambda.zip"
  role = aws_iam_role.lambda_role.arn
  source_code_hash = filebase64sha256("../lambda.zip")
}
resource "aws_lambda_function" "lambda_aggregate"{
  function_name = "fh6-lambda-aggregate"
  runtime = "python3.12"
  handler = "aggregation.handler"
  filename = "../lambda.zip"
  role = aws_iam_role.lambda_role.arn
  timeout = 30
  source_code_hash = filebase64sha256("../lambda.zip")
}
resource "aws_lambda_function" "lambda_preaggregate"{
  function_name = "fh6-lambda-preaggregate"
  runtime = "python3.12"
  handler = "preaggregate.handler"
  filename = "../lambda.zip"
  role = aws_iam_role.lambda_role.arn
  timeout = 600
  source_code_hash = filebase64sha256("../lambda.zip")
  memory_size = 1024
}
resource "aws_lambda_function" "lambda_stream_processor"{
  function_name = "fh6-lambda-stream-processor"
  runtime = "python3.12"
  handler = "stream_processor.handler"
  filename = "../lambda.zip"
  role = aws_iam_role.lambda_role.arn
  source_code_hash = filebase64sha256("../lambda.zip")
}
resource "aws_lambda_event_source_mapping" "lambda_event_source_mapping"{
  event_source_arn = var.stream_arn
  function_name = aws_lambda_function.lambda_stream_processor.function_name
  starting_position = "LATEST"
}
resource "aws_lambda_permission" "allow_api_gateway" {
  statement_id = "AllowAPIGatewayInvoke"
  action = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lambda_function.function_name
  principal = "apigateway.amazonaws.com"
}
resource "aws_lambda_permission" "allow_api_gateway_aggregate" {
  statement_id = "AllowAPIGatewayInvokeAggregate"
  action = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lambda_aggregate.function_name
  principal = "apigateway.amazonaws.com"
}
resource "aws_cloudwatch_event_rule" "preaggregate_schedule" {
  name = "preaggregate_schedule"
  schedule_expression = "rate(15 minutes)"
}
resource "aws_cloudwatch_event_target" "preaggregate_target" {
  rule = aws_cloudwatch_event_rule.preaggregate_schedule.name
  arn = aws_lambda_function.lambda_preaggregate.arn
  target_id = "preaggregate_target"
}
resource "aws_lambda_permission" "allow_eventbridge_preaggregate" {
  statement_id = "AllowEventBridgeInvoke"
  action = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lambda_preaggregate.function_name
  principal = "events.amazonaws.com"
}

