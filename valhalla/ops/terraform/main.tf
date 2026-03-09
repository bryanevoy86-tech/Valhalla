provider "aws" {
  region = "us-east-1"
}

resource "aws_ecs_cluster" "valhalla" {
  name = "valhalla-cluster"
}

resource "aws_db_instance" "valhalla_db" {
  allocated_storage    = 20
  engine               = "postgres"
  engine_version       = "15.5"
  instance_class       = "db.t3.micro"
  name                 = "valhalla"
  username             = "valhalla"
  password             = "changeme123!"
  skip_final_snapshot  = true
}
