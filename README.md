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
  <a href="#trust-list">Trust List</a> •
  <a href="#repository-structure">Repository Structure</a> •
  <a href="#onboarding">Onboarding</a> •
  <a href="#service-types">Service Types</a> •
  <a href="#licensing">Licensing</a>
</p>

## About

This repository hosts the **NXD Foundation Trust List**, an open, machine-readable registry of the Trust Service Providers (TSPs) recognised within the NXD Foundation ecosystem. It is based on the **ETSI TS 119 475** specification and aligned with the EU Digital Identity framework under **Regulation (EU) No 910/2014 (eIDAS)** as amended by [EU Regulation 2024/1183](https://eur-lex.europa.eu/eli/reg/2024/1183/oj/eng).

The Trust List is published as a static XML file via GitHub Pages so it can be fetched and verified by wallets, issuers, and verifiers.

## Trust List

The NXD Foundation Trust List is available at: [https://nxd-foundation.github.io/nxd-trust-list/NXD-TL](https://nxd-foundation.github.io/nxd-trust-list/NXD-TL).

**NOTE:** Any changes to the Trust List shall only be made via a pull request. See [Onboarding](#onboarding) for the process.

## Repository Structure

| Path | Description |
| ---- | ----------- |
| `NXD-TL.xml` | The Trust List itself — the single source of truth for all registered Trust Service Providers. |
| `nxd-trust-list-onboarding.md` | Step-by-step guide for adding an organisation to the Trust List. |
| `TrstSvc/Svctype/` | Definitions for the NXD-specific service types (`PID`, `LPID`, `NPWP`, `LPWP`). |
| `LICENSE` | Apache 2.0 license. |

## Onboarding

All participants in the NXD Foundation ecosystem must ensure they are onboarded into the NXD Trust List. Instructions can be found [here](https://nxd-foundation.github.io/nxd-trust-list/nxd-trust-list-onboarding).

In short:

1. Fork [`NXD-Foundation/nxd-trust-list`](https://github.com/NXD-Foundation/nxd-trust-list).
2. Add your `<TrustServiceProvider>` entry to `NXD-TL.xml`.
3. Open a pull request for review by the NXD Foundation team.

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
