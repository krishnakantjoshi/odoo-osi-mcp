# Privacy

Odoo OSI is designed to run locally or in a self-hosted environment.

By default, the project reads:

- local configuration from `.env`
- public GitHub repository metadata and files
- local PostgreSQL data created by indexing jobs

Do not commit real `.env` files, GitHub tokens, private database dumps, or private customer module
data. If you deploy this as a hosted service, you are responsible for adding appropriate user
accounts, tenant isolation, token storage, deletion flows, logs, privacy policy, and terms of use.

For public deployments, prefer GitHub App or OAuth-based authorization over storing raw personal
access tokens.
