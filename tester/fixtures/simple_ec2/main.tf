# Simple EC2 instance for E2E testing
# This configuration produces a deterministic plan without requiring real AWS credentials

resource "aws_instance" "test_instance" {
  ami           = "ami-0c55b159cbfafe1f0" # Amazon Linux 2 AMI (us-east-1)
  instance_type = "t3.micro"

  tags = {
    Name        = "E2E-Test-Instance"
    Environment = "test"
    ManagedBy   = "platform-tester"
  }
}

# Output for verification
output "instance_id" {
  description = "The ID of the EC2 instance"
  value       = aws_instance.test_instance.id
}

output "instance_type" {
  description = "The instance type"
  value       = aws_instance.test_instance.instance_type
}
