output "api_url" {
  description = "Base URL of the IAM-authenticated Notes API"
  value       = aws_apigatewayv2_api.notes.api_endpoint
}

output "api_execution_arn" {
  description = "Execution ARN used to scope API invocation permissions"
  value       = aws_apigatewayv2_api.notes.execution_arn
}

output "lambda_name" {
  value = aws_lambda_function.notes.function_name
}

output "table_name" {
  value = aws_dynamodb_table.notes.name
}

output "log_group_name" {
  value = aws_cloudwatch_log_group.lambda.name
}
