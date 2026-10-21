---
name: Local Django test database
description: How to avoid the injected workspace PostgreSQL URL when running the local test suite.
---

For local Django test runs in this workspace, set `DATABASE_URL=` so settings use the project's SQLite test database. The injected PostgreSQL endpoint has rejected SSL, while production database URLs are intentionally configured to require it.

**Why:** A normal test run attempted to connect to the workspace PostgreSQL service and failed because it does not support the SSL mode enforced for `DATABASE_URL`.

**How to apply:** Prefix local `manage.py test` commands with `DATABASE_URL=`. Do not change production SSL settings or the workspace's stored environment variable to work around this local test limitation.
