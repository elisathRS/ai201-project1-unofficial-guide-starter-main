"""
Milestone 5b — Gradio interface for The Unofficial Guide.

The full pipeline behind this UI:
    query -> retrieve.py (ChromaDB + all-MiniLM-L6-v2, top-k)
          -> generate.py (Groq llama-3.3-70b-versatile, grounded prompt)
          -> answer + programmatic source list

Run:
    python app.py
then open the printed local URL (http://127.0.0.1:7860).
"""

from __future__ import annotations

import gradio as gr

from generate import answer_question

# The 5 evaluation-plan questions, as one-click examples for graders/users.
EXAMPLE_QUESTIONS = [
    "Does Miami Dade College provide student dormitories?",
    "What websites can students use to search for apartments near MDC?",
    "What housing resources are available for international students?",
    "What are common housing options for MDC students?",
    "Why do many students look for roommates?",
]


def handle_query(question: str) -> tuple[str, str]:
    """UI callback: run the RAG pipeline; return (answer, sources) for two boxes."""
    try:
        result = answer_question(question)
    except Exception as err:                       # surface config/runtime errors
        return f"⚠️ {err}", ""
    sources = "\n".join(f"• {s}" for s in result["sources"])
    return result["answer"], sources


with gr.Blocks(title="The Unofficial Guide — MDC Off-Campus Housing") as demo:
    gr.Markdown(
        "# The Unofficial Guide — MDC Off-Campus Housing\n"
        "Ask about off-campus housing for Miami Dade College students. Answers are "
        "**grounded in retrieved documents only** — if the documents don't cover your "
        "question, the assistant says so. The documents used are listed under *Retrieved from*."
    )
    inp = gr.Textbox(
        label="Your question",
        placeholder="e.g. What are common housing options for MDC students?",
        lines=2,
    )
    btn = gr.Button("Ask", variant="primary")
    answer = gr.Textbox(label="Answer", lines=8)
    sources = gr.Textbox(label="Retrieved from", lines=4)

    gr.Examples(examples=EXAMPLE_QUESTIONS, inputs=inp)

    btn.click(handle_query, inputs=inp, outputs=[answer, sources])
    inp.submit(handle_query, inputs=inp, outputs=[answer, sources])


if __name__ == "__main__":
    demo.launch()
