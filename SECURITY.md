# Security Policy

## Scope

This repository ships **skill definitions, Python scripts, and small library
wrappers** that talk to public clinical / biomedical APIs and data sources
(ClinicalTrials.gov, PubMed / NCBI E-utilities, OpenAlex, openFDA, ClinVar,
ClinPGx, COSMIC, etc.). It is a **tooling** repository — it does not host
patient data, model weights, or backend services.

## Supported Versions

| Branch            | Supported |
|-------------------|-----------|
| `main`            | ✅ Yes    |
| Feature / fix branches | Best effort, until merged or abandoned |

Older tags are not patched; please upgrade to the latest `main` if you depend
on a specific skill.

## Reporting a Vulnerability

**Please do not open a public GitHub issue for security-sensitive reports.**

Use one of the following private channels:

1. **GitHub Security Advisories (preferred)**
   Go to the repository → `Security` tab → `Advisories` → `New draft security
   advisory`. This routes the report to the maintainers privately.
2. **Email**
   Reach the maintainer via the address linked on their GitHub profile
   ([`@ZimaBlue123`](https://github.com/ZimaBlue123)). Mark the subject
   `[SECURITY] <short summary>`.

Please include:

- A clear description of the issue and its impact.
- Reproduction steps, proof-of-concept code, or a minimal failing example.
- The affected commit / tag / branch.
- Whether you want public credit when the advisory is published.

We aim to acknowledge new reports within **7 days** and to ship a fix or
mitigation within **30 days** for high-severity issues. Timelines for lower
severity issues are negotiated case by case.

## What is *in scope*

- Credential / API-key leakage in committed files (including history).
- Network calls (HTTP / HTTPS) made by the bundled scripts that bypass TLS
  verification, follow unvalidated redirects to untrusted hosts, or expose
  the caller's environment in error messages.
- Path traversal, command injection, or unsafe deserialization in scripts
  under `scripts/` or `skills/`.
- Unsafe handling of DOCX / PPTX / PDF inputs that can lead to remote code
  execution or information disclosure (e.g. when running macros, embedding
  external content, or executing shell commands embedded in templates).
- Supply-chain issues: typosquatted or compromised dependencies pinned in
  `requirements.txt` / `requirements-dev.txt`.

## What is *out of scope*

- Vulnerabilities in the third-party APIs themselves (ClinicalTrials.gov,
  PubMed, OpenAlex, openFDA, COSMIC, …) — please report them upstream.
- Vulnerabilities in upstream skills re-distributed from
  [`K-Dense-AI/claude-scientific-skills`](https://github.com/K-Dense-AI/claude-scientific-skills)
  or [`yizhiyanhua-ai/fireworks-tech-graph`](https://github.com/yizhiyanhua-ai/fireworks-tech-graph)
  — please report them upstream as well; we will then pull the fix.

## Data & Privacy Reminders

- **Never** commit patient-level data, raw subject exports, or anything that
  contains PHI / PII. The `.gitignore` already excludes `data/`, `raw_data/`,
  `output/`, `review_materials/`, `secrets/`, `.env*`, and common data
  formats, but this is a defense-in-depth measure, not a substitute for
  review.
- The repository includes `THIRD_PARTY_NOTICES.md` with the data-source
  usage rules that apply when you call those APIs.
- If you accidentally commit a secret or PHI file, rotate / revoke the
  credential **immediately** and contact the maintainers — `git rm` does
  not erase history.

## Acknowledgements

We are grateful to anyone who reports a vulnerability responsibly. Public
credit is given in the corresponding GitHub Security Advisory (unless
requested otherwise).
