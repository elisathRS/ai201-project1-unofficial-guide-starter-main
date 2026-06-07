# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

<!-- What topic or category of knowledge does your system cover?
     Why is this knowledge valuable, and why is it hard to find through official channels?
     Example: "Student reviews of CS professors at [university] — useful because official
     course descriptions don't reflect teaching style, exam difficulty, or workload." -->

Off-Campus Housing for Miami Dade College (MDC) Students

I chose this domain because Miami Dade College does not provide traditional student housing, so students must find apartments, shared housing, or roommate arrangements on their own. Information about housing options, costs, neighborhoods, and student experiences is scattered across many websites and discussion forums rather than being available through a single official source. A retrieval-based system could help students quickly find answers about housing options, affordability, commuting, and common challenges.     

---

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | MDC Housing Resources for International Students | Official College Resource | https://www.mdc.edu/internationalstudents/resources/housing.aspx |
| 2 | MDC FAQ: Does MDC Have Student Housing? | Official FAQ | https://faq.mdc.edu/knowledgebase/does-mdc-have-student-housing/ |
| 3 | Rent.com – Apartments for Rent in Miami, FL | Apartment Listing Guide | https://www.rent.com/florida/miami-apartments |
| 4 | Fllat – Off-Campus Housing Near Miami Dade College | Student Housing Platform | https://fllat.com/miami/off-campus-housing-near-miami-dade-college |
| 5 | CollegeFind – Apartments Near Miami Dade College | Apartment Search Guide | https://www.college-find.com/apartments/miami-dade-college |
| 6 | Student.com – Miami Dade College Housing | Student Accommodation Directory | https://www.student.com/us/miami/u/miami-dade-college |
| 7 | Room Choice – Housing Near Miami Dade College | Student Housing Directory | https://www.roomchoice.com/schools/fl/miami-dade-college/ |
| 8 | CampusRent – Miami Dade College Apartments | Apartment Listings | https://www.campusrent.com/miami-dade-college-apartments.cfm |
| 9 | Casita – Student Accommodation Near MDC | Student Housing Platform | https://www.casita.com/student-accommodation/usa/miami/miami-dade-college |
| 10 | Looking for Student Housing Options/Roommates (r/Miami) | Reddit Forum Discussion | https://old.reddit.com/r/Miami/comments/ho17nc/looking_for_student_housing_optionsroommates/ |

---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunk size:** 500 characters

**Overlap:** 100 characters

**Preprocessing** (implemented in `documents/ingest.py`, using BeautifulSoup):

- Parse each saved page and extract text from `<body>` only (the `<head><title>`
  "Page Name | Site Name" string is title-spam that otherwise out-ranks real content).
- Remove HTML tags and whole noise sections: `<script>`, `<style>`, `<nav>`, `<aside>`,
  `<form>`, `<button>`, plus `<header>`/`<footer>` *unless* they are an article's own title
  header (`<header class="entry-header">` inside `<article>` holds the post title).
- Remove boilerplate widgets by class/id token match: cookie/consent banners, ads,
  share/social buttons, comment widgets, newsletter signups, breadcrumbs, modals, and known
  site-chrome ids (e.g. old.reddit's `#sr-header-area`).
- Drop UI-chrome and CMS-metadata lines ("Read more", "Skip to…", copyright, "Last Updated",
  "Tags", "Posted in") and globally de-duplicate repeated short, digit-free nav/site-name
  lines (the digit-free guard protects repeated prices and zip codes in listing tables).
- Decode all HTML entities (`&amp;`, `&nbsp;`, `&#39;`), normalize whitespace, and collapse
  duplicate blank lines while preserving paragraph breaks.
- Chunk with a sliding character window, snapping both boundaries to whitespace so chunks
  neither start nor end mid-word.

**Why these choices fit your documents:**

Most of the sources are housing guides, FAQs, apartment listings, and student discussion posts. These documents typically contain short to medium-length sections rather than long articles. A chunk size of 500 characters is large enough to capture a complete housing recommendation, apartment description, FAQ answer, or student comment while remaining small enough for accurate retrieval.

I use a 100-character overlap because important information may span chunk boundaries. For example, details about rental costs, housing requirements, or neighborhood recommendations may begin near the end of one chunk and continue into the next. The overlap helps preserve context and improves retrieval quality.

If chunks were significantly smaller, important information could be split apart and retrieved without sufficient context. If chunks were much larger, retrieval could return irrelevant information mixed with the relevant answer.

**Final chunk count:** **186 chunks across all 10 documents** (each ≤ 500 characters with
~100-character overlap). This sits comfortably in the healthy 50–2,000 range: large enough
that each chunk carries meaning, small enough that specific queries can match precisely. Two
of the ten sources blocked automated fetching — apartments.com returns HTTP 403, so it was
**swapped for Rent.com** (same "apartment listings near MDC" subtopic); and the Reddit thread
served a JS-challenge page on www.reddit.com, so it is fetched via **old.reddit.com** instead.

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:** **all-MiniLM-L6-v2** via `sentence-transformers`, loaded locally with
`SentenceTransformer("all-MiniLM-L6-v2")` (see `embed.py`). Embeddings are normalized to unit
length and stored in a persistent **ChromaDB** collection configured for **cosine** similarity
(`metadata={"hnsw:space": "cosine"}`); each record carries `{source, chunk_index}` metadata for
attribution. I chose this model because it runs locally with no API key and no rate limits,
is fast (all 186 chunks embed in ~1 second on a laptop), and produces 384-dimensional vectors
that capture enough semantic meaning for short housing guides, FAQ answers, and listings.
Retrieval uses **top-k = 7** (tuned up from an initial k = 5 — see Failure Case Analysis).

**Production tradeoff reflection:** If I were deploying this for real users and cost were not
a constraint, I would compare larger, higher-accuracy embedding models (e.g. `bge-large-en`,
`text-embedding-3-large`, or a multilingual model like `paraphrase-multilingual-mpnet`). The
tradeoffs I would weigh:

- **Domain/synonym accuracy:** all-MiniLM-L6-v2 missed the "dormitories" → "housing
  facilities" link (see Failure Case). A larger model with stronger semantic coverage would
  likely bridge that vocabulary gap.
- **Multilingual support:** many MDC students are international and Spanish-speaking; a
  multilingual model would let them query in Spanish against English documents.
- **Context length:** MiniLM truncates at 256 tokens — fine for my 500-character chunks, but a
  longer-context model would let me use bigger chunks without truncation.
- **Latency / hosting:** larger local models are slower and need more memory; API-hosted
  models add per-call cost and network latency but offload compute. For a free student
  project, MiniLM's local speed-vs-quality balance is the right call.

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

Generation uses **Groq `llama-3.3-70b-versatile`** at temperature 0 (see `generate.py`).
Grounding is *enforced*, not merely suggested, through three mechanisms:

**System prompt grounding instruction** (verbatim from `generate.py`):

> You are a helpful assistant that answers questions about off-campus housing for Miami Dade
> College (MDC) students. Follow these rules with no exceptions:
> 1. Answer using ONLY the information in the CONTEXT documents provided in the user message.
>    Do not use any outside or prior knowledge.
> 2. Do not guess, infer, or invent facts, prices, names, or sources. Every claim in your
>    answer must be supported by the context.
> 3. If the context does not contain enough information to answer the question, reply with
>    EXACTLY this sentence and nothing else: "I don't have enough information on that."
> 4. Keep the answer concise and directly focused on the question.

**Structural choices that reinforce grounding:**

- The prompt contains *only* the numbered, source-labelled retrieved chunks — the model
  literally has nothing else to draw from.
- Temperature 0 minimizes improvisation.
- A **code-level gate**: if retrieval returns zero chunks, the system returns the
  "I don't have enough information on that." fallback *without ever calling the LLM*, so it
  cannot answer from training knowledge.

**How source attribution is surfaced in the response:** Attribution is **programmatic, not
LLM-trusted**. After generation, `unique_sources()` builds the source list from the
`source` metadata of the chunks that were actually retrieved — it does *not* parse citations
out of the model's text. The list is rendered under each answer (the Gradio UI shows it in a
separate "Retrieved from" box). When the answer is the "not enough information" fallback, the
`grounded` flag is `False` and **no sources are attached** (nothing supported a non-answer).

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:**

**What the system returned:**

**Root cause (tied to a specific pipeline stage):**

**What you would change to fix it:**

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:**

**One way your implementation diverged from the spec, and why:**

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1**

- *What I gave the AI:*
- *What it produced:*
- *What I changed or overrode:*

**Instance 2**

- *What I gave the AI:*
- *What it produced:*
- *What I changed or overrode:*
