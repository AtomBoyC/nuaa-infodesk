# Linux 服务器部署操作指南

NUAA InfoDesk · 从私有 GitHub 仓库下载到 Docker Compose 部署

适用版本：Python + Streamlit + SQLite 主版本，GitHub `main` 分支。编写日期：2026 年 10 月 21 日。

项目仓库：[AtomBoyC/nuaa-infodesk](https://github.com/AtomBoyC/nuaa-infodesk)。仓库目前是私有的，下载前必须登录有权限的 GitHub 账号。无需将仓库改为公开。

## 一 阅读顺序与准备

首次部署按第二至第六节操作；没有 Docker 时先看附录 A。需要域名公开访问，再做第七节；服务器无法访问 GitHub，改用第八节上传 ZIP。

**命令执行位置**：“自己电脑”指你现在使用的电脑终端；“服务器”指通过 SSH 登录后的 Linux 终端。除特别标注外，部署命令都在服务器的项目根目录执行。不要复制命令框外的说明文字。某一步报错时先解决，不要继续执行后续步骤。

准备以下信息：

- 服务器公网 IP、SSH 用户名、SSH 端口，以及密码或 SSH 密钥。
- 有权读取该私有仓库的 GitHub 账号。
- 一台支持 Docker 的 64 位 Linux 服务器。本文安装示例针对 Ubuntu 22.04 或 24.04；其他发行版不要直接套用 Ubuntu 安装命令。
- 服务器能访问 GitHub、Docker 镜像仓库和 Python 包源。下载代码成功不等于镜像和依赖也能下载。
- 普通账号具有 `sudo` 权限。本文统一使用 `sudo docker`；如果已经是 root，可去掉 `sudo`。`gh`、解压和初始化仍使用同一个 SSH 账号，不要中途切换账号。

**三个密码不要混淆**：SSH 密码用于登录服务器；GitHub 授权用于读取私有代码；应用管理员密码用于“知识维护”，在第五节生成。

## 二 登录服务器并检查环境

**在自己电脑执行**。将 `SERVER_USER`、`SERVER_IP`、`22` 替换为实际账号、公网 IP 和 SSH 端口：

```bash
ssh -p 22 SERVER_USER@SERVER_IP
```

使用密钥时，在 `ssh` 后增加 `-i /你的密钥文件路径`。首次连接先核对服务器指纹；使用密码时，终端不显示输入字符是正常现象。

**登录后在服务器执行：**

```bash
cat /etc/os-release
sudo docker version
sudo docker compose version
```

Docker 应同时显示客户端和服务端信息，Compose 应能输出版本。本文使用带空格的 `docker compose`，不是旧版 `docker-compose`。没有安装、没有服务端或不支持 `--wait` 时，先按附录 A 安装或更新。已有生产容器的服务器不要直接卸载现有 Docker。

Ubuntu 上准备辅助工具：

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl python3 unzip
```

宿主机 Python 仅用于初始化配置，不必安装 Streamlit 或创建虚拟环境；运行依赖由 Docker 镜像安装。

## 三 授权服务器下载私有仓库

**以下在服务器执行**。先检查 GitHub CLI：

```bash
gh --version
```

没有 `gh` 时，按附录 B 安装。然后登录：

```bash
gh auth login --hostname github.com --git-protocol https --web
```

按照提示完成浏览器授权：

1. 终端显示一次性验证码和授权网址时，保留该终端。
2. 在自己电脑的浏览器打开提示的网址，通常是 `https://github.com/login/device`。
3. 使用有仓库权限的账号登录，输入本次验证码，核对请求后授权。
4. 回到服务器等待登录完成。服务器无法自动打开浏览器时，手动在自己电脑打开网址即可。

授权后检查访问权限：

```bash
gh auth status --hostname github.com
gh repo view AtomBoyC/nuaa-infodesk
```

看到项目名称和仓库信息后再继续。不要给 `gh` 增加 `sudo`，否则会切换为另一套登录状态。未经授权直接 `wget` 私有仓库链接，可能得到 404 或登录页面，并不是代码包。登录方式参见 [GitHub CLI 官方说明](https://cli.github.com/manual/gh_auth_login)。

**凭据保管**：无系统钥匙环的 Linux 服务器可能将 GitHub 凭据保存在当前用户配置文件中。不要复制或上传 `~/.config/gh/`，不要把 Token 写进下载链接。只部署一次时，完成下载后可执行 `gh auth logout --hostname github.com` 清除服务器上的 CLI 登录；后续更新再授权。若不愿在服务器保存 GitHub 授权，直接使用第八节。

## 四 从 GitHub 下载并解压项目

**在服务器执行。仅用于首次部署，目标目录应为空。**

```bash
mkdir -p "$HOME/apps/nuaa-infodesk"
cd "$HOME/apps"
gh api --hostname github.com \
  repos/AtomBoyC/nuaa-infodesk/tarball/main \
  > nuaa-infodesk-main.tar.gz
```

下载结束且没有报错后，验证压缩包并解压：

```bash
tar -tzf nuaa-infodesk-main.tar.gz > /dev/null
tar -xzf nuaa-infodesk-main.tar.gz \
  --strip-components=1 -C nuaa-infodesk
cd "$HOME/apps/nuaa-infodesk"
ls -a
```

`--strip-components=1` 去掉 GitHub 压缩包最外层目录，使 `compose.yaml` 直接位于项目根目录。下载的是 `main` 分支的完整源码快照，不包含 Git 历史；以后不要在此目录使用 `git pull`，更新见第十节。接口依据见 [GitHub 源码压缩包 API](https://docs.github.com/en/rest/repos/contents#download-a-repository-archive-tar)。

确认关键文件存在：

```bash
ls Dockerfile compose.yaml compose.https.yaml .env.example
ls deploy/setup.py streamlit_app.py data/info_service.db
```

数据库已经随代码下载，不需要另建 MySQL。首次初始化随附 254 条知识、9 个分类，后续版本或人工维护后数量可能变化。`react-next-version/` 是归档前端，不参与本次部署，不需要安装 Node.js。

## 五 生成配置并启动容器

**在服务器的项目根目录执行：**

```bash
python3 deploy/setup.py
sudo docker compose config --quiet
sudo docker compose up -d --build --wait --wait-timeout 180
```

初始化会创建 `.env` 和 `.secrets/admin_password`，不会覆盖已有配置或密码。构建时需要下载基础镜像和 Python 依赖，耗时取决于服务器网络。`--wait` 超时不一定代表容器已经停止，应先检查状态和日志。

检查运行情况：

```bash
sudo docker compose ps
sudo docker compose logs --tail=100 infodesk
curl -fsS http://127.0.0.1:8501/_stcore/health
sudo docker compose exec infodesk python check_knowledge.py
```

成功时应看到应用容器运行且健康，健康接口返回 `ok`，知识库检查没有完整性错误。退出 SSH 不会停止容器；配置已设置 `restart: unless-stopped`，Docker 服务启动后会恢复未手动停止的容器。

查看知识维护密码：

```bash
cat .secrets/admin_password
```

妥善保管，不要把密码发送到公开群或提交到 GitHub。密码目录为 0700，密码文件为 0444，后者是为便于非 root 容器读取独立挂载的 secret；宿主机其他普通用户无法穿过该私有目录。不要擅自把文件改成 0600，否则容器可能无法读取。

## 六 在自己电脑打开页面

默认 `.env` 绑定服务器 `127.0.0.1:8501`，不向公网直接开放。此时访问 `http://服务器IP:8501/` 打不开是预期行为；不必为此开放安全组 8501。

**在自己电脑另开一个终端执行，不是在服务器执行：**

```bash
ssh -p 22 -N -L 8502:127.0.0.1:8501 SERVER_USER@SERVER_IP
```

替换实际 SSH 参数，保持这个终端连接。在自己电脑浏览器打开：

```text
http://localhost:8502/
```

本地使用 8502，避免与你电脑原有开发版 8501 冲突。此连接通过 SSH 加密；关闭隧道后浏览器将无法继续访问，但服务器应用仍在运行。

验证搜索、匹配结果、知识目录和常用服务。进入“知识维护”时，输入第五节查询到的应用管理员密码；普通问答页面不需要该密码。

如果修改了服务器 `.env` 的 `INFODESK_PORT`，需要修改隧道中最后一个端口；本地 8502 被占用时，可以把第一个端口改成 8503，并改用 `http://localhost:8503/`。

## 七 用域名和 HTTPS 对外开放

这是可选步骤，适用于需要让其他人访问的站点。准备实际域名，使 A 记录指向服务器公网 IP；若存在 AAAA 记录，也应正确指向可达的服务器 IPv6。开放云安全组和主机防火墙的 TCP 80、443，并保留实际 SSH 端口。

**先检查端口占用，不要覆盖已有网站：**

```bash
sudo ss -lntp
```

已有 Nginx、宝塔或其他服务占用 80/443 时，不启动下述 Caddy。保留基础 Compose，由现有网关提供 HTTPS，反向代理到 `127.0.0.1:8501`，并启用 WebSocket 支持。

端口空闲时，在服务器项目目录编辑 `.env`，例如运行 `nano .env`；如果没有该编辑器，使用服务器已有的编辑器。内容如下，将示例域名换成自己的真实域名，不带 `https://` 或路径：

```dotenv
INFODESK_BIND_ADDRESS=127.0.0.1
INFODESK_PORT=8501
INFODESK_DOMAIN=qa.example.com
```

启动 HTTPS 配置：

```bash
sudo docker compose -f compose.yaml -f compose.https.yaml \
  config --quiet
sudo docker compose -f compose.yaml -f compose.https.yaml \
  up -d --build --wait --wait-timeout 180
sudo docker compose -f compose.yaml -f compose.https.yaml ps
sudo docker compose -f compose.yaml -f compose.https.yaml \
  logs --tail=100 caddy
```

浏览器访问 `https://你的真实域名/`。首次申请证书可能需要等待；条件见 [Caddy 自动 HTTPS 说明](https://caddyserver.com/docs/automatic-https)。不要将 `qa.example.com` 原样用于申请证书。

**后续规则**：使用 Caddy 后，更新、停止、备份等 Compose 命令都在 `compose` 后加 `-f compose.yaml -f compose.https.yaml`，保持配置一致。不要为了临时访问就把管理员登录暴露在公网明文 HTTP 上。

## 八 备选方案 在电脑下载 ZIP 再上传

适用于服务器访问不了 GitHub，或不希望在服务器登录 GitHub。此方案替代第三、四节，其余启动步骤相同。服务器仍需能下载 Docker 镜像和 Python 依赖。

1. 在自己电脑浏览器登录有权限的 GitHub 账号，打开 [项目仓库](https://github.com/AtomBoyC/nuaa-infodesk)。
2. 确认分支选择 `main`，点击 **Code → Download ZIP**。操作方式见 [GitHub 官方下载说明](https://docs.github.com/en/repositories/working-with-files/using-files/downloading-source-code-archives)。
3. 首次部署时，在服务器执行 `mkdir -p "$HOME/apps"`。
4. 在自己电脑终端执行上传命令，将文件路径和服务器参数换成实际值：

```bash
scp -P 22 "$HOME/Downloads/nuaa-infodesk-main.zip" \
  SERVER_USER@SERVER_IP:~/apps/
```

`scp` 的端口参数是大写 `-P`。然后回到服务器执行：

```bash
cd "$HOME/apps"
unzip nuaa-infodesk-main.zip
mv nuaa-infodesk-main nuaa-infodesk
cd nuaa-infodesk
ls -a
```

这些目录必须尚不存在；已有部署不要直接重复 `mv` 或覆盖旧目录，应按第十节的升级原则保留配置。确认 `compose.yaml`、`.env.example`、`deploy/setup.py`、数据库均存在后，接第五节执行。不要手工只复制可见文件，否则容易漏掉 `.dockerignore` 和 `.env.example`。

## 九 数据位置与备份

数据库在 Docker 命名卷 `nuaa-infodesk_knowledge_data` 中，容器内路径为 `/app/data/info_service.db`。主机源码目录的 `data/info_service.db` 只是首次建卷用的初始数据，不能代表运行中的最新知识库。

已有卷时，新镜像不会用随附数据库覆盖线上知识和反馈。更改项目名、使用 `-p` 参数或更换 Docker 主机，可能连到另一个数据卷；不要自行修改 Compose 的 `name: nuaa-infodesk`。

**在服务器项目目录执行在线备份并导出到主机：**

```bash
BACKUP="infodesk-$(date -u +%Y%m%d-%H%M%S).db"
sudo docker compose exec -T infodesk python database_backup.py \
  --output "/app/data/backups/$BACKUP"
mkdir -p "$HOME/backups/nuaa-infodesk"
sudo docker compose cp \
  "infodesk:/app/data/backups/$BACKUP" \
  "$HOME/backups/nuaa-infodesk/$BACKUP"
sudo chown "$(id -u):$(id -g)" \
  "$HOME/backups/nuaa-infodesk/$BACKUP"
echo "$HOME/backups/nuaa-infodesk/$BACKUP"
```

记下最后输出的实际路径。在自己电脑使用 `scp -P 22 SERVER_USER@SERVER_IP:/实际备份路径 ./` 下载备份。只保存在同一台服务器或同一个卷里，不能防止整机故障或磁盘丢失。备份可能包含反馈内容，应限制访问，不要直接上传公开仓库。

**不要删除线上数据卷**。不要执行 `docker compose down --volumes`、`docker volume rm nuaa-infodesk_knowledge_data` 或带卷清理的全局清理命令，这些操作可能删除线上数据库。

恢复涉及覆盖现有数据，具体步骤见仓库内 `docs/docker-compose.md` 的“导出、恢复备份”，执行前先备份当前数据库。

## 十 下载新版本并更新

更新前按第九节备份。采用新目录解压方式，保留旧版本源码和部署配置。以下示例针对服务器下载方案；ZIP 上传也应采用新目录，并保留 `.env` 和整个 `.secrets`。

**在服务器执行。**`OLD` 必须指向当前正在使用的项目目录，第一次升级通常如下；后续升级应改为上次成功升级后的实际目录。

```bash
OLD="$HOME/apps/nuaa-infodesk"
NEW="$HOME/apps/nuaa-infodesk-$(date -u +%Y%m%d-%H%M%S)"
cd "$HOME/apps"
gh api --hostname github.com \
  repos/AtomBoyC/nuaa-infodesk/tarball/main \
  > nuaa-infodesk-update.tar.gz
tar -tzf nuaa-infodesk-update.tar.gz > /dev/null
mkdir "$NEW"
tar -xzf nuaa-infodesk-update.tar.gz \
  --strip-components=1 -C "$NEW"
cp -p "$OLD/.env" "$NEW/.env"
cp -a "$OLD/.secrets" "$NEW/.secrets"
cd "$NEW"
python3 deploy/setup.py
sudo docker compose config --quiet
sudo docker compose up -d --build --wait --wait-timeout 180
sudo docker compose exec infodesk python check_knowledge.py
pwd
```

若已退出 GitHub 登录，先重新执行第三节授权。启用 Caddy 的站点要为以上 Compose 命令加上第七节的双配置参数。之后验证网页功能，并记录 `pwd` 输出，今后从这个新目录操作；不要删除旧目录或数据库卷，也不要在旧目录运行 `down`，同名项目会影响当前服务。

更新代码不会自动导入 GitHub 仓库中更新过的知识数据。线上知识应通过“知识维护”或经过确认的导入流程更新，避免覆盖线上新增数据。数据库结构变化时，也不要仅通过切回旧源码目录来回滚数据库。

## 十一 日常命令和常见报错

以下命令在当前部署目录执行。HTTPS 站点须增加第七节所述的双配置参数。

```bash
sudo docker compose ps
sudo docker compose logs --tail=100 infodesk
sudo docker compose restart infodesk
```

前两条查看状态和日志，第三条重启应用。需要停止整个项目且保留数据时执行 `sudo docker compose down`；恢复时执行 `sudo docker compose up -d --wait --wait-timeout 180`。修改源码后需增加 `--build`，普通重启不会重新构建镜像。

- **GitHub 返回 404 或提示无权限**：确认授权账号可以在浏览器看到私有仓库；用 `gh auth status` 和 `gh repo view` 检查。不要因此修改仓库可见性。
- **解压提示不是 gzip 或 ZIP**：很可能下载到了错误页面，或下载中断。先解决下载错误，再重新下载和验证，不要用错误文件继续部署。
- **Docker permission denied**：使用本文的 `sudo docker`；不要给 Docker socket 设置 777 权限。
- **Cannot connect to the Docker daemon**：检查 Docker 服务是否启动，例如 Ubuntu 上执行 `sudo systemctl status docker`。
- **找不到 compose.yaml**：先 `pwd`、`ls -a`，进入包含该文件的目录；ZIP 可能多嵌套了一层。
- **找不到 secret 或密码读取失败**：先运行 `python3 deploy/setup.py`，检查 `.secrets` 的 0700 和密码文件的 0444 权限，不要把密码写进代码。
- **构建时拉取镜像或 pip 超时**：是服务器网络或包源问题，不是缺少知识库。使用可信的网络和镜像代理；不要关闭 TLS 校验或采用不明脚本。
- **端口被占用**：在 `.env` 修改 `INFODESK_PORT`，例如 8503，重新启动 Compose；同步修改 SSH 隧道目标和已有代理的目标端口。
- **容器健康但公网 IP 打不开**：默认仅绑定服务器本机，用第六节 SSH 隧道或第七节 HTTPS，不要在自己电脑直接打开服务器的 `127.0.0.1`。
- **网页一直连接中**：检查隧道是否断开，或反向代理是否支持 WebSocket。
- **HTTPS 证书申请失败**：检查域名解析、80/443 访问、AAAA 记录和端口占用，再看 Caddy 日志。
- **登录管理员失败**：使用当前部署目录的 `.secrets/admin_password`，不是 SSH 密码或 GitHub 密码。

## 附录 A 在新 Ubuntu 服务器安装 Docker

**仅适用于没有运行现有容器的新 Ubuntu 22.04 或 24.04 服务器**。已有 Docker 的服务器先检查版本，不要盲目卸载或替换。其他发行版按 [Docker 官方安装入口](https://docs.docker.com/engine/install/) 选择对应系统。以下按 [Docker 官方 Ubuntu 安装步骤](https://docs.docker.com/engine/install/ubuntu/) 整理，使用官方 apt 源，不运行来历不明的一键安装脚本。

在服务器安装工具并添加签名密钥：

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
```

添加 Ubuntu 软件源，下面从 `sudo tee` 到 `EOF` 是一个完整命令块：

```bash
sudo tee /etc/apt/sources.list.d/docker.sources > /dev/null <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF
```

安装并启用服务：

```bash
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io \
  docker-buildx-plugin docker-compose-plugin
sudo systemctl enable --now docker
sudo docker version
sudo docker compose version
```

如果提示与 `docker.io`、旧 Compose、containerd 或 runc 冲突，应先核实是否已有业务使用它们，再参考官方说明处理，不要在有业务的机器上直接删除。

## 附录 B 在 Ubuntu 安装 GitHub CLI

只在 `gh --version` 不可用时执行。以下采用 [GitHub CLI 官方 Linux 安装源](https://github.com/cli/cli/blob/trunk/docs/install_linux.md)，拆成几步方便检查：

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL \
  https://cli.github.com/packages/githubcli-archive-keyring.gpg \
  -o /etc/apt/keyrings/githubcli-archive-keyring.gpg
sudo chmod a+r /etc/apt/keyrings/githubcli-archive-keyring.gpg
```

添加软件源：

```bash
sudo tee /etc/apt/sources.list.d/github-cli.sources > /dev/null <<EOF
Types: deb
URIs: https://cli.github.com/packages
Suites: stable
Components: main
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/githubcli-archive-keyring.gpg
EOF
```

安装并检查：

```bash
sudo apt-get update
sudo apt-get install -y gh
gh --version
```

完成后回到第三节进行授权；单纯安装 `gh` 不会自动取得私有仓库访问权限。

## 部署完成检查

- 能从自己电脑通过 SSH 隧道或真实 HTTPS 域名打开页面。
- 搜索能显示匹配结果，知识目录和常用服务正常。
- 知识维护必须登录，管理员密码已妥善保存。
- `check_knowledge.py` 检查通过，数据库数量符合预期。
- 已做一次备份，并将备份复制到服务器之外。
- 密码、`.env`、GitHub 凭据均未提交到 GitHub；正式数据卷未被清理。

本文命令与仓库的 Compose、初始化及备份脚本核对。容器构建与持久化流程已在 GitHub Linux CI 验证，但尚未在你的远程服务器上执行；实际结果仍取决于服务器网络、权限、系统和域名配置。
