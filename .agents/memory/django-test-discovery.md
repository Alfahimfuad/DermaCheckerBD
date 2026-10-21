---
name: Django test discovery in the imported project
description: Avoids an import collision caused by the repository's nested copy during default unittest discovery.
---

This imported project has a duplicate nested source/test tree. Django's default test discovery can import a nested module with the same name as a root test module, then fail with an "incorrectly imported" `ImportError`. Running the root test modules by explicit labels avoids that discovery collision without changing application code.

**Why:** The repository contains the active root project and a second nested copy; default discovery traverses both.

**How to apply:** If `python manage.py test` reports a duplicate test-module import, run the intended root test modules explicitly or configure discovery to exclude the nested copy. Do not delete or restructure the duplicate project as a test workaround.
