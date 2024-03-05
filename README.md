# Project Name
 - Flask Blog Python Project

## Description
This project is centered on creating a web application using Python that consolidates and presents news from the Hacker News portal. The application comes equipped with fundamental features such as Registration/Sign-In, a News Feed, User Profiles, and an Administrative panel. A distinctive feature of the platform is the implementation of 'Like' and 'Dislike' options for individual news stories, which play a role in determining the prominence of popular stories within the feed. To assure user security, the application integrates Auth0, ensuring robust authentication processes. The objective of this project is to deliver a smooth and engaging news reading experience, demonstrating the versatility of Python in crafting web-based applications.

## Table of Contents
- [Features]
- [Installation]
- [Configs]
- [Testing]

## Features

- News Feed: Users can browse the latest news items fetched from the Hacker News portal which is updated every hour using a cron job.
URL: https://marmelada.site/newsfeed

- User Authentication: Implemented a secure authentication and sign-up system with Auth0, enabling user account creation and access via their Google email credentials.
Login URL: https://marmelada.site/login

- Profile Page: Designed an individual user page for viewing a user’s personal profile details. Specifically profile picture, email, and name.
URL: https://marmelada.site/profiles

- Admin Panel: Coded an admin panel to oversee all users who have accessed the domain, with capabilities to view and remove user accounts as needed.
URL: https://marmelada.site/admin

- API Endpoint for News: Developed a JSON API endpoint that serves up-to-date news articles, allowing seamless integration with external applications or services.
URL: https://marmelada.site/newsfeed

## Installations and Configurations:

- Setting up Linode Server
- Server: Ubuntu 22.04 instance using a cloud provider: Linode (HighPerformance SSD Linux Servers)
- Region selected for Linode server: Newark, NJ
- Linode Plan => Shared CPU => Nanode 1 GB
- Linode label => cop4521_mt20e
-Accessing server
- From local machine => ssh root@<ip_address>
- Update software: apt update && apt upgrade
- Change hostname: hostnamectl set-hostname <fsuid>-server
- Add a limited user: adduser <username>
	- Add <password> 
- Access server with now limited user: ssh <username>@<_id_address>
- Add grader user to sudo group
- Sudo without inputting password:
		- sudo visudo
		- newusername ALL=(ALL) NOPASSWD: ALL  
- Set Up SSH for the New User: 
	- sudo mkdir /home/newusername/.ssh
	- echo "PUBLIC_KEY_CONTENT" | sudo tee -a /home/newusername/.ssh/authorized_keys
- Adjust the permissions for security:
	- sudo chmod 700 /home/newusername/.ssh
	- sudo chmod 600 /home/newusername/.ssh/authorized_keys
	- sudo chown -R newusername:newusername /home/newusername/.ssh

- Install Python and Dependencies: 
	- sudo apt install python3
	- pip install -r home/marija8t/project_part2/requirements.txt
- Requirements:
flask>=2.0.3
python-dotenv>=0.19.2
authlib>=1.0
requests>=2.27.1
blinker==1.6.3
certifi==2023.7.22
charset-normalizer==3.3.0
click==8.1.7
Flask==3.0.0
greenlet==3.0.0
gunicorn==21.2.0
idna==3.4
itsdangerous==2.1.2
Jinja2==3.1.2
MarkupSafe==2.1.3
packaging==23.2
requests==2.31.0
SQLAlchemy==2.0.22
typing_extensions==4.8.0
urllib3==2.0.7
Werkzeug==3.0.0
- Create a Virtual Environment and Activate It:
	- sudo apt install python3-venv
	- python3 -m venv venv
	- source venv/bin/activate
- Set Up Nginx and Gunicorn:
	- sudo apt install nginx
	- pip install gunicorn
- Install nginx and gunicorn dependencies:
	- sudo apt install python3-pip
	- sudo apt install python3-dev
	- sudo apt install build-essential
	- sudo apt install libssl-dev
	- sudo apt install libffi-dev
	- sudo apt install python3-setuptools
- Enable HTTPS with free SSL/TLS Certificate:
	- Certbot: https://certbot.eff.org/
	- sudo apt-get update
	- sudo apt-get install software-properties-common
	- sudo apt-get install python-certbot-nginx
- Change server name to domain name:
	- sudo nano /etc/nginx/sites-enabled/marmelada.site
	- server_name www.marmelada.site
	- sudo certbot --nginx (redirect)
	- sudo nginx -t
	- sudo ufw allow https
- Restart Nginx and Supervisor:
	- sudo systemctl restart nginx
	- sudo systemctl restart supervisor
- To determine the user and group under which the Nginx process is running:
	- ps -aux | grep nginx
- Verify Nginx Status: 
	- sudo systemctl status nginx
- Verify Supervisor status:
	- sudo supervisorctl status

## Other Configs
- To check Nginx configurations:
	- cat /etc/nginx/nginx.conf
Content: 
user www-data;
worker_processes auto;
pid /run/nginx.pid;
include /etc/nginx/modules-enabled/*.conf;

events {
	worker_connections 768;
	# multi_accept on;
}

http {

	##
	# Basic Settings
	##

	sendfile on;
	tcp_nopush on;
	tcp_nodelay on;
	keepalive_timeout 65;
	types_hash_max_size 2048;
	# server_tokens off;

	# server_names_hash_bucket_size 64;
	# server_name_in_redirect off;

	include /etc/nginx/mime.types;
	default_type application/octet-stream;

	##
	# SSL Settings
	##

	ssl_protocols TLSv1 TLSv1.1 TLSv1.2 TLSv1.3; # Dropping SSLv3, ref: POODLE
	ssl_prefer_server_ciphers on;

	##
	# Logging Settings
	##

	access_log /var/log/nginx/access.log;
	error_log /var/log/nginx/error.log;

	##
	# Gzip Settings
	##

	gzip on;

	# gzip_vary on;
	# gzip_proxied any;
	# gzip_comp_level 6;
	# gzip_buffers 16 8k;
	# gzip_http_version 1.1;
	# gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

	##
	# Virtual Host Configs
	##

	include /etc/nginx/conf.d/*.conf;
	include /etc/nginx/sites-enabled/*;
}


mail {
	# See sample authentication script at:
	# http://wiki.nginx.org/ImapAuthenticateWithApachePhpScript
 
	# auth_http localhost/auth.php;
	# pop3_capabilities "TOP" "USER";
	# imap_capabilities "IMAP4rev1" "UIDPLUS";
 
	server {
		listen     localhost:110;
		protocol   pop3;
		proxy      on;
	}
 
	server {
		listen     localhost:143;
		protocol   imap;
		proxy      on;
	}
}
	
/**************************************************************/
- Supervisor Configurations: 
[program:project_part2]
directory=/home/marija8t/project_part2
command=/home/marija8t/project_part2/venv/bin/gunicorn -w 3 myapp:app
user=marija8t
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/project_part2/project_part2.err.log
stdout_logfile=/var/log/project_part2/project_part2.out.log

/**************************************************************/

/**************************************************************/
- Nginx Configurations: 
	-sudo vim /etc/nginx/sites-enabled/marmelada.site
-content:
server {
    server_name marmelada.site  www.marmelada.site;

    root /var/www/marmelada.site;  # Path to your website files

    index index.html index.htm;

    location / {
        proxy_pass http://localhost:8000;
        include /etc/nginx/proxy_params;
        proxy_redirect off;
    }

    location /newsfeed {
        proxy_pass http://localhost:8000;
        include /etc/nginx/proxy_params;
        proxy_redirect off;
    }

    listen 443 ssl; # managed by Certbot
    ssl_certificate /etc/letsencrypt/live/marmelada.site/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/marmelada.site/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot
	
	add_header Strict-Transport-Security "max-age=31536000; includeSubdomains; preload" always;
	add_header X-Content-Type-Options nosniff;
	add_header X-Frame-Options "SAMEORIGIN";
	add_header X-XSS-Protection "1; mode=block";

}
server {
    if ($host = www.marmelada.site) {
        return 301 https://$host$request_uri;
    } # managed by Certbot


    if ($host = marmelada.site) {
        return 301 https://$host$request_uri;
    } # managed by Certbot


    listen 80;
    server_name marmelada.site  www.marmelada.site;
    return 404; # managed by Certbot

  
}

/**************************************************************/
- Check Cron configurations:
	- crontab -l
Content:
0 * * * * /home/marija8t/project_part2/env/bin/python3 /home/marija8t/project_part2/update_database.py
## Testing
-Testing pytest
-cd into project directory after ssh into the server
	-cd project_part2
	-run the environment
		-source venv/bin/activate
	-run the test script
		-python3 test_app.py
	-overall pytest score: %60
-Testing pylint
	-cd into project directory after ssh into the server
	-cd project_part2
	-run the environment
		-source venv/bin/activate
	-run pylint
		-pylint app.py
		-pylint update_database.py
	-run coverage report
		-coverage report
	-app.py score: 9.43/10
	-update_database.py score: 8.86/10
