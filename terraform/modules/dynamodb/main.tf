resource "aws_dynamodb_table" "table" {
  name = "fh6-heatmap-table"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "sessionId"
  range_key = "timestamp"
  attribute {
    name = "sessionId"
    type = "S"
  }
  attribute {
    name = "timestamp"
    type = "S"
  }
}