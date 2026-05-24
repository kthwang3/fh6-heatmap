resource "aws_cloudfront_distribution" "heatmap_distribution"{
  enabled = true
  default_root_object = "index.html"
  origin {
    domain_name = var.s3_website_endpoint
    origin_id = "s3_website_endpoint"
  }
  default_cache_behavior {
    target_origin_id = "s3_website_endpoint"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods = ["GET", "HEAD"]
    cached_methods = ["GET", "HEAD"]
    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }
  }
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }
  viewer_certificate {
    cloudfront_default_certificate = true
  }
}