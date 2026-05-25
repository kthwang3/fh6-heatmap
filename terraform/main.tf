terraform {
  required_providers{
    aws = {
      source = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
provider "aws" {
  region = "us-east-1"
}
module "dynamodb" {
  source = "./modules/dynamodb"
}
module "lambda" {
  source = "./modules/lambda"
  dynamodb_table_name = module.dynamodb.table_name
}
module "api_gateway" {
  source = "./modules/api_gateway"
  lambda_invoke_arn = module.lambda.invoke_arn
  lambda_aggregate_invoke_arn = module.lambda.aggregate_invoke_arn
}
module "s3" {
  source = "./modules/s3"
}
module "cloudfront" {
  source = "./modules/cloudfront"
  s3_website_endpoint = module.s3.bucket_website_endpoint
}