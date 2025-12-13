terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"

  # Skip credentials for plan-only execution
  skip_credentials_validation = true
  skip_requesting_account_id  = true
  skip_metadata_api_check     = true
}

resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.medium"

  tags = {
    Name        = "WebServer"
    Environment = "Production"
  }
}

resource "aws_s3_bucket" "data" {
  bucket = "my-data-bucket-12345"

  tags = {
    Name        = "DataBucket"
    Environment = "Production"
  }
}

resource "aws_db_instance" "database" {
  identifier        = "mydb"
  engine            = "postgres"
  engine_version    = "15.3"
  instance_class    = "db.t3.micro"
  allocated_storage = 20

  db_name  = "mydb"
  username = "admin"
  password = "changeme123" # Not a real password, just for plan

  skip_final_snapshot = true

  tags = {
    Name        = "Database"
    Environment = "Production"
  }
}
