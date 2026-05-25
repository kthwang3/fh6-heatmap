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

resource "aws_lambda_function" "lambda_function" {
  function_name = "fh6-lambda"
  runtime = "python3.12"
  handler = "main.handler"
  filename = "../lambda.zip"
  role = aws_iam_role.lambda_role.arn
}
resource "aws_lambda_function" "lambda_aggregate"{
  function_name = "fh6-lambda-aggregate"
  runtime = "python3.12"
  handler = "aggregation.handler"
  filename = "../lambda.zip"
  role = aws_iam_role.lambda_role.arn
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

