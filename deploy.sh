#!/bin/bash

# Deploy phishing detector to remote server
# Server: langchao6 (192.168.1.246)
# User: root
# Password: 3646287

SERVER="192.168.1.246"
USER="root"
PASSWORD="3646287"
REMOTE_DIR="/opt/phishing-detector"

echo "=== Deploying Phishing Detector to $SERVER ==="

# Create deployment script
cat > /tmp/deploy_script.sh << 'EOF'
#!/bin/bash

# Install system dependencies
apt update
apt install -y python3-pip python3-dev python3-venv mysql-server libmysqlclient-dev nginx supervisor

# Create application directory
mkdir -p /opt/phishing-detector
cd /opt/phishing-detector

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Configure MySQL
mysql -e "CREATE DATABASE IF NOT EXISTS phishing_detector CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -e "CREATE USER IF NOT EXISTS 'phishing_user'@'localhost' IDENTIFIED BY 'phishing_password';"
mysql -e "GRANT ALL PRIVILEGES ON phishing_detector.* TO 'phishing_user'@'localhost';"
mysql -e "FLUSH PRIVILEGES;"

# Create systemd service
cat > /etc/systemd/system/phishing-detector.service << 'EOL'
[Unit]
Description=Phishing Detector API
After=network.target mysql.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/phishing-detector
Environment=PATH=/opt/phishing-detector/venv/bin
ExecStart=/opt/phishing-detector/venv/bin/python -m app.api.routes
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOL

# Enable and start service
systemctl daemon-reload
systemctl enable phishing-detector
systemctl start phishing-detector

# Configure Nginx
cat > /etc/nginx/sites-available/phishing-detector << 'EOL'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static {
        alias /opt/phishing-detector/app/web/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOL

ln -sf /etc/nginx/sites-available/phishing-detector /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test and reload Nginx
nginx -t
systemctl reload nginx

echo "=== Deployment Complete ==="
echo "Service status: systemctl status phishing-detector"
echo "Access URL: http://$(hostname -I | awk '{print $1}')"
EOF

# Use expect to handle password authentication
cat > /tmp/expect_deploy.sh << 'SCRIPT'
#!/usr/bin/expect -f

set server [lindex $argv 0]
set user [lindex $argv 1]
set password [lindex $argv 2]
set script [lindex $argv 3]

spawn ssh $user@$server "bash -s" < $script
expect {
    "assword:" {
        send "$password\r"
        exp_continue
    }
    "Are you sure you want to continue connecting" {
        send "yes\r"
        exp_continue
    }
    timeout {
        send_user "Connection timed out\n"
        exit 1
    }
    eof
}
SCRIPT

# Make scripts executable
chmod +x /tmp/deploy_script.sh
chmod +x /tmp/expect_deploy.sh

# Check if expect is available
if ! command -v expect &> /dev/null; then
    echo "Installing expect..."
    brew install expect
fi

# Run deployment
/tmp/expect_deploy.sh $SERVER $USER $PASSWORD /tmp/deploy_script.sh

echo "=== Deployment initiated ==="