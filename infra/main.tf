terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  backend "s3" {
    # bucket/key/region are injected at runtime via -backend-config flags
    # (platform patches these; do NOT hardcode values here)
  }
}

provider "aws" {
  region = var.aws_region
}

# ---------------------------------------------------------------------------
# Data sources
# ---------------------------------------------------------------------------

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# ---------------------------------------------------------------------------
# Security Group
# ---------------------------------------------------------------------------

resource "aws_security_group" "app" {
  name        = "${var.project_name}-sg"
  description = "URL Shortener security group"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "${var.project_name}-sg"
    Project = var.project_name
  }
}

# ---------------------------------------------------------------------------
# EC2 Key Pair (injected by platform)
# ---------------------------------------------------------------------------

resource "aws_key_pair" "deploy" {
  key_name   = "${var.project_name}-key"
  public_key = var.ssh_public_key
}

# ---------------------------------------------------------------------------
# EC2 Instance
# ---------------------------------------------------------------------------

locals {
  user_data = <<-BOOTSTRAP
#!/bin/bash
set -euxo pipefail

PROJECT="${var.project_name}"
APP_DIR="/opt/url-shortener"
DB_NAME="urlshortener"
DB_USER="urlshortener"
DB_CRED="${var.db_password}"

export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y python3 python3-pip python3-venv python3-dev \
  postgresql postgresql-contrib nginx git curl

systemctl enable postgresql
systemctl start postgresql

sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_CRED';" 2>/dev/null || true
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;" 2>/dev/null || true
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;" 2>/dev/null || true

mkdir -p "$APP_DIR"
chown ubuntu:ubuntu "$APP_DIR"

cat > "$APP_DIR/.env" <<ENVEOF
DATABASE_URL=postgresql://$DB_USER:$DB_CRED@localhost:5432/$DB_NAME
SECRET_KEY=${var.secret_key}
DEBUG=False
ALLOWED_HOSTS=${var.allowed_hosts}
ENVEOF

cat > /etc/nginx/sites-available/url-shortener <<'NGINX'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    client_max_body_size 10M;
    location /static/ {
        alias /opt/url-shortener/staticfiles/;
    }
    location / {
        proxy_pass         http://127.0.0.1:8000;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }
}
NGINX

ln -sf /etc/nginx/sites-available/url-shortener /etc/nginx/sites-enabled/url-shortener
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl enable nginx
systemctl restart nginx

cat > /etc/systemd/system/url-shortener.service <<'UNIT'
[Unit]
Description=URL Shortener Gunicorn
After=network.target postgresql.service
[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/opt/url-shortener
EnvironmentFile=/opt/url-shortener/.env
ExecStart=/opt/url-shortener/venv/bin/gunicorn \
    --workers 3 \
    --bind 127.0.0.1:8000 \
    --access-logfile - \
    --error-logfile - \
    url_shortener.wsgi:application
Restart=always
RestartSec=5
[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable url-shortener
BOOTSTRAP
}

resource "aws_instance" "app" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = "t3.micro"
  subnet_id              = data.aws_subnets.default.ids[0]
  vpc_security_group_ids = [aws_security_group.app.id]
  key_name               = aws_key_pair.deploy.key_name
  user_data              = local.user_data

  root_block_device {
    volume_size = 20
    volume_type = "gp3"
  }

  tags = {
    Name    = "${var.project_name}-app"
    Project = var.project_name
  }
}

# ---------------------------------------------------------------------------
# Elastic IP
# ---------------------------------------------------------------------------

resource "aws_eip" "app" {
  instance = aws_instance.app.id
  domain   = "vpc"

  tags = {
    Name    = "${var.project_name}-eip"
    Project = var.project_name
  }
}
