import streamlit as st

from agent import run_agent


st.set_page_config(
    page_title="Gemini AI Agent",
    page_icon="🤖",
    layout="centered",
)

st.title("Gemini AI Agent")
st.caption("Ask questions that use the calculator, customer lookup, or text analyzer.")

with st.sidebar:
    st.header("Agent settings")
    st.write("The agent can use multiple tools and return a final answer.")
    st.write("Rate limiting is controlled by `GEMINI_REQUESTS_PER_MINUTE`.")

    if st.button("Clear history"):
        st.session_state.pop("history", None)
        st.rerun()

if "history" not in st.session_state:
    st.session_state.history = []

for item in st.session_state.history:
    with st.chat_message("user"):
        st.write(item["task"])

    with st.chat_message("assistant"):
        st.write(item["answer"])
        st.caption(
            f"Status: {item['status']} | "
            f"Steps: {item.get('steps', 'N/A')}"
        )
        with st.expander("View agent trace"):
            st.json(item.get("scratchpad", []))

task = st.chat_input("Example: Find C106 and calculate their annual fee.")

if task:
    with st.chat_message("user"):
        st.write(task)

    with st.chat_message("assistant"):
        with st.spinner("The agent is working..."):
            try:
                result = run_agent(task)
            except Exception as exc:
                st.error(f"Agent request failed: {exc}")
                st.stop()

        st.write(result["answer"])
        st.caption(
            f"Status: {result['status']} | "
            f"Steps: {result.get('steps', 'N/A')}"
        )
        with st.expander("View agent trace", expanded=True):
            st.json(result.get("scratchpad", []))

    st.session_state.history.append(
        {
            "task": task,
            "answer": result["answer"],
            "status": result["status"],
            "steps": result.get("steps"),
            "scratchpad": result.get("scratchpad", []),
        }
    )
