# Document-processing runbook

## What these services do

- **RabbitMQ** is the queue: it temporarily holds commands for background work.
- A **Celery worker** is a separate process that takes a command from RabbitMQ
  and performs it. Here it extracts text from a document.
- The **outbox** is a PostgreSQL table holding a command that has not yet been
  sent to RabbitMQ. It prevents a document-processing command from being lost
  while RabbitMQ is unavailable.
- **Flower** is a local web page for observing workers and tasks. It does not
  store the document's real state; PostgreSQL does.

## Start the project

```powershell
docker compose up -d --build
```

Check that PostgreSQL, Redis, RabbitMQ, API, worker, and Beat are running:

```powershell
docker compose ps
```

## Open Flower

The local secret is stored in `.env.flower`, which is ignored by Git.
Change it there if another person can use your computer.

```powershell
docker compose --profile tools up -d flower
```

Open <http://localhost:5555> and sign in with the credentials from
`.env.flower`.

Flower is available only from this computer because Compose binds its port to
`127.0.0.1`. It can show task events and exposes Prometheus-compatible
metrics at <http://localhost:5555/metrics>.

## Inspect logs

```powershell
docker compose logs -f app
docker compose logs -f worker
docker compose logs -f beat
```

Important worker log events:

- `outbox_messages_published`: pending outbox rows were sent to RabbitMQ.
- `document_processing_started`: a worker claimed the document.
- `document_processing_completed`: extracted text and `COMPLETED` were
  saved in PostgreSQL.
- `document_processing_transient_error`: a temporary storage failure will be
  retried with a bounded delay.
- `document_processing_retries_exhausted`: retry limit was reached and the
  document was marked `FAILED`.

## RabbitMQ queue dashboard

Open <http://localhost:15672>. The username and password are defined locally
in `compose.yaml`. Use it only for development.

## Check database migrations

```powershell
uv run alembic current
uv run alembic check
```

## Verify that RabbitMQ recovery does not lose a document

This is an **outage drill**: a deliberate, short service failure used to prove
that the recovery path works.

1. Start the project and upload a small `.txt` document through Swagger
   (<http://localhost:8000/docs>) or the API.
2. Stop RabbitMQ before uploading another document:

   ```powershell
   docker compose stop rabbitmq
   ```

3. Upload the document. The API must still return `201 Created`; its
   PostgreSQL status is `PENDING`.
4. Restore RabbitMQ:

   ```powershell
   docker compose up -d rabbitmq
   ```

5. Wait up to one Beat interval (currently 10 seconds), then fetch the
   document. It must become `COMPLETED`.

Why this works: the API saved both `Document` and its outbox row in one
PostgreSQL transaction. After RabbitMQ returns, Beat runs the outbox publisher,
which sends the waiting command to the worker.

## Check retry behavior safely

Do not change permissions or delete files from the shared Docker volume just
to create an error. The focused tests simulate temporary and permanent storage
failures without damaging real documents:

```powershell
uv run pytest -q tests/test_document_processing.py tests/test_document_task.py
```

Temporary `OSError` failures are retried at most three times. Missing files
and permission errors are permanent failures: the worker marks the document
`FAILED` without pointless retries.

## Full verification before a commit

```powershell
uv run pytest -q
uv run alembic current
uv run alembic check
```
