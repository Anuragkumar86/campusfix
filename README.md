# CampusFix

Campus issue reporting and resolution platform (INT 253 Django project).
Students report maintenance issues; department managers prioritise and assign them; maintenance staff work and
resolve them; everyone sees status, history and deadlines. Administrators manage the system through Django Admin.

> **Start here:** [`SETUP_AND_TESTING_GUIDE.md`](SETUP_AND_TESTING_GUIDE.md) - complete step-by-step installation, run and test instructions.

## Technology stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS 3.4 |
| Backend | Python 3.12, Django 5.2, Django REST Framework 3.18, django-filter, django-cors-headers |
| Database | PostgreSQL 16 (psycopg 3) |
| Auth | Django session authentication + CSRF protection (HttpOnly cookie) |
| Uploads | Pillow validation; files stored under `backend/media/` (served only via authorised API) |
| Tests | Django test framework + DRF `APITestCase` (106 tests); Vitest (12 tests) |

## Features

* Four roles with server-enforced permissions: Student, Maintenance Staff, Department Manager, Administrator.
* Ticket lifecycle `OPEN -> ASSIGNED -> IN_PROGRESS -> RESOLVED -> CLOSED / REOPENED` with a validated transition table.
* Unique ticket numbers (`CF-2026-000001`), category-to-department routing, optional image attachment.
* Assignment and reassignment with preserved assignment history; one active assignment per ticket enforced by PostgreSQL.
* Comments, append-only audit history, priority and SLA deadlines (sample values), overdue detection.
* Search, filters, sorting, pagination; role-specific dashboards, category report, overdue list.
* Django Admin with groups and permissions; `/demo/` area covering templates, forms, `re_path`, cookies, sessions, login/logout.
* Responsive, keyboard-accessible UI with loading, error and empty states.

## Repository layout

```text
campusfix/
|-- backend/      Django project (config/, apps/accounts|departments|tickets|dashboard|django_demo, templates/)
|-- frontend/     Next.js app (app/, components/, lib/, types/)
|-- docs/         requirements, architecture (+DFDs), database design (ER), API, syllabus checklist, notes
|-- scripts/      e2e_smoke_test.py (browser-like API workflow check)
|-- docker-compose.yml   optional local PostgreSQL
`-- SETUP_AND_TESTING_GUIDE.md
```

## Quick start (summary - full details in the guide)

```bash
docker compose up -d db                       # or install PostgreSQL natively (see guide)

cd backend
python -m venv venv && source venv/bin/activate      # Windows: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env                                  # Windows: copy .env.example .env
python manage.py migrate
python manage.py seed_demo_data
python manage.py test                                 # 106 tests
python manage.py runserver 8000

# second terminal
cd frontend
npm install
cp .env.example .env.local                            # Windows: copy .env.example .env.local
npm run dev                                           # http://localhost:3000
```

## Environment variables

Backend (`backend/.env`, see `.env.example`): `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `DATABASE_URL`,
`FRONTEND_ORIGIN`, `CSRF_TRUSTED_ORIGINS`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SESSION_COOKIE_AGE`,
`MEDIA_ROOT`, `MAX_UPLOAD_SIZE`, `DEMO_PASSWORD`.
Frontend (`frontend/.env.local`): `NEXT_PUBLIC_API_BASE_URL` (public value only).
Never commit real `.env` files. In production set `DJANGO_DEBUG=False`, a strong `DJANGO_SECRET_KEY`, HTTPS, and both `*_COOKIE_SECURE=True`.

## Test commands

| What | Command |
|---|---|
| Backend (all) | `cd backend && python manage.py test` |
| One app | `python manage.py test apps.tickets` |
| Frontend unit tests | `cd frontend && npm test` |
| Frontend type check | `npm run typecheck` |
| Frontend production build | `npm run build` |
| Live end-to-end workflow | `python scripts/e2e_smoke_test.py` (servers running, `pip install requests`) |

## Demo accounts policy

Demo users are created **only** by `python manage.py seed_demo_data` for local demonstration. They use the `@campusfix.test`
domain and a shared password taken from `DEMO_PASSWORD` (default `CampusFix@123`). Never create or keep these accounts in a real deployment.
The full account list is in the setup guide.

## Documentation

[`docs/architecture.md`](docs/architecture.md) (components, flows, DFDs, state machine) -
[`docs/database-design.md`](docs/database-design.md) (ER diagram) - [`docs/api.md`](docs/api.md) -
[`docs/design-decisions.md`](docs/design-decisions.md) (assumptions and deviations) - [`docs/screenshots/`](docs/screenshots/README.md)


