resource "aws_api_gateway_rest_api" "heatmap" {
  name = "fh6-heatmap-api"
}
resource "aws_api_gateway_resource" "position" {
  rest_api_id = aws_api_gateway_rest_api.heatmap.id
  parent_id = aws_api_gateway_rest_api.heatmap.root_resource_id
  path_part = "position"
}
resource "aws_api_gateway_method" "position_method"{
  rest_api_id = aws_api_gateway_rest_api.heatmap.id
  resource_id = aws_api_gateway_resource.position.id
  http_method = "POST"
  authorization = "NONE"
}
resource "aws_api_gateway_integration" "position_integration"{
  rest_api_id = aws_api_gateway_rest_api.heatmap.id
  resource_id = aws_api_gateway_resource.position.id
  http_method = aws_api_gateway_method.position_method.http_method
  integration_http_method = "POST"
  type = "AWS_PROXY"
  uri = var.lambda_invoke_arn
}
resource "aws_api_gateway_deployment" "position_deployment" {
  rest_api_id = aws_api_gateway_rest_api.heatmap.id
  depends_on = [
    aws_api_gateway_integration.position_integration
  ]
}