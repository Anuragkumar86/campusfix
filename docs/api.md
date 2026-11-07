# CampusFix - API Reference

Base URL (development): `http://localhost:8000`. All bodies are JSON unless noted (ticket creation and
attachments use `multipart/form-data`).

## Authentication method

Django **session cookie** (`sessionid`, HttpOnly). Browsers must send `credentials: "include"`.
Unsafe methods (POST, PATCH) must include header **`X-CSRFToken`** with the token from `GET /api/auth/csrf/`.

## Error conventions

| Status | Meaning | Body example |
|---|---|---|
| 400 | Validation error | `{"title": ["This field may not be blank."]}` or `{"detail": "Invalid email or password."}` |
| 401 | Not signed in / session expired | `{"detail": "Authentication credentials were not provided."}` |
| 403 | Signed in but not allowed (role/permission/CSRF) | `{"detail": "You do not have permission to perform this action."}` |
| 404 | Not found **or** outside the caller's scope | `{"detail": "No Ticket matches the given query."}` |
| 405 | Method not allowed (no PUT/DELETE on tickets) | `{"detail": "Method \"DELETE\" not allowed."}` |
| 409 | Conflicting state | `{"detail": "A ticket cannot move from OPEN to CLOSED."}` |
| 500 | Server error (no internals leaked) | `{"detail": "A server error occurred."}` |

## Endpoints

### Health and authentication
| Method | URL | Who | Description |
|---|---|---|---|
| GET | `/api/health/` | public | `{"status":"ok"}` |
| GET | `/api/auth/csrf/` | public | Sets `csrftoken` cookie; returns `{"csrfToken": "..."}` |
| POST | `/api/auth/login/` | public (CSRF) | Body `{"email","password"}` -> current user. Same generic 400 for unknown/wrong/inactive. Rate-limited. |
| POST | `/api/auth/logout/` | signed in (CSRF) | 204, session destroyed |
| GET | `/api/auth/me/` | signed in | `{id,email,name,first_name,last_name,role,role_label,department}` |

### Reference data
| Method | URL | Description |
|---|---|---|
| GET | `/api/departments/` | Active departments |
| GET | `/api/categories/` | Active categories (with department) |
| GET | `/api/staff/eligible/?department=<id>` | Active maintenance staff. Manager: own department only. Admin: optional department. Others: 403. |

### Tickets (`/api/tickets/`)
| Method | URL | Who | Description |
|---|---|---|---|
| GET | `/api/tickets/` | any signed-in | Paginated list **within the caller's scope** (see filters) |
| POST | `/api/tickets/` | student, admin | Create (multipart: `title, description, category, building, floor, room_or_area, image?`) |
| GET | `/api/tickets/{id}/` | in scope | Detail incl. attachments, comments, history, `permissions` block |
| PATCH | `/api/tickets/{id}/` | reporter (while OPEN), manager, admin | Edit `title, description, building, floor, room_or_area` only |
| GET | `/api/tickets/{id}/history/` | in scope | Audit trail |
| GET/POST | `/api/tickets/{id}/comments/` | in scope | List / add (`{"message"}`) |
| POST | `/api/tickets/{id}/attachments/` | in scope, not CLOSED | multipart `file` (JPEG/PNG/WEBP/GIF) |
| GET | `/api/tickets/{id}/attachments/{aid}/` | in scope | Image bytes (permission-checked; `nosniff`) |
| POST | `/api/tickets/{id}/assignments/` | manager (own dept), admin | `{"assigned_to": <staff id>, "note"?}` -> 201 + ticket |
| POST | `/api/tickets/{id}/status/` | per transition rules | `{"status","note"?}` |
| POST | `/api/tickets/{id}/priority/` | manager (own dept), admin | `{"priority","note"?}`; deadlines recalculated |

**Scope:** student = own tickets; staff = tickets actively assigned to them (+ own reports); manager = own department
(+ own reports); administrator = all.

**List query parameters:** `page`, `page_size` (max 100, default 20), `search`, `status`, `priority`,
`category` (id or name text), `building`, `created_after`, `created_before` (YYYY-MM-DD), `overdue=true|false`,
`unassigned=true|false`, `ordering` = `created_at`, `updated_at`, `priority`, `due_date` (prefix `-` for descending;
priority sorts by severity, not alphabetically). Invalid values -> 400.

### Dashboard
| Method | URL | Who | Description |
|---|---|---|---|
| GET | `/api/dashboard/summary/` | any signed-in | Role-specific counts (same scope as the list) |
| GET | `/api/dashboard/categories/` | manager, admin | `[{category_id, category, count}]` |
| GET | `/api/dashboard/overdue/` | staff (own work), manager, admin | `{count, results[]}` |

## Sample exchanges

**Create ticket**
```http
POST /api/tickets/            (multipart/form-data, X-CSRFToken: ...)
title=Ceiling fan wobbling&description=Dangerous wobble&category=1&building=Block-B&image=@fan.png
```
```json
201 {"id": 6, "ticket_number": "CF-2026-000006", "status": "OPEN", "priority": "MEDIUM",
     "reporter": {"id": 14, "name": "Student 1", "role": "STUDENT"},
     "department": {"id": 1, "name": "Electrical Maintenance"},
     "permissions": {"can_comment": true, "can_attach": true, "can_assign": false,
                     "can_set_priority": false, "can_edit": true, "available_transitions": []}, "...": "..."}
```

**Assign**
```http
POST /api/tickets/6/assignments/   {"assigned_to": 7, "note": "Check today"}
```
```json
201 {"id": 6, "status": "ASSIGNED", "assigned_to": {"id": 7, "name": "Staff Electrical1"}, "...": "..."}
```

**Invalid transition**
```http
POST /api/tickets/6/status/   {"status": "CLOSED"}
```
```json
409 {"detail": "A ticket cannot move from OPEN to CLOSED."}
```

**Resolve without a note**
```json
400 {"note": ["A resolution note is required."]}
```
