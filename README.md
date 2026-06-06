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

---

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | MDC Housing Resources for International Students | Official College Resource | https://www.mdc.edu/internationalstudents/resources/housing.aspx |
| 2 | MDC FAQ: Does MDC Have Student Housing? | Official FAQ | https://faq.mdc.edu/knowledgebase/does-mdc-have-student-housing/ |
| 3 | Apartments.com – Off-Campus Housing Near MDC Wolfson Campus | Apartment Listing Guide | https://www.apartments.com/local-guide/off-campus-housing/fl/miami/miami-dade-college-wolfson-campus/ |
| 4 | Fllat – Off-Campus Housing Near Miami Dade College | Student Housing Platform | https://fllat.com/miami/off-campus-housing-near-miami-dade-college |
| 5 | CollegeFind – Apartments Near Miami Dade College | Apartment Search Guide | https://www.college-find.com/apartments/miami-dade-college |
| 6 | Student.com – Miami Dade College Housing | Student Accommodation Directory | https://www.student.com/us/miami/u/miami-dade-college |
| 7 | Room Choice – Housing Near Miami Dade College | Student Housing Directory | https://www.roomchoice.com/schools/fl/miami-dade-college/ |
| 8 | CampusRent – Miami Dade College Apartments | Apartment Listings | https://www.campusrent.com/miami-dade-college-apartments.cfm |
| 9 | Casita – Student Accommodation Near MDC | Student Housing Platform | https://www.casita.com/student-accommodation/usa/miami/miami-dade-college |
| 10 | Housing and Apartment Recommendation Discussions | Reddit Forum Discussions | r/MiamiDadeCollege (housing-related threads and posts) |

---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunk size: ** 500 characters

**Overlap:** 100 characters

**Preprocessing:**

- Extract text from each webpage.
- Remove HTML tags, navigation menus, advertisements, and footer content.
- Normalize whitespace and remove duplicate blank lines.
- Preserve paragraph breaks when possible before chunking.

**Why these choices fit your documents:**

**Final chunk count:** Most of the sources are housing guides, FAQs, apartment listings, and student discussion posts. These documents typically contain short to medium-length sections rather than long articles. A chunk size of 500 characters is large enough to capture a complete housing recommendation, apartment description, FAQ answer, or student comment while remaining small enough for accurate retrieval.

I use a 100-character overlap because important information may span chunk boundaries. For example, details about rental costs, housing requirements, or neighborhood recommendations may begin near the end of one chunk and continue into the next. The overlap helps preserve context and improves retrieval quality.

If chunks were significantly smaller, important information could be split apart and retrieved without sufficient context. If chunks were much larger, retrieval could return irrelevant information mixed with the relevant answer.

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:**

**Production tradeoff reflection:**

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:**

**How source attribution is surfaced in the response:**

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
