### SESTI (SErver STatus Informer)
Simple server monitoring based on ssh access.

## Install
-   Download repo somewhere
-   Install dependencies and create nesessary directories

```bash
sudo pip install flask, simplepam, paramiko, pretty, apscheduler
sudo mkdir /etc/sesti/
mkdir ./reports/
```


## Configure: 

- /etc/sesti/servers.yaml

```yaml
servers:
    server1: 
        address: serv1.example.com

    server2: 
        address: serv2.example.com

    server#1:
        address: serv#!.example.com
        range: [1, 10]

    server#2:
        address: newserv#!.example.com
        range: [1, 20]
     
groups:
    Group1:
    - server1
    - server#1
    
    Group2:
    - server2
    - server#2
```
#! - is a range substitution for a simple list.

- check if it works: python main.py and navigate in browser to 127.0.0.1:8000


- run monitor process. 
```bash
python monitor.py
```
It hardcoded to run a 16-processes pool onece in 30 seconds.

It is nesessary to have no password on ssh access for servers, described in servers.yaml. 


## Configure apache and WSGI
- Configure apache at /etc/apache2/conf.d/sesti.conf

```
<Directory /usr/local/share/sesti>
Require all granted
</Directory>

WSGIScriptAlias /sesti   /usr/local/share/sesti/main.wsgi
WSGIPassAuthorization On
# create some wsgi daemons - use user/group same as your data_dir:
WSGIDaemonProcess main user=informer group=www processes=1 threads=1 maximum-requests=1000 umask=0007

# use the daemons we defined above to process requests!
WSGIProcessGroup main

# WSGISocketPrefix
WSGISocketPrefix /var/run/sesti-wsgi
```
- run monitor: 
```bash
su - -c "cd /usr/local/share/sesti; python ./monitor.py &"
```
    
Set "cd sesti_dir; python monitor.py" on the server startup

