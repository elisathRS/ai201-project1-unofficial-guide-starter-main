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

I will retrieve the **top 5 most relevant chunks (top-k = 5)** for each query. Retrieving five chunks provides enough context to answer most housing-related questions while reducing the amount of irrelevant information passed to the language model.

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

**Milestone 4 — Embedding and retrieval:**

**Milestone 5 — Generation and interface:**
