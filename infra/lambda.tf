resource "aws_lambda_function" "notes" {
  function_name = local.function_name
  description   = "Notes API backed by DynamoDB"

  role          = aws_iam_role.lambda.arn
  runtime       = "python3.14"
  architectures = ["x86_64"]
  handler       = "notes.lambda_handler.handler"

  filename         = "${path.module}/../dist/lambda.zip"
  source_code_hash = filebase64sha256("${path.module}/../dist/lambda.zip")

  memory_size = 128
  timeout     = 10

  environment {
    variables = {
      NOTES_TABLE_NAME = aws_dynamodb_table.notes.name
    }
  }

  depends_on = [
    aws_iam_role_policy.lambda,
    aws_cloudwatch_log_group.lambda
  ]
}
