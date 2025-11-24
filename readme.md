## open-webuiにpython3.11が必要な場合
```bash
# python3.11導入
$ sudo add-apt-repository ppa:deadsnakes/ppa -y
$ sudo apt update
$ sudo apt install python3.11 python3.11-venv python3.11-distutils -y
$ curl -sS https://bootstrap.pypa.io/get-pip.py -o get-pip.py
$ sudo python3.11 get-pip.py
```
```bash
# PEP683対策
$ python3.11 -m venv open-webui
$ cd open-webui
$ source bin/activate
$ pip install open-webui
$ open-webui serve
```

## Flask導入
1. リポジトリクローン
2. ディレクトリ移動
3. PEP683対策する

## nginxの導入
```bash
$ sudo apt install nginx
```

1. `nginx.conf`から`conf.d`をすべてincludeする行を削除
2. 読み込み
   ```bash
   include /etc/nginx/conf.d/lm-proxy.conf;
   ```
3. config作成
   ```bash
   $ sudo nano /etc/nginx/conf.d/lm-proxy.conf
   ```
   Flaskが作成するサーバーリストを`/home/user/nginx-backend-health/upstream_servers.conf`とすると、
   ```bash
   upstream backend {
       least_conn;
       include /home/user/nginx-backend-health/upstream_servers.conf`;
    }

   log_format

   location / {
       proxy_pass http://backend;
   }
   ```

4. nginxテストしてエラー訂正
   ```bash
   $ sudo nginx -t
   ```

## visudo
```bash
$ sudo visudo
```
```bash
#追記する
ユーザー名 ALL=(ALL) NOPASSWD:/usr/sbin/nginx
```

## systemd登録
```bash
[Unit]
Description=open-webui
After=network.target

[Service]
Type=simple

# アプリを動かしたいユーザー
User=ubuntu
Group=ubuntu

# 手動で cd していたディレクトリ
WorkingDirectory=/home/ubuntu/open-webui

# venv の中の実行ファイルをフルパスで指定
ExecStart=/home/ubuntu/open-webui/bin/open-webui serve

# 落ちたら自動再起動
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
[Unit]
Description=Automatically reconfigure nginx upstream
After=network.target

[Service]
Type=simple

# アプリを動かしたいユーザー
User=ubuntu
Group=ubuntu

# 手動で cd していたディレクトリ
WorkingDirectory=/home/ubuntu/nginx-backend-health

# venv の中の実行ファイルをフルパスで指定
ExecStart=/home/ubuntu/nginx-backend-health/nginx-backend/bin/python app.py

# 落ちたら自動再起動
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

だえもんりろーどする。enableもね