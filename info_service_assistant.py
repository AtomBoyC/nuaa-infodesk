from __future__ import annotations

from dataclasses import dataclass, asdict
import re
from typing import Iterable

from knowledge_taxonomy import ordered_categories


@dataclass(frozen=True)
class KnowledgeItem:
    id: str
    title: str
    category: str
    audience: str
    summary: str
    answer: str
    steps: tuple[str, ...]
    source: str
    owner: str
    updated: str
    tags: tuple[str, ...]
    link: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


KNOWLEDGE_BASE: tuple[KnowledgeItem, ...] = (
    KnowledgeItem(
        id="account-reset",
        title="统一身份认证密码找回",
        category="账号与安全",
        audience="学生 / 教职工",
        summary="处理账号登录失败、忘记密码、手机号变更后的身份核验问题。",
        answer=(
            "统一身份认证密码可在认证登录页通过绑定手机或邮箱自助找回。"
            "若绑定信息已失效，请携带校园卡或身份证件联系信息化服务大厅完成身份核验后重置。"
        ),
        steps=(
            "进入统一身份认证登录页，选择“忘记密码”。",
            "使用已绑定手机、邮箱或密保方式完成验证。",
            "绑定信息不可用时，提交人工核验申请或到服务大厅办理。",
        ),
        source="信息化处服务大厅办事指南",
        owner="账号安全岗",
        updated="2026-08-20",
        tags=("统一身份认证", "密码", "登录", "手机号", "账号"),
        link="https://software.nuaa.edu.cn",
    ),
    KnowledgeItem(
        id="campus-network",
        title="校园网无法连接",
        category="网络服务",
        audience="学生 / 教职工 / 访客",
        summary="排查宿舍区、办公区、教学区有线或无线网络连接异常。",
        answer=(
            "校园网连接异常通常需要先确认账号状态、终端 IP 获取情况和所在区域是否存在维护。"
            "若同区域多人异常，可直接提交网络报修；若只有单台设备异常，优先重新认证并忘记 Wi-Fi 后重连。"
        ),
        steps=(
            "确认终端已连接校园网 SSID 或有线端口，关闭代理后重新认证。",
            "检查账号是否欠费、停用或达到在线终端数量上限。",
            "保留楼宇、房间、端口、报错截图，提交网络报修。",
        ),
        source="校园网常见问题知识库",
        owner="网络运行岗",
        updated="2026-08-16",
        tags=("校园网", "Wi-Fi", "网络", "认证", "报修", "掉线", "无法连接"),
    ),
    KnowledgeItem(
        id="vpn-access",
        title="校外访问校内资源 VPN",
        category="网络服务",
        audience="教职工 / 研究生",
        summary="说明在校外访问图书馆数据库、校内业务系统的安全通道。",
        answer=(
            "校外访问校内资源时，请使用学校提供的 VPN 或 WebVPN 服务，并使用统一身份认证登录。"
            "涉密或内部管理系统需按部门权限开通后访问。"
        ),
        steps=(
            "打开学校 VPN 或 WebVPN 入口。",
            "使用统一身份认证账号登录并完成二次验证。",
            "在资源导航页进入目标系统，无法访问时申请系统权限。",
        ),
        source="远程访问服务说明",
        owner="网络安全岗",
        updated="2026-08-10",
        tags=("VPN", "WebVPN", "校外访问", "图书馆", "数据库", "校内资源"),
    ),
    KnowledgeItem(
        id="software-license",
        title="正版软件下载安装",
        category="软件服务",
        audience="学生 / 教职工",
        summary="说明正版软件平台入口、授权范围和安装注意事项。",
        answer=(
            "学校正版软件平台面向校内师生提供授权范围内的软件下载安装。"
            "下载前请确认软件适用对象、授权期限和终端数量，安装包不得对校外传播。"
        ),
        steps=(
            "访问学校正版软件平台首页。",
            "选择所需软件，阅读授权说明和安装环境要求。",
            "使用统一身份认证登录后下载安装包或获取授权方式。",
        ),
        source="正版软件平台使用说明",
        owner="软件服务岗",
        updated="2026-08-12",
        tags=("正版软件", "安装包", "Office", "Windows", "授权", "software", "软件"),
        link="https://software.nuaa.edu.cn",
    ),
    KnowledgeItem(
        id="email-service",
        title="校园邮箱开通与容量问题",
        category="协同办公",
        audience="学生 / 教职工",
        summary="处理邮箱开通、别名、容量预警、客户端配置等问题。",
        answer=(
            "校园邮箱通常随统一身份认证账号自动开通。容量不足时请先清理大附件和已删除邮件；"
            "客户端收发异常时，优先使用网页版确认账号状态。"
        ),
        steps=(
            "登录邮箱网页版，确认账号可正常收发。",
            "清理大附件、垃圾邮件和已删除邮件。",
            "按官方参数重新配置客户端，仍异常时提交工单。",
        ),
        source="邮箱服务 FAQ",
        owner="协同办公岗",
        updated="2026-08-18",
        tags=("邮箱", "邮件", "容量", "客户端", "SMTP", "IMAP"),
    ),
    KnowledgeItem(
        id="repair-ticket",
        title="信息化服务报修与进度查询",
        category="服务大厅",
        audience="全校师生",
        summary="帮助用户选择报修类型、提交材料并追踪办理状态。",
        answer=(
            "信息化问题建议通过服务大厅统一提交，系统会按账号、网络、软件、办公系统等类型分派处理。"
            "提交时请补充地点、账号、设备、报错截图和可复现步骤。"
        ),
        steps=(
            "进入信息化服务大厅，选择对应报修类型。",
            "填写联系人、地点、问题现象和影响范围。",
            "提交后在“我的工单”中查看处理进度和补充材料。",
        ),
        source="信息化服务大厅流程",
        owner="服务受理岗",
        updated="2026-08-22",
        tags=("报修", "工单", "进度", "服务大厅", "截图", "故障"),
    ),
    KnowledgeItem(
        id="data-security",
        title="数据安全与钓鱼邮件处置",
        category="账号与安全",
        audience="全校师生",
        summary="识别钓鱼邮件、异常登录和敏感数据外发风险。",
        answer=(
            "收到疑似钓鱼邮件时不要点击链接或提交密码，应保留邮件头、发件人和正文截图并上报。"
            "若已输入密码，请立即修改统一身份认证密码并申请安全排查。"
        ),
        steps=(
            "不要点击可疑链接，不下载陌生附件。",
            "转发邮件头信息或截图给安全受理渠道。",
            "疑似泄露后立即改密，并退出所有在线会话。",
        ),
        source="网络安全应急处置手册",
        owner="网络安全岗",
        updated="2026-08-14",
        tags=("安全", "钓鱼邮件", "密码泄露", "异常登录", "数据", "泄露"),
    ),
    KnowledgeItem(
        id="portal-access",
        title="网上办事大厅无法进入",
        category="办事大厅",
        audience="学生 / 教职工",
        summary="处理网上办事大厅打不开、流程入口找不到、待办加载失败等问题。",
        answer=(
            "网上办事大厅无法进入时，请先确认浏览器兼容性、统一身份认证状态和网络环境。"
            "若流程入口缺失，通常与个人身份、部门权限或流程开放范围有关，可联系流程主管部门确认。"
        ),
        steps=(
            "优先使用新版 Chrome、Edge 或 Safari 浏览器访问。",
            "退出统一身份认证后重新登录，避免旧会话失效。",
            "记录流程名称、账号、浏览器版本和报错截图，提交服务大厅工单。",
        ),
        source="网上办事大厅使用说明",
        owner="业务系统岗",
        updated="2026-08-25",
        tags=("网上办事大厅", "办事大厅", "流程", "待办", "权限", "打不开"),
    ),
    KnowledgeItem(
        id="campus-card",
        title="校园卡挂失、补办与充值",
        category="校园服务",
        audience="学生 / 教职工",
        summary="说明校园卡遗失、补卡、充值失败和消费异常的处理方式。",
        answer=(
            "校园卡遗失后应尽快在校园卡平台或服务终端办理挂失。补办时请携带有效证件，"
            "充值或消费异常需保留交易时间、金额、终端位置等信息便于核查。"
        ),
        steps=(
            "发现校园卡遗失后立即自助挂失。",
            "到指定补卡点携带身份证件办理补卡。",
            "充值未到账或扣费异常时，提交交易截图和发生时间。",
        ),
        source="校园卡服务指南",
        owner="校园卡服务岗",
        updated="2026-08-19",
        tags=("校园卡", "一卡通", "挂失", "补办", "充值", "消费异常"),
    ),
    KnowledgeItem(
        id="teaching-system",
        title="教务系统登录与选课异常",
        category="业务系统",
        audience="学生 / 教职工",
        summary="处理教务系统登录失败、页面空白、选课提交异常等问题。",
        answer=(
            "教务系统登录异常通常与统一身份认证、浏览器缓存或系统访问高峰有关。"
            "选课期间如提交失败，请不要频繁刷新，先截图保存异常信息，再按教务处通知渠道处理。"
        ),
        steps=(
            "清理浏览器缓存或更换浏览器后重新登录。",
            "确认当前是否处于选课高峰或系统维护窗口。",
            "保存学号、课程号、报错时间和截图，联系教务系统支持。",
        ),
        source="教务系统常见问题说明",
        owner="业务系统岗",
        updated="2026-08-23",
        tags=("教务系统", "选课", "成绩", "培养方案", "登录", "页面空白"),
    ),
    KnowledgeItem(
        id="research-system",
        title="科研管理系统权限申请",
        category="业务系统",
        audience="教职工 / 科研秘书",
        summary="说明科研管理系统账号权限、项目角色和部门授权申请流程。",
        answer=(
            "科研管理系统权限通常按人员身份、项目角色和部门职责分配。"
            "若看不到项目、经费或审批菜单，应先由所在单位管理员确认角色，再提交权限调整申请。"
        ),
        steps=(
            "确认本人统一身份认证账号可正常登录。",
            "联系学院或部门管理员核对系统角色。",
            "提交权限申请，注明系统名称、所需菜单和业务理由。",
        ),
        source="科研管理系统权限说明",
        owner="业务系统岗",
        updated="2026-08-21",
        tags=("科研管理", "权限", "项目", "经费", "审批", "角色"),
    ),
    KnowledgeItem(
        id="printer-service",
        title="校园自助打印无法使用",
        category="校园服务",
        audience="学生 / 教职工",
        summary="处理自助打印登录失败、余额异常、打印任务卡住等问题。",
        answer=(
            "自助打印异常时，请先确认账号登录、打印余额和文件格式。"
            "若任务长时间排队或扣费未出纸，请记录打印点位、设备编号、文件名和时间后提交反馈。"
        ),
        steps=(
            "重新登录自助打印平台，确认余额和任务状态。",
            "将文件转为 PDF 后重新提交。",
            "记录设备编号、扣费金额和异常截图，提交打印服务反馈。",
        ),
        source="自助打印服务 FAQ",
        owner="校园服务岗",
        updated="2026-08-17",
        tags=("打印", "自助打印", "扣费", "PDF", "任务", "设备编号"),
    ),
    KnowledgeItem(
        id="classroom-multimedia",
        title="多媒体教室设备报修",
        category="教学支持",
        audience="教师 / 教学秘书",
        summary="处理投影、电脑、麦克风、中控、录播等教学设备故障。",
        answer=(
            "多媒体教室设备故障会直接影响教学，应优先按楼宇和教室号提交紧急报修。"
            "上课中故障可联系值班人员现场处理，课后补充工单用于闭环记录。"
        ),
        steps=(
            "记录校区、楼宇、教室号和课程时间。",
            "说明故障设备，例如投影、电脑、麦克风或中控。",
            "上传现场照片或报错信息，选择教学支持类工单。",
        ),
        source="多媒体教室运维指南",
        owner="教学技术岗",
        updated="2026-08-24",
        tags=("多媒体教室", "投影", "麦克风", "中控", "录播", "报修"),
    ),
    KnowledgeItem(
        id="meeting-service",
        title="视频会议与直播支持申请",
        category="协同办公",
        audience="教职工 / 部门管理员",
        summary="说明会议账号、直播推流、活动保障和录制支持申请。",
        answer=(
            "部门会议、学术报告或大型活动如需视频会议和直播支持，应提前提交保障申请。"
            "申请中需注明会议时间、参会规模、是否录制、是否需要直播链接和现场技术支持。"
        ),
        steps=(
            "提前提交会议保障申请，写明活动时间和地点。",
            "确认参会人数、会议平台、直播范围和录制需求。",
            "活动前完成设备联调，重要活动建议预留彩排时间。",
        ),
        source="视频会议服务说明",
        owner="协同办公岗",
        updated="2026-08-26",
        tags=("视频会议", "直播", "录制", "会议", "活动保障", "推流"),
    ),
    KnowledgeItem(
        id="cloud-drive",
        title="校内云盘和文件共享",
        category="协同办公",
        audience="学生 / 教职工",
        summary="处理云盘登录、容量、共享链接、协作文档等问题。",
        answer=(
            "校内云盘适合存放教学、科研和办公协作文件。共享文件时请按最小权限原则设置访问范围，"
            "不要通过公开链接传播含个人信息、考试材料或内部资料的文件。"
        ),
        steps=(
            "使用统一身份认证登录云盘平台。",
            "根据协作对象设置仅本人、指定人员或校内可见。",
            "容量不足时清理历史版本、大文件和回收站。",
        ),
        source="云盘服务使用规范",
        owner="协同办公岗",
        updated="2026-08-15",
        tags=("云盘", "文件共享", "协作文档", "容量", "共享链接", "权限"),
    ),
    KnowledgeItem(
        id="terminal-limit",
        title="校园网在线终端数量超限",
        category="网络服务",
        audience="学生 / 教职工",
        summary="说明账号被提示在线终端超限时如何下线旧设备。",
        answer=(
            "校园网账号达到在线终端数量上限时，新设备会认证失败。"
            "可在网络自服务平台查看在线设备并下线不再使用的终端，再重新认证当前设备。"
        ),
        steps=(
            "进入网络自服务平台，查看当前在线终端。",
            "下线不认识或暂不使用的设备。",
            "当前设备断开网络后重新连接并完成认证。",
        ),
        source="网络自服务平台说明",
        owner="网络运行岗",
        updated="2026-08-13",
        tags=("终端超限", "在线设备", "网络自服务", "认证失败", "下线"),
    ),
    KnowledgeItem(
        id="ip-address",
        title="固定 IP 地址申请",
        category="网络服务",
        audience="教职工 / 实验室管理员",
        summary="说明服务器、实验室设备和业务系统固定 IP 申请要求。",
        answer=(
            "固定 IP 地址主要面向服务器、实验室公共设备和确有业务需要的终端。"
            "申请时需说明用途、责任人、使用地点、设备 MAC 地址和安全管理措施。"
        ),
        steps=(
            "填写固定 IP 申请，注明业务用途和使用期限。",
            "提供设备 MAC 地址、放置地点和责任人联系方式。",
            "获批后按分配的 IP、网关和 DNS 参数配置设备。",
        ),
        source="校园网地址资源管理办法",
        owner="网络运行岗",
        updated="2026-08-11",
        tags=("固定IP", "IP地址", "MAC地址", "服务器", "实验室", "DNS"),
    ),
    KnowledgeItem(
        id="website-publish",
        title="部门网站信息发布申请",
        category="网站与数据",
        audience="部门管理员 / 网站信息员",
        summary="说明部门网站栏目维护、信息发布、账号权限和内容审核要求。",
        answer=(
            "部门网站信息发布应遵循先审核后发布原则。新增栏目、调整权限或发布重要通知时，"
            "需由部门网站信息员提交申请，并确保内容来源真实、表述准确、无敏感信息泄露。"
        ),
        steps=(
            "确认发布内容已经部门审核。",
            "提交栏目、账号或发布权限申请。",
            "发布后复核页面展示、附件下载和移动端效果。",
        ),
        source="网站群管理与信息发布规范",
        owner="网站管理岗",
        updated="2026-08-27",
        tags=("部门网站", "信息发布", "网站群", "栏目", "权限", "审核"),
    ),
    KnowledgeItem(
        id="data-report",
        title="数据报表与统计口径咨询",
        category="网站与数据",
        audience="机关部门 / 学院管理员",
        summary="处理数据报表口径、权限、导出和跨系统数据不一致问题。",
        answer=(
            "数据报表差异通常来自统计时间、人员范围、业务状态或系统同步延迟。"
            "咨询时请提供报表名称、统计条件、截图和期望口径，便于信息化处联合业务部门核对。"
        ),
        steps=(
            "明确报表名称、查询时间和筛选条件。",
            "截图标注差异字段和期望统计口径。",
            "提交数据咨询工单，由业务部门和数据管理员共同确认。",
        ),
        source="数据服务咨询流程",
        owner="数据治理岗",
        updated="2026-08-28",
        tags=("数据报表", "统计口径", "数据治理", "导出", "权限", "同步"),
    ),
)


QUICK_QUESTIONS = (
    "校园网连不上怎么办？",
    "校外怎么访问图书馆数据库？",
    "正版软件平台怎么下载 Office？",
    "统一身份认证密码忘了怎么办？",
    "信息化问题在哪里报修？",
    "网上办事大厅打不开怎么办？",
    "多媒体教室投影坏了怎么报修？",
    "校园网提示终端数量超限怎么办？",
)


def categories(items: Iterable[KnowledgeItem]) -> list[str]:
    return ordered_categories(item.category for item in items)


def normalize(value: str) -> str:
    return value.lower().strip()


def tokenize(query: str) -> list[str]:
    normalized = normalize(query)
    tokens = [token for token in re.split(r"[\s,，。！？?;；、/\\]+", normalized) if token]

    # Chinese questions often arrive without spaces. Add short phrase fragments so
    # “校外怎么访问校内资源” can still match a “校外访问校内途径” knowledge item.
    for phrase in re.findall(r"[\u4e00-\u9fff]{2,}", normalized):
        cleaned = re.sub(r"^(如何|怎么|请问|我要|我想|能否|可以|在)", "", phrase)
        for length in (2, 3, 4):
            tokens.extend(
                cleaned[index:index + length]
                for index in range(max(len(cleaned) - length + 1, 0))
            )

    return list(dict.fromkeys(token for token in tokens if token))


def score_item(query: str, item: KnowledgeItem) -> int:
    if not query.strip():
        return 0

    text = normalize(
        " ".join(
            [
                item.title,
                item.category,
                item.summary,
                item.answer,
                " ".join(item.tags),
            ]
        )
    )
    score = 9 if normalize(query) in text else 0

    for token in tokenize(query):
        if token in normalize(item.title):
            score += 5
        if any(token in normalize(tag) or normalize(tag) in token for tag in item.tags):
            score += 4
        if token in text:
            score += 2

    score += sum(3 for tag in item.tags if tag in query)
    return score


def confidence_for_score(score: int) -> int:
    return min(96, max(42, 48 + score * 6))


def rank_knowledge(
    query: str,
    items: Iterable[KnowledgeItem] = KNOWLEDGE_BASE,
    *,
    limit: int | None = None,
) -> list[tuple[KnowledgeItem, int]]:
    ranked = sorted(
        ((item, score_item(query, item)) for item in items),
        key=lambda entry: (entry[1], entry[0].title),
        reverse=True,
    )
    return ranked if limit is None else ranked[:limit]


def match_knowledge(
    query: str,
    items: Iterable[KnowledgeItem] = KNOWLEDGE_BASE,
) -> tuple[KnowledgeItem, int, list[KnowledgeItem]]:
    ranked = rank_knowledge(query, items)
    if not ranked:
        raise ValueError("knowledge base is empty")

    best_item, best_score = ranked[0]
    confidence = confidence_for_score(best_score)
    related = [item for item, _score in ranked[:3]]
    return best_item, confidence, related


def build_answer(query: str, item: KnowledgeItem, confidence: int) -> str:
    if confidence < 55:
        return f"我没有完全匹配到“{query}”的专门条目，先按“{item.title}”给出相近建议：{item.answer}"
    return item.answer
