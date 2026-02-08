## Contributing to StreamGuard

Thanks for your interest in contributing! This guide keeps things simple and consistent.

## Quick Start

1. Fork the repo and create a feature branch:
   - `git checkout -b feature/my-change`
2. Make your changes.
3. Run the checks (see below).
4. Open a Pull Request.

## Development Setup

### Docker (recommended)

- Copy `.env.example` to `.env` and adjust values.
- Start services:
  - `docker-compose up -d`

### Manual (local)

Backend:
- `cd backend`
- `pip install -r requirements.txt`
- `uvicorn main:app --reload`

Frontend:
- `cd frontend`
- `npm install`
- `npm run dev`

## Running Tests

Backend tests:
- `pytest backend/tests/`

Frontend checks:
- `cd frontend`
- `npm run build`

## Code Style

- Python: Black formatting is preferred.
- TypeScript/React: Prettier formatting is preferred.
- Keep code readable and avoid large, unrelated refactors in a single PR.

## Commit Messages

Use clear, imperative messages:
- `Add host validation`
- `Fix dashboard chart crash`
- `Update CAC cache handling`

## Pull Requests

Please include:
- A clear description of what and why
- Tests or verification steps you ran
- Screenshots for UI changes

## Reporting Issues

Use GitHub Issues for bugs and feature requests. For security issues, see
`SECURITY.md`.
