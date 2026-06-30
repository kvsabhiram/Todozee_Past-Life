# ─────────────────────────────────────────────────────────────────────
# CloudWatch log groups for the logs the CW agent ships (see the
# logs.collect_list in user_data.sh.tpl). The agent auto-creates these on
# first boot with NO retention (never expire); declaring them here codifies
# the retention policy so it survives and is managed by Terraform.
#
# NOTE: these already exist (agent-created), so on first use they must be
# imported into state:
#   terraform import aws_cloudwatch_log_group.bootstrap /todozee-past-life/bootstrap
#   terraform import aws_cloudwatch_log_group.app       /todozee-past-life/app
# ─────────────────────────────────────────────────────────────────────
resource "aws_cloudwatch_log_group" "bootstrap" {
  name              = "/${var.project_name}/bootstrap"
  retention_in_days = var.log_retention_days
}

resource "aws_cloudwatch_log_group" "app" {
  name              = "/${var.project_name}/app"
  retention_in_days = var.log_retention_days
}
