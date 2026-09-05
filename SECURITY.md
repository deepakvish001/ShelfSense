# Security Policy

## Supported version

Security fixes are applied to the latest release on `main`.

## Reporting a vulnerability

Do not open a public issue containing exploit details, credentials, or affected user data. Use GitHub's private vulnerability reporting feature for this repository when available. Include the affected endpoint, reproduction steps, impact, and any suggested mitigation.

## Deployment responsibilities

- Terminate HTTPS at a trusted reverse proxy or platform load balancer.
- Generate high-entropy API keys and inject them through the environment.
- Rotate compromised keys immediately.
- Restrict access to the SQLite data volume and its backups.
- Set explicit browser origins in production.
- Review administrator audit events regularly.

ShelfSense does not claim regulatory compliance. Operators remain responsible for retention, privacy, access review, and incident-response requirements in their jurisdiction.
