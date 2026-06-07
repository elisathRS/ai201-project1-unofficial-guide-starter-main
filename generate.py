"""
Milestone 5a — Grounded generation for The Unofficial Guide.

Pipeline stage 5:  Retrieval -> Generation
(retrieve.py supplies the context; app.py wraps this in a Gradio UI.)

Design decisions that satisfy the assignment's grounding + attribution rules:

1. GROUNDING IS ENFORCED, NOT SUGGESTED:
   - The system prompt forbids outside knowledge and pins the exact fallback
     string ("I don't have enough information on that.") for missing info.
   - The context block NUMBERS each chunk and labels it with its source, so the
     model literally only sees the retrieved text — nothing else is in the prompt.
   - A programmatic gate short-circuits BEFORE calling the LLM when retrieval
     returns nothing, so the model can never answer from thin air.

2. SOURCE ATTRIBUTION IS PROGRAMMATIC, NOT LLM-TRUSTED:
   - The source list is built from the metadata of the chunks we actually
     retrieved (retrieve.py results), then attached to the response in code.
     We do NOT parse citations out of the model's text or trust it to list
     sources. If the answer is the "not enough information" fallback, we attach
     no sources (nothing supported it).

Run a single query from the CLI (needs GROQ_API_KEY in .env):
    python generate.py "Does MDC have student housing?"
"""

from __future__ import annotations

import os
import sys

from dotenv import load_dotenv
from groq import Groq

from retrieve import retrieve, Result

load_dotenv()

MODEL = "llama-3.3-70b-versatile"
TOP_K = 5                              # chunks of context per answer
INSUFFICIENT = "I don't have enough information on that."

# Human-readable labels for each source file, for the attribution list.
SOURCE_LABELS = {
    "01_mdc_intl_housing": "MDC International Student Housing Resources",
    "02_mdc_faq_housing":  "MDC FAQ — Does MDC Have Student Housing?",
    "03_rent_com_miami":   "Rent.com — Apartments in Miami, FL",
    "04_fllat":            "Fllat — Off-Campus Housing Near MDC",
    "05_collegefind":      "CollegeFind — Apartments Near MDC",
    "06_student_com":      "Student.com — MDC Housing",
    "07_roomchoice":       "Room Choice — Housing Near MDC",
    "08_campusrent":       "CampusRent — MDC Apartments",
    "09_casita":           "Casita — Student Accommodation Near MDC",
    "10_reddit_miami":     "Reddit r/Miami — Student Housing Discussion",
}

SYSTEM_PROMPT = (
    "You are a helpful assistant that answers questions about off-campus housing "
    "for Miami Dade College (MDC) students.\n"
    "Follow these rules with no exceptions:\n"
    "1. Answer using ONLY the information in the CONTEXT documents provided in "
    "the user message. Do not use any outside or prior knowledge.\n"
    "2. Do not guess, infer, or invent facts, prices, names, or sources. Every "
    "claim in your answer must be supported by the context.\n"
    f"3. If the context does not contain enough information to answer the "
    f"question, reply with EXACTLY this sentence and nothing else: "
    f"\"{INSUFFICIENT}\"\n"
    "4. Cite your source INLINE: after the fact(s) you state, name the source in "
    "parentheses using the exact label shown after 'source:' in the context — "
    "for example, \"(source: MDC FAQ — Does MDC Have Student Housing?)\". Do not "
    "use the bracket numbers like [1]; use the readable source label.\n"
    "5. Keep the answer concise and directly focused on the question."
)


def _client() -> Groq:
    key = os.getenv("GROQ_API_KEY")
    if not key or key == "your_key_here":
        raise RuntimeError(
            "GROQ_API_KEY is missing. Copy .env.example to .env and set your "
            "key (free at https://console.groq.com)."
        )
    return Groq(api_key=key)


def label_for(source: str) -> str:
    """Map a source filename to a readable label (falls back to the filename)."""
    stem = source.rsplit(".", 1)[0]
    return SOURCE_LABELS.get(stem, source)


def build_context(results: list[Result]) -> str:
    """Format retrieved chunks into a numbered, source-labelled context block."""
    blocks = []
    for i, r in enumerate(results, 1):
        blocks.append(f"[{i}] (source: {label_for(r.source)})\n{r.text}")
    return "\n\n".join(blocks)


def unique_sources(results: list[Result]) -> list[str]:
    """Distinct source labels of the retrieved chunks, in first-seen order."""
    seen, ordered = set(), []
    for r in results:
        lbl = label_for(r.source)
        if lbl not in seen:
            seen.add(lbl)
            ordered.append(lbl)
    return ordered


def answer_question(query: str, k: int = TOP_K) -> dict:
    """Retrieve context, generate a grounded answer, and attach sources in code.

    Returns {"answer": str, "sources": list[str], "grounded": bool}.
    """
    query = (query or "").strip()
    if not query:
        return {"answer": "Please enter a question.", "sources": [], "grounded": False}

    results = retrieve(query, k)

    # Grounding gate: with no retrieved context, never call the LLM.
    if not results:
        return {"answer": INSUFFICIENT, "sources": [], "grounded": False}

    context = build_context(results)
    user_message = (
        f"CONTEXT:\n{context}\n\n"
        f"QUESTION: {query}\n\n"
        "Answer using only the context above."
    )

    completion = _client().chat.completions.create(
        model=MODEL,
        temperature=0,                 # deterministic, less room to improvise
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
    )
    answer = completion.choices[0].message.content.strip()

    # Programmatic attribution: only attach sources to a real (grounded) answer.
    grounded = INSUFFICIENT.lower() not in answer.lower()
    sources = unique_sources(results) if grounded else []
    return {"answer": answer, "sources": sources, "grounded": grounded}


def format_response(result: dict) -> str:
    """Render the answer + a programmatically-built Sources list as Markdown."""
    out = result["answer"]
    if result["sources"]:
        out += "\n\n**Sources:**\n" + "\n".join(f"- {s}" for s in result["sources"])
    return out


def main() -> None:
    if len(sys.argv) < 2:
        print('Usage: python generate.py "your question"')
        return
    result = answer_question(" ".join(sys.argv[1:]))
    print(format_response(result))


if __name__ == "__main__":
    main()
