# Progressively Enhanced Issue Tracker with Django and HTMX

A modern, resilient web application for managing and tracking software issues, built using **Django**, **PostgreSQL**, and **HTMX**, containerized with **Docker** and **Docker Compose**.

This application is designed following the principles of **Progressive Enhancement**:
- **Baseline Layer**: Fully functional without JavaScript enabled, utilizing standard Django Server-Side Rendering (SSR) and HTTP POST redirects (302).
- **Enhancement Layer**: When JavaScript is available, HTMX intercepts interactions and issues AJAX requests with the `HX-Request: true` header. The server responds with targeted HTML fragments (200 OK) that HTMX swaps directly into the DOM without a full page reload.

---

## Architecture & System Design

### Progressive Enhancement Flow

```
+-------------------------------------------------------------+
|                       User Browser                          |
|  (User clicks "Move to Done" or submits a comment)          |
+-------------------------------------------------------------+
                              |
                              | HTTP POST Request
                              v
+-------------------------------------------------------------+
|                        Django View                          |
|         Does the request contain 'HX-Request' header?       |
+-------------------------------------------------------------+
               /                              \
       NO (Standard SSR)               YES (Enhanced HTMX)
             /                                  \
            v                                    v
+------------------------+             +------------------------+
| 302 Redirect to        |             | 200 OK with HTML       |
| full board / detail    |             | partial fragment only  |
| page                   |             | (_issue_card.html)     |
+------------------------+             +------------------------+
            |                                    |
            v                                    v
+------------------------+             +------------------------+
| Browser reloads page   |             | HTMX swaps fragment    |
| and renders full state |             | into DOM in-place      |
+------------------------+             +------------------------+
```

### Trade-offs: SSR + HTMX vs. Single Page Applications (SPA)

| Metric / Dimension | Django + HTMX (Progressive Enhancement) | Traditional SPA (React/Vue/Angular) |
| :--- | :--- | :--- |
| **Resilience & Accessibility** | High. Fully operational if JS fails, is disabled, or blocked by corporate firewalls. | Low. If the JavaScript bundle fails to parse or download, the app is unusable. |
| **Architectural Complexity** | Low. Single unified codebase; business logic and state management stay on the server. | High. Separate backend API, duplicate validation logic, complex client-side state managers (Redux/Pinia). |
| **First Contentful Paint (FCP)** | Instant. Pure server-rendered HTML is rendered immediately by the browser. | Slower. Requires downloading large JS bundles, parsing scripts, and fetching data via JSON APIs. |
| **SEO & Crawlability** | Native. Search engines parse HTML directly without requiring headless browsers. | Requires complex Server-Side Rendering (SSR) or Hydration infrastructure (Next.js/Nuxt). |
| **Developer Velocity** | Very high for data-heavy and CRUD workflows. | Slower due to maintaining dual models, DTOs, serializers, and frontend routing. |

---

## Database Schema

The database uses PostgreSQL with the following core relational models:

### 1. `tracker_project`
- `id` (BigInt, Primary Key)
- `name` (Varchar(255))
- `description` (Text)
- `created_at` (Timestamp with time zone)

### 2. `tracker_issue`
- `id` (BigInt, Primary Key)
- `title` (Varchar(255))
- `description` (Text)
- `status` (Varchar(50), Choices: `'To Do'`, `'In Progress'`, `'Done'`)
- `project_id` (ForeignKey to `tracker_project`, CASCADE)
- `created_at` (Timestamp with time zone)
- `updated_at` (Timestamp with time zone)

### 3. `tracker_comment`
- `id` (BigInt, Primary Key)
- `content` (Text)
- `issue_id` (ForeignKey to `tracker_issue`, CASCADE)
- `created_at` (Timestamp with time zone)

---

## Key Endpoints

| Method | Endpoint | Description | Standard Mode | HTMX Enhanced Mode |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/` | Home / Project List | Full HTML (200 OK) | Full HTML (200 OK) |
| `GET` | `/projects/` | All Projects Overview | Full HTML (200 OK) | Full HTML (200 OK) |
| `GET` | `/projects/<id>/` | Project Kanban Board | Full HTML (200 OK) grouped by status | Full HTML (200 OK) |
| `POST` | `/projects/<id>/issues/create/` | Create a new Issue | 302 Redirect to board | 302 Redirect to board |
| `GET` | `/issues/<id>/` | Issue Detail & Discussion | Full HTML (200 OK) | Full HTML (200 OK) |
| `POST` | `/issues/<id>/update-status/` | Update issue status | 302 Redirect to board | **200 OK Partial Fragment** (`_issue_card.html`) |
| `POST` | `/issues/<id>/status/` | Status update alias | 302 Redirect to board | **200 OK Partial Fragment** (`_issue_card.html`) |
| `POST` | `/issues/<id>/comments/add/` | Add comment to issue | 302 Redirect to detail | **200 OK Partial Fragment** (`_comment.html`) |
| `GET` | `/health/` | Service Health Check | JSON (`{"status": "ok"}`) | JSON (`{"status": "ok"}`) |

---

## Quick Start with Docker Compose

Running the entire stack requires only Docker and Docker Compose. All migrations, database health checks, and initial seeding occur automatically.

```bash
# 1. Clone the repository and navigate into the workspace
git clone <repo-url>
cd Gpp

# 2. Build and start services in detached mode
docker-compose up --build -d

# 3. Check service health
docker-compose ps
```

The application will be live at `http://localhost:8000/`.

---

## Local Development Setup (Without Docker)

If you prefer to run the application locally with a Python virtual environment:

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Apply database migrations
python manage.py migrate

# 4. Seed initial projects and issues
python manage.py seed_data

# 5. Start the development server
python manage.py runserver 8000
```

---

## Environment Variables Configuration

Copy `.env.example` to `.env` to override configuration:

```bash
cp .env.example .env
```

| Variable | Description | Default in Docker Compose |
| :--- | :--- | :--- |
| `DEBUG` | Enable/Disable Django debug mode | `True` |
| `SECRET_KEY` | Secret cryptographic key for Django | `production-super-secret-key...` |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hostnames | `localhost,127.0.0.1,0.0.0.0,web` |
| `DATABASE_URL` | Complete connection string for PostgreSQL | `postgres://tracker_user:tracker_pass@db:5432/tracker_db` |
| `POSTGRES_DB` | PostgreSQL database name | `tracker_db` |
| `POSTGRES_USER` | PostgreSQL user | `tracker_user` |
| `POSTGRES_PASSWORD`| PostgreSQL password | `tracker_pass` |
| `POSTGRES_HOST` | Database host | `db` |
| `POSTGRES_PORT` | Database port | `5432` |

---

## Running the Test Suite

The test suite validates both standard requests and progressively enhanced HTMX requests:

```bash
# Run tests inside local virtual environment
python manage.py test

# Or run tests inside Docker container
docker-compose exec web python manage.py test
```

### Verified Scenarios:
1. Database Schema introspection (verifies `tracker_project`, `tracker_issue`, `tracker_comment` tables, columns, and foreign keys).
2. Project board SSR: `GET /projects/{project_id}/` renders full HTML document with distinct sections ('To Do', 'In Progress', 'Done') and issue titles.
3. Standard Issue creation: `POST /projects/{project_id}/issues/create/` returns `302 Found` redirect and inserts record into database.
4. Standard Status update: `POST /issues/{issue_id}/update-status/` returns `302 Found` redirect and updates status in database.
5. Standard Comment submission: `POST /issues/{issue_id}/comments/add/` returns `302 Found` redirect and creates comment row.
6. Enhanced Status update: `POST /issues/{issue_id}/update-status/` with `HTTP_HX_REQUEST='true'` returns `200 OK` with only the HTML fragment (no `<html>` or `<body>`).
7. Enhanced Comment submission: `POST /issues/{issue_id}/comments/add/` with `HTTP_HX_REQUEST='true'` returns `200 OK` with only the comment HTML fragment.
8. Request Differentiating: Tests the exact same endpoint with and without `HX-Request` header, asserting `302 Redirect` vs `200 OK Partial Fragment`.

---

## Automated Database Seeding

The application automatically seeds initial data on startup through:
1. **Django Data Migration**: `tracker/migrations/0002_seed_initial_data.py` runs automatically during `migrate`.
2. **Custom Management Command**: `python manage.py seed_data` is also executed in the container entrypoint to guarantee data idempotency.

Default Seed Data Includes:
- **Project 1 (Core Platform)**: Issues spanning 'To Do', 'In Progress', and 'Done', along with comments.
- **Project 2 (Mobile Application)**: Cross-platform mobile client issues.
- **Project 3 (Cloud Infrastructure)**: DevOps & CI/CD pipeline issues.

---

## License

MIT License. Designed and developed with Django and HTMX.
