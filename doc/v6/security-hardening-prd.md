# PRD: Security Headers and Baseline Hardening

## Problem Statement

The system currently works as a local-development setup, but it does not yet
present a strong production security baseline.

The main gaps are:

- no explicit application-level security header policy
- auth cookies are not marked secure for HTTPS delivery
- the JWT signing secret has a dangerous default fallback
- FastAPI docs and OpenAPI endpoints are left on the default surface
- the frontend delivery layer does not declare a response header policy of its own

That means the app is more exposed than it needs to be if deployed publicly.
The risk is not only XSS or token theft. It is also accidental production
deployment with development defaults still active.

## Solution

Harden the app by making security posture explicit at the edge and in the core:

- require a real production secret instead of accepting a guessable fallback
- set auth cookies to secure transport behavior in non-local environments
- add a clear security header policy for API and frontend responses
- disable or gate docs surfaces outside trusted environments
- keep authentication behavior compatible with the current cookie-based flow
- preserve local development convenience while making production safer by
  default

The goal is not to redesign auth. The goal is to raise the baseline so the
system ships with safer defaults and predictable browser-facing controls.

## User Stories

1. As an operator, I want the app to fail startup when a production secret is
   missing, so that I do not accidentally deploy with a forgeable JWT key.
2. As an operator, I want auth cookies to be marked secure in HTTPS
   environments, so that session tokens are not sent over plain HTTP.
3. As an operator, I want auth cookies to remain HTTP-only, so that browser
   JavaScript cannot read them directly.
4. As an operator, I want auth cookies to keep a sensible same-site policy, so
   that cross-site abuse is reduced without breaking the current web flow.
5. As an operator, I want logout to clear the session cookie cleanly, so that
   stale sessions do not linger after sign-out.
6. As a security reviewer, I want the app to emit explicit security headers, so
   that browser protections are not left to chance.
7. As a security reviewer, I want a content security policy, so that script
   injection and unsafe resource loading are constrained.
8. As a security reviewer, I want transport security headers, so that browsers
   prefer HTTPS once the app is deployed that way.
9. As a security reviewer, I want framing protection, so that the app cannot be
   trivially embedded in hostile iframes.
10. As a security reviewer, I want MIME-sniffing protection, so that browsers do
   not reinterpret responses unexpectedly.
11. As a security reviewer, I want a referrer policy, so that sensitive URLs are
   not leaked unnecessarily.
12. As a security reviewer, I want a permissions policy, so that unused browser
   capabilities are not exposed.
13. As a developer, I want the frontend and backend to share the same baseline
   security posture, so that one layer does not undo the other.
14. As a developer, I want production-only defaults to be explicit in config, so
   that local development remains easy to run.
15. As a developer, I want docs and OpenAPI to be disabled or gated outside
   trusted environments, so that internal metadata is not openly exposed.
16. As a developer, I want auth to keep working with cookie-based session
   handling, so that the current login flow does not regress.
17. As a developer, I want the system to keep accepting bearer tokens where the
   code already uses them, so that existing automation and tests continue to
   function.
18. As a QA engineer, I want response-header tests, so that baseline security
   does not regress unnoticed.
19. As a QA engineer, I want cookie-flag tests, so that secure and HTTP-only
   behavior is verified.
20. As a QA engineer, I want startup-config tests, so that missing security
   secrets fail fast.
21. As a site operator, I want local development to remain low-friction, so that
   the security posture does not make everyday work harder than necessary.
22. As a site operator, I want a clear environment switch between local and
   production behavior, so that the correct safety level is applied in each
   deployment.
23. As a site operator, I want the frontend to advertise safe browser behavior,
   so that the delivery layer does not rely only on backend headers.
24. As a platform owner, I want the app to avoid secret defaults, so that
   accidental deployments are less dangerous.
25. As a platform owner, I want security posture to be testable, so that future
   changes can be reviewed mechanically.

## Implementation Decisions

- Introduce a single environment-aware security configuration boundary that
  decides local versus production behavior.
- Make the JWT signing secret required for non-local execution.
- Keep token generation and validation behavior unchanged apart from secret
  handling.
- Keep the current cookie-based auth model, but set transport-safe cookie flags
  in production.
- Add a response-header policy to the API layer and mirror the needed browser
  headers from the frontend delivery layer if that is where they are served.
- Gate docs and OpenAPI exposure behind environment settings rather than leaving
  defaults in place.
- Preserve existing login and session contracts so the frontend does not need a
  rewrite.
- Keep the hardening narrow: no auth protocol migration, no new login provider,
  no refresh-token redesign, and no broader perimeter architecture work in this
  PRD.
- Treat the current bearer-token support as compatibility behavior, not as the
  preferred long-term browser storage strategy.

## Testing Decisions

- Test external behavior, not implementation details.
- Add tests for security headers on representative API responses.
- Add tests for cookie flags on login, tenant switch, and logout flows.
- Add tests that missing production secrets fail startup or config validation.
- Add tests that docs and OpenAPI are unavailable or gated in production mode.
- Add frontend delivery tests only where the frontend itself is responsible for
  emitted response headers.
- Prior art should follow the existing integration-test style already used for
  auth, dashboard, refresh, export, and admin API coverage.

## Out of Scope

- Full auth redesign
- OAuth / SSO integration
- MFA
- Role model changes
- Encryption-at-rest work outside existing platform defaults
- WAF, CDN, or reverse-proxy policy changes
- CSP nonce architecture or broader frontend code-splitting redesign
- Secret rotation workflow automation
- Penetration testing engagement
- Infrastructure rebuilds

## Further Notes

The current state is acceptable for local development, but it is not a strong
production baseline yet.

The most important principle is fail closed:

- no guessable secret in production
- no insecure cookie delivery in HTTPS deployments
- no silent exposure of docs and schema metadata
- no assumption that a proxy will fix missing application defaults

Security headers are only part of the answer, but they are the fastest
meaningful improvement here because they reduce common browser-side attack
paths without changing product behavior.
