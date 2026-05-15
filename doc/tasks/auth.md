# Auth Module Tasks

## Goal

Deliver simple email/password authentication for v1 with narrow backend auth
services, protected API access, and frontend session-aware routing.

## Tasks

- [ ] Define auth domain types for user identity, session state, and login input/output.
- [ ] Create backend auth persistence schema for `users`.
- [ ] Implement password hashing utilities behind a narrow interface.
- [ ] Implement auth repository methods for user lookup and login metadata updates.
- [ ] Implement `AuthService.login`.
- [ ] Implement `AuthService.logout`.
- [ ] Implement `AuthService.validate_session`.
- [ ] Add API transport schemas for login, logout, and session responses.
- [ ] Add `POST /api/auth/login`.
- [ ] Add `POST /api/auth/logout`.
- [ ] Add `GET /api/auth/session`.
- [ ] Add backend route protection dependency for dashboard, refresh, anomalies, export, and department routes.
- [ ] Create frontend auth API adapter.
- [ ] Create frontend login form container and presentational component split.
- [ ] Create frontend session guard for protected routes.
- [ ] Surface invalid-session and login-failure states in the UI.

## Testing

- [ ] Add backend unit tests for password hashing helpers.
- [ ] Add backend unit tests for `AuthService` success and failure cases.
- [ ] Add backend integration tests for login, logout, and session endpoints.
- [ ] Add frontend unit tests for login form states and session guard behavior.
- [ ] Add frontend integration test for login-to-dashboard happy path.
