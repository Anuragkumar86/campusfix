# Design Decisions, Assumptions and Deviations

The requirements document leaves some values open ("TBD") or allows implementation choices.
This file records what was decided so that code, report and presentation stay aligned.

| # | Topic | Decision | Reason |
|---|---|---|---|
| 1 | Login identifier | **E-mail address** (case-insensitive); `username` field removed | SRS requires not revealing which account exists; e-mail is natural for a campus system |
| 2 | SLA durations | Sample values in `settings.SLA_TARGETS` (e.g. Urgent 1 h response / 8 h resolution; Medium 8 h / 72 h; calendar hours) | SRS says durations are TBD. **Not real policy** - change in one place |
| 3 | Default priority | `MEDIUM` for new tickets; only manager/admin change it | SRS: priority is not student-controlled |
| 4 | Ticket number | `CF-<year>-<id padded to 6>`; sequence does not reset yearly | SRS: "exact format may be finalised" |
| 5 | Upload limit | 5 MB; JPEG, PNG, WEBP, GIF | SRS: size/types TBD - sample values via `MAX_UPLOAD_SIZE` / `ALLOWED_IMAGE_FORMATS` |
| 6 | First response | First action by someone other than the reporter (assignment, status change or comment) | Needed to evaluate the response deadline |
| 7 | Reopen | Restarts the SLA clock (`sla_started_at`) and clears first response/resolved/closed timestamps | Reopened work needs fresh deadlines |
| 8 | Reassigning an in-progress ticket | Returns to `ASSIGNED` for the new person | New assignee must explicitly start work |
| 9 | Unassign | Manager/admin: `ASSIGNED -> OPEN` via the status endpoint, active assignment closed | Needed to return a ticket to the queue |
| 10 | Extra fields | `Ticket.resolution_note`, `Ticket.sla_started_at` | Students must see resolution details; SLA clock tracking |
| 11 | Administrator in Next.js | Administrators use the manager screens (all departments) plus a link to Django Admin | SRS: Django Admin is the primary admin interface |
| 12 | Staff list scope | Assigned tickets **and** tickets the staff member reported themselves | SRS permission matrix: "if also reporter" |
| 13 | Assignment notes | Hidden from reporter-only viewers in history/detail | They are manager-to-staff instructions |
| 14 | Priority change | Not allowed on Resolved/Closed tickets (409) | Meaningless after completion |
| 15 | Demo accounts | Created only by `seed_demo_data`; shared demo password from `DEMO_PASSWORD` | Local demonstration only |
| 16 | Frontend versions | Next.js 16 / React 19 / Tailwind 3.4 / TypeScript 5 / Vitest 5 (needs Node 22+) | Verified together; `npm audit` reported 0 vulnerabilities when built |
| 17 | Screenshots | Not included (cannot be captured without a real browser session); capture list in `docs/screenshots/README.md` | SRS forbids fake artefacts |
