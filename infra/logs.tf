resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/notes-api-serverless"
  retention_in_days = 14
}
