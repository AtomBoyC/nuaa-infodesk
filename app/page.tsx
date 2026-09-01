"use client";

import { FormEvent, useMemo, useState } from "react";

type KnowledgeItem = {
  id: string;
  title: string;
  category: string;
  audience: string;
  summary: string;
  answer: string;
  steps: string[];
  source: string;
  owner: string;
  updated: string;
  tags: string[];
  link?: string;
};

type ChatMessage = {
  id: number;
  question: string;
  answer: string;
  matchedTitle: string;
  confidence: number;
  source: string;
};

type Feedback = {
  helpful: number;
  followUp: number;
};

const baseKnowledge: KnowledgeItem[] = [
  {
    id: "account-reset",
    title: "统一身份认证密码找回",
    category: "账号与安全",
    audience: "学生 / 教职工",
    summary: "处理账号登录失败、忘记密码、手机号变更后的身份核验问题。",
    answer:
      "统一身份认证密码可在认证登录页通过绑定手机或邮箱自助找回。若绑定信息已失效，请携带校园卡或身份证件联系信息化服务大厅完成身份核验后重置。",
    steps: [
      "进入统一身份认证登录页，选择“忘记密码”。",
      "使用已绑定手机、邮箱或密保方式完成验证。",
      "绑定信息不可用时，提交人工核验申请或到服务大厅办理。",
    ],
    source: "信息化处服务大厅办事指南",
    owner: "账号安全岗",
    updated: "2026-08-20",
    tags: ["统一身份认证", "密码", "登录", "手机号", "账号"],
    link: "https://software.nuaa.edu.cn",
  },
  {
    id: "campus-network",
    title: "校园网无法连接",
    category: "网络服务",
    audience: "学生 / 教职工 / 访客",
    summary: "排查宿舍区、办公区、教学区有线或无线网络连接异常。",
    answer:
      "校园网连接异常通常需要先确认账号状态、终端 IP 获取情况和所在区域是否存在维护。若同区域多人异常，可直接提交网络报修；若只有单台设备异常，优先重新认证并忘记 Wi-Fi 后重连。",
    steps: [
      "确认终端已连接校园网 SSID 或有线端口，关闭代理后重新认证。",
      "检查账号是否欠费、停用或达到在线终端数量上限。",
      "保留楼宇、房间、端口、报错截图，提交网络报修。",
    ],
    source: "校园网常见问题知识库",
    owner: "网络运行岗",
    updated: "2026-08-16",
    tags: ["校园网", "Wi-Fi", "网络", "认证", "报修", "掉线"],
  },
  {
    id: "vpn-access",
    title: "校外访问校内资源 VPN",
    category: "网络服务",
    audience: "教职工 / 研究生",
    summary: "说明在校外访问图书馆数据库、校内业务系统的安全通道。",
    answer:
      "校外访问校内资源时，请使用学校提供的 VPN 或 WebVPN 服务，并使用统一身份认证登录。涉密或内部管理系统需按部门权限开通后访问。",
    steps: [
      "打开学校 VPN 或 WebVPN 入口。",
      "使用统一身份认证账号登录并完成二次验证。",
      "在资源导航页进入目标系统，无法访问时申请系统权限。",
    ],
    source: "远程访问服务说明",
    owner: "网络安全岗",
    updated: "2026-08-10",
    tags: ["VPN", "WebVPN", "校外访问", "图书馆", "数据库"],
  },
  {
    id: "software-license",
    title: "正版软件下载安装",
    category: "软件服务",
    audience: "学生 / 教职工",
    summary: "说明正版软件平台入口、授权范围和安装注意事项。",
    answer:
      "学校正版软件平台面向校内师生提供授权范围内的软件下载安装。下载前请确认软件适用对象、授权期限和终端数量，安装包不得对校外传播。",
    steps: [
      "访问学校正版软件平台首页。",
      "选择所需软件，阅读授权说明和安装环境要求。",
      "使用统一身份认证登录后下载安装包或获取授权方式。",
    ],
    source: "正版软件平台使用说明",
    owner: "软件服务岗",
    updated: "2026-08-12",
    tags: ["正版软件", "安装包", "Office", "Windows", "授权", "software"],
    link: "https://software.nuaa.edu.cn",
  },
  {
    id: "email-service",
    title: "校园邮箱开通与容量问题",
    category: "协同办公",
    audience: "学生 / 教职工",
    summary: "处理邮箱开通、别名、容量预警、客户端配置等问题。",
    answer:
      "校园邮箱通常随统一身份认证账号自动开通。容量不足时请先清理大附件和已删除邮件；客户端收发异常时，优先使用网页版确认账号状态。",
    steps: [
      "登录邮箱网页版，确认账号可正常收发。",
      "清理大附件、垃圾邮件和已删除邮件。",
      "按官方参数重新配置客户端，仍异常时提交工单。",
    ],
    source: "邮箱服务 FAQ",
    owner: "协同办公岗",
    updated: "2026-08-18",
    tags: ["邮箱", "邮件", "容量", "客户端", "SMTP", "IMAP"],
  },
  {
    id: "repair-ticket",
    title: "信息化服务报修与进度查询",
    category: "服务大厅",
    audience: "全校师生",
    summary: "帮助用户选择报修类型、提交材料并追踪办理状态。",
    answer:
      "信息化问题建议通过服务大厅统一提交，系统会按账号、网络、软件、办公系统等类型分派处理。提交时请补充地点、账号、设备、报错截图和可复现步骤。",
    steps: [
      "进入信息化服务大厅，选择对应报修类型。",
      "填写联系人、地点、问题现象和影响范围。",
      "提交后在“我的工单”中查看处理进度和补充材料。",
    ],
    source: "信息化服务大厅流程",
    owner: "服务受理岗",
    updated: "2026-08-22",
    tags: ["报修", "工单", "进度", "服务大厅", "截图"],
  },
  {
    id: "data-security",
    title: "数据安全与钓鱼邮件处置",
    category: "账号与安全",
    audience: "全校师生",
    summary: "识别钓鱼邮件、异常登录和敏感数据外发风险。",
    answer:
      "收到疑似钓鱼邮件时不要点击链接或提交密码，应保留邮件头、发件人和正文截图并上报。若已输入密码，请立即修改统一身份认证密码并申请安全排查。",
    steps: [
      "不要点击可疑链接，不下载陌生附件。",
      "转发邮件头信息或截图给安全受理渠道。",
      "疑似泄露后立即改密，并退出所有在线会话。",
    ],
    source: "网络安全应急处置手册",
    owner: "网络安全岗",
    updated: "2026-08-14",
    tags: ["安全", "钓鱼邮件", "密码泄露", "异常登录", "数据"],
  },
];

const categories = ["全部", ...Array.from(new Set(baseKnowledge.map((item) => item.category)))];

const quickQuestions = [
  "校园网连不上怎么办？",
  "校外怎么访问图书馆数据库？",
  "正版软件平台怎么下载 Office？",
  "统一身份认证密码忘了怎么办？",
  "信息化问题在哪里报修？",
];

const defaultFeedback: Feedback = { helpful: 0, followUp: 0 };

const normalize = (value: string) => value.toLowerCase().trim();

function readJsonStorage<T>(key: string, fallback: T): T {
  if (typeof window === "undefined") return fallback;

  try {
    const value = window.localStorage.getItem(key);
    return value ? (JSON.parse(value) as T) : fallback;
  } catch {
    return fallback;
  }
}

function scoreItem(query: string, item: KnowledgeItem) {
  const text = normalize(
    [item.title, item.category, item.summary, item.answer, item.tags.join(" ")].join(" "),
  );
  const tokens = normalize(query)
    .split(/[\s,，。！？?;；、/\\]+/)
    .filter(Boolean);

  if (!query.trim()) return 0;

  let score = text.includes(normalize(query)) ? 9 : 0;
  for (const token of tokens) {
    if (item.title.toLowerCase().includes(token)) score += 5;
    if (item.tags.some((tag) => normalize(tag).includes(token) || token.includes(normalize(tag)))) score += 4;
    if (text.includes(token)) score += 2;
  }

  const keywordHits = item.tags.filter((tag) => query.includes(tag)).length;
  return score + keywordHits * 3;
}

function matchKnowledge(query: string, knowledge: KnowledgeItem[]) {
  const ranked = knowledge
    .map((item) => ({ item, score: scoreItem(query, item) }))
    .sort((a, b) => b.score - a.score);

  const best = ranked[0]?.score > 0 ? ranked[0] : { item: knowledge[0], score: 0 };
  const confidence = Math.min(96, Math.max(42, 48 + best.score * 6));
  return { best: best.item, confidence, related: ranked.slice(0, 3).map((entry) => entry.item) };
}

function buildAnswer(query: string, item: KnowledgeItem, confidence: number) {
  if (confidence < 55) {
    return `我没有完全匹配到“${query}”的专门条目，先按“${item.title}”给出相近建议：${item.answer}`;
  }

  return item.answer;
}

export default function Home() {
  const [question, setQuestion] = useState("校园网连不上怎么办？");
  const [activeCategory, setActiveCategory] = useState("全部");
  const [selectedId, setSelectedId] = useState(baseKnowledge[1].id);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [feedback, setFeedback] = useState<Feedback>(() =>
    readJsonStorage("xxh-feedback", defaultFeedback),
  );
  const [customKnowledge, setCustomKnowledge] = useState<KnowledgeItem[]>(() =>
    readJsonStorage("xxh-custom-knowledge", []),
  );
  const [draftTitle, setDraftTitle] = useState("");
  const [draftAnswer, setDraftAnswer] = useState("");

  const knowledge = useMemo(() => [...customKnowledge, ...baseKnowledge], [customKnowledge]);
  const selectedItem = knowledge.find((item) => item.id === selectedId) ?? knowledge[0];

  const filteredKnowledge = useMemo(() => {
    return knowledge.filter((item) => activeCategory === "全部" || item.category === activeCategory);
  }, [activeCategory, knowledge]);

  const topMatch = useMemo(() => matchKnowledge(question, knowledge), [question, knowledge]);

  function ask(nextQuestion?: string) {
    const currentQuestion = (nextQuestion ?? question).trim();
    if (!currentQuestion) return;

    const match = matchKnowledge(currentQuestion, knowledge);
    const answer = buildAnswer(currentQuestion, match.best, match.confidence);

    setSelectedId(match.best.id);
    setQuestion(currentQuestion);
    setMessages((current) => [
      {
        id: Date.now(),
        question: currentQuestion,
        answer,
        matchedTitle: match.best.title,
        confidence: match.confidence,
        source: match.best.source,
      },
      ...current,
    ].slice(0, 5));
  }

  function submitQuestion(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    ask();
  }

  function recordFeedback(type: keyof Feedback) {
    const next = { ...feedback, [type]: feedback[type] + 1 };
    setFeedback(next);
    window.localStorage.setItem("xxh-feedback", JSON.stringify(next));
  }

  function addKnowledge(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!draftTitle.trim() || !draftAnswer.trim()) return;

    const nextItem: KnowledgeItem = {
      id: `custom-${Date.now()}`,
      title: draftTitle.trim(),
      category: "临时知识",
      audience: "内部维护",
      summary: draftAnswer.trim().slice(0, 42),
      answer: draftAnswer.trim(),
      steps: ["由维护人员审核后发布到正式知识库。"],
      source: "本地维护草稿",
      owner: "知识库管理员",
      updated: "2026-09-01",
      tags: draftTitle.split(/\s+/).filter(Boolean),
    };

    const next = [nextItem, ...customKnowledge].slice(0, 6);
    setCustomKnowledge(next);
    window.localStorage.setItem("xxh-custom-knowledge", JSON.stringify(next));
    setDraftTitle("");
    setDraftAnswer("");
    setSelectedId(nextItem.id);
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">信息化处服务问答工具</p>
          <h1>校内信息服务智能问答台</h1>
        </div>
        <div className="topbar-stats" aria-label="服务统计">
          <span><strong>{knowledge.length}</strong> 条知识</span>
          <span><strong>{messages.length}</strong> 次会话</span>
          <span><strong>本地</strong> 可运行</span>
        </div>
      </header>

      <section className="workspace">
        <aside className="knowledge-panel" aria-label="知识库">
          <div className="panel-heading">
            <span>知识库</span>
            <small>来源可追溯</small>
          </div>

          <div className="category-tabs" aria-label="问题分类">
            {categories.map((category) => (
              <button
                className={category === activeCategory ? "active" : ""}
                key={category}
                onClick={() => setActiveCategory(category)}
                type="button"
              >
                {category}
              </button>
            ))}
          </div>

          <div className="article-list">
            {filteredKnowledge.map((item) => (
              <button
                className={`article-card ${selectedItem.id === item.id ? "selected" : ""}`}
                key={item.id}
                onClick={() => setSelectedId(item.id)}
                type="button"
              >
                <span>{item.category}</span>
                <strong>{item.title}</strong>
                <small>{item.summary}</small>
              </button>
            ))}
          </div>
        </aside>

        <section className="assistant-panel" aria-label="问答区域">
          <div className="ask-strip">
            <div>
              <p className="eyebrow">在线咨询</p>
              <h2>输入一个信息化问题</h2>
            </div>
            <div className="confidence">
              <span>{topMatch.confidence}%</span>
              <small>预计匹配</small>
            </div>
          </div>

          <form className="question-box" onSubmit={submitQuestion}>
            <input
              aria-label="输入问题"
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="例如：校外怎么访问校内资源？"
              value={question}
            />
            <button type="submit">提问</button>
          </form>

          <div className="quick-grid" aria-label="常见问题">
            {quickQuestions.map((item) => (
              <button key={item} onClick={() => ask(item)} type="button">
                {item}
              </button>
            ))}
          </div>

          <div className="answer-card">
            <div className="answer-meta">
              <span>{topMatch.best.category}</span>
              <span>匹配：{topMatch.best.title}</span>
            </div>
            <p>{buildAnswer(question, topMatch.best, topMatch.confidence)}</p>
            <ol>
              {topMatch.best.steps.map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ol>
            <div className="source-row">
              <span>来源：{topMatch.best.source}</span>
              <span>更新：{topMatch.best.updated}</span>
              <span>责任岗：{topMatch.best.owner}</span>
            </div>
            <div className="feedback-row">
              <button onClick={() => recordFeedback("helpful")} type="button">
                有帮助 {feedback.helpful}
              </button>
              <button onClick={() => recordFeedback("followUp")} type="button">
                需人工跟进 {feedback.followUp}
              </button>
            </div>
          </div>

          <div className="history-block">
            <div className="panel-heading">
              <span>最近会话</span>
              <small>保留 5 条</small>
            </div>
            {messages.length === 0 ? (
              <p className="empty-state">提交一次问题后，会话记录会显示在这里。</p>
            ) : (
              messages.map((message) => (
                <article key={message.id} className="history-item">
                  <strong>{message.question}</strong>
                  <p>{message.answer}</p>
                  <small>
                    {message.matchedTitle} · {message.confidence}% · {message.source}
                  </small>
                </article>
              ))
            )}
          </div>
        </section>

        <aside className="detail-panel" aria-label="服务详情">
          <div className="service-card">
            <span>{selectedItem.audience}</span>
            <h2>{selectedItem.title}</h2>
            <p>{selectedItem.summary}</p>
            <div className="tag-row">
              {selectedItem.tags.slice(0, 5).map((tag) => (
                <small key={tag}>{tag}</small>
              ))}
            </div>
          </div>

          <div className="service-links">
            <div className="panel-heading">
              <span>服务入口</span>
              <small>演示数据</small>
            </div>
            <a href="https://software.nuaa.edu.cn" rel="noreferrer" target="_blank">
              正版软件平台
            </a>
            <a href="https://software.nuaa.edu.cn" rel="noreferrer" target="_blank">
              工单与材料提交
            </a>
            <a href="https://software.nuaa.edu.cn" rel="noreferrer" target="_blank">
              信息化服务公告
            </a>
          </div>

          <form className="maintenance" onSubmit={addKnowledge}>
            <div className="panel-heading">
              <span>知识维护</span>
              <small>本机保存</small>
            </div>
            <input
              aria-label="知识标题"
              onChange={(event) => setDraftTitle(event.target.value)}
              placeholder="新增问题标题"
              value={draftTitle}
            />
            <textarea
              aria-label="知识答案"
              onChange={(event) => setDraftAnswer(event.target.value)}
              placeholder="新增标准答案"
              value={draftAnswer}
            />
            <button type="submit">保存草稿</button>
          </form>
        </aside>
      </section>
    </main>
  );
}
