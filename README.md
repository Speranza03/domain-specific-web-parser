# Domain-Specific Web Content Extraction System

University project developed by a three-person team to extract clean, relevant text from heterogeneous web pages.

The system supports four domains:

- `en.wikipedia.org`
- `curryfuneralhome.org`
- `www.boxofficemojo.com`
- `www.mymovies.it`

Each domain is handled by a dedicated parser built on top of a shared `BaseParser`. The parsers combine Crawl4AI, CSS-based filtering, regular expressions and, where needed, BeautifulSoup. The MyMovies parser also detects different page types and applies dedicated cleaning strategies.

## Main components

- **Parsing layer** — shared crawling/cleaning logic plus domain-specific parsers.
- **Parser manager** — selects the appropriate parser from the requested URL.
- **FastAPI backend** — exposes endpoints for URL/HTML parsing and evaluation.
- **Web frontend** — simple FastAPI/Jinja interface for submitting URLs and inspecting results.
- **Evaluation pipeline** — compares extracted text with manually curated gold standards using token-level precision, recall and F1-score.
- **Docker setup** — backend and frontend are containerized and can be started together with Docker Compose.

## Evaluation

For the original university submission, parser outputs were compared with manually curated reference texts. Texts were normalized and evaluated as sets of unique tokens.

| Domain | Precision | Recall | F1 |
| --- | ---: | ---: | ---: |
| Wikipedia | 0.9911 | 0.9964 | 0.9937 |
| Curry Funeral Home | 0.9909 | 0.9953 | 0.9931 |
| Box Office Mojo | 0.9914 | 0.9929 | 0.9921 |
| MyMovies | 0.9963 | 0.9995 | 0.9979 |

The original evaluation dataset is **not included** in this public repository because it contains archived HTML and textual content from third-party websites. The values above are the results obtained with the dataset used for the university submission. Features that directly depend on the local gold-standard files therefore require that dataset to be supplied separately.

Because the parsers depend on the structure of live websites, current extraction results may differ if those websites have changed since the project was completed.

## Technologies

Python 3.10, FastAPI, Crawl4AI, Playwright/Chromium, BeautifulSoup, Pydantic, Jinja2, HTTPX, Docker and Docker Compose.

The original project did not pin individual dependency versions; the Docker configuration uses Python 3.10.

## Running the project

Docker and Docker Compose are required.

```bash
docker compose up --build
```

After startup:

- Frontend: `http://localhost:8004`
- Backend API documentation: `http://localhost:8003/docs`

The core parsing API can be used without the original evaluation dataset.

## Team contributions

The project was developed by a team of three, with responsibilities divided across the system and the domain-specific parsers.

My main contributions were the shared project architecture and parsing infrastructure, backend and frontend services, evaluation pipeline, and the Wikipedia and Curry Funeral Home parsers. My teammates developed the Box Office Mojo and MyMovies parsers. Before submission, we worked together to refine the extraction logic across all four domains and improve the final evaluation results.

The project placed among the top 10 teams in the course and led to the opportunity to continue the work through an individually supervised BSc thesis.
