from __future__ import annotations

import json
from datetime import date, datetime
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
    match_knowledge,
)


st.set_page_config(
    page_title="校内信息服务智能问答台",
    page_icon="IT",
    layout="wide",
)


st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1440px;
    }
    .hero {
        border: 1px solid #dfe4df;
        background: linear-gradient(135deg, #f4fbf8 0%, #ffffff 52%, #fff7ed 100%);
        padding: 1.2rem 1.35rem;
        margin-bottom: 1rem;
    }
    .hero h1 {
        margin: 0;
        color: #17212b;
        font-size: 2rem;
        line-height: 1.15;
    }
    .hero p {
        color: #586270;
        margin: .5rem 0 0;
        line-height: 1.7;
    }
    .answer-box {
        border: 1px solid #dfe4df;
        background: #ffffff;
        padding: 1rem 1.1rem;
        margin-top: .75rem;
    }
    .meta-line {
        color: #66717c;
        font-size: .86rem;
        line-height: 1.8;
    }
    .source-pill {
        display: inline-block;
        border: 1px solid #dfe4df;
        background: #f6f7f4;
        padding: .25rem .5rem;
        margin: .15rem .25rem .15rem 0;
        color: #315d58;
        font-size: .82rem;
    }
    div[data-testid="stMetric"] {
        border: 1px solid #dfe4df;
        background: #ffffff;
        padding: .75rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

DB_PATH = Path("data/info_service.db")


def bootstrap_state() -> None:
    st.session_state.setdefault("chat_history", [])
    st.session_state.setdefault("question", "校园网连不上怎么办？")


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
    add_chat(question, item, confidence)
    return item, confidence, related


def export_knowledge_json() -> str:
    payload = [item.to_dict() for item in all_knowledge()]
    return json.dumps(payload, ensure_ascii=False, indent=2)


bootstrap_state()
db = get_db()
knowledge_items = all_knowledge()
feedback = feedback_summary(db)

st.markdown(
    """
    <div class="hero">
      <h1>校内信息服务智能问答台</h1>
      <p>面向师生的信息化处自助问答工具：输入问题后，系统从知识库中匹配标准答案，
      同时展示办理步骤、来源、责任岗位和反馈入口。</p>
    </div>
    """,
    unsafe_allow_html=True,
)

metric_1, metric_2, metric_3, metric_4 = st.columns(4)
metric_1.metric("知识条目", len(knowledge_items))
metric_2.metric("服务分类", len(categories(knowledge_items)) - 1)
metric_3.metric("最近会话", len(st.session_state.chat_history))
metric_4.metric("反馈总数", feedback["helpful"] + feedback["manual"])

left, center, right = st.columns([0.9, 1.55, 0.95], gap="large")

with left:
    st.subheader("知识库")
    category = st.radio("问题分类", categories(knowledge_items), horizontal=False)
    filtered = [
        item for item in knowledge_items
        if category == "全部" or item.category == category
    ]

    selected_title = st.selectbox(
        "查看条目",
        [item.title for item in filtered],
        index=0,
    )
    selected_item = next(item for item in filtered if item.title == selected_title)

    st.markdown(f"**{selected_item.title}**")
    st.caption(selected_item.summary)
    st.markdown(
        " ".join(f"<span class='source-pill'>{tag}</span>" for tag in selected_item.tags[:5]),
        unsafe_allow_html=True,
    )

with center:
    st.subheader("在线问答")

    for question in QUICK_QUESTIONS:
        if st.button(question, use_container_width=True):
            st.session_state.question = question
            ask_question(question)

    with st.form("question_form", clear_on_submit=False):
        user_question = st.text_input(
            "请输入信息化服务问题",
            key="question",
            placeholder="例如：校外怎么访问校内资源？",
        )
        submitted = st.form_submit_button("生成答复", use_container_width=True)

    if submitted and user_question.strip():
        ask_question(user_question.strip())

    preview_item, preview_confidence, related_items = match_knowledge(
        st.session_state.question,
        all_knowledge(),
    )
    answer = build_answer(st.session_state.question, preview_item, preview_confidence)

    st.markdown(
        f"""
        <div class="answer-box">
          <div class="meta-line">匹配条目：{preview_item.title} · 预计匹配度：{preview_confidence}%</div>
          <h3>{preview_item.category}</h3>
          <p>{answer}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("**办理步骤**")
    for index, step in enumerate(preview_item.steps, start=1):
        st.write(f"{index}. {step}")

    st.markdown(
        f"""
        <div class="meta-line">
        来源：{preview_item.source} · 责任岗：{preview_item.owner} · 更新时间：{preview_item.updated}
        </div>
        """,
        unsafe_allow_html=True,
    )

    feedback_col_1, feedback_col_2 = st.columns(2)
    if feedback_col_1.button("有帮助", use_container_width=True):
        record_feedback(
            db,
            "helpful",
            question=st.session_state.question,
            knowledge_item_id=preview_item.id,
        )
        st.toast("已记录：有帮助")
        st.rerun()
    if feedback_col_2.button("需人工跟进", use_container_width=True):
        record_feedback(
            db,
            "manual",
            question=st.session_state.question,
            knowledge_item_id=preview_item.id,
        )
        st.toast("已记录：需人工跟进")
        st.rerun()

    st.markdown("**相关条目**")
    for item in related_items:
        st.caption(f"{item.category} · {item.title} · {item.source}")

with right:
    st.subheader("知识维护")
    with st.form("knowledge_form", clear_on_submit=True):
        title = st.text_input("新增问题标题")
        category_input = st.text_input("分类", value="临时知识")
        answer_input = st.text_area("标准答案", height=120)
        tags_input = st.text_input("关键词，用逗号分隔")
        save_item = st.form_submit_button("保存草稿", use_container_width=True)

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

    st.download_button(
        "导出知识库 JSON",
        data=export_knowledge_json(),
        file_name="information_service_knowledge.json",
        mime="application/json",
        use_container_width=True,
    )

    st.markdown("**最近会话**")
    if not st.session_state.chat_history:
        st.caption("提交问题后会显示最近 5 条问答。")
    for message in st.session_state.chat_history:
        with st.expander(message["question"]):
            st.write(message["answer"])
            st.caption(
                f"{message['matched_title']} · {message['confidence']}% · {message['source']}"
            )
