# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

Off-Campus Housing for Miami Dade College (MDC) Students

I chose this domain because Miami Dade College does not provide traditional student housing, so students must find apartments, shared housing, or roommate arrangements on their own. Information about housing options, costs, neighborhoods, and student experiences is scattered across many websites and discussion forums rather than being available through a single official source. A retrieval-based system could help students quickly find answers about housing options, affordability, commuting, and common challenges. 

---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->


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
| 10 | Housing and Apartment Recommendation Discussions | Reddit Forum Discussions | r/MiamiDadeCollege (housing-related threads and posts) |

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:** 500 characters

**Overlap:** 100 characters

**Preprocessing:**

- Extract text from each webpage.
- Remove HTML tags, navigation menus, advertisements, and footer content.
- Normalize whitespace and remove duplicate blank lines.
- Preserve paragraph breaks when possible before chunking.


**Reasoning:** Most of the sources are housing guides, FAQs, apartment listings, and student discussion posts. These documents typically contain short to medium-length sections rather than long articles. A chunk size of 500 characters is large enough to capture a complete housing recommendation, apartment description, FAQ answer, or student comment while remaining small enough for accurate retrieval.

I use a 100-character overlap because important information may span chunk boundaries. For example, details about rental costs, housing requirements, or neighborhood recommendations may begin near the end of one chunk and continue into the next. The overlap helps preserve context and improves retrieval quality.

If chunks were significantly smaller, important information could be split apart and retrieved without sufficient context. If chunks were much larger, retrieval could return irrelevant information mixed with the relevant answer.


---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:**

I will use **all-MiniLM-L6-v2** from the Sentence Transformers library. This model is lightweight, fast, and commonly used for semantic search tasks. It generates embeddings that capture the meaning of text, allowing the system to retrieve relevant information even when the query uses different wording than the source documents.

**Top-k:**

I started at **top-k = 5** and tuned up to **top-k = 7** after seeing real retrieval
results. A borderline-but-correct chunk (notably the MDC FAQ "no on-campus housing" answer)
kept landing just outside the top 5 behind several apartment-listing chunks, so widening to
7 improves recall without adding much irrelevant context. (I also de-spammed the listing
pages' title/nav chunks during ingestion, which were falsely out-ranking real content.)

**Production tradeoff reflection:**

If I were deploying this system for real users and cost was not a constraint, I would evaluate larger embedding models that provide stronger semantic understanding, better multilingual support, and improved performance on domain-specific queries. Larger models may retrieve more relevant chunks and better understand complex questions, especially from international students who may search using different terminology.

However, larger models require more computational resources, increased memory usage, and higher latency. The all-MiniLM-L6-v2 model offers a good balance between retrieval quality, speed, and efficiency for a student housing knowledge base. For a production system, I would compare retrieval accuracy, response time, context length support, and multilingual capabilities before selecting a more advanced embedding model.

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | Does Miami Dade College provide student dormitories? | No. MDC does not provide traditional student housing and students must arrange off-campus housing independently. |
| 2 | What websites can students use to search for apartments near MDC? | Apartments.com, Student.com, Casita, CampusRent, Room Choice, and similar housing platforms. |
| 3 | What housing resources are available for international students? | MDC provides housing resource information and referrals through its International Student Services pages. |
| 4 | What are common housing options for MDC students? | Apartments, shared apartments, private rooms, roommate arrangements, and student-oriented housing. |
| 5 | Why do many students look for roommates? | To reduce housing costs and make living in the Miami area more affordable. |

---

## Anticipated Challenges

1. **Inconsistent information**  
   Official sources, housing websites, and Reddit discussions may provide conflicting or outdated information.

2. **Outdated housing data**  
   Rental prices and apartment availability change frequently, which can reduce answer accuracy.

3. **Off-topic retrieval**  
   Some webpages contain ads or unrelated content that may be retrieved instead of useful housing information.

4. **Chunk boundary issues**  
   Important details may be split across multiple chunks, causing incomplete retrieval results.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:**

- **Tool:** Claude (Claude Code).
- **Input I gave it:** my Documents section (10 web/HTML sources + a Reddit thread), my
  Chunking Strategy section (500-char chunks, 100-char overlap, preprocessing rules:
  strip HTML/nav/ads/footer, normalize whitespace, preserve paragraph breaks), and the
  pipeline stages (Ingestion → Chunking → Embedding/ChromaDB → Retrieval → Generation).
- **What I expected:** a `documents/ingest.py` that loads local source files, cleans them,
  and produces overlapping chunks matching my exact size/overlap, with per-document and
  total chunk counts and a `chunks.json` output for the embedding stage.
- **How I verified it matches the spec:** ran a test confirming max chunk length 495 ≤ 500
  and exactly 100-char overlap between consecutive chunks; confirmed the HTML cleaner
  removes `<nav>`, ad/cookie banners, and `<footer>` while keeping real paragraphs.
- **What it produced:** two scripts — `fetch_sources.py` (downloads each URL's raw HTML
  into documents/raw/ in a consistent format before any cleaning) and `ingest.py`
  (cleans + chunks, with a `--inspect` mode that prints one cleaned document).
- **What I changed/overrode (three corrections after reviewing output):**
  1. The first cut used a regex HTML strip that did *not* remove nav/footer, so I switched
     to BeautifulSoup (tag-aware) and added it + `requests` to requirements.txt, keeping the
     regex as a fallback.
  2. Inspecting the cleaned MDC FAQ showed 31 KB → 30 chars: my noise filter matched class
     names by *substring*, so `"sidebar"`/`"header"` hit the `content-sidebar-wrap` layout
     wrapper (and the `<body>` class) and deleted the whole answer. I fixed it to match whole
     class *tokens* and to never decompose structural tags (html/body/main/article/section).
  3. A leftover-junk scan still found `Skip to`, `©`, and `Privacy Policy` footer text as
     plain lines, so I added a line-level boilerplate filter.
- **How I verified:** all 187 chunks are ≤ 500 chars with ~100-char overlap; the cleaned
  FAQ chunk contains the gold answer to test question #1; a scan confirms zero HTML entities
  and no nav/footer text across all 9 fetched documents (2 sources — apartments.com 403 and
  Reddit's challenge page — must be saved manually into documents/raw/).

**Milestone 4 — Embedding and retrieval:**

- **Tool:** Claude (Claude Code).
- **Input I gave it:** my Retrieval Approach section (all-MiniLM-L6-v2, top-k = 5, ChromaDB)
  and the chunk schema produced by ingest.py ({id, source, chunk_index, text}).
- **What it produced:** `embed.py` (loads documents/chunks.json, embeds with all-MiniLM-L6-v2,
  upserts into a persistent ChromaDB collection with {source, chunk_index} metadata) and
  `retrieve.py` (retrieve(query, k=5) returning chunks + source + similarity score).
- **How I verified:** built the index (194 chunks) and ran all 5 evaluation questions;
  metadata attribution is attached to every result and similarity scores are sensible.
- **Notable finding to revisit:** for Q1 ("does MDC provide dormitories?") the definitive
  FAQ chunk ("Miami Dade does not provide or supervise housing facilities") did NOT rank in
  the top-5 — listing-page titles out-scored it. Good candidate for the Failure Case Analysis
  and for k-tuning.

**Milestone 5 — Generation and interface:**
