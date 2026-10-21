from __future__ import annotations

import json
from collections import Counter
from datetime import date, datetime
from hashlib import sha1, sha256
from html import escape

import streamlit as st

from database import (
    DEFAULT_DB_PATH,
    add_knowledge_item,
    bootstrap_database,
    feedback_summary,
    list_knowledge_items,
    publish_knowledge_item,
    record_feedback,
)
from info_service_assistant import (
    QUICK_QUESTIONS,
    KnowledgeItem,
    build_answer,
    categories,
    confidence_for_score,
    match_knowledge,
    rank_knowledge,
)
from maintenance_auth import admin_password, password_matches


st.set_page_config(
    page_title="校内信息服务智能问答台",
    page_icon="IT",
    layout="wide",
)


st.markdown(
    """
    <style>
    :root {
        --page: #191919;
        --header: #303030;
        --surface: #232323;
        --surface-2: #2b2b2b;
        --surface-3: #353535;
        --line: #3d3d3d;
        --line-soft: #323232;
        --text: #e7e7e7;
        --muted: #a7aaad;
        --blue: #2d91cf;
        --blue-soft: #203f52;
        --green: #58b996;
        --amber: #d8ad62;
    }
    html, body {
        font-family: "PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", Arial, sans-serif;
        letter-spacing: 0;
    }
    .stApp {
        background: var(--page);
        color: var(--text);
    }
    header[data-testid="stHeader"] { display: none; }
    .block-container {
        padding: .8rem 2rem 2.5rem;
        max-width: 1520px;
    }
    .st-key-portal_header {
        box-sizing: border-box;
        width: 100%;
        background: var(--header);
        border: 1px solid #3b3b3b;
        border-bottom-color: #454545;
        padding: .85rem 1rem .65rem;
        margin-bottom: 0;
    }
    .brand-lockup { min-height: 3.05rem; display: flex; flex-direction: column; justify-content: center; }
    .brand-name {
        color: #f4f4f4;
        font-size: 1.46rem;
        line-height: 1;
        font-weight: 800;
        letter-spacing: 0;
    }
    .brand-name span { color: var(--blue); }
    .brand-sub {
        color: var(--muted);
        margin-top: .42rem;
        font-size: .76rem;
    }
    .st-key-portal_nav {
        box-sizing: border-box;
        width: 100%;
        background: #252525;
        border: 1px solid var(--line);
        border-top: 0;
        margin: 0 0 1.45rem;
        padding: 0;
    }
    .st-key-portal_nav [data-testid="stHorizontalBlock"] {
        gap: 0 !important;
    }
    .st-key-portal_nav [data-testid="stColumn"] {
        border-right: 1px solid #3a3a3a;
    }
    .st-key-portal_nav [data-testid="stColumn"]:last-child {
        border-right: 0;
    }
    .st-key-portal_nav [data-testid="stPageLink"] {
        margin: 0;
    }
    .st-key-portal_nav a {
        color: #b9babc;
        text-decoration: none;
        text-align: center;
        justify-content: center;
        width: 100%;
        min-height: 3.35rem;
        padding: .85rem .65rem;
        font-size: .9rem;
        border-radius: 0;
        transition: color .15s ease, background .15s ease;
    }
    .st-key-portal_nav a:hover,
    .st-key-portal_nav a[aria-current="page"] {
        color: #ffffff;
        background: #2c2c2c;
    }
    .st-key-portal_nav a[aria-current="page"] {
        box-shadow: inset 0 -2px 0 var(--blue);
    }
    .st-key-portal_nav a * { color: inherit !important; }
    .st-key-portal_nav a p { font-size: .86rem; }
    .st-key-portal_nav button:disabled { opacity: .45; }
    .page-title {
        text-align: center;
        border-bottom: 1px solid var(--line-soft);
        padding: .15rem 1rem 1.1rem;
        margin-bottom: 1rem;
    }
    .page-title h1 {
        color: #dedede;
        font-size: 1.72rem;
        font-weight: 600;
        line-height: 1.45;
        margin: 0;
        letter-spacing: 0;
    }
    .page-title h1 > span:first-child { color: #dedede; }
    .page-title h1 > span:first-child > span { color: var(--blue); }
    .page-title p { color: #85898c; font-size: .84rem; margin: .45rem 0 0; }
    .section-heading {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        border-bottom: 1px solid var(--line);
        padding: .4rem 0 .7rem;
        margin: 1.55rem 0 1rem;
    }
    .section-heading h2 {
        color: #eeeeee;
        font-size: 1.05rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: 0;
    }
    .section-heading span { color: #777b7e; font-size: .78rem; }
    .service-dossier {
        background: #202020;
        border: 1px solid var(--line);
        min-height: 100%;
    }
    .panel-head {
        color: #e7e7e7;
        background: #303030;
        border-bottom: 1px solid var(--line);
        padding: .7rem .85rem;
        font-size: .88rem;
        font-weight: 700;
    }
    .dossier-row {
        display: grid;
        grid-template-columns: 4.6rem minmax(0, 1fr);
        gap: .65rem;
        padding: .68rem .85rem;
        border-bottom: 1px dotted #3b3b3b;
        font-size: .84rem;
        line-height: 1.55;
    }
    .dossier-row:last-child { border-bottom: 0; }
    .dossier-row .label { color: #85898c; }
    .dossier-row .value { color: #d4d4d4; overflow-wrap: anywhere; }
    .confidence-value { color: var(--green); font-weight: 700; }
    .answer-box {
        border: 1px solid var(--line);
        background: #101010;
        padding: 1.25rem 1.35rem 1.35rem;
        min-height: 13.8rem;
    }
    .answer-kicker {
        color: var(--blue);
        font-size: .76rem;
        font-weight: 700;
        margin-bottom: .5rem;
    }
    .answer-box h2 {
        color: #f0f0f0;
        font-size: 1.12rem;
        margin: 0 0 .75rem;
        letter-spacing: 0;
    }
    .answer-box p {
        color: #d7d7d7;
        line-height: 1.85;
        margin: 0;
        white-space: normal;
    }
    .step-list {
        background: #252525;
        border: 1px solid var(--line);
        border-top: 0;
        padding: .15rem .95rem;
    }
    .step-row {
        display: grid;
        grid-template-columns: 2rem minmax(0, 1fr);
        gap: .45rem;
        color: #c6c6c6;
        border-bottom: 1px dotted #404040;
        padding: .68rem 0;
        font-size: .86rem;
        line-height: 1.6;
    }
    .step-row:last-child { border-bottom: 0; }
    .step-number { color: var(--blue); font-weight: 700; }
    .directory-preview {
        background: #202020;
        border: 1px solid var(--line);
        border-left: 3px solid var(--blue);
        padding: 1rem 1.15rem;
        min-height: 8.5rem;
    }
    .directory-preview h3 { color: #ececec; font-size: 1rem; margin: 0 0 .5rem; }
    .directory-preview p { color: #aaaeb0; line-height: 1.7; margin: 0 0 .6rem; }
    .meta-line, .directory-meta {
        color: var(--muted);
        font-size: .78rem;
        line-height: 1.8;
    }
    .source-pill {
        display: inline-block;
        border: 1px solid #454545;
        background: #323232;
        padding: .16rem .42rem;
        margin: .15rem .25rem .15rem 0;
        color: #bfc1c2;
        font-size: .76rem;
        border-radius: 2px;
    }
    .coverage-item {
        display: flex;
        align-items: center;
        justify-content: space-between;
        min-height: 3.2rem;
        margin-bottom: .5rem;
        padding: .65rem .8rem;
        background: #252525;
        border: 1px solid var(--line);
        border-left: 2px solid #4b4b4b;
        color: #c7c9ca;
        font-size: .86rem;
    }
    .coverage-item strong { color: var(--blue); font-size: 1rem; }
    .recent-query {
        padding: .75rem .9rem;
        background: #232323;
        border-left: 3px solid var(--blue);
        color: #d7d7d7;
        line-height: 1.55;
    }
    .st-key-results_candidates {
        background: #202020;
        border: 1px solid var(--line);
        margin-bottom: .6rem;
    }
    .st-key-results_candidates > div { padding: 0; }
    .st-key-results_candidates div[data-testid="stRadio"] { padding: .45rem .8rem .7rem; }
    .st-key-results_candidates div[data-testid="stRadio"] label {
        align-items: flex-start;
        padding: .38rem 0;
    }
    .st-key-results_candidates div[data-testid="stRadio"] label p {
        color: #c8cacc !important;
        line-height: 1.5;
        overflow-wrap: anywhere;
    }
    div[data-testid="stMetric"] {
        border: 1px solid var(--line);
        background: #252525;
        padding: .58rem .78rem;
        border-radius: 2px;
        min-height: 74px;
    }
    div[data-testid="stMetric"] label { color: #85898c; font-size: .74rem; }
    div[data-testid="stMetricValue"] { color: #d9d9d9; font-size: 1.35rem; }
    .stButton > button, .stFormSubmitButton > button,
    .stDownloadButton > button, .stLinkButton > a {
        border-radius: 2px;
        border: 1px solid #4b4b4b;
        color: #d2d2d2;
        background: #333333;
        min-height: 2.45rem;
        font-weight: 500;
    }
    .stButton > button:hover, .stFormSubmitButton > button:hover,
    .stDownloadButton > button:hover, .stLinkButton > a:hover {
        border-color: #646464;
        color: #ffffff;
        background: #3c3c3c;
    }
    button[kind="primary"], .stFormSubmitButton button[kind="primary"] {
        background: var(--blue);
        border-color: var(--blue);
        color: #ffffff;
    }
    button[kind="primary"]:hover, .stFormSubmitButton button[kind="primary"]:hover {
        background: #3da3df;
        border-color: #3da3df;
        color: #ffffff;
    }
    div[data-testid="stTextInputRootElement"],
    div[data-testid="stTextAreaRootElement"],
    div[data-baseweb="select"] > div, textarea {
        border-radius: 2px !important;
        border-color: #484848 !important;
        background: #303030 !important;
        color: #ededed !important;
    }
    div[data-testid="stTextInputRootElement"]:focus-within,
    div[data-testid="stTextAreaRootElement"]:focus-within {
        border-color: var(--blue) !important;
        box-shadow: 0 0 0 1px var(--blue) !important;
    }
    [data-testid="stIconMaterial"] {
        font-family: "Material Symbols Rounded" !important;
    }
    input, textarea { color: #ededed !important; caret-color: var(--blue); }
    input::placeholder, textarea::placeholder { color: #85898c !important; }
    label, .stCaption, div[data-testid="stCaptionContainer"] { color: #9da0a2 !important; }
    div[data-testid="stExpander"] {
        background: #252525;
        border: 1px solid var(--line);
        border-radius: 2px;
    }
    div[data-testid="stExpander"] summary:hover { color: #ffffff; }
    div[data-testid="stRadio"] label { color: #c6c6c6 !important; padding: .12rem 0; }
    div[data-testid="stRadio"] label p { color: #c6c6c6 !important; }
    hr { border-color: var(--line) !important; }
    h1, h2, h3, p { letter-spacing: 0; }
    @media (max-width: 800px) {
        .block-container { padding: .55rem .8rem 2rem; }
        .st-key-portal_header { padding: .75rem; }
        .st-key-portal_header [data-testid="stHorizontalBlock"] { gap: .65rem !important; }
        .st-key-portal_nav { overflow-x: auto; }
        .st-key-portal_nav [data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            gap: 0 !important;
            min-width: max-content;
        }
        .st-key-portal_nav [data-testid="stColumn"] {
            flex: 0 0 8rem !important;
            width: 8rem !important;
            min-width: 8rem !important;
        }
        .st-key-portal_nav a { min-width: 8rem; padding: .8rem .6rem; }
        .st-key-metrics_grid > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] {
            display: grid !important;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: .7rem !important;
        }
        .st-key-metrics_grid > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
            flex: none !important;
            width: auto !important;
            min-width: 0 !important;
        }
        .st-key-results_layout > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: column !important;
            gap: .75rem !important;
        }
        .st-key-results_layout > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
            width: 100% !important;
            min-width: 0 !important;
        }
        .st-key-results_layout > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child {
            order: 2;
        }
        .st-key-results_layout > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child {
            order: 1;
        }
        .page-title h1 { font-size: 1.3rem; }
        .dossier-row { grid-template-columns: 4rem minmax(0, 1fr); }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

DB_PATH = DEFAULT_DB_PATH


def bootstrap_state() -> None:
    st.session_state.setdefault("chat_history", [])
    st.session_state.setdefault("question", "")
    st.session_state.setdefault("search_input", st.session_state.question)
    st.session_state.setdefault("selected_candidate_id", "")
    st.session_state.setdefault("pending_search_input", "")
    if st.session_state.pending_search_input:
        st.session_state.search_input = st.session_state.pending_search_input
        st.session_state.pending_search_input = ""


def all_knowledge(*, include_drafts: bool = False) -> list[KnowledgeItem]:
    return list_knowledge_items(get_db(), include_drafts=include_drafts)


def get_db():
    if "_database" not in st.session_state:
        st.session_state._database = bootstrap_database(DB_PATH)
    return st.session_state._database


def add_chat(question: str, item: KnowledgeItem, confidence: int) -> None:
    answer = build_answer(question, item, confidence)
    st.session_state.chat_history.insert(
        0,
        {
            "question": question,
            "answer": answer,
            "matched_title": item.title,
            "confidence": confidence,
            "source": item.source,
        },
    )
    st.session_state.chat_history = st.session_state.chat_history[:5]


def ask_question(question: str) -> tuple[KnowledgeItem, int, list[KnowledgeItem]]:
    item, confidence, related = match_knowledge(question, all_knowledge())
    st.session_state.selected_candidate_id = item.id
    if related:
        add_chat(question, item, confidence)
    return item, confidence, related


def export_knowledge_json() -> str:
    connection = get_db()
    drafts = {
        row["id"]
        for row in connection.execute("SELECT id FROM knowledge_items WHERE is_published = 0")
    }
    payload = [
        {**item.to_dict(), "is_published": item.id not in drafts}
        for item in all_knowledge(include_drafts=True)
    ]
    return json.dumps(payload, ensure_ascii=False, indent=2)


def render_page_title(title: str, accent: str, subtitle: str = "") -> None:
    subtitle_html = f"<p>{escape(subtitle)}</p>" if subtitle else ""
    st.markdown(
        f"""
        <div class="page-title">
          <h1>{escape(title)} <span>| {escape(accent)}</span></h1>
          {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_heading(title: str, detail: str) -> None:
    st.markdown(
        f"""
        <div class="section-heading">
          <h2>{escape(title)}</h2><span>{escape(detail)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def prepare_result(question: str, *, record_history: bool = True) -> None:
    cleaned = question.strip()
    if not cleaned:
        st.warning("请先输入信息化服务问题。")
        return
    st.session_state.question = cleaned
    st.session_state.pending_search_input = cleaned
    if record_history:
        ask_question(cleaned)
    else:
        item, _, _ = match_knowledge(cleaned, all_knowledge())
        st.session_state.selected_candidate_id = item.id
    st.switch_page(RESULTS_PAGE)


def render_portal_header() -> None:
    with st.container(key="portal_header"):
        brand_column, search_column = st.columns(
            [1.15, 4.85], gap="large", vertical_alignment="center"
        )
        with brand_column:
            st.markdown(
                """
                <div class="brand-lockup">
                  <div class="brand-name">NUAA <span>InfoDesk</span></div>
                  <div class="brand-sub">信息化处知识服务门户</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with search_column:
            with st.form("global_question_form", clear_on_submit=False, border=False):
                search_input, search_action = st.columns(
                    [7.4, 1], gap="small", vertical_alignment="bottom"
                )
                user_question = search_input.text_input(
                    "请输入信息化服务问题",
                    key="search_input",
                    placeholder="搜索校园网、统一身份认证、VPN、邮箱、办事大厅等服务",
                    label_visibility="collapsed",
                )
                submitted = search_action.form_submit_button(
                    "搜索",
                    type="primary",
                    icon=":material/search:",
                    use_container_width=True,
                )
        if submitted:
            prepare_result(user_question)


def render_portal_navigation() -> None:
    navigation = (
        (HOME_PAGE, "智能问答", ":material/home:", False),
        (RESULTS_PAGE, "匹配结果", ":material/search_check:", not st.session_state.question),
        (DIRECTORY_PAGE, "知识目录", ":material/menu_book:", False),
        (SERVICES_PAGE, "常用服务", ":material/apps:", False),
        (HISTORY_PAGE, "最近会话", ":material/history:", False),
        (MAINTENANCE_PAGE, "知识维护", ":material/database:", False),
    )
    with st.container(key="portal_nav"):
        columns = st.columns(len(navigation), gap="small")
        for column, (page, label, icon, disabled) in zip(columns, navigation):
            column.page_link(
                page,
                label=label,
                icon=icon,
                disabled=disabled,
                use_container_width=True,
            )


def render_metrics(
    knowledge_items: list[KnowledgeItem],
    *,
    match_confidence: int | None = None,
) -> None:
    feedback = feedback_summary(get_db())
    with st.container(key="metrics_grid"):
        metric_1, metric_2, metric_3, metric_4 = st.columns(4)
        if match_confidence is None:
            metric_1.metric("知识状态", "正常")
        else:
            metric_1.metric("匹配度", f"{match_confidence}%")
        metric_2.metric("知识条目", len(knowledge_items))
        metric_3.metric("服务分类", len(categories(knowledge_items)) - 1)
        metric_4.metric("反馈总数", feedback["helpful"] + feedback["manual"])


def render_home_page() -> None:
    knowledge_items = all_knowledge()
    render_page_title(
        "信息化服务智能问答",
        "服务总览",
        "NUAA InfoDesk 校内知识库",
    )
    render_metrics(knowledge_items)

    category_counts = Counter(item.category for item in knowledge_items)
    render_section_heading("知识覆盖", f"{len(category_counts)} 个服务分类")
    category_columns = st.columns(3, gap="small")
    for index, (category, count) in enumerate(
        sorted(category_counts.items(), key=lambda entry: (-entry[1], entry[0]))
    ):
        category_columns[index % 3].markdown(
            f"""
            <div class="coverage-item">
              <span>{escape(category)}</span><strong>{count}</strong>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if st.session_state.question:
        render_section_heading("最近查询", "最近一次搜索")
        recent_label, recent_action = st.columns([4.8, 1.2], vertical_alignment="center")
        recent_label.markdown(
            f"<div class='recent-query'>{escape(st.session_state.question)}</div>",
            unsafe_allow_html=True,
        )
        recent_action.page_link(
            RESULTS_PAGE,
            label="查看答复",
            icon=":material/arrow_forward:",
            use_container_width=True,
        )


def result_candidates(question: str) -> tuple[dict[str, tuple[KnowledgeItem, int]], str]:
    ranked = rank_knowledge(question, all_knowledge(), limit=10)
    candidate_by_id = {item.id: (item, score) for item, score in ranked}
    candidate_id = st.session_state.selected_candidate_id
    if candidate_id not in candidate_by_id:
        candidate_id = next(iter(candidate_by_id), "")
        st.session_state.selected_candidate_id = candidate_id
    return candidate_by_id, candidate_id


def candidate_label(item: KnowledgeItem, score: int) -> str:
    title = item.title.replace("https://", "https：//").replace("http://", "http：//")
    return f"{title} · {item.category} · {confidence_for_score(score)}%"


def render_answer_panel(item: KnowledgeItem, question: str, confidence: int) -> None:
    answer = build_answer(question, item, confidence)
    safe_title = escape(item.title)
    safe_answer = escape(answer).replace("\n", "<br>")
    st.markdown(
        f"""
        <div class="answer-box">
          <div class="answer-kicker">STANDARD RESPONSE / 标准答复</div>
          <h2>{safe_title}</h2>
          <p>{safe_answer}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    step_rows = "".join(
        f"<div class='step-row'><span class='step-number'>{index:02d}</span>"
        f"<span>{escape(step)}</span></div>"
        for index, step in enumerate(item.steps, start=1)
    )
    st.markdown(
        f"<div class='step-list'><div class='panel-head'>办理步骤</div>{step_rows}</div>",
        unsafe_allow_html=True,
    )


def render_service_dossier(item: KnowledgeItem, confidence: int) -> None:
    st.markdown(
        f"""
        <div class="service-dossier">
          <div class="panel-head">服务档案</div>
          <div class="dossier-row"><span class="label">分类</span><span class="value">{escape(item.category)}</span></div>
          <div class="dossier-row"><span class="label">适用对象</span><span class="value">{escape(item.audience)}</span></div>
          <div class="dossier-row"><span class="label">责任岗位</span><span class="value">{escape(item.owner)}</span></div>
          <div class="dossier-row"><span class="label">知识来源</span><span class="value">{escape(item.source)}</span></div>
          <div class="dossier-row"><span class="label">更新时间</span><span class="value">{escape(item.updated)}</span></div>
          <div class="dossier-row"><span class="label">匹配度</span><span class="value confidence-value">{confidence}%</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_feedback_actions(item: KnowledgeItem, question: str) -> None:
    source_action, helpful_action, manual_action, action_spacer = st.columns(
        [1.15, 1, 1.15, 3.4], gap="small"
    )
    if item.link:
        source_action.link_button(
            "查看来源",
            item.link,
            icon=":material/open_in_new:",
            use_container_width=True,
        )
    else:
        source_action.button("暂无来源链接", disabled=True, use_container_width=True)
    if helpful_action.button(
        "有帮助", icon=":material/thumb_up:", use_container_width=True
    ):
        record_feedback(get_db(), "helpful", question=question, knowledge_item_id=item.id)
        st.toast("已记录：有帮助")
        st.rerun()
    if manual_action.button(
        "需人工跟进", icon=":material/support_agent:", use_container_width=True
    ):
        record_feedback(get_db(), "manual", question=question, knowledge_item_id=item.id)
        st.toast("已记录：需人工跟进")
        st.rerun()


def render_results_page() -> None:
    question = st.session_state.question.strip()
    if not question:
        render_page_title("匹配结果", "暂无查询", "等待新的信息化服务问题")
        st.info("当前没有可展示的搜索结果。")
        st.page_link(
            HOME_PAGE,
            label="返回智能问答",
            icon=":material/arrow_back:",
        )
        return

    knowledge_items = all_knowledge()
    candidate_by_id, candidate_id = result_candidates(question)
    if not candidate_by_id:
        render_page_title(question, "未找到相关知识")
        st.info("暂无相关知识，请补充服务名称、设备类型或具体报错。")
        st.page_link(DIRECTORY_PAGE, label="浏览知识目录", icon=":material/menu_book:")
        return
    widget_key = f"result_candidate_{sha1(question.encode('utf-8')).hexdigest()[:12]}"
    if (
        widget_key not in st.session_state
        or st.session_state[widget_key] not in candidate_by_id
    ):
        st.session_state[widget_key] = candidate_id
    candidate_id = st.session_state[widget_key]
    st.session_state.selected_candidate_id = candidate_id
    preview_item, preview_score = candidate_by_id[candidate_id]
    preview_confidence = confidence_for_score(preview_score)

    render_page_title(question, "匹配结果", f"当前匹配：{preview_item.title}")
    render_metrics(knowledge_items, match_confidence=preview_confidence)

    with st.container(key="results_layout"):
        candidate_column, answer_column = st.columns([1.02, 2.35], gap="small")
        with candidate_column:
            with st.container(key="results_candidates"):
                st.markdown(
                    f"<div class='panel-head'>候选知识 · {len(candidate_by_id)} 条</div>",
                    unsafe_allow_html=True,
                )
                selected_id = st.radio(
                    "匹配条目",
                    list(candidate_by_id),
                    key=widget_key,
                    format_func=lambda item_id: candidate_label(*candidate_by_id[item_id]),
                    label_visibility="collapsed",
                )
                st.session_state.selected_candidate_id = selected_id

        with answer_column:
            selected_item, selected_score = candidate_by_id[selected_id]
            selected_confidence = confidence_for_score(selected_score)
            render_answer_panel(selected_item, question, selected_confidence)
            render_service_dossier(selected_item, selected_confidence)
            render_feedback_actions(selected_item, question)


def render_directory_page() -> None:
    knowledge_items = all_knowledge()
    render_page_title(
        "知识目录",
        "分类浏览",
        f"当前收录 {len(knowledge_items)} 条知识",
    )

    filter_column, search_column = st.columns([1, 2.3], gap="small")
    category = filter_column.selectbox("服务分类", categories(knowledge_items), index=0)
    directory_query = search_column.text_input(
        "目录内检索",
        placeholder="按问题、关键词或服务名称筛选",
        icon=":material/filter_alt:",
    )
    filtered = [
        item
        for item in knowledge_items
        if category == "全部" or item.category == category
    ]
    if directory_query.strip():
        filtered = [
            item
            for item, score in rank_knowledge(directory_query, filtered)
            if score > 0
        ]

    render_section_heading("目录结果", f"{len(filtered)} 条")
    if not filtered:
        st.info("当前筛选条件下没有知识条目。")
        return

    directory_filter, directory_content = st.columns([1.02, 2.35], gap="small")
    with directory_filter:
        selected_id = st.selectbox(
            "知识条目",
            [item.id for item in filtered],
            index=0,
            format_func=lambda item_id: next(
                item.title for item in filtered if item.id == item_id
            ),
        )
        selected_item = next(item for item in filtered if item.id == selected_id)
        st.caption(f"{selected_item.category} · {selected_item.updated}")
    with directory_content:
        selected_pills = " ".join(
            f"<span class='source-pill'>{escape(tag)}</span>"
            for tag in selected_item.tags[:7]
        )
        st.markdown(
            f"""
            <div class="directory-preview">
              <h3>{escape(selected_item.title)}</h3>
              <p>{escape(selected_item.answer).replace(chr(10), '<br>')}</p>
              <div>{selected_pills}</div>
              <div class="directory-meta">来源：{escape(selected_item.source)} · 责任岗：{escape(selected_item.owner)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if selected_item.link:
            st.link_button(
                "查看来源",
                selected_item.link,
                icon=":material/open_in_new:",
            )


def render_services_page() -> None:
    render_page_title("常用服务", "高频入口", f"{len(QUICK_QUESTIONS)} 项常用问题")
    render_section_heading("服务列表", "点击后打开独立匹配结果页")
    service_columns = st.columns(2, gap="small")
    for index, question in enumerate(QUICK_QUESTIONS):
        if service_columns[index % 2].button(
            question,
            key=f"service_question_{index}",
            icon=":material/arrow_forward:",
            use_container_width=True,
        ):
            prepare_result(question)


def render_history_page() -> None:
    history = st.session_state.chat_history
    render_page_title("最近会话", "查询记录", f"当前保留 {len(history)} 条")
    if not history:
        st.info("当前会话还没有搜索记录。")
        return
    for index, message in enumerate(history):
        with st.expander(message["question"], expanded=index == 0):
            st.write(message["answer"])
            st.caption(
                f"{message['matched_title']} · {message['confidence']}% · {message['source']}"
            )
            if st.button(
                "重新查看",
                key=f"reopen_history_{index}",
                icon=":material/open_in_new:",
            ):
                prepare_result(message["question"], record_history=False)


def maintenance_access_allowed() -> bool:
    try:
        password = admin_password()
    except RuntimeError:
        st.error("管理员登录配置异常，请联系服务器管理员。")
        return False
    if password is None:
        return True

    password_version = sha256(password.encode("utf-8")).hexdigest()
    if st.session_state.get("_admin_password_version") == password_version:
        if st.button("退出管理", icon=":material/logout:"):
            del st.session_state._admin_password_version
            st.rerun()
        return True

    render_page_title("知识维护", "管理员登录")
    with st.form("admin_login"):
        candidate = st.text_input("管理员密码", type="password")
        submitted = st.form_submit_button("登录", icon=":material/login:", type="primary")
    if submitted:
        if password_matches(candidate, password):
            st.session_state._admin_password_version = password_version
            st.rerun()
        st.error("密码不正确。")
    return False


def render_maintenance_page() -> None:
    if not maintenance_access_allowed():
        return
    knowledge_items = all_knowledge(include_drafts=True)
    draft_ids = {
        row["id"]
        for row in get_db().execute("SELECT id FROM knowledge_items WHERE is_published = 0")
    }
    drafts = [item for item in knowledge_items if item.id in draft_ids]
    render_page_title(
        "知识维护",
        "本地管理",
        "新增草稿与导出 SQLite 知识数据",
    )
    metric_1, metric_2, metric_3 = st.columns(3)
    metric_1.metric("全部知识", len(knowledge_items))
    metric_2.metric("本地草稿", len(drafts))
    metric_3.metric("数据格式", "SQLite")

    render_section_heading("新增知识草稿", "写入本地数据库")
    with st.form("knowledge_form", clear_on_submit=True):
        title_column, category_column, tag_column = st.columns(
            [1.5, 1, 1.5], gap="small"
        )
        title = title_column.text_input("新增问题标题")
        category_input = category_column.text_input("分类", value="临时知识")
        tags_input = tag_column.text_input("关键词，用逗号分隔")
        answer_input = st.text_area("标准答案", height=160)
        save_item = st.form_submit_button(
            "保存草稿",
            type="primary",
            icon=":material/save:",
            use_container_width=True,
        )

    if save_item and (not title.strip() or not answer_input.strip()):
        st.error("请填写问题标题和标准答案。")
    elif save_item:
        tags = tuple(
            tag.strip()
            for tag in tags_input.replace("，", ",").split(",")
            if tag.strip()
        )
        new_item = KnowledgeItem(
            id=f"custom-{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            title=title.strip(),
            category=category_input.strip() or "临时知识",
            audience="内部维护",
            summary=answer_input.strip()[:48],
            answer=answer_input.strip(),
            steps=("由维护人员审核后发布到正式知识库。",),
            source="本地维护草稿",
            owner="知识库管理员",
            updated=date.today().isoformat(),
            tags=tags or (title.strip(),),
        )
        add_knowledge_item(get_db(), new_item)
        st.success("草稿已保存到 SQLite 数据库。")
        st.rerun()

    if drafts:
        render_section_heading("待审核知识", f"{len(drafts)} 条")
        draft = st.selectbox(
            "选择草稿", drafts, format_func=lambda item: item.title, key="review_draft"
        )
        st.write(draft.answer)
        if st.button("审核并发布", icon=":material/publish:"):
            publish_knowledge_item(get_db(), draft.id)
            st.rerun()

    render_section_heading("数据导出", "JSON 交换格式")
    export_column, export_spacer = st.columns([1.2, 4.8])
    export_column.download_button(
        "导出知识库 JSON",
        data=export_knowledge_json(),
        file_name="information_service_knowledge.json",
        mime="application/json",
        icon=":material/download:",
        use_container_width=True,
    )


bootstrap_state()
HOME_PAGE = st.Page(
    render_home_page,
    title="智能问答",
    icon=":material/home:",
    url_path="",
    default=True,
)
RESULTS_PAGE = st.Page(
    render_results_page,
    title="匹配结果",
    icon=":material/search_check:",
    url_path="search-results",
    visibility="hidden",
)
DIRECTORY_PAGE = st.Page(
    render_directory_page,
    title="知识目录",
    icon=":material/menu_book:",
    url_path="knowledge-directory",
)
SERVICES_PAGE = st.Page(
    render_services_page,
    title="常用服务",
    icon=":material/apps:",
    url_path="common-services",
)
HISTORY_PAGE = st.Page(
    render_history_page,
    title="最近会话",
    icon=":material/history:",
    url_path="recent-history",
)
MAINTENANCE_PAGE = st.Page(
    render_maintenance_page,
    title="知识维护",
    icon=":material/database:",
    url_path="knowledge-maintenance",
)

current_page = st.navigation(
    [
        HOME_PAGE,
        RESULTS_PAGE,
        DIRECTORY_PAGE,
        SERVICES_PAGE,
        HISTORY_PAGE,
        MAINTENANCE_PAGE,
    ],
    position="hidden",
)
render_portal_header()
render_portal_navigation()
current_page.run()
