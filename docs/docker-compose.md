# 使用 Docker Compose 部署到远程服务器

适用于 Python + Streamlit 主版本。基础配置运行一个应用容器；有域名时可叠加 Caddy，提供 HTTPS 和反向代理。

## 1. 服务器准备

需要 Linux、Docker Engine、Docker Compose v2 或更新版本，以及有 Docker 使用权限的 SSH 账号。先在服务器检查：

```bash
docker version
docker compose version
```

没有安装时，按 [Docker 官方安装文档](https://docs.docker.com/engine/install/) 选择服务器发行版。以下命令均在工程目录执行；首次部署应使用包含 Dockerfile 和 compose.yaml 的最新工程文件。

如果服务器暂时无法访问 GitHub，可以直接上传本地工程部署包。应包含本版本的 Python 源码、requirements.txt、Dockerfile、.dockerignore、Compose 文件、deploy 目录以及 `data/info_service.db`；不需要上传虚拟环境、node_modules、Git 凭据或数据库备份。

在本机工程目录生成部署包，数据库会通过 SQLite 在线备份接口形成一致快照：

```bash
python3 deploy/package.py
```

部署包位于 `outputs/`，使用 SSH 工具上传到服务器，在单独的应用目录中解压后再执行下一节。包内不含 `.env`、管理员密码、Git 目录或数据库备份。

## 2. 初始化配置并启动

```bash
python3 deploy/setup.py
docker compose config --quiet
docker compose up -d --build --wait --wait-timeout 180
docker compose ps
docker compose logs --tail=100 infodesk
```

初始化程序创建 `.env` 和 `.secrets/admin_password`，后续重复运行不会覆盖已有配置或密码。随机生成的管理员密码不会输出到部署日志，需要在服务器终端自行查看：

```bash
cat .secrets/admin_password
```

问答和目录无需密码；进入“知识维护”时需要该密码。退出管理后重新登录，修改密码文件也会使旧登录失效。

密码目录权限为 0700。文件权限为 0444，便于容器内 UID 10001 读取独立挂载的密码文件；宿主机其他普通用户无法穿过私有目录访问它。不要修改成 0600 后直接沿用非 root 容器，否则可能读不到密码。密码和 `.env` 均不参与 Git 提交，也不发送到镜像构建上下文。Compose 使用文件形式的 [secrets](https://docs.docker.com/compose/how-tos/use-secrets/)，宿主机上仍需妥善保管原文件。

## 3. 没有域名：先用 SSH 隧道访问

基础配置只映射服务器的 `127.0.0.1:8501`，可通过 SSH 转发访问。在自己的电脑上执行，替换为实际 SSH 账号、IP 和端口：

```bash
ssh -p 22 -N -L 8502:127.0.0.1:8501 用户名@服务器IP
```

保持该终端连接，浏览器打开 `http://localhost:8502/`。这里使用 8502，避免与本机正在运行的开发版 8501 冲突。若 `.env` 中修改了 `INFODESK_PORT`，相应调整转发目标端口。

这条路径适合个人检查。要向其他师生开放，建议使用下一节的域名和 HTTPS 配置。基础部署无需在云安全组开放 8501。

## 4. 有域名：启用 HTTPS

把域名 A 记录指向服务器公网 IP；配置 AAAA 记录时也要确保 IPv6 能到达这台服务器。确认 80、443 端口未被其他服务占用，并允许云安全组和主机防火墙访问这两个端口。

在 `.env` 中填写实际域名，不要包含路径：

```dotenv
INFODESK_BIND_ADDRESS=127.0.0.1
INFODESK_PORT=8501
INFODESK_DOMAIN=问答站点的实际域名
```

启动应用和 Caddy：

```bash
docker compose -f compose.yaml -f compose.https.yaml config --quiet
docker compose -f compose.yaml -f compose.https.yaml up -d --build --wait --wait-timeout 180
docker compose -f compose.yaml -f compose.https.yaml logs --tail=100 caddy
```

然后访问 `https://你的实际域名/`。Caddy 根据域名申请和续期证书，并代理 Streamlit 连接。具体网络与 DNS 条件见 [Caddy 自动 HTTPS 文档](https://caddyserver.com/docs/automatic-https)。

如果服务器已有 Nginx、宝塔或其他网关占用了 80/443，可以保留基础 Compose 配置，让现有网关代理 `127.0.0.1:8501`，并开启 WebSocket 支持，不再启动 Caddy。

## 5. 数据持久化与更新

数据库目录挂载到命名卷 `nuaa-infodesk_knowledge_data`。首次创建空卷时，Docker 会将镜像内随附的知识库复制进去；重新构建镜像或替换应用容器时，继续使用卷中的已有数据库。参见 [Docker 数据卷说明](https://docs.docker.com/engine/storage/volumes/)。

镜像内知识库在初始版本含 254 条知识。后续部署新代码不会用镜像内数据库覆盖服务器上新增的知识和反馈；需要更新知识内容时，在知识维护页发布，或通过导入器导入到数据卷中的数据库。

更新前先备份，再上传或拉取新代码、重新构建：

```bash
docker compose exec infodesk python database_backup.py
docker compose up -d --build --wait --wait-timeout 180
docker compose exec infodesk python check_knowledge.py
```

HTTPS 部署时，上述 Compose 命令都应加上 `-f compose.yaml -f compose.https.yaml`，保持使用同一份组合配置。

可以停止容器而保留数据库：

```bash
docker compose down
```

不要在正式服务器使用 `docker compose down --volumes` 或删除 `nuaa-infodesk_knowledge_data`，这些操作会删除持久化数据库。

## 6. 导出、恢复备份

容器内备份使用 SQLite 在线备份接口，可以在应用运行时执行：

```bash
docker compose exec infodesk python database_backup.py --output /app/data/backups/manual_backup.db
mkdir -p backups
docker compose cp infodesk:/app/data/backups/manual_backup.db ./backups/manual_backup.db
```

同名备份已存在时命令会拒绝覆盖。请更换文件名，或使用不传 `--output` 的 UTC 时间戳文件名，并将其复制到服务器之外另存。

恢复时先停止应用，再用备份覆盖数据卷中的数据库，最后启动并检查：

```bash
docker compose stop infodesk
docker compose run --rm --no-deps --entrypoint python infodesk -c "from pathlib import Path; import shutil,sqlite3; source=Path('/app/data/backups/manual_backup.db'); c=sqlite3.connect(source.resolve().as_uri()+'?mode=ro',uri=True); assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'; c.close(); shutil.copyfile(source,'/app/data/info_service.db')"
docker compose up -d --wait --wait-timeout 180
docker compose exec infodesk python check_knowledge.py
```

这里恢复的是数据卷内已有的 `manual_backup.db`，操作前先保留当前数据库备份。不要在应用仍运行时用普通文件复制覆盖 SQLite 数据库。

## 7. 健康检查与排错

```bash
docker compose ps
docker compose logs --tail=100 infodesk
curl -fsS http://127.0.0.1:8501/_stcore/health
docker compose exec infodesk python check_knowledge.py
```

常见情况：

- 启动时找不到 secret：先运行 `python3 deploy/setup.py`。
- 密码文件读取失败：检查文件及私有目录权限，不要把 secret 留成宿主机 0600 文件。
- 页面没有管理员密码提示：确认是用仓库的 compose.yaml 启动；它会设置必须登录的环境变量。
- 网页能开但一直连接中：检查反向代理 WebSocket 支持和容器日志。
- HTTPS 证书失败：检查域名解析、80/443 端口及服务器已有网关。
- 端口已被占用：修改 `.env` 的 `INFODESK_PORT`，现有网关的目标端口也要相应修改。

当前适合单台服务器、单个应用容器和本地 SQLite 数据卷。不要通过多容器副本共享同一个 SQLite 文件进行横向扩容；有此需求时再迁移数据库架构。
