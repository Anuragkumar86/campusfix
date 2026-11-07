# CampusFix - Architecture

## 1. Components

```mermaid
flowchart LR
    subgraph Browser
        UI["Next.js 16 frontend<br/>(React, TypeScript, Tailwind)<br/>http://localhost:3000"]
    end
    subgraph Backend["Django 5.2 backend - http://localhost:8000"]
        API["DRF API<br/>/api/..."]
        ADM["Django Admin<br/>/admin/"]
        DEMO["django_demo<br/>templates, forms, cookies, sessions<br/>/demo/"]
        SVC["tickets.services<br/>(business rules, transactions)"]
        PERM["tickets.permissions<br/>(scope + transition rules)"]
    end
    DB[("PostgreSQL 16")]
    FS[["media/ (uploaded images,<br/>never public)"]]

    UI -- "fetch + session cookie + X-CSRFToken (CORS)" --> API
    API --> PERM
    API --> SVC
    SVC --> DB
    SVC --> FS
    ADM --> DB
    DEMO --> DB
```

| Component | Responsibility |
|---|---|
| **Next.js frontend** | Pages, forms, validation for convenience, role-based navigation, loading/error/empty states. Holds **no** secrets and makes **no** authorization decisions that the server does not repeat. |
| **`accounts`** | Custom `User` (email login, role, department), session login/logout/me/CSRF endpoints, role-to-Group synchronisation (`services.py`), eligible-staff endpoint. |
| **`departments`** | `Department`, `Category` (category -> department routing), read-only reference endpoints. |
| **`tickets`** | `Ticket`, `Assignment`, `Comment`, `TicketHistory`, `Attachment`; `permissions.py` (visibility scope + transition table), `services.py` (create/assign/status/priority/comment/attachment inside transactions), filters, pagination, admin. |
| **`dashboard`** | Role-scoped summary, category counts, overdue list (ORM aggregates). |
| **`django_demo`** | Server-rendered syllabus demonstration area (INT 253 Units II-IV, VI). |
| **PostgreSQL** | System of record; enforces FKs, unique ticket numbers, and *one active assignment per ticket*. |

## 2. Layering inside the backend

```text
HTTP request -> URL -> DRF view/viewset -> serializer (input validation)
                                  |-> permissions.visible_tickets_for(user)   (data scope; 404 outside scope)
                                  |-> services.<operation>()                  (transaction + row lock + rule checks
                                  |                                            + history record in same transaction)
                                  `-> serializer (output)  -> JSON
```

Key rule: **every ticket query starts from `visible_tickets_for(user)`**, so a ticket outside the
caller's scope returns **404** on the detail route and on every sub-resource
(`/history/`, `/comments/`, `/attachments/<id>/` ...). Existence is never revealed.

## 3. Authentication, session and CSRF flow

```mermaid
sequenceDiagram
    participant B as Browser (localhost:3000)
    participant D as Django (localhost:8000)
    B->>D: GET /api/auth/csrf/  (credentials: include)
    D-->>B: Set-Cookie csrftoken + JSON {csrfToken}
    B->>D: POST /api/auth/login/ {email,password} + X-CSRFToken
    D-->>B: 200 user JSON + Set-Cookie sessionid (HttpOnly, SameSite=Lax); CSRF token rotates
    B->>D: GET /api/auth/me/  (cookie sent automatically)
    D-->>B: {id, email, role, department}
    B->>D: POST /api/tickets/ + X-CSRFToken (+ cookie)
    D-->>B: 201 ticket
    B->>D: POST /api/auth/logout/ + X-CSRFToken
    D-->>B: 204 (session destroyed)
```

* Session cookie is **HttpOnly** - JavaScript can never read it. No tokens in `localStorage`.
* All unsafe methods (POST/PATCH) require the `X-CSRFToken` header. The login view enforces CSRF explicitly
  (`csrf_protect`), because DRF only checks CSRF for already-authenticated sessions.
* CORS: exactly one allowed origin (`FRONTEND_ORIGIN`), `Access-Control-Allow-Credentials: true`, no wildcard.
* Unauthenticated -> **401**; authenticated but forbidden -> **403**; outside scope -> **404**;
  invalid transition -> **409**; invalid input -> **400**.

## 4. Ticket state machine

```mermaid
stateDiagram-v2
    [*] --> OPEN: student creates
    OPEN --> ASSIGNED: manager assigns (assignment endpoint)
    ASSIGNED --> ASSIGNED: manager reassigns
    ASSIGNED --> OPEN: manager removes assignment
    ASSIGNED --> IN_PROGRESS: assignee starts work
    IN_PROGRESS --> RESOLVED: assignee/manager (resolution note required)
    RESOLVED --> CLOSED: reporter / manager
    RESOLVED --> REOPENED: reporter / manager (reason required)
    CLOSED --> REOPENED: manager only (reason required)
    REOPENED --> ASSIGNED: manager assigns
```

Reassigning a ticket that is `IN_PROGRESS` returns it to `ASSIGNED` for the new person (documented decision).
Administrators may perform any permitted transition. Anything not drawn is rejected with **409**.

## 5. Data flow diagrams

### 5.1 DFD Level 0 (context)

```mermaid
flowchart LR
    S([Student]) -- "issue report, image, comments, close/reopen" --> P((0<br/>CampusFix))
    P -- "ticket number, status, resolution, history" --> S
    M([Department Manager]) -- "priority, assignment, status actions" --> P
    P -- "queue, dashboards, overdue list" --> M
    F([Maintenance Staff]) -- "progress, comments, resolution note" --> P
    P -- "assigned work, deadlines" --> F
    A([Administrator]) -- "users, roles, departments, categories" --> P
    P -- "audit data, system records" --> A
```

### 5.2 DFD Level 1

```mermaid
flowchart TB
    S([Student]) --> P1["1.0 Authenticate<br/>(session + CSRF)"]
    M([Manager]) --> P1
    F([Staff]) --> P1
    A([Administrator]) --> P1
    P1 <--> D1[("D1 Users / Groups")]

    S --> P2["2.0 Report issue"]
    P2 --> D2[("D2 Tickets")]
    P2 --> D5[("D5 Attachments / media")]
    P2 --> D4[("D4 Ticket history")]
    D6[("D6 Departments / Categories")] --> P2

    M --> P3["3.0 Prioritise and assign"]
    P3 <--> D2
    P3 --> D3[("D3 Assignments")]
    P3 --> D4
    D1 --> P3

    F --> P4["4.0 Work and resolve"]
    P4 <--> D2
    P4 --> D7[("D7 Comments")]
    P4 --> D4

    S --> P5["5.0 Review resolution<br/>close / reopen"]
    P5 <--> D2
    P5 --> D4

    D2 --> P6["6.0 Dashboards, search, overdue"]
    D3 --> P6
    P6 --> M
    P6 --> F
    P6 --> S
```

## 6. Security measures implemented

Server-side authorization on every endpoint; object-level scope; server-derived reporter and department;
ORM only (no raw SQL); DRF serializer validation; upload size + real-image (Pillow) check + generated
file names + `X-Content-Type-Options: nosniff`; uploads served only through a permission-checked endpoint;
generic login errors (no account enumeration) and login rate limit; HttpOnly + SameSite session cookie;
CSRF on unsafe requests; strict CORS; secrets only in environment variables; append-only history;
`PROTECT` foreign keys so referenced users/departments/categories cannot be hard-deleted.
