output "cloudfront_domain_name" {
  value = aws_cloudfront_distribution.heatmap_distribution.domain_name
}