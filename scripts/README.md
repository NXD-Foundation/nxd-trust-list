# Trust list build & signing pipeline

Generates the per-provider-type trust lists in [`trust-lists/`](../trust-lists/)
from the participant entries in [`onboarding/`](../onboarding/), signs them
(XAdES Baseline B for XML, JAdES Compact Baseline B for JSON), and validates
them against the ETSI schemas vendored in [`schemas/`](schemas/):

- `19612_xsd.xsd` - ETSI TS 119 612 v2.4.1 trusted list XML schema
- `1960201_json_schema.json` - ETSI TS 119 602-1 LoTE JSON schema

## Usage

This is a [uv](https://docs.astral.sh/uv/) project (`pyproject.toml` + `uv.lock`).

```bash
uv sync --group dev

# Unsigned (PR validation)
uv run python scripts/generate_lists.py --no-sign --output-dir /tmp/generated

# Signed (key/cert from env or certs/)
export NXD_TL_SIGNING_KEY="$(cat certs/nxd-tl-signing-key.pem)"
export NXD_TL_SIGNING_CERT="$(cat certs/nxd-tl-signing-cert.pem)"
uv run python scripts/generate_lists.py

# Lint and type check
uv run ruff check scripts/
uv run mypy
```

Outputs land in `trust-lists/` plus `lotl-submission/{tl_type}/nxd-foundation.json`
(entry files for registering each list in an ETSI list of trusted lists; not
committed).

## Signing certificate

Self-signed, ETSI TS 119 612 clause 5.7.1-compliant (ECDSA P-256, KeyUsage
digitalSignature+nonRepudiation, ExtendedKeyUsage id-tsl-kp-tslSigning,
BasicConstraints CA=false). The private key must never be committed - it lives
in the `NXD_TL_SIGNING_KEY` GitHub secret (and locally in `certs/`, which is
gitignored).

## CI/CD

- `.github/workflows/validate.yml` - on PRs: ruff + mypy, validates onboarding
  entries against the JSON schema, regenerates all lists unsigned, and verifies
  the signatures of the committed lists.
- `.github/workflows/publish.yml` - on merge to `main` touching `onboarding/`:
  regenerates, signs with repository secrets, commits `trust-lists/`, and tags
  `tl-v{n}`. GitHub Pages serves the results.

## Re-issuance

ETSI TS 119 612 clause 5.3.15 caps `NextUpdate` at 6 months after
`ListIssueDateTime`; the generator sets it to issue + 182 days. Re-run the
publish workflow (workflow_dispatch) before the lists expire even if no
onboarding changes happened.
