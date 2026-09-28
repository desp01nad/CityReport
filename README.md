# City Report

[![CI](https://github.com/desp01nad/CityReport/actions/workflows/ci.yml/badge.svg)](https://github.com/desp01nad/CityReport/actions/workflows/ci.yml)

A municipal issue-reporting platform: a REST API for citizens, an LLM triage step,
and a Streamlit operations dashboard for city staff.

![Reports dashboard](docs/images/dashboard.png)

## What it does

Citizens file reports about problems in the city — a pothole, a broken street
light, an abandoned vehicle — through a REST API, attaching a title, description,
category, GPS coordinates and a photo. Each incoming report is passed to an LLM
that reads it and assigns two triage bands: a **quality** score for how usable the
report is, and a **priority** for how urgently it needs attention. City staff then
work the queue from an admin dashboard, where reports appear on a map of the city
and in a filterable table: they can open any report to see its photo, its AI
assessment and the current weather at its location, then change its status and
leave notes for the department handling it. A second dashboard page tracks how the
backlog is moving — volume over time, breakdown by category and status, and how
long each category takes to resolve.

## Screenshots

The reports dashboard (shown at the top) has a city-wide map, filters across every
report field, and the full report queue.

![Report detail](docs/images/report-detail.png)
*Opening a report shows its photo, the LLM-assigned quality and priority, and live weather at the reported coordinates.*

![Analysis page](docs/images/analysis.png)
*The analysis page: headline metrics plus volume, category, status and resolution-time charts.*

## Features

- **REST API** — 8 endpoints covering report creation, retrieval, partial updates,
  image serving, and a list endpoint with 14 filter and sort parameters.
- **AI triage** — every created or updated report is assessed by `gpt-oss:20b` on
  Ollama Cloud, which returns a quality and priority band. Unparseable or failed
  responses fall back to safe defaults, so the API never fails on the LLM's account.
- **Interactive map** — Leaflet map of all reports, re-centred on the selected one.
- **Weather context** — current conditions at a report's coordinates, from Open-Meteo.
- **Analytics** — Plotly charts for report volume over time, category and status
  breakdowns, and resolution time per category.
- **Seeded demo data** — 30 realistic reports across 8 categories and 4 statuses,
  with photos, loaded on first start, so the app is worth looking at immediately.
- **Fully containerised** — database, API and dashboard come up with one command.

## Architecture

```mermaid
flowchart LR
    citizen["Citizen client"]
    api["user_api<br/>Flask REST API"]
    dash["admin_dashboard<br/>Streamlit"]
    repo["db_repository<br/>shared data access"]
    db[("PostgreSQL 18")]
    images[("report-images<br/>Docker volume")]
    ollama["Ollama Cloud<br/>gpt-oss:20b"]
    meteo["Open-Meteo API"]

    citizen -->|"REST /api/v1"| api
    api -->|"quality / priority assessment"| ollama
    api --> repo
    dash --> repo
    repo --> db
    api -->|"stores photos"| images
    dash -->|"reads photos"| images
    dash -->|"weather at report location"| meteo
```

`db_repository` is a shared package that both services import: all SQL lives there,
so the API and the dashboard never talk to PostgreSQL directly. Report photos are
written by the API to a Docker volume that the dashboard reads them back from.

## Tech stack

Python 3.14 · Flask · Streamlit · PostgreSQL 18 · psycopg 3 · pandas · Plotly ·
Leaflet · Open-Meteo · Ollama Cloud · Docker Compose

## API

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/v1/healthcheck` | Liveness probe |
| GET | `/api/v1/categories` | List report categories |
| GET | `/api/v1/statuses` | List report statuses |
| POST | `/api/v1/reports` | Create a report |
| GET | `/api/v1/reports` | List, filter and sort reports |
| GET | `/api/v1/report/<ticket_id>` | Fetch a single report |
| PATCH | `/api/v1/report/<ticket_id>` | Update a report |
| GET | `/api/v1/report-images/<ticket_id>` | Serve a report's image |


## Getting started

### Prerequisites

- Docker and Docker Compose
- Optional: an [Ollama Cloud](https://ollama.com) API key for the AI assessment.
  Without one, reports get the default assessment (`normal` quality, `medium` priority).
- Python 3.12 or newer, only to run the tests

### Configure

All commands are run from the `code/` directory, where `compose.yaml` lives.

```bash
cd code
cp example.env .env
```

Then edit `.env`:

```
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<choose-a-password>
OLLAMA_API_KEY=<your-ollama-cloud-api-key>
API_BASE_URL=http://localhost:5000
```

### Run

```bash
docker compose up --build -d
```

Then open:

- **Admin dashboard:** http://localhost:8501
- **REST API:** http://localhost:5000 (e.g. http://localhost:5000/api/v1/healthcheck)

To stop the services:

```bash
docker compose down
```

To stop **and wipe the database and images** (start from scratch on the next
`up`, re-running the seed script):

```bash
docker compose down -v
```

### Test

The suite covers the API's request validation. It stubs the database lookups, so
it needs no running services, network or credentials. From the `code/` directory:

```bash
python -m venv .venv
```

Activate it: `.venv\Scripts\activate` on Windows, `source .venv/bin/activate` on
macOS/Linux. Then:

```bash
pip install -r user_api/requirements.txt -r admin_dashboard/requirements.txt -r requirements-dev.txt
pytest
```

<details>
<summary>Managing dependencies</summary>

Dependencies are pinned with [pip-tools](https://github.com/jazzband/pip-tools).
From the `code/` directory:

```bash
pip install pip-tools
pip-compile user_api/requirements.in admin_dashboard/requirements.in requirements-dev.in -o constraints.txt
for txt in user_api/requirements admin_dashboard/requirements requirements-dev; do
  pip-compile "$txt.in" -c constraints.txt -o "$txt.txt"
done
```

</details>

## Credits

- Weather data from [Open-Meteo](https://open-meteo.com/).
- Map tiles from [Stadia Maps](https://stadiamaps.com/), © OpenMapTiles, © OpenStreetMap contributors.
- Triage model `gpt-oss:20b`, served by [Ollama Cloud](https://ollama.com).

This project is not affiliated with or endorsed by any of them. Their services and data
remain with their owners and are not covered by the MIT license.

## License

Released under the [MIT License](LICENSE). The demo report photos in
`code/demo-report-images/` are original or AI-generated for this project and are
covered by the same license.
