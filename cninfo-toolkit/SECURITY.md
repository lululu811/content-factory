# Security Policy

## Supported Versions

We release security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in cninfo-toolkit, please report it
privately via one of these channels:

- **Email**: [chenliitaz@gmail.com](mailto:chenliitaz@gmail.com) (GPG key available on request)
- **GitHub Security Advisories**: Use the [private vulnerability reporting](https://github.com/chenliitaz/cninfo-toolkit/security/advisories/new) feature.

**Please do NOT open a public GitHub issue for security vulnerabilities.**

We aim to acknowledge security reports within 48 hours and provide a fix or
mitigation within 7 days for critical issues, or 30 days for non-critical issues.

## What to Include

When reporting a vulnerability, please include:

- A clear description of the vulnerability
- Steps to reproduce the issue
- Affected versions
- Potential impact
- Any suggested fixes (optional)

## Disclosure Policy

We follow a coordinated disclosure process:

1. **Initial Report** — You report the vulnerability privately.
2. **Acknowledgment** — We confirm receipt within 48 hours.
3. **Investigation** — We investigate and develop a fix (up to 30 days).
4. **Pre-release Notice** — We notify you before public disclosure.
5. **Public Disclosure** — After the fix is released, we publish a security advisory.
6. **Credit** — We credit you in the advisory (unless you prefer to remain anonymous).

## Out-of-Scope Vulnerabilities

The following are **not** considered security vulnerabilities:

- Denial of service via excessive API calls (use rate limiting)
- Issues in upstream dependencies (file with the upstream project)
- Theoretical attacks requiring physical access to the user's machine
- Social engineering attacks

## Best Practices for Users

To use cninfo-toolkit securely:

- **Pin versions** in your `requirements.txt` (e.g., `cninfo-toolkit==0.1.0`)
- **Use virtual environments** to isolate dependencies
- **Review announcements** before downloading PDFs at scale
- **Respect rate limits** (don't override the 0.5s default without good reason)
- **Keep dependencies updated**: `pip install --upgrade cninfo-toolkit`

## Dependencies

We monitor the security of our key dependencies:

- `pdfplumber` — maintained by the jsvine community
- `requests` — maintained by the psf community
- `typer` — maintained by the tiangolo community
- `rich` — maintained by the willmcgugan community

We use GitHub Dependabot to alert us to known vulnerabilities.

## Acknowledgements

We thank the following security researchers for responsibly disclosing vulnerabilities:

(None yet — be the first!)