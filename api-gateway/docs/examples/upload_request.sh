#!/bin/bash

# Example: Upload Terraform files as ZIP

# Create a sample Terraform file
cat > main.tf << 'EOF'
resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.medium"
  
  tags = {
    Name = "WebServer"
  }
}

resource "aws_s3_bucket" "data" {
  bucket = "my-data-bucket"
}
EOF

# Create ZIP file
zip terraform.zip main.tf

# Upload to API
curl -X POST http://localhost:8000/api/v1/uploads \
  -F "file=@terraform.zip" \
  -F "project_name=my-terraform-project" \
  -F "description=Production infrastructure"

# Expected response:
# {
#   "upload_id": "upload_456def",
#   "project_name": "my-terraform-project",
#   "file_count": 1,
#   "total_size_bytes": 245,
#   "message": "Files uploaded successfully"
# }

# Clean up
rm main.tf terraform.zip
