# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |

## Reporting a vulnerability

Please report security issues privately rather than opening a public GitHub
issue. Include:

- A clear description of the issue
- Steps to reproduce
- Potential impact
- Any suggested remediation

MusicBloom is a portfolio project; response times may vary, but legitimate
reports will be acknowledged and addressed as promptly as possible.

## Security practices in MusicBloom

- **Secrets stay server-side.** Spotify client secrets, Azure DevOps PATs, and
  encryption keys are loaded from environment variables and never returned by the
  REST API.
- **Token storage.** Spotify OAuth tokens are encrypted at rest when
  `MUSICBLOOM_TOKEN_ENCRYPTION_KEY` is configured.
- **Secret redaction.** Azure DevOps and OAuth error paths redact sensitive
  material before logging or returning safe error messages.
- **Demo mode defaults.** Local development runs in demo mode so tests and demos
  do not require external credentials.
- **Production guards.** Production configuration requires a strong
  `MUSICBLOOM_SECRET_KEY`, disables debug/demo mode, and requires an explicit
  database URL.
- **No audio proxying.** MusicBloom does not download, proxy, cache, or analyze
  Spotify audio.
- **CI hygiene.** Azure Pipelines YAML does not contain Spotify or Azure DevOps
  secrets. Use secure pipeline variables or secret stores for real deployments.

## Out of scope for this release

- Production deployment hardening beyond configuration guards
- Multi-user authentication
- Automated secret rotation

If you are evaluating MusicBloom for production use, treat the current release
as a validated portfolio baseline rather than a fully hardened production
platform.
