# UniSpace Backend

REST backend for **UniSpace**, an academic university-space reservation system developed for the **Secure Software Design** course at the University of Calabria (UniCal).

The backend provides authentication, authorization, domain models and REST endpoints consumed by both the web application and the terminal client.

> **Project status:** completed academic project. This repository is kept as a portfolio/reference snapshot and is not actively maintained.

## Project ecosystem

UniSpace is split across three repositories:

- [`backend`](https://github.com/UniSpace-SSD/backend) — this repository
- [`web-frontend`](https://github.com/UniSpace-SSD/web-frontend) — SvelteKit/TypeScript web client
- [`tui`](https://github.com/UniSpace-SSD/tui) — Python terminal client

## Core functionality

The backend models and exposes functionality around:

- user registration, login and logout
- user profiles
- `student` and `professor` roles
- university departments
- buildings and reservable spaces
- room, laboratory, auditorium, meeting-room and library space types
- reservation creation and cancellation
- reservation approval workflows
- role- and ownership-aware authorization
- administrative management through Django
- OpenAPI / Swagger / ReDoc documentation

Reservations can move through the following states:

```text
PENDING -> CONFIRMED
       \-> CANCELLED
```

Professor-level reservation management is restricted according to the authorization rules implemented by the API, while users can access and manage their own reservations.

## Tech stack

- **Python 3.13**
- **Django 5.2**
- **Django REST Framework**
- **dj-rest-auth**
- **django-allauth**
- **drf-yasg**
- **django-cors-headers**
- **pytest / pytest-django**
- **coverage / pytest-cov**
- **Poetry**

## Main Django apps

```text
UniSpace/       # project configuration, authentication and root URLs
spaces/         # departments, buildings, spaces, permissions and API endpoints
reservations/   # reservation model, status workflow, permissions and API endpoints
userProfile/    # custom user model and registration/profile data
```

## Getting started

### Prerequisites

- Python 3.13
- Poetry

### Install dependencies

```bash
poetry install
```

### Run database migrations

```bash
poetry run python manage.py migrate
```

### Optional: create an administrator

```bash
poetry run python manage.py createsuperuser
```

### Start the development server

```bash
poetry run python manage.py runserver
```

The API is then available under:

```text
http://127.0.0.1:8000/api/
```

## API documentation

With the development server running:

- Swagger UI: `http://127.0.0.1:8000/swagger/`
- ReDoc: `http://127.0.0.1:8000/redoc/`
- OpenAPI schema: `http://127.0.0.1:8000/schema/`

Authentication endpoints are exposed under:

```text
/api/auth/
```

with registration under:

```text
/api/auth/registration/
```

The `spaces` and `reservations` apps expose their endpoints below `/api/`.

## Authentication and authorization

UniSpace uses token-based authentication through `dj-rest-auth`.

Authorization is enforced on the backend. In particular:

- read-only access to space data is available through safe HTTP methods
- modifications to spaces require staff/superuser privileges
- reservation object access is restricted to authorized users
- reservation owners can access their own reservations
- professors can manage eligible student reservations within the relevant department
- staff and superusers receive elevated permissions

These controls are implemented through custom Django REST Framework permission classes.

## Testing

Run the test suite with:

```bash
poetry run pytest
```

Coverage support is configured through `coverage`, `pytest-cov` and `.coveragerc`.

## Academic context

UniSpace was built as a two-person project for the **Secure Software Design** course at the **University of Calabria**. The architecture separates the backend from its clients so that the same API can be consumed by both a SvelteKit web application and a Python terminal interface.

The project focuses on API design, validation, authentication/authorization, role-based behaviour and automated testing.

## Contributors

- [Ronnie2603](https://github.com/Ronnie2603)
- [Shadowz-git](https://github.com/shadowz-git)

See the [UniSpace-SSD organization](https://github.com/UniSpace-SSD) for the complete project.
