# 校内信息服务智能问答台

面向校内师生的信息化处信息问答工具。当前主版本采用 **Python + Streamlit + SQLite** 开发，适合比赛演示、快速部署和后续维护；仓库中也保留了一个 React/Next.js Web 版本，可作为视觉增强备选方案。

## 作品基本信息

- 作品名称：校内信息服务智能问答台
- 作品类型：可运行的软件工具
- 技术路线：Python + Streamlit + SQLite
- 使用场景：校园信息化处服务咨询、服务大厅导办、常见问题自助查询
- 面向对象：校内学生、教职工、访客服务人员
- 核心价值：减少重复咨询，提高服务响应效率，让问答结果有来源、有责任岗、有反馈

## 功能介绍

- 问答检索：通过页面顶部搜索框输入自然语言问题，展示最多 10 条相关候选及对应标准答复；无匹配时提示补充问题。
- 独立页面：智能问答、匹配结果、知识目录、常用服务、最近会话、知识维护分别使用独立路由。
- 分类浏览：统一按网络服务、账号与安全、服务大厅、信息系统、协同办公、软件服务、通知与制度、新闻与党建、部门信息分类查看。
- 来源追溯：每条回答展示来源、更新时间、责任岗位，便于后续审核和维护。
- 快捷问题：内置校园网、VPN、正版软件、统一身份认证、报修等高频入口。
- 反馈闭环：记录“有帮助”和“需人工跟进”，用于评估知识库质量。
- 知识维护：支持保存草稿、审核并发布，以及导出包含发布状态的完整知识库 JSON；草稿在发布前不参与问答和目录检索。
- 数据持久化：知识库条目和反馈记录保存在本地数据库中，应用重启后仍可保留。
- 随仓数据：`data/info_service.db` 包含 254 条知识、9 个分类。缺失数据库时，系统创建空库并补入 19 条默认示例。
- 官网导入：可将信息化处官网的公开页面按主题分类后写入 SQLite，并保留原文链接。

## 文件结构

```text
streamlit_app.py              # Streamlit 界面入口
info_service_assistant.py     # 知识库数据、检索评分、答案生成逻辑
database.py                    # SQLite 建表、初始化、读写和反馈统计
site_importer.py               # 信息化处官网公开页面抓取、分类、导入工具
docx_importer.py               # 本地 Word 问答资料解析、分类、导入工具
knowledge_taxonomy.py          # 知识分类归一化规则
knowledge_dedup.py             # 数据库重复条目检查与清理工具
check_knowledge.py             # 只读检查完整性、必填字段和同名重复
requirements.txt              # Python 依赖
data/info_service.db           # 正式知识库，已纳入版本控制
docs/                         # 参赛提交清单和检查记录
.github/workflows/tests.yml    # GitHub 自动测试
tests/test_info_service_assistant.py
tests/test_database.py
react-next-version/          # 早期 React/Next.js Web 版本，已独立归档
README.md
```

React/Next.js 版本已移动到 `react-next-version/`，不影响根目录的 Python 主版本运行。

## 运行环境

- Python：建议 3.10 或以上
- 主要依赖：Streamlit 1.62.0，版本在 requirements.txt 中固定
- 数据存储：SQLite，本地数据库文件默认生成在 `data/info_service.db`

## 安装与运行

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m streamlit run streamlit_app.py --server.address localhost
```

启动后浏览器会打开本地地址，通常为：

```text
http://localhost:8501/
```

从仓库下载时已包含正式知识库，可以直接使用。只有数据库文件缺失时，才会自动创建数据库并写入 19 条默认示例。数据库默认路径相对于本工程目录解析，避免从不同目录启动时误建新库。

点击顶部“知识维护”可以保存草稿并审核发布。新增条目和反馈保存在 `data/info_service.db`。升级时会自动补充缺失的数据库字段，原有知识保留。Docker Compose 部署会为知识维护启用管理员密码；本机开发未配置密码时保留直接访问。

## Docker Compose 部署

GitHub 仓库已公开，下载项目不需要登录、Token 或 GitHub CLI。首次下载并解压到 Linux 服务器，请按 [Linux 服务器部署操作指南](docs/linux-github-deployment.md) 操作，包含公开仓库下载、Ubuntu 环境准备、SSH 隧道、HTTPS、更新和备份。知识维护的管理员登录仍然保留。

```bash
python3 deploy/setup.py
docker compose up -d --build --wait --wait-timeout 180
```

首次启动使用随镜像附带的知识库，数据库放在持久化数据卷中。基础配置绑定服务器 `127.0.0.1:8501`，可以用 SSH 隧道或现有网关访问；有域名时可叠加 `compose.https.yaml` 提供 HTTPS。详细的域名配置、管理员登录、更新和备份恢复步骤见 [远程服务器部署说明](docs/docker-compose.md)。

匹配度是文本检索的相关程度，不代表答案正确概率。当前版本使用本地知识检索和已有标准答复，没有连接大模型 API。最近会话仅保留当前浏览器会话中的 5 次有效查询，刷新重连后可能清空。

默认知识库覆盖：

- 账号与安全：统一身份认证密码找回、数据安全与钓鱼邮件处置
- 网络服务：校园网无法连接、VPN / WebVPN、终端数量超限、固定 IP 申请
- 软件服务：正版软件下载安装
- 协同办公：校园邮箱、视频会议与直播、校内云盘
- 办事大厅：网上办事大厅访问异常、工单报修与进度查询
- 校园服务：校园卡、自助打印
- 教学支持：多媒体教室设备报修
- 业务系统：教务系统、科研管理系统
- 网站与数据：部门网站信息发布、数据报表与统计口径咨询

## 导入信息化处官网公开内容

下面的命令会从 `https://xxhc.nuaa.edu.cn` 开始，抓取本域名内公开的 HTML 页面（默认最多 300 页），按服务指南、常见问题、网络服务、制度规范、通知公告等主题分类后写入 SQLite。每条记录保留官网来源链接，供回答时追溯完整原文。

```bash
python site_importer.py --max-pages 300
```

导入器只处理公开 HTML 页面，自动跳过登录/管理入口和图片、PDF、Office 文档等附件；为减少对官网的访问压力，请保持默认的 0.25 秒请求间隔。先预览而不写入数据库时可运行：

```bash
python site_importer.py --dry-run --max-pages 30
```

官网内容会随时间变化。需要更新时重新运行相同命令即可，系统会根据网页链接覆盖更新对应记录，而不会重复新增。
同步会先完整抓取并校验内容，默认需要发现至少 50 个有效正文页面才会在一个数据库事务中更新旧的官网记录；抓取异常或数量明显不足时，原数据库不会被修改。

## 导入本地 Word 问答资料

对于以“问：… / 答：…”编写的 `.docx` 问答资料，可一次导入多个文件：

```bash
python docx_importer.py "网络知识库问答版.docx" "信息系统知识库问答版.docx"
```

导入器会合并同一答案的多段说明，按服务主题归入统一分类。同一个问题在不同版本中重复出现时，优先采用文件名年份较新的版本，再按输入顺序选择。可加 `--dry-run` 预览解析结果。

Word 导入采用**整批替换**：成功后会替换数据库中全部 `docx-` 条目。因此更新时应一次传入全部需要保留的 Word 文件，而不只是本次新增文件。空输入、文件不存在或单个文件少于 5 组有效问答时会中止。官网导入也采用整批替换；两类导入都保留其他来源的知识和反馈。

## 数据检查与备份

```bash
python check_knowledge.py
python check_knowledge.py --db /绝对路径/知识库.db
```

检查命令只读，不创建或修改数据库，输出完整性、条目数量、分类、必填字段缺失和规范化标题重复。发现问题时返回非零退出码，便于自动检查。它不判断两条不同标题的答案是否语义重复，也不判断业务口径是否过期。

导入、清理或升级前，先备份当前数据库。可以使用 SQLite 的在线备份接口：

```bash
python -c "from pathlib import Path; import sqlite3; Path('data/backups').mkdir(parents=True, exist_ok=True); source=sqlite3.connect('data/info_service.db'); target=sqlite3.connect('data/backups/info_service_before_update.db'); source.backup(target); target.close(); source.close()"
```

正式数据库参与 Git 版本控制，备份及 SQLite 临时日志不上传。更新知识库后需要单独检查并提交数据库变动。反馈含用户输入，提交数据库前也应检查是否包含不适合分享的内容。

## 测试方法

```bash
python -m unittest discover -s tests -p "test_*.py"
```

也可以直接用 Python 执行核心逻辑检查：

```bash
python -m compileall -q info_service_assistant.py database.py streamlit_app.py site_importer.py docx_importer.py check_knowledge.py
```

## 演示建议

1. 在顶部搜索“校园网连不上怎么办？”，进入独立的匹配结果页。
2. 输入“校外怎么访问图书馆数据库？”展示 VPN / WebVPN 匹配。
3. 展示回答下方的办理步骤、来源、责任岗和更新时间。
4. 点击“有帮助”或“需人工跟进”，说明反馈闭环。
5. 在“知识维护”中新增草稿，先确认公开检索不可见，再审核发布后重新搜索。
6. 导出知识库 JSON，说明数据库内容可以交给管理员审核或迁移。

## 后续扩展方向

- 接入学校正式 FAQ、办事指南、服务公告和工单系统数据。
- 增加后台页面，对 SQLite 中的知识条目进行编辑、审核、下架和版本管理。
- 增加管理员审核流程，将临时知识草稿发布到正式知识库。
- 在学校允许的前提下接入合规大模型 API，实现更自然的多轮问答。
- 增加问题脱敏、敏感词识别、人工转派和服务满意度报表。

## 第三方依赖与许可说明

本作品使用公开开源依赖构建，主要依赖为 Streamlit。参赛提交时可附带 `requirements.txt` 作为依赖清单，按依赖原始开源协议执行。

参赛材料准备情况见 [提交清单](docs/submission-checklist.md)，本轮技术检查记录见 [检查记录](docs/project-audit.md)。

## 原创与合规承诺

本项目源码和页面内容由参赛者围绕校园信息化服务场景自主设计开发。项目不包含破解软件、激活工具或规避授权机制，不采集真实个人敏感信息。示例链接和服务条目用于演示，可在正式提交前替换为学校审核后的真实材料。
