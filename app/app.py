"""
Ask My Pension: the web app.

A worker types a question about the Nigerian Contributory Pension Scheme and gets:
1. the answer first, in large text
2. simple explanations of any pension terms in it (from the hand-written glossary)
3. the full passage it came from, and the document's name, so they can read more

If the system cannot find an answer, it says so politely instead of guessing.

Run from the project root:
    python app/app.py
"""

import sys
import time
from pathlib import Path

import gradio as gr

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.answer_pipeline import Answer, answer_question, load_system  # noqa: E402

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

SYSTEM = load_system()


def answer_markdown(result: Answer) -> str:
    if not result["answer"]:
        return f"### {REFUSAL}"

    return f"## {result['answer']}"


def glossary_markdown(result: Answer) -> str:
    if not result["glossary"]:
        return ""

    lines = ["**Words in this answer, explained simply:**", ""]

    for entry in result["glossary"]:
        source = f" *(Source: {entry['source']})*" if entry["source"] else ""

        lines.append(f"- **{entry['term']}**: {entry['explanation']}{source}")

    return "\n".join(lines)


def source_markdown(result: Answer) -> str:
    if not result["answer"] or result["source"] is None:
        return ""

    source = result["source"]

    return (
        f"**Where this answer comes from:** [{source['title']}]({source['url']}), {source['publisher']}  \n"
        f"Section: {result['section']}\n\n"
        f"> {result['passage_text']}"
    )


def ask(question: str) -> tuple[str, str, str]:
    if not question.strip():
        return "Please type a question first.", "", ""

    started = time.perf_counter()

    result = answer_question(SYSTEM, question.strip())

    print(f"answered in {time.perf_counter() - started:.1f}s: {question.strip()!r}")

    return answer_markdown(result), glossary_markdown(result), source_markdown(result)


with gr.Blocks(title=TITLE) as page:
    gr.Markdown(f"# {TITLE}\n\n{WELCOME}")

    with gr.Row():
        question_box = gr.Textbox(label="Your question", placeholder="For example: What is an RSA?", scale=4)

        ask_button = gr.Button("Ask", variant="primary", scale=1)

    gr.Examples(examples=EXAMPLES, inputs=question_box, label="Try one of these")

    answer_box = gr.Markdown()

    glossary_box = gr.Markdown()

    source_box = gr.Markdown()

    gr.Markdown(f"*{DISCLAIMER}*")

    outputs = [answer_box, glossary_box, source_box]

    ask_button.click(ask, inputs=question_box, outputs=outputs)

    question_box.submit(ask, inputs=question_box, outputs=outputs)


if __name__ == "__main__":
    page.launch()
