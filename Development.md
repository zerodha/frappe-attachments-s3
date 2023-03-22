## Prerequisites
- python 3.10
- docker
- docker-compose
- redis-server
- nodejs
- crontab

To install few of above tools you can use something like
```
yay -Sy cronie redis-server nodejs
```


#### Installation.
```
pip3 install frappe-bench
pip3 install MarkupSafe
```

#### Activate virtual environment
```
python3 -m venv .python
source .python/bin/activate
```

#### Initial setup

```
bench init s3uninstall --frappe-path https://github.com/frappe/frappe --frappe-branch version-13
cd s3uninstall
bench new-site ims.improwised.com
bench use ims.improwised.com
bench get-app erpnext --branch version-13
bench get-app frappe_s3_attachment ./frappe_s3_attachment
bench --site ims.improwised.com install-app erpnext
bench --site ims.improwised.com install-app frappe_s3_attachment
bench start
```