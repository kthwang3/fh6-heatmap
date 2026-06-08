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
  attribute {
    name = "date"
    type = "S"
  }
  global_secondary_index {
    name = "date-index"
    hash_key = "date"
    range_key = "timestamp"
    projection_type = "ALL"
  }
  stream_enabled = true
  stream_view_type = "NEW_IMAGE"
}
resource "aws_dynamodb_table" "counters_table" {
  name = "fh6-heatmap-grid-table"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "col_row"
  attribute {
    name = "col_row"
    type = "S"
  }
}