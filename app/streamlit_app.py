"""
Ask My Pension: the web app.

A worker types a question about the Nigerian Contributory Pension Scheme and gets:
1. the answer first, in large text
2. simple explanations of any pension terms in it (from the hand-written glossary)
3. the full passage it came from, and the document's name, so they can read more

If the system cannot find an answer, it says so politely instead of guessing.

Run from the project root:
    streamlit run app/streamlit_app.py
"""

import sys
import time
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.answer_pipeline import Answer, System, answer_question, load_system  # noqa: E402
from src.assets import ensure_assets  # noqa: E402

TITLE = "Ask My Pension"

WELCOME = (
    "Ask any question about your pension in Nigeria, the Contributory Pension Scheme. "
    "The answer comes from pension documents, and you can always see where it came from."
)

DISCLAIMER = (
    "This is a student project for a university course. It is not official financial or legal advice, "
    "and it is not connected to or endorsed by the National Pension Commission (PenCom) or any pension "
    "company. Please confirm important decisions with your Pension Fund Administrator (PFA)."
)

REFUSAL = (
    "Sorry, I could not find an answer to that in the pension documents. I can only answer questions about "
    "pensions in Nigeria, such as your Retirement Savings Account (RSA), your PFA, contributions, moving your "
    "RSA, and retirement benefits."
)

EXAMPLES = [
    "What is an RSA?",
    "What is a PFA?",
    "How much does my employer have to pay into my pension?",
    "What is the retirement age?",
    "Can I have more than one RSA?",
]


@st.cache_resource(show_spinner="Loading the pension documents and models. The first start takes a minute or two.")
def get_system() -> System:
    ensure_assets()

    return load_system()


def use_example(example: str) -> None:
    st.session_state["question"] = example


def show_answer(result: Answer) -> None:
    if not result["answer"]:
        st.warning(REFUSAL)
        return

    st.markdown(f"### {result['answer']}")

    if result["glossary"]:
        st.markdown("**Words in this answer, explained simply:**")

        for entry in result["glossary"]:
            st.info(f"**{entry['term']}**: {entry['explanation']}\n\n*Source: {entry['source']}*")

    source = result["source"]

    if source is not None:
        st.markdown(
            f"**Where this answer comes from:** [{source['title']}]({source['url']}), {source['publisher']}  \n"
            f"Section: {result['section']}"
        )

        st.markdown(f"> {result['passage_text']}")


def main() -> None:
    st.set_page_config(page_title=TITLE)

    st.title(TITLE)

    st.write(WELCOME)

    system = get_system()

    st.write("Try one of these:")

    for example in EXAMPLES:
        st.button(example, on_click=use_example, args=(example,))

    question = st.text_input("Your question", key="question", placeholder="For example: What is an RSA?")

    if question.strip():
        started = time.perf_counter()

        result = answer_question(system, question.strip())

        print(f"answered in {time.perf_counter() - started:.1f}s: {question.strip()!r}")

        show_answer(result)

    st.caption(DISCLAIMER)


main()
