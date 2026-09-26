# Security and data handling

This repository is a synthetic-data demonstration. Do not open issues or pull requests containing patient information, secrets, credentials, or private records. The `.gitignore` excludes `.env` and the generated data folder, but always review `git status` and staged changes before pushing. If a key is exposed, revoke or rotate it with AWS immediately.

The current reader and tools allow access to every fictional patient. There is no authentication, authorization, consent management, or audit trail. This code is not ready for real patient information or clinical deployment.
