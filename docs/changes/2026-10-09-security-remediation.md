# Dependency security remediation and code review — 9 October 2026

## Purpose and scope

This public repository is a learning/work backup project, not a hosted deployment. This change updates vulnerable dependencies, strengthens authentication configuration, and makes GitHub Actions reproducible. No production service, database, ImageKit account, or user data was accessed. No deployment was performed.

Base reviewed: `9f21038d61a144fbeb7ce933b5e915469bb116af` on `main`.
Branch: `security/dependency-remediation-2026-10-09`.

## Dependency changes

| Package | Before | After | Existing PR covered |
| --- | --- | --- | --- |
| PyJWT | 2.13.0 | 2.15.1 | #12 (supersedes its 2.15.0 target) |
| urllib3 | 2.7.0 | 2.8.0 | #13 |
| Pillow | 12.2.0 | 12.3.0 | #3 |
| AnyIO | 4.13.0 | 4.14.2 | #11 |
| GitPython | 3.1.50 | 3.1.62 | #14 |
| cryptography | 49.0.0 | 50.0.0 | #7 |
| pip | 26.1.2 | 26.2 | #9 |

`uv.lock` was resolved with targeted updates, not a blanket upgrade. The PyJWT minimum in `pyproject.toml` is now 2.15.1. The other packages are transitive dependencies, preserved by the reviewed lockfile. Python remains 3.13+.

PyJWT 2.14.0 addresses key-confusion and JWKS-related security issues; 2.15.0 adds further malformed-input handling; 2.15.1 fixes valid trailing Base64URL padding compatibility. The application's inspected authentication path uses one configured algorithm, not a mixed HS/RS allow-list or PyJWKClient. Presence of a vulnerable dependency alone does not prove exploitability of every advisory.

Sources:
- https://pyjwt.readthedocs.io/en/stable/changelog.html
- https://github.com/jpadilla/pyjwt/security/advisories
- https://github.com/urllib3/urllib3/releases/tag/2.8.0
- https://github.com/gitpython-developers/GitPython/releases/tag/3.1.62
- Release notes attached to the seven original Dependabot PRs.

## Code and configuration changes

- `app/core/config.py`: removes the predictable signing-secret fallback; requires an explicit secret of at least 32 characters; rejects documented placeholder prefixes. Secret generation remains the user's responsibility: length alone does not guarantee entropy. Suppresses settings input values in string-form validation errors and excludes the signing secret from settings repr. Restricts this shared-secret application to HS256.
- `app/core/security.py`: requires both `exp` and `sub` during JWT decoding, in addition to signature and expiry validation.
- `app/app.py`: `/health` returns a generic database-unavailable message instead of a raw database exception.
- `.gitignore`: ignores all `.env.*` files except the intentionally public `.env.example`.
- `README.md`: correct repository URL, locked installation instructions, and secret-generation guidance. No generated secret was committed.

Compatibility impact: existing local setups that relied on the default/short/placeholder JWT secret must set a generated `AUTH_SECRET_KEY` in their ignored `.env`. Changing a signing secret invalidates previously issued tokens. Non-HS256 configurations are rejected deliberately because this application uses a shared-secret authentication design. Tokens without an expiry or subject are rejected.

## CI changes

- `.github/workflows/ci.yml`: `uv sync --locked` and `uv run --locked` prevent CI from silently resolving a different dependency set; use the already declared pip-audit dependency instead of mutating the environment before scanning; workflow token permissions are read-only.
- `.github/workflows/secret-scan.yml`: checksum-verified Gitleaks 8.30.1 scans fetched Git history with values redacted on PRs and main pushes. It uses no external account secrets and uploads no secret reports. SHA256 verification checks asset integrity against the publisher's checksum file; it is not independent publisher authentication.
- Existing main rules require a PR and linear history; the intended merge method is squash. No protection rules were changed or bypassed.

## Validation performed before PR creation

- Locked dependency resolution and installation succeeded on Python 3.13.16.
- Ruff lint and format checks passed.
- mypy passed.
- 26 tests passed: app import; valid/invalid/expired/wrong-signature/wrong-algorithm tokens; required claims; absent/inactive users; secret/algorithm configuration; sanitized health errors; password/account-status login checks; mocked ImageKit adapter; Requests/urllib3 loopback HTTP; Pillow PNG roundtrip; GitPython local repository; AnyIO task group; ephemeral RSA signing/verification through cryptography and PyJWT.
- `uv run --locked pip-audit`: no known vulnerabilities found in the installed environment at the time of the scan. No advisories were ignored. Advisory databases can change later.
- Gitleaks full accessible Git history scan: 10 commits, no leaks detected. Includes fetched Dependabot branch history.
- Gitleaks proposed tracked/source files scan: no leaks detected. Dependency-install folders are excluded from this source-only check. An initial unrestricted scratch-directory scan flagged bundled third-party pydeck source-map strings inside `.venv`; those are not project files and were not uploaded.
- Streamlit server startup and loopback health endpoint returned HTTP 200. This does not establish full browser/UI or live backend compatibility.
- Initial tests in this environment hit an inherited SOCKS-proxy configuration unsupported by the installed HTTPX extras; reran local tests with proxy variables removed. No application dependency was added to work around an environment-only issue.

GitHub Actions results are recorded in the remediation PR; this file records pre-PR checks, not a promise that remote checks have run.

## Review limitations and follow-up work

This is a targeted security review, not a complete penetration test. Automated scanners can miss credentials; no finding is not proof that no secret has ever leaked. Repository-specific Dependabot/security alert state was unavailable through the connector, so no exact open-alert count or dismissal claim is made. Public source, dependency audit and accessible Git history were checked; account secrets, inaccessible refs, external logs and live environments were not.

Before any future hosting:
- Add upload size limits and validate actual file content; currently upload handling trusts MIME headers and reads the file into memory.
- Add authentication/registration rate limiting and abuse protection.
- Review raw exception logging across database/storage handlers; the health response fix does not sanitize all application logs.
- Add real PostgreSQL/ImageKit integration tests and a full browser flow; current database/storage tests use mocks.
- Test custom HTTPS proxies if introduced: urllib3 2.8.0 separates proxy TLS configuration from destination TLS settings.
- Test custom Git subprocess/diff/submodule uses if introduced; security hardening can reject formerly accepted unsafe operations.
- Review cryptography 50 key/certificate parsing changes and pip 26.2 isolated-build constraints if those features are used.

## How to inspect this work later

Read this file, the remediation PR's Files changed, its Checks tab, and the squash commit on main. Original Dependabot PRs are closed only after the merged changes cover their updates; their conversation/history remains available.

## Local synchronization when development resumes

If the local checkout has no uncommitted changes:

```bash
git switch main
git pull --ff-only origin main
uv sync --locked
```

Keep real `.env` values local. Generate an explicit signing secret if needed; do not commit it. For development checks, use `uv sync --locked --all-extras --dev` followed by the CI commands. No local working directory on the user's computer was changed by this work.
