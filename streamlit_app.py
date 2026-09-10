from __future__ import annotations

import json
from datetime import date, datetime
from html import escape
from pathlib import Path

import streamlit as st

from database import (
    add_knowledge_item,
    bootstrap_database,
    feedback_summary,
    list_knowledge_items,
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
    .portal-nav {
        display: flex;
        align-items: center;
        justify-content: space-around;
        overflow-x: auto;
        background: #252525;
        border: 1px solid var(--line);
        border-top: 0;
        margin: 0 0 1.45rem;
        min-height: 3.35rem;
    }
    .portal-nav a {
        color: #b9babc;
        text-decoration: none;
        text-align: center;
        min-width: 8.3rem;
        padding: 1rem 1.2rem;
        border-right: 1px solid #3a3a3a;
        font-size: .9rem;
        transition: color .15s ease, background .15s ease;
    }
    .portal-nav a:last-child { border-right: 0; }
    .portal-nav a:hover, .portal-nav a.active {
        color: #ffffff;
        background: #2c2c2c;
    }
    .portal-nav a.active { box-shadow: inset 0 -2px 0 var(--blue); }
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
    hr { border-color: var(--line) !important; }
    h1, h2, h3, p { letter-spacing: 0; }
    [id$="-zone"] { scroll-margin-top: 1rem; }
    @media (max-width: 800px) {
        .block-container { padding: .55rem .8rem 2rem; }
        .st-key-portal_header { padding: .75rem; }
        .portal-nav { justify-content: flex-start; }
        .portal-nav a { min-width: 7.4rem; padding: .9rem .75rem; }
        .page-title h1 { font-size: 1.3rem; }
        .dossier-row { grid-template-columns: 4rem minmax(0, 1fr); }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

DB_PATH = Path("data/info_service.db")


def bootstrap_state() -> None:
    st.session_state.setdefault("chat_history", [])
    st.session_state.setdefault("question", "校园网连不上怎么办？")
    st.session_state.setdefault("pending_question", "")


def all_knowledge() -> list[KnowledgeItem]:
    return list_knowledge_items(get_db())


@st.cache_resource
def get_db():
    return bootstrap_database(DB_PATH)


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
    add_chat(question, item, confidence)
    return item, confidence, related


def choose_quick_question(question: str) -> None:
    st.session_state.question = question
    st.session_state.pending_question = question


def choose_match_candidate(widget_key: str) -> None:
    st.session_state.selected_candidate_id = st.session_state[widget_key]


def export_knowledge_json() -> str:
    payload = [item.to_dict() for item in all_knowledge()]
    return json.dumps(payload, ensure_ascii=False, indent=2)


bootstrap_state()
db = get_db()
knowledge_items = all_knowledge()
feedback = feedback_summary(db)

with st.container(key="portal_header"):
    brand_column, search_column = st.columns([1.15, 4.85], gap="large", vertical_alignment="center")
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
        with st.form("question_form", clear_on_submit=False, border=False):
            search_input, search_action = st.columns([7.4, 1], gap="small", vertical_alignment="bottom")
            user_question = search_input.text_input(
                "请输入信息化服务问题",
                key="question",
                placeholder="搜索校园网、统一身份认证、VPN、邮箱、办事大厅等服务",
                label_visibility="collapsed",
            )
            submitted = search_action.form_submit_button(
                "搜索",
                type="primary",
                icon=":material/search:",
                use_container_width=True,
            )

    if submitted and user_question.strip():
        ask_question(user_question.strip())
    elif st.session_state.pending_question:
        ask_question(st.session_state.pending_question)
        st.session_state.pending_question = ""

    ranked_candidates = rank_knowledge(
        st.session_state.question,
        all_knowledge(),
        limit=10,
    )
    candidate_by_id = {item.id: (item, score) for item, score in ranked_candidates}
    candidate_id = st.session_state.get("selected_candidate_id")
    if candidate_id not in candidate_by_id:
        candidate_id = next(iter(candidate_by_id))
        st.session_state.selected_candidate_id = candidate_id

    candidate_column, quick_column = st.columns([1.6, 1], gap="small")
    candidate_widget_key = f"candidate-choice-{st.session_state.question}"
    with candidate_column.expander(f"相关匹配结果（{len(ranked_candidates)} 条）", expanded=False):
        st.radio(
            "匹配条目",
            list(candidate_by_id),
            index=list(candidate_by_id).index(candidate_id),
            key=candidate_widget_key,
            format_func=lambda item_id: (
                f"{candidate_by_id[item_id][0].title}"
                f" · {candidate_by_id[item_id][0].category}"
                f" · {confidence_for_score(candidate_by_id[item_id][1])}%"
            ),
            on_change=choose_match_candidate,
            args=(candidate_widget_key,),
        )
    with quick_column.expander("常用问题", expanded=False):
        quick_columns = st.columns(2)
        for index, question in enumerate(QUICK_QUESTIONS):
            quick_columns[index % 2].button(
                question,
                key=f"quick-question-{index}",
                use_container_width=True,
                on_click=choose_quick_question,
                args=(question,),
            )

st.markdown(
    """
    <nav class="portal-nav" aria-label="页面导航">
      <a class="active" href="#answer-zone">智能问答</a>
      <a href="#directory-zone">知识目录</a>
      <a href="#quick-zone">常用服务</a>
      <a href="#history-zone">最近会话</a>
      <a href="#maintenance-zone">知识维护</a>
    </nav>
    """,
    unsafe_allow_html=True,
)

preview_item, preview_score = candidate_by_id[candidate_id]
preview_confidence = confidence_for_score(preview_score)
answer = build_answer(st.session_state.question, preview_item, preview_confidence)

safe_question = escape(st.session_state.question)
safe_title = escape(preview_item.title)
safe_category = escape(preview_item.category)
safe_answer = escape(answer).replace("\n", "<br>")
safe_source = escape(preview_item.source)
safe_owner = escape(preview_item.owner)
safe_audience = escape(preview_item.audience)
safe_updated = escape(preview_item.updated)

st.markdown(
    f"""
    <div id="answer-zone" class="page-title">
      <h1>{safe_question} <span>| 智能答复</span></h1>
      <p>当前匹配：{safe_title}</p>
    </div>
    """,
    unsafe_allow_html=True,
)

metric_1, metric_2, metric_3, metric_4 = st.columns(4)
metric_1.metric("匹配度", f"{preview_confidence}%")
metric_2.metric("知识条目", len(knowledge_items))
metric_3.metric("服务分类", len(categories(knowledge_items)) - 1)
metric_4.metric("反馈总数", feedback["helpful"] + feedback["manual"])

answer_left, answer_right = st.columns([0.78, 2.55], gap="small")
with answer_left:
    st.markdown(
        f"""
        <div class="service-dossier">
          <div class="panel-head">服务档案</div>
          <div class="dossier-row"><span class="label">分类</span><span class="value">{safe_category}</span></div>
          <div class="dossier-row"><span class="label">适用对象</span><span class="value">{safe_audience}</span></div>
          <div class="dossier-row"><span class="label">责任岗位</span><span class="value">{safe_owner}</span></div>
          <div class="dossier-row"><span class="label">知识来源</span><span class="value">{safe_source}</span></div>
          <div class="dossier-row"><span class="label">更新时间</span><span class="value">{safe_updated}</span></div>
          <div class="dossier-row"><span class="label">匹配度</span><span class="value confidence-value">{preview_confidence}%</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with answer_right:
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
        for index, step in enumerate(preview_item.steps, start=1)
    )
    st.markdown(
        f"<div class='step-list'><div class='panel-head'>办理步骤</div>{step_rows}</div>",
        unsafe_allow_html=True,
    )

source_action, helpful_action, manual_action, action_spacer = st.columns([1.15, 1, 1.15, 3.4], gap="small")
if preview_item.link:
    source_action.link_button(
        "查看来源",
        preview_item.link,
        icon=":material/open_in_new:",
        use_container_width=True,
    )
else:
    source_action.button("暂无来源链接", disabled=True, use_container_width=True)
if helpful_action.button("有帮助", icon=":material/thumb_up:", use_container_width=True):
    record_feedback(
        db,
        "helpful",
        question=st.session_state.question,
        knowledge_item_id=preview_item.id,
    )
    st.toast("已记录：有帮助")
    st.rerun()
if manual_action.button("人工跟进", icon=":material/support_agent:", use_container_width=True):
    record_feedback(
        db,
        "manual",
        question=st.session_state.question,
        knowledge_item_id=preview_item.id,
    )
    st.toast("已记录：需人工跟进")
    st.rerun()

st.markdown(
    """
    <div id="directory-zone" class="section-heading">
      <h2>知识目录</h2><span>按服务分类浏览数据库条目</span>
    </div>
    """,
    unsafe_allow_html=True,
)
directory_filter, directory_content = st.columns([0.92, 2.4], gap="small")
with directory_filter:
    category = st.selectbox("服务分类", categories(knowledge_items), index=0)
    filtered = [
        item for item in knowledge_items
        if category == "全部" or item.category == category
    ]
    selected_id = st.selectbox(
        "知识条目",
        [item.id for item in filtered],
        index=0,
        format_func=lambda item_id: next(item.title for item in filtered if item.id == item_id),
    )
    selected_item = next(item for item in filtered if item.id == selected_id)

with directory_content:
    selected_pills = " ".join(
        f"<span class='source-pill'>{escape(tag)}</span>" for tag in selected_item.tags[:7]
    )
    st.markdown(
        f"""
        <div class="directory-preview">
          <h3>{escape(selected_item.title)}</h3>
          <p>{escape(selected_item.summary)}</p>
          <div>{selected_pills}</div>
          <div class="directory-meta">来源：{escape(selected_item.source)} · 责任岗：{escape(selected_item.owner)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown(
    """
    <div id="quick-zone" class="section-heading">
      <h2>常用服务</h2><span>一键发起高频问题</span>
    </div>
    """,
    unsafe_allow_html=True,
)
service_columns = st.columns(3, gap="small")
for index, question in enumerate(QUICK_QUESTIONS):
    service_columns[index % 3].button(
        question,
        key=f"service-question-{index}",
        use_container_width=True,
        on_click=choose_quick_question,
        args=(question,),
    )

st.markdown(
    """
    <div id="history-zone" class="section-heading">
      <h2>最近会话</h2><span>保留最近 5 次问答</span>
    </div>
    """,
    unsafe_allow_html=True,
)
if not st.session_state.chat_history:
    st.caption("搜索问题后，这里会显示最近的问答记录。")
for message in st.session_state.chat_history:
    with st.expander(message["question"]):
        st.write(message["answer"])
        st.caption(
            f"{message['matched_title']} · {message['confidence']}% · {message['source']}"
        )

st.markdown(
    """
    <div id="maintenance-zone" class="section-heading">
      <h2>知识维护</h2><span>新增本地草稿与数据导出</span>
    </div>
    """,
    unsafe_allow_html=True,
)
with st.expander("新增知识草稿", expanded=False):
    with st.form("knowledge_form", clear_on_submit=True):
        title_column, category_column, tag_column = st.columns([1.5, 1, 1.5], gap="small")
        title = title_column.text_input("新增问题标题")
        category_input = category_column.text_input("分类", value="临时知识")
        tags_input = tag_column.text_input("关键词，用逗号分隔")
        answer_input = st.text_area("标准答案", height=120)
        save_item = st.form_submit_button(
            "保存草稿",
            type="primary",
            icon=":material/save:",
            use_container_width=True,
        )

if save_item and title.strip() and answer_input.strip():
    tags = tuple(tag.strip() for tag in tags_input.replace("，", ",").split(",") if tag.strip())
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
    add_knowledge_item(db, new_item)
    st.success("草稿已保存到 SQLite 数据库。")
    st.rerun()

export_column, export_spacer = st.columns([1.2, 4.8])
export_column.download_button(
    "导出知识库 JSON",
    data=export_knowledge_json(),
    file_name="information_service_knowledge.json",
    mime="application/json",
    icon=":material/download:",
    use_container_width=True,
)
