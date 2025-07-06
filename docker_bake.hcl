

target "service_a" {
  context = "./service_a"
  dockerfile = "Dockerfile"
  tags = ["service_a:latest"]
}

target "service_b" {
  context = "./service_b"
  dockerfile = "Dockerfile"
  tags = ["service_b:latest"]
}


group "default" {
  targets = ["service_a", "service_b"]
}