resource "null_resource" "dangerous" {
  provisioner "local-exec" {
    command = "echo 'This should be blocked by security controls'"
  }
}
