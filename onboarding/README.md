# Onboarding to the NXD Foundation Trust Lists

Participants are onboarded via pull request. One JSON file per participant in
this directory drives the generation of the per-provider-type trust lists
published under [`trust-lists/`](../trust-lists/):

| List | Published as | Format |
|------|-------------|--------|
| `qeaa` | `trust-lists/NXD-TL-QEAA.xml` | ETSI TS 119 612 XML TSL, XAdES-signed |
| `eaa` | `trust-lists/NXD-TL-EAA.xml` / `trust-lists/nxd-eaa-providers-lote.json` | ETSI TS 119 602 LoTE, XAdES / JAdES-signed |
| `pub-eaa` | `trust-lists/NXD-TL-PubEAA.xml` / `trust-lists/nxd-pub-eaa-providers-lote.json` | ETSI TS 119 602 LoTE |
| `pid` | `trust-lists/NXD-TL-PID.xml` / `trust-lists/nxd-pid-providers-lote.json` | ETSI TS 119 602 LoTE |
| `wallet` | `trust-lists/NXD-TL-WalletProviders.xml` / `trust-lists/nxd-wallet-providers-lote.json` | ETSI TS 119 602 LoTE |
| `wrpac` | `trust-lists/NXD-TL-WRPAC.xml` / `trust-lists/nxd-wrpac-providers-lote.json` | ETSI TS 119 602 LoTE |
| `wrprc` | `trust-lists/NXD-TL-WRPRC.xml` / `trust-lists/nxd-wrprc-providers-lote.json` | ETSI TS 119 602 LoTE |
| `registrars` | `trust-lists/NXD-TL-Registrars.xml` / `trust-lists/nxd-registrars-and-registers-lote.json` | ETSI TS 119 602 LoTE |

The legacy full list `NXD-TL.xml` is **frozen** - kept for backward
compatibility only and does not grow. All new registrations happen here.

## How to onboard

1. Fork this repository.
2. Add `onboarding/<your-participant-id>.json` following
   [`schema/participant.schema.json`](schema/participant.schema.json) -
   start from [`example.json.template`](example.json.template).
   `participant_id` must match the file name.
3. Open a pull request. CI validates your entry (JSON schema) and regenerates
   all lists to prove they stay ETSI-conformant.
4. After NXD Foundation review and merge, CI re-generates, signs, and publishes
   the lists via GitHub Pages automatically.

## Digital identities

Each service MUST provide at least one X.509 certificate
(`x509_certificates`, base64 DER - the PEM body without header/footer lines).
Other identifier types (DIDs, JWKS URIs) are not accepted in the new lists;
they exist only in the frozen legacy `NXD-TL.xml`.

## Updating or withdrawing

Update your JSON file via PR. Removal of a service or the whole file removes
it from the generated lists at the next publication.
