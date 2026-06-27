# Pulse AI — Patient Note App (backend)

> A Django REST backend that turns recorded therapy sessions into searchable
> transcripts and AI-generated summaries, so clinicians spend less time writing
> notes and more time with patients.

[![Built with Django](https://img.shields.io/badge/Django-4.2-092E20?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![DRF](https://img.shields.io/badge/DRF-3.15-A30000?logo=django&logoColor=white)](https://www.django-rest-framework.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## What it does

Pulse AI is the API and orchestration layer for an AI-assisted clinical-notes
product. A therapist uploads the audio recording of a session; the backend
stores it, hands it off to an asynchronous worker for **speech-to-text
transcription** and **summarization**, and then exposes the resulting transcript
and summary back to the therapist as downloadable files.

**The problem it solves.** Writing up session notes is slow, manual, and easy to
put off. Automating transcription and summarization gives clinicians a draft of
every session's notes within minutes of finishing it.

> **Scope note.** This repository is the **backend / API** only. The actual
> AI processing (speech-to-text + summarization) runs in a **separate worker
> service** that consumes an AWS SQS queue and is *not* part of this repo. This
> service is responsible for storage, auth, queueing the job, and ingesting the
> worker's results.

---

## Key features

All of the following are implemented in this codebase:

- **Email-first authentication.** Custom `User` model (no username; email is the
  login identifier) built on Django's `AbstractUser`, with Argon2 password
  hashing.
- **JWT + token auth.** Login issues SimpleJWT access/refresh tokens plus a DRF
  auth token; endpoints for register, login, change password, account deletion,
  and "me".
- **Profile pictures** with server-side validation (max 5 MB, max 8192×8192,
  JPEG/PNG only).
- **Therapy session management.** Upload session audio (MIME-sniffed with
  `python-magic`, max 50 MB), list/retrieve your own sessions, with a
  `pending → done / failed` status lifecycle.
- **Ownership-scoped access.** Querysets are filtered to the authenticated
  therapist; an `IsOwnerOrReadOnly` permission guards object access (IDOR-safe by
  design).
- **Async processing pipeline.** Creating a session enqueues a `speech-to-text`
  job on AWS SQS. An external worker transcribes + summarizes the audio and
  POSTs the results back to a secured callback endpoint.
- **Secured ingestion webhook.** `/session-data/<id>/` accepts the worker's
  transcript + summary files (or an error report), authenticated with a shared
  `X-API-KEY`.
- **S3-backed storage** via `django-storages`, with short-lived **presigned
  download URLs** generated through a singleton boto3 client.
- **OpenAPI 3 schema + Swagger UI** via `drf-spectacular`.

---

## Tech stack

| Area | Choice |
|---|---|
| Language / runtime | Python 3.12 |
| Web framework | Django 4.2, Django REST Framework 3.15 |
| Auth | `djangorestframework-simplejwt`, DRF tokens, `django-allauth`, Argon2 |
| Database | PostgreSQL (`psycopg` 3) |
| Object storage | AWS S3 via `django-storages` + `boto3` |
| Async / queue | AWS SQS (Celery configured with an SQS broker) |
| Cache | Redis via `django-redis` (configured, currently using LocMem) |
| API docs | `drf-spectacular` (OpenAPI + Swagger UI) |
| File validation | `python-magic` (MIME sniffing), Pillow |
| Tooling | pre-commit (Ruff lint+format, djLint, django-upgrade), mypy, pytest |
| Docs | Sphinx + Read the Docs config |
| Serving | Gunicorn |
| Project template | [cookiecutter-django](https://github.com/cookiecutter/cookiecutter-django) |

---

## Architecture

```
  Therapist (client)
        │  1. POST audio  (JWT auth, multipart)
        ▼
 ┌──────────────────────┐    2. store audio     ┌────────────┐
 │  Django REST API      │ ────────────────────▶ │  AWS S3     │
 │  (this repository)    │                       └────────────┘
 │                       │    3. enqueue job
 │  TherapistSessionView │ ───────────────────▶ ┌────────────┐
 └──────────────────────┘   {audio_url, id}     │  AWS SQS    │
        ▲                                         └─────┬──────┘
        │  6. presigned download URLs                  │ 4. consume
        │     (transcript + summary)                   ▼
        │                                       ┌──────────────────┐
        │  5. POST results  (X-API-KEY)         │  Worker service  │
        └────────────────────────────────────── │  (separate repo) │
           /session-data/<id>/                  │  STT + summarize │
                                                 └──────────────────┘
```

### Data model

| Model | Purpose | Notable fields |
|---|---|---|
| `User` | Email-based account | `email` (unique, login), `name`, `profile_picture` |
| `TherapistSession` | One uploaded session | `therapist` (FK), `session_name`, `session_audio`, `status` (`pending`/`done`/`failed`) |
| `Transcription` | STT output for a session | `session` (FK), `transcription_text_file` |
| `Summary` | Summary for a session | `session` (FK), `summary_text_file` |
| `Error` | Worker failure record | `session` (FK), `error_message`, `error_code` |

A `TherapistSession` has many transcriptions, summaries, and errors. Audio,
transcripts, and summaries are stored in S3 and served as presigned URLs.

### Selected endpoints

| Method | Path | Description | Auth |
|---|---|---|---|
| `POST` | `/users/register` | Register a new user | public |
| `POST` | `/users/login` | Log in, returns JWT + token | public |
| `PATCH` | `/users/password` | Change password | JWT |
| `PATCH` | `/users/picture` | Update profile picture | JWT |
| `POST` | `/auth-token/` | DRF obtain-token | public |
| `GET/POST` | `/api/therapist_session/` | List/create owned sessions | JWT |
| `GET/PUT/DELETE` | `/api/therapist_session/<id>/` | Retrieve/update/delete a session | JWT (owner) |
| `GET` | `/api/users/me/` | Current user | JWT |
| `POST` | `/session-data/<session_id>/` | Worker callback (results / error) | `X-API-KEY` |
| `GET` | `/api/schema/`, `/api/docs/` | OpenAPI schema & Swagger UI | per config |
| — | `/admin/`, `/accounts/` | Django admin, allauth | — |

---

## Project structure

```
patient-note-app/
├── config/                       # Django project configuration
│   ├── settings/
│   │   ├── base.py               # shared settings (apps, DB, S3, SQS, JWT…)
│   │   └── production.py         # production overrides
│   ├── urls.py                   # root URL conf
│   └── api_router.py             # DRF router (users, therapist_session)
├── pulse_ai/                     # application packages
│   ├── users/                    # custom user, auth API, request-logging middleware
│   │   ├── models.py
│   │   ├── api/{serializers,views}.py
│   │   ├── middleware.py
│   │   └── migrations/
│   ├── therapist_session/        # sessions, transcripts, summaries, errors
│   │   ├── models.py
│   │   ├── api/{serializers,views}.py
│   │   ├── s3_client.py          # singleton boto3 S3 client
│   │   ├── validators.py         # audio MIME validation
│   │   └── migrations/
│   └── templates/
├── .github/workflows/deploy.yml  # CI: SSH deploy on push to pulse_ai
├── .pre-commit-config.yaml       # Ruff, djLint, django-upgrade hooks
├── .readthedocs.yml              # Sphinx docs build config
├── requirements.txt
├── .env.example                  # template for required environment variables
└── LICENSE
```

---

## Getting started

> **Heads-up (see [Project status](#project-status)).** This repository contains
> the application code (settings, apps, models, API), but a few standard Django
> bootstrap files that cookiecutter-django normally generates are **not committed
> here** — notably `manage.py`, `config/wsgi.py`, `config/settings/__init__.py`
> and `local.py`, the per-package `__init__.py` / `apps.py`, and a couple of
> `users` helpers (`managers.py`, `adapters.py`, `forms.py`). You will need to
> supply those (e.g. by scaffolding a cookiecutter-django project) before the
> server will boot. The commands below describe the intended workflow.

### Prerequisites

- Python 3.12
- PostgreSQL
- An AWS account with an S3 bucket and an SQS queue (the S3 credentials are
  read at startup and have no defaults)
- `libmagic` installed on the host (for `python-magic`)

### 1. Clone and create a virtual environment

```bash
git clone https://github.com/AjaxAueleke/patient-note-app.git
cd patient-note-app
python3.12 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# then edit .env and fill in DB, S3 and SQS credentials
```

### 4. Run migrations and start the server

```bash
export DJANGO_SETTINGS_MODULE=config.settings.base   # or config.settings.production
python manage.py migrate
python manage.py runserver
```

API docs will be available at `http://127.0.0.1:8000/api/docs/`.

---

## Development

```bash
pre-commit install        # set up the Ruff / djLint / django-upgrade hooks
pre-commit run --all-files
pytest                    # test runner is configured (pytest-django)
```

---

## Project status

This is a **portfolio / work-in-progress** project that demonstrates a real,
non-trivial Django REST backend: custom auth, S3-backed media with presigned
URLs, an async SQS processing pipeline, and a secured ingestion webhook.

What's present is the **application logic** — settings, URL routing, the two app
packages (`users`, `therapist_session`), their models/serializers/views,
migrations, and the worker-callback API. Some of the boilerplate that
cookiecutter-django generates (the `manage.py` entry point, WSGI/ASGI modules, a
local settings module, package `__init__.py` / `apps.py` files, and a few
`users` helper modules referenced in settings) is **not committed in this
repository**, so it is not runnable as a standalone checkout without
regenerating that scaffolding.

All committed Python modules are syntactically valid (verified with
`python -m py_compile`).

---

## License

Released under the [MIT License](LICENSE).
