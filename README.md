<h1 align="center">
    NXD Foundation - Trust List
</h1>

<p align="center">
    <a href="/../../commits/" title="Last Commit"><img src="https://img.shields.io/github/last-commit/NXD-Foundation/nxd-trust-list?style=flat"></a>
    <a href="/../../issues" title="Open Issues"><img src="https://img.shields.io/github/issues/NXD-Foundation/nxd-trust-list?style=flat"></a>
    <a href="/../../pulls" title="Open Pull Requests"><img src="https://img.shields.io/github/issues-pr/NXD-Foundation/nxd-trust-list?style=flat"></a>
    <a href="./LICENSE" title="License"><img src="https://img.shields.io/badge/License-Apache%202.0-yellowgreen?style=flat"></a>
</p>

<p align="center">
  <a href="#about">About</a> •
  <a href="#trust-lists">Trust Lists</a> •
  <a href="#repository-structure">Repository Structure</a> •
  <a href="#onboarding">Onboarding</a> •
  <a href="#service-types">Service Types</a> •
  <a href="#licensing">Licensing</a>
</p>

## About

This repository hosts the **NXD Foundation Trust List**, an open, machine-readable registry of the Trust Service Providers (TSPs) recognised within the NXD Foundation ecosystem. It is based on the **ETSI TS 119 475** specification and aligned with the EU Digital Identity framework under **Regulation (EU) No 910/2014 (eIDAS)** as amended by [EU Regulation 2024/1183](https://eur-lex.europa.eu/eli/reg/2024/1183/oj/eng).

The Trust List is published as a static XML file via GitHub Pages so it can be fetched and verified by wallets, issuers, and verifiers.

## Trust Lists

The NXD Foundation publishes one signed trust list per provider type under
[`trust-lists/`](trust-lists/):

| List | URL | Format |
| ---- | --- | ------ |
| QEAA Providers | [`trust-lists/NXD-TL-QEAA.xml`](https://trustlist.nxd.foundation/trust-lists/NXD-TL-QEAA.xml) | ETSI TS 119 612 XML, XAdES-signed |
| EAA Providers | [`trust-lists/NXD-TL-EAA.xml`](https://trustlist.nxd.foundation/trust-lists/NXD-TL-EAA.xml) / [JSON](https://trustlist.nxd.foundation/trust-lists/nxd-eaa-providers-lote.json) | ETSI TS 119 602 LoTE, XAdES / JAdES-signed |
| Pub-EAA Providers | [`trust-lists/NXD-TL-PubEAA.xml`](https://trustlist.nxd.foundation/trust-lists/NXD-TL-PubEAA.xml) / [JSON](https://trustlist.nxd.foundation/trust-lists/nxd-pub-eaa-providers-lote.json) | ETSI TS 119 602 LoTE |
| PID Providers | [`trust-lists/NXD-TL-PID.xml`](https://trustlist.nxd.foundation/trust-lists/NXD-TL-PID.xml) / [JSON](https://trustlist.nxd.foundation/trust-lists/nxd-pid-providers-lote.json) | ETSI TS 119 602 LoTE |
| Wallet Providers | [`trust-lists/NXD-TL-WalletProviders.xml`](https://trustlist.nxd.foundation/trust-lists/NXD-TL-WalletProviders.xml) / [JSON](https://trustlist.nxd.foundation/trust-lists/nxd-wallet-providers-lote.json) | ETSI TS 119 602 LoTE |
| WRPAC Providers | [`trust-lists/NXD-TL-WRPAC.xml`](https://trustlist.nxd.foundation/trust-lists/NXD-TL-WRPAC.xml) / [JSON](https://trustlist.nxd.foundation/trust-lists/nxd-wrpac-providers-lote.json) | ETSI TS 119 602 LoTE |
| WRPRC Providers | [`trust-lists/NXD-TL-WRPRC.xml`](https://trustlist.nxd.foundation/trust-lists/NXD-TL-WRPRC.xml) / [JSON](https://trustlist.nxd.foundation/trust-lists/nxd-wrprc-providers-lote.json) | ETSI TS 119 602 LoTE |
| Registrars & Registers | [`trust-lists/NXD-TL-Registrars.xml`](https://trustlist.nxd.foundation/trust-lists/NXD-TL-Registrars.xml) / [JSON](https://trustlist.nxd.foundation/trust-lists/nxd-registrars-and-registers-lote.json) | ETSI TS 119 602 LoTE |

The legacy full list [`NXD-TL.xml`](https://trustlist.nxd.foundation/NXD-TL)
is **frozen**: it is kept for backward compatibility and does not grow.

**NOTE:** Any changes to the trust lists shall only be made via a pull request. See [Onboarding](#onboarding) for the process.

## Repository Structure

| Path | Description |
| ---- | ----------- |
| `trust-lists/` | The signed, generated trust lists (one per provider type). Never edit by hand. |
| `onboarding/` | Participant registration entries (source of truth) + JSON schema + guide. |
| `scripts/` | List generator/signer and vendored ETSI schemas. |
| `.github/workflows/` | CI: PR validation; CD: sign & publish on merge. |
| `NXD-TL.xml` | Legacy full Trust List (frozen, backward compatibility only). |
| `nxd-trust-list-onboarding.md` | Legacy onboarding guide for `NXD-TL.xml` (superseded by `onboarding/`). |
| `TrstSvc/Svctype/` | Definitions for the NXD-specific service types (`PID`, `LPID`, `NPWP`, `LPWP`). |
| `LICENSE` | Apache 2.0 license. |

## Onboarding

New registrations happen in [`onboarding/`](onboarding/) - see the
[onboarding guide](onboarding/README.md).

In short:

1. Fork [`NXD-Foundation/nxd-trust-list`](https://github.com/NXD-Foundation/nxd-trust-list).
2. Add `onboarding/<your-participant-id>.json` (JSON-schema-validated; X.509 certificates only).
3. Open a pull request. CI validates the entry; after review and merge, CI regenerates, signs, and publishes the lists.

## Service Types

### NXD Service Types

These service types are defined for the NXD Foundation ecosystem, based on the EU Digital Identity framework.

| Provider Type                  | Abbreviation(s) | URI                                                                                                                                            |
| ------------------------------ | --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| Natural Person PID Provider    | PID             | [https://nxd-foundation.github.io/nxd-trust-list/TrstSvc/Svctype/PID](https://nxd-foundation.github.io/nxd-trust-list/TrstSvc/Svctype/PID)   |
| Legal Person PID Provider      | LPID            | [https://nxd-foundation.github.io/nxd-trust-list/TrstSvc/Svctype/LPID](https://nxd-foundation.github.io/nxd-trust-list/TrstSvc/Svctype/LPID) |
| Natural Person Wallet Provider | NPWP            | [https://nxd-foundation.github.io/nxd-trust-list/TrstSvc/Svctype/NPWP](https://nxd-foundation.github.io/nxd-trust-list/TrstSvc/Svctype/NPWP) |
| Legal Person Wallet Provider   | LPWP            | [https://nxd-foundation.github.io/nxd-trust-list/TrstSvc/Svctype/LPWP](https://nxd-foundation.github.io/nxd-trust-list/TrstSvc/Svctype/LPWP) |

### Existing Service Types

Several additional service types are defined as per **ETSI TS 119 612**. See the [list of service type URIs](https://www.etsi.org/deliver/etsi_ts/119600_119699/119612/) for reference.

## Licensing

Licensed under the Apache 2.0 License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the [LICENSE](./LICENSE) for the specific language governing permissions and limitations under the License.
