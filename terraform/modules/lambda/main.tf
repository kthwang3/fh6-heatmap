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
resource "aws_lambda_function" "lambda_function" {
  function_name = "fh6-lambda"
  runtime = "python3.12"
  handler = "main.handler"
  filename = "../../../lambda.zip"
  role = aws_iam_role.lambda_role.arn
}