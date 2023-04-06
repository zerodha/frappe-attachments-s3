## Prerequisites
- docker
- docker-compose
- VS code remote extention

#### Run below commands in container. You can access it using

```
nvm use v14
PYENV_VERSION=3.9.9 bench init --skip-redis-config-generation --frappe-branch version-13 frappe-bench
cd frappe-bench
bench set-config -g db_host mariadb
bench set-config -g redis_cache redis://redis-cache:6379
bench set-config -g redis_queue redis://redis-queue:6379
bench set-config -g redis_socketio redis://redis-socketio:6379
bench new-site ims.localhost --no-mariadb-socket
bench use ims.localhost --no-mariadb-socket
bench --site ims.localhost set-config developer_mode 1
bench get-app --branch version-13 erpnext
bench --site mysite.localhost install-app erpnext
bench get-app frappe_s3_attachment ./frappe_s3_attachment
bench --site ims.localhost install-app frappe_s3_attachment
bench start
```