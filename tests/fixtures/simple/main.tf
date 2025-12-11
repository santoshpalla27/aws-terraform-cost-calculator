provider "aws" {
  region = "us-east-1"
}

variable "instance_type" {
  default = "t3.micro"
}

resource "aws_instance" "web" {
  ami           = "ami-12345678"
  instance_type = var.instance_type
}

resource "aws_eip" "ip" {
  instance = aws_instance.web.id
  vpc      = true
}
