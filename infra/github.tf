resource "aws_iam_role" "github" {
  name = "notes-api-github-deploy"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Federated = "arn:aws:iam::726862573245:oidc-provider/token.actions.githubusercontent.com"
      }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          "token.actions.githubusercontent.com:sub" = "repo:Gabrielewebdev/notes-api-serverless:ref:refs/heads/main"
        }
      }
    }]
  })
}

resource "aws_iam_role_policy" "github" {
  name = "notes-api-deploy"
  role = aws_iam_role.github.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ManageState"
        Effect = "Allow"
        Action = "s3:*"
        Resource = [
          "arn:aws:s3:::notes-api-tfstate-726862573245",
          "arn:aws:s3:::notes-api-tfstate-726862573245/*"
        ]
      },
      {
        Sid      = "ManageNotesTable"
        Effect   = "Allow"
        Action   = "dynamodb:*"
        Resource = aws_dynamodb_table.notes.arn
      },
      {
        Sid      = "ManageNotesFunction"
        Effect   = "Allow"
        Action   = "lambda:*"
        Resource = aws_lambda_function.notes.arn
      },
      {
        Sid    = "ManageNotesApi"
        Effect = "Allow"
        Action = [
          "apigateway:GET", "apigateway:POST", "apigateway:PUT",
          "apigateway:PATCH", "apigateway:DELETE", "apigateway:Tag*"
        ]
        Resource = [
          "arn:aws:apigateway:us-east-1::/apis/9k4d935soc",
          "arn:aws:apigateway:us-east-1::/apis/9k4d935soc/*",
          "arn:aws:apigateway:us-east-1::/tags/*"
        ]
      },
      {
        Sid    = "ManageFunctionLogs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup", "logs:DeleteLogGroup",
          "logs:PutRetentionPolicy", "logs:DeleteRetentionPolicy",
          "logs:ListTagsLogGroup", "logs:TagLogGroup",
          "logs:UntagLogGroup", "logs:ListTagsForResource",
          "logs:TagResource", "logs:UntagResource"
        ]
        Resource = [
          aws_cloudwatch_log_group.lambda.arn,
          "${aws_cloudwatch_log_group.lambda.arn}:*"
        ]
      },
      {
        Sid      = "ReadLogGroupMetadata"
        Effect   = "Allow"
        Action   = "logs:DescribeLogGroups"
        Resource = "*"
        Condition = {
          StringEquals = {
            "aws:RequestedRegion" = "us-east-1"
          }
        }
      },
      {
        Sid    = "ManageErrorAlarm"
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricAlarm", "cloudwatch:DeleteAlarms",
          "cloudwatch:DescribeAlarms", "cloudwatch:ListTagsForResource",
          "cloudwatch:TagResource", "cloudwatch:UntagResource"
        ]
        Resource = aws_cloudwatch_metric_alarm.lambda_errors.arn
      },
      {
        Sid    = "ReadProjectRoles"
        Effect = "Allow"
        Action = [
          "iam:GetRole", "iam:ListRoleTags",
          "iam:ListRolePolicies", "iam:ListAttachedRolePolicies",
          "iam:GetRolePolicy"
        ]
        Resource = [
          aws_iam_role.lambda.arn,
          aws_iam_role.github.arn
        ]
      },
      {
        Sid    = "ManageLambdaRole"
        Effect = "Allow"
        Action = [
          "iam:UpdateAssumeRolePolicy", "iam:UpdateRole",
          "iam:TagRole", "iam:UntagRole",
          "iam:PutRolePolicy", "iam:DeleteRolePolicy"
        ]
        Resource = aws_iam_role.lambda.arn
      },
      {
        Sid      = "PassLambdaRole"
        Effect   = "Allow"
        Action   = "iam:PassRole"
        Resource = aws_iam_role.lambda.arn
        Condition = {
          StringEquals = {
            "iam:PassedToService" = "lambda.amazonaws.com"
          }
        }
      },
      {
        Sid      = "TestNotesApi"
        Effect   = "Allow"
        Action   = "execute-api:Invoke"
        Resource = "${aws_apigatewayv2_api.notes.execution_arn}/$default/*/notes*"
      }
    ]
  })
}
