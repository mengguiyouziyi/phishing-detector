#!/usr/bin/env python3
"""
Deploy phishing detector to remote server using paramiko
"""

import paramiko
import sys
import os

def deploy_to_server():
    server = "192.168.1.246"
    username = "root"
    password = "3646287"

    # Commands to run on remote server
    commands = [
        # Update system and install dependencies
        "apt update",
        "apt install -y python3-pip python3-dev python3-venv mysql-server libmysqlclient-dev nginx supervisor",

        # Create application directory
        "mkdir -p /opt/phishing-detector",
        "cd /opt/phishing-detector",

        # Create virtual environment
        "python3 -m venv venv",
        "source venv/bin/activate",

        # Upgrade pip
        "pip install --upgrade pip",

        # Configure MySQL
        "mysql -e 'CREATE DATABASE IF NOT EXISTS phishing_detector CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;'",
        "mysql -e \"CREATE USER IF NOT EXISTS 'phishing_user'@'localhost' IDENTIFIED BY 'phishing_password';\"",
        "mysql -e 'GRANT ALL PRIVILEGES ON phishing_detector.* TO '\\'phishing_user\\'@'\\'localhost\\';'",
        "mysql -e 'FLUSH PRIVILEGES;'",

        # Start MySQL service
        "systemctl start mysql",
        "systemctl enable mysql",
    ]

    print(f"=== Connecting to {server} ===")

    try:
        # Create SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Connect to server
        ssh.connect(server, username=username, password=password)
        print("✅ Connected to server")

        # Execute commands
        for cmd in commands:
            print(f"🔧 Executing: {cmd}")
            stdin, stdout, stderr = ssh.exec_command(cmd)

            # Read output
            output = stdout.read().decode()
            error = stderr.read().decode()

            if output:
                print(f"   Output: {output.strip()}")
            if error:
                print(f"   Error: {error.strip()}")

        # Create SFTP client to transfer files
        sftp = ssh.open_sftp()

        # Create project structure on remote server
        remote_files = [
            ("requirements.txt", "/opt/phishing-detector/requirements.txt"),
            ("config/settings.yaml", "/opt/phishing-detector/config/settings.yaml"),
        ]

        # Transfer files
        for local_path, remote_path in remote_files:
            if os.path.exists(local_path):
                print(f"📦 Transferring {local_path} -> {remote_path}")
                sftp.put(local_path, remote_path)

        # Install Python dependencies
        print("🔧 Installing Python dependencies...")
        stdin, stdout, stderr = ssh.exec_command("cd /opt/phishing-detector && source venv/bin/activate && pip install -r requirements.txt")

        output = stdout.read().decode()
        error = stderr.read().decode()

        if output:
            print(f"   Output: {output.strip()}")
        if error:
            print(f"   Error: {error.strip()}")

        # Create systemd service
        service_content = '''[Unit]
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
WantedBy=multi-user.target'''

        # Write service file
        sftp.putfo(ssh.open_sftp().file('/etc/systemd/system/phishing-detector.service', 'w'),
                  service_content.encode())

        # Enable and start service
        print("🚀 Starting service...")
        ssh.exec_command("systemctl daemon-reload")
        ssh.exec_command("systemctl enable phishing-detector")
        ssh.exec_command("systemctl start phishing-detector")

        # Check service status
        stdin, stdout, stderr = ssh.exec_command("systemctl status phishing-detector")
        status = stdout.read().decode()
        print(f"📊 Service Status:\n{status}")

        sftp.close()
        ssh.close()

        print("✅ Deployment completed successfully!")

    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        return False

    return True

if __name__ == "__main__":
    # Check if paramiko is available
    try:
        import paramiko
    except ImportError:
        print("Installing paramiko...")
        os.system("pip install paramiko")
        import paramiko

    deploy_to_server()