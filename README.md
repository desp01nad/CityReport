# City Report

## Prerequisites

- Docker and Docker Compose
- An Ollama Cloud API key (https://ollama.com) for the AI assessment subsystem

## Configuration

All commands are run from the `code/` directory, where `compose.yaml` lives.

1. Create the environment file from the example and fill in the values:

   ```bash
   cd code
   cp example.env .env
   ```

2. Edit `.env`:

   ```
   POSTGRES_DB=postgres
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=<choose-a-password>
   OLLAMA_API_KEY=<your-ollama-cloud-api-key>
   ```

## Running the app

From the `code/` directory:

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
