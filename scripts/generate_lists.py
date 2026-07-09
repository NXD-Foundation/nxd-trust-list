#!/usr/bin/env python3
"""Generate the NXD Foundation per-type trust lists from onboarding entries.

Source of truth: ``onboarding/*.json`` (one file per participant, validated
against ``onboarding/schema/participant.schema.json``). The legacy full list
``NXD-TL.xml`` is frozen and NOT touched by this pipeline.

Outputs (under ``trust-lists/``), one list per provider type, suitable for
referencing from an ETSI list of trusted lists (LoTL):

  trust-lists/NXD-TL-QEAA.xml                  TS 119 612 XML TSL (XAdES Baseline B)
  trust-lists/NXD-TL-{EAA,PubEAA,PID,WalletProviders,WRPAC,WRPRC,Registrars}.xml
                                               TS 119 602 LoTE XML (XAdES B)
  trust-lists/nxd-*-lote.json                  TS 119 602-1 LoTE JSON (JAdES B)
  lotl-submission/{tl_type}/nxd-foundation.json   LoTL tl_entries files

Empty lists are valid: the TSL omits TrustServiceProviderList, the LoTE
XML carries an empty TrustedEntitiesList element and the LoTE JSON omits
TrustedEntitiesList (minItems 1).

Signing key/cert resolution order:
  1. --signing-key / --signing-cert file paths
  2. env NXD_TL_SIGNING_KEY / NXD_TL_SIGNING_CERT (PEM content)
  3. certs/nxd-tl-signing-key.pem / certs/nxd-tl-signing-cert.pem
Use --no-sign to generate unsigned lists (PR validation).
"""
from __future__ import annotations

import argparse
import base64
import calendar
import json
import os
import sys
import time
from collections.abc import Callable, Iterable, Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol, TypedDict, cast

import jsonschema
from cryptography import x509
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PublicFormat,
)
from jwcrypto import jwk, jws
from jwcrypto.common import json_encode
from lxml import etree
from signxml import XMLSigner, XMLVerifier

REPO = Path(__file__).resolve().parent.parent
SCHEMAS = Path(__file__).resolve().parent / "schemas"

TSL_NS = "http://uri.etsi.org/02231/v2#"
LOTE_NS = "http://uri.etsi.org/019602/v1#"
DS_NS = "http://www.w3.org/2000/09/xmldsig#"
XMLLANG = "{http://www.w3.org/XML/1998/namespace}lang"

PAGES = "https://trustlist.nxd.foundation"
LIST_DIR = "trust-lists"
ETSI_19602 = "http://uri.etsi.org/19602"

class Operator(TypedDict):
    name: str
    street: str
    locality: str
    postal_code: str
    country: str
    emails: list[str]


OPERATOR: Operator = {
    "name": "NXD Foundation",
    "street": "Bössvägen 28",
    "locality": "Sollentuna, Stockholm",
    "postal_code": "19255",
    "country": "SE",
    "emails": ["mailto:info@nxd.foundation"],
}

QEAA_SVC_TYPE = "http://uri.etsi.org/TrstSvc/Svctype/EAA/Q"
QEAA_SVC_STATUS = "https://uri.etsi.org/TrstSvc/TrustedList/Svcstatus/granted/"


def lote_config(tl_type: str, xml: str, json_file: str, label: str,
                etsi_name: str, svc_type: str, rules: str | None = None) -> dict[str, str]:
    """Build a LoTE list config; ETSI URIs follow the TS 119 602 Annex H pattern."""
    return {
        "tl_type": tl_type,
        "xml": xml,
        "json": json_file,
        "scheme_name": f"TT:EN_NXD Foundation - {label}",
        "lote_type": f"{ETSI_19602}/LoTEType/EU{etsi_name}",
        "status_detn": f"{ETSI_19602}/{etsi_name}/StatusDetn/EU",
        "rules": rules or f"{ETSI_19602}/{etsi_name}/schemerules/EU",
        "svc_type": f"{ETSI_19602}/SvcType/{svc_type}",
        "svc_status": f"{ETSI_19602}/{etsi_name}/SvcStatus/notified",
    }


# One list per provider type (LoTL tl_type). "qeaa" is a TS 119 612 TSL;
# the rest are TS 119 602 LoTE lists.
LISTS = {
    "qeaa": {
        "tl_type": "qeaa-provider",
        "xml": "NXD-TL-QEAA.xml",
        "scheme_name": "TT:EN_NXD Foundation - QEAA Providers",
    },
    "eaa": lote_config(
        "eaa-provider", "NXD-TL-EAA.xml", "nxd-eaa-providers-lote.json",
        "EAA Providers", "PubEAAProvidersList", "PubEAA/Issuance"),
    "pub-eaa": lote_config(
        "pub-eaa-provider", "NXD-TL-PubEAA.xml", "nxd-pub-eaa-providers-lote.json",
        "Pub-EAA Providers", "PubEAAProvidersList", "PubEAA/Issuance"),
    "pid": lote_config(
        "pid-provider", "NXD-TL-PID.xml", "nxd-pid-providers-lote.json",
        "PID Providers", "PIDProvidersList", "PID/Issuance",
        rules=f"{ETSI_19602}/PIDProviders/schemerules/EU"),
    "wallet": lote_config(
        "wallet-provider", "NXD-TL-WalletProviders.xml", "nxd-wallet-providers-lote.json",
        "Wallet Providers", "WalletProvidersList", "WalletSolution/Issuance"),
    "wrpac": lote_config(
        "wrpac-provider", "NXD-TL-WRPAC.xml", "nxd-wrpac-providers-lote.json",
        "WRPAC Providers", "WRPACProvidersList", "WRPAC/Issuance"),
    "wrprc": lote_config(
        "wrprc-provider", "NXD-TL-WRPRC.xml", "nxd-wrprc-providers-lote.json",
        "WRPRC Providers", "WRPRCProvidersList", "WRPRC/Issuance"),
    "registrars": lote_config(
        "ebwoid-provider", "NXD-TL-Registrars.xml", "nxd-registrars-and-registers-lote.json",
        "Registrars and Registers", "RegistrarsAndRegistersList", "Register"),
}


def q(tag: str) -> str:
    return f"{{{TSL_NS}}}{tag}"


def lq(tag: str) -> str:
    return f"{{{LOTE_NS}}}{tag}"


# --------------------------------------------------------------------------
# XML building helpers
# --------------------------------------------------------------------------

class Sub(Protocol):
    """SubElement helper bound to one namespace."""

    def __call__(self, parent: etree._Element, tag: str, text: str | None = None,
                 lang: str | None = None) -> etree._Element: ...


def make_sub(ns_fn: Callable[[str], str]) -> Sub:
    """Return a SubElement helper bound to a namespace-qualifying function."""
    def sub(parent: etree._Element, tag: str, text: str | None = None,
            lang: str | None = None) -> etree._Element:
        el = etree.SubElement(parent, ns_fn(tag))
        if text is not None:
            el.text = text
        if lang:
            el.set(XMLLANG, lang)
        return el
    return sub


def add_address(sub: Sub, parent: etree._Element, street: str, locality: str,
                postal_code: str | None, country: str, emails: list[str]) -> None:
    """Fill an *Address element with PostalAddresses + ElectronicAddress."""
    addresses = sub(parent, "PostalAddresses")
    postal = sub(addresses, "PostalAddress", lang="en")
    sub(postal, "StreetAddress", street)
    sub(postal, "Locality", locality)
    if postal_code:
        sub(postal, "PostalCode", postal_code)
    sub(postal, "CountryName", country)
    electronic = sub(parent, "ElectronicAddress")
    for uri in emails:
        sub(electronic, "URI", uri, lang="en")


def add_participant_address(sub: Sub, parent: etree._Element,
                            participant: dict[str, Any]) -> None:
    addr = participant["address"]
    add_address(sub, parent, addr["street"], addr["locality"],
                addr.get("postal_code"), addr["country"],
                participant["electronic_addresses"])


def add_six_months(dt: datetime) -> datetime:
    """Exactly six calendar months later, clamping to the target month's last day.

    TS 119 612 clause 5.3.15 caps NextUpdate at six months after
    ListIssueDateTime; a fixed day count (182/183) can overshoot the
    calendar-month boundary for some issue dates.
    """
    month = dt.month + 6
    year = dt.year + (month - 1) // 12
    month = (month - 1) % 12 + 1
    day = min(dt.day, calendar.monthrange(year, month)[1])
    return dt.replace(year=year, month=month, day=day)


# --------------------------------------------------------------------------
# signing (XAdES Baseline B via signxml enveloped; JAdES Compact B via jwcrypto)
# --------------------------------------------------------------------------

def sign_xml(xml_bytes: bytes, key_pem: bytes, cert_pem: bytes) -> bytes:
    root = etree.fromstring(xml_bytes)
    signer = XMLSigner(
        signature_algorithm="ecdsa-sha256",
        digest_algorithm="sha256",
        c14n_algorithm="http://www.w3.org/2001/10/xml-exc-c14n#",
    )
    signed = signer.sign(root, key=key_pem.decode(), cert=cert_pem.decode(),
                         always_add_key_value=False)
    return etree.tostring(signed, encoding="utf-8", xml_declaration=True,
                          pretty_print=True)


def verify_xml(xml_bytes: bytes, cert_pem: bytes) -> None:
    XMLVerifier().verify(etree.fromstring(xml_bytes), x509_cert=cert_pem.decode())


def sign_json(payload: dict[str, Any], key_pem: bytes,
              cert_pem: bytes) -> dict[str, Any]:
    """JAdES Compact Baseline B; stored per RFC 7515 section 7.2.2."""
    key = jwk.JWK.from_pem(key_pem)
    der = x509.load_pem_x509_certificate(cert_pem).public_bytes(Encoding.DER)

    payload = dict(payload)
    payload.pop("signature", None)
    header = {
        "alg": "ES256",
        "x5c": [base64.b64encode(der).decode()],
        "iat": int(time.time()),
    }
    token = jws.JWS(json_encode(payload))
    token.add_signature(key, None, json_encode(header), None)
    parts = token.serialize(compact=True).split(".")
    payload["signature"] = {"protected": parts[0], "signature": parts[2]}
    return payload


def verify_json(payload: dict[str, Any]) -> None:
    sig = payload.get("signature")
    if not sig:
        raise ValueError("No signature in payload")
    body = {k: v for k, v in payload.items() if k != "signature"}
    protected = json.loads(base64.urlsafe_b64decode(
        sig["protected"] + "=" * (-len(sig["protected"]) % 4)))
    der = base64.b64decode(protected["x5c"][0])
    cert = x509.load_der_x509_certificate(der)
    pub_pem = cert.public_key().public_bytes(
        Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)
    key = jwk.JWK.from_pem(pub_pem)
    b64_payload = base64.urlsafe_b64encode(
        json_encode(body).encode()).rstrip(b"=").decode()
    token = jws.JWS()
    token.deserialize(f"{sig['protected']}.{b64_payload}.{sig['signature']}")
    token.verify(key)


# --------------------------------------------------------------------------
# onboarding input
# --------------------------------------------------------------------------

def load_participants(onboarding_dir: Path) -> list[dict[str, Any]]:
    schema = json.loads(
        (onboarding_dir / "schema/participant.schema.json").read_text())
    validator = jsonschema.Draft202012Validator(
        schema, format_checker=jsonschema.FormatChecker())
    participants = []
    for f in sorted(onboarding_dir.glob("*.json")):
        data = json.loads(f.read_text())
        errors = [f"{f.name}: {'/'.join(map(str, e.absolute_path))}: {e.message}"
                  for e in validator.iter_errors(data)]
        if errors:
            raise SystemExit("Onboarding validation failed:\n" + "\n".join(errors))
        if data["participant_id"] != f.stem:
            raise SystemExit(
                f"{f.name}: participant_id {data['participant_id']!r} "
                "must match file name")
        participants.append(data)
    return participants


def services_for(participants: list[dict[str, Any]], list_key: str,
                 ) -> Iterator[tuple[dict[str, Any], list[dict[str, Any]]]]:
    for p in participants:
        svcs = [s for s in p["services"] if s["list"] == list_key]
        if svcs:
            yield p, svcs


def entity_dicts(participants: list[dict[str, Any]], list_key: str,
                 issue: str) -> list[dict[str, Any]]:
    """Normalize (participant, services) pairs for the LoTE builders."""
    ents = []
    for p, svcs in services_for(participants, list_key):
        services = [{
            "name": s["name"],
            "x509": s["digital_ids"]["x509_certificates"],
            "start": s.get("status_starting_time", issue),
            "supply": s.get("service_supply_points", []),
        } for s in svcs]
        ents.append({"p": p, "services": services})
    return ents


# --------------------------------------------------------------------------
# TS 119 612 TSL (QEAA)
# --------------------------------------------------------------------------

def build_qeaa_tsl(participants: list[dict[str, Any]], issue: str, nxt: str,
                   sequence: int) -> bytes:
    nsmap = cast("dict[str, str]", {None: TSL_NS, "ds": DS_NS})
    root = etree.Element(q("TrustServiceStatusList"), nsmap=nsmap)
    root.set("TSLTag", "https://uri.etsi.org/19612/TSLTag/")
    root.set("Id", "nxd-tl-qeaa-1")
    sub = make_sub(q)

    si = etree.SubElement(root, q("SchemeInformation"))
    sub(si, "TSLVersionIdentifier", "5")
    sub(si, "TSLSequenceNumber", str(sequence))
    sub(si, "TSLType", "https://uri.etsi.org/TrstSvc/TrustedList/TSLType/EUgeneric")
    sub(sub(si, "SchemeOperatorName"), "Name", OPERATOR["name"], lang="en")
    add_address(sub, sub(si, "SchemeOperatorAddress"),
                OPERATOR["street"], OPERATOR["locality"],
                OPERATOR["postal_code"], OPERATOR["country"], OPERATOR["emails"])
    sub(sub(si, "SchemeName"), "Name", LISTS["qeaa"]["scheme_name"], lang="en")
    sub(sub(si, "SchemeInformationURI"), "URI", f"{PAGES}/", lang="en")
    sub(si, "StatusDeterminationApproach",
        "https://uri.etsi.org/TrstSvc/TrustedList/StatusDetn/EUappropriate/")
    sub(sub(si, "SchemeTypeCommunityRules"), "URI",
        "https://uri.etsi.org/TrstSvc/TrustedList/schemerules/EU/", lang="en")
    sub(si, "SchemeTerritory", "TT")
    sub(si, "HistoricalInformationPeriod", "65535")
    sub(si, "ListIssueDateTime", issue)
    sub(sub(si, "NextUpdate"), "dateTime", nxt)

    entries = list(services_for(participants, "qeaa"))
    if entries:
        tspl = etree.SubElement(root, q("TrustServiceProviderList"))
        for p, svcs in entries:
            tsp = etree.SubElement(tspl, q("TrustServiceProvider"))
            info = etree.SubElement(tsp, q("TSPInformation"))
            sub(sub(info, "TSPName"), "Name", p["name"], lang="en")
            sub(sub(info, "TSPTradeName"), "Name",
                p.get("trade_name", p["name"]), lang="en")
            add_participant_address(sub, sub(info, "TSPAddress"), p)
            sub(sub(info, "TSPInformationURI"), "URI",
                p["information_uri"], lang="en")
            tspss = sub(tsp, "TSPServices")
            for s in svcs:
                sinfo = sub(sub(tspss, "TSPService"), "ServiceInformation")
                sub(sinfo, "ServiceTypeIdentifier", QEAA_SVC_TYPE)
                sub(sub(sinfo, "ServiceName"), "Name", s["name"], lang="en")
                sdi = sub(sinfo, "ServiceDigitalIdentity")
                for v in s["digital_ids"]["x509_certificates"]:
                    sub(sub(sdi, "DigitalId"), "X509Certificate", v)
                sub(sinfo, "ServiceStatus", QEAA_SVC_STATUS)
                sub(sinfo, "StatusStartingTime",
                    s.get("status_starting_time", issue))
                if s.get("service_supply_points"):
                    ssp = sub(sinfo, "ServiceSupplyPoints")
                    for u in s["service_supply_points"]:
                        sub(ssp, "ServiceSupplyPoint", u)
    return etree.tostring(root, encoding="UTF-8", xml_declaration=True,
                          pretty_print=True)


# --------------------------------------------------------------------------
# TS 119 602 LoTE (JSON + XML)
# --------------------------------------------------------------------------

def _ml(value: str) -> list[dict[str, str]]:
    return [{"lang": "en", "value": value}]


def _mluri(uris: list[str]) -> list[dict[str, str]]:
    return [{"lang": "en", "uriValue": u} for u in uris]


def build_lote_json(cfg: dict[str, str], ents: list[dict[str, Any]], issue: str,
                    nxt: str, sequence: int) -> dict[str, Any]:
    lasi = {
        "LoTEVersionIdentifier": 1,
        "LoTESequenceNumber": sequence,
        "LoTEType": cfg["lote_type"],
        "SchemeOperatorName": _ml(OPERATOR["name"]),
        "SchemeOperatorAddress": {
            "SchemeOperatorPostalAddress": [{
                "lang": "en",
                "StreetAddress": OPERATOR["street"],
                "Locality": OPERATOR["locality"],
                "PostalCode": OPERATOR["postal_code"],
                "Country": OPERATOR["country"],
            }],
            "SchemeOperatorElectronicAddress": _mluri(
                OPERATOR["emails"] + [f"{PAGES}/"]),
        },
        "SchemeName": _ml(cfg["scheme_name"]),
        "SchemeInformationURI": _mluri(
            [f"{PAGES}/", "https://github.com/NXD-Foundation/nxd-trust-list"]),
        "StatusDeterminationApproach": cfg["status_detn"],
        "SchemeTypeCommunityRules": _mluri([cfg["rules"]]),
        "SchemeTerritory": "EU",
        "ListIssueDateTime": issue,
        "NextUpdate": nxt,
        "DistributionPoints": [f"{PAGES}/{LIST_DIR}/{cfg['json']}"],
    }
    entities = []
    for e in ents:
        p = e["p"]
        services = []
        for s in e["services"]:
            entry = {
                "ServiceTypeIdentifier": cfg["svc_type"],
                "ServiceName": _ml(s["name"]),
                "ServiceDigitalIdentity": {
                    "X509Certificates": [{"val": v} for v in s["x509"]],
                },
                "ServiceStatus": cfg["svc_status"],
                "StatusStartingTime": s["start"],
            }
            if s["supply"]:
                entry["ServiceSupplyPoints"] = [
                    {"uriValue": u} for u in s["supply"]]
            services.append({"ServiceInformation": entry})
        entities.append({
            "TrustedEntityInformation": {
                "TEName": _ml(p["name"]),
                "TETradeName": _ml(p.get("trade_name", p["name"])),
                "TEAddress": {
                    "TEPostalAddress": [{
                        "lang": "en",
                        "StreetAddress": p["address"]["street"],
                        "Locality": p["address"]["locality"],
                        "PostalCode": p["address"].get("postal_code", ""),
                        "Country": p["address"]["country"],
                    }],
                    "TEElectronicAddress": _mluri(p["electronic_addresses"]),
                },
                "TEInformationURI": _mluri([p["information_uri"]]),
            },
            "TrustedEntityServices": services,
        })
    lote: dict[str, Any] = {"LoTE": {"ListAndSchemeInformation": lasi}}
    if entities:  # TrustedEntitiesList has minItems 1 -> omit when empty
        lote["LoTE"]["TrustedEntitiesList"] = entities
    return lote


def build_lote_xml(cfg: dict[str, str], ents: list[dict[str, Any]], issue: str,
                   nxt: str, sequence: int) -> bytes:
    nsmap = cast("dict[str, str]", {None: LOTE_NS, "ds": DS_NS})
    root = etree.Element(lq("TrustedEntitiesList"), nsmap=nsmap)
    root.set("LOTETag", "https://uri.etsi.org/19602/LOTETag/")
    root.set("Id", f"nxd-{cfg['tl_type']}-1")
    sub = make_sub(lq)

    def named(parent: etree._Element, tag: str, value: str) -> None:
        sub(sub(sub(parent, tag), "Name", lang="en"),
            "NonEmptyNormalizedString", value)

    lasi = etree.SubElement(root, lq("ListAndSchemeInformation"))
    sub(lasi, "LoTEVersionIdentifier", "1")
    sub(lasi, "LoTESequenceNumber", str(sequence))
    sub(lasi, "LoTEType", cfg["lote_type"])
    named(lasi, "SchemeOperatorName", OPERATOR["name"])
    add_address(sub, sub(lasi, "SchemeOperatorAddress"),
                OPERATOR["street"], OPERATOR["locality"],
                OPERATOR["postal_code"], OPERATOR["country"],
                OPERATOR["emails"] + [f"{PAGES}/"])
    named(lasi, "SchemeName", cfg["scheme_name"])
    sub(sub(lasi, "SchemeInformationURI"), "URI", f"{PAGES}/", lang="en")
    sub(lasi, "StatusDeterminationApproach", cfg["status_detn"])
    sub(sub(lasi, "SchemeTypeCommunityRules"), "URI", cfg["rules"], lang="en")
    sub(lasi, "SchemeTerritory", "EU")
    sub(sub(lasi, "PolicyOrLegalNotice"), "LoTEPolicy", f"{PAGES}/", lang="en")
    sub(lasi, "ListIssueDateTime", issue)
    sub(sub(lasi, "NextUpdate"), "dateTime", nxt)

    tel = sub(root, "TrustedEntitiesList")  # kept even when empty
    for e in ents:
        p = e["p"]
        te = sub(tel, "TrustedEntity")
        tei = sub(te, "TrustedEntityInformation")
        named(tei, "TEName", p["name"])
        named(tei, "TETradeName", p.get("trade_name", p["name"]))
        add_participant_address(sub, sub(tei, "TEAddress"), p)
        sub(sub(tei, "TEInformationURI"), "URI", p["information_uri"], lang="en")
        tes = sub(te, "TrustedEntityServices")
        for s in e["services"]:
            si = sub(sub(tes, "TrustedEntityService"), "ServiceInformation")
            sub(si, "ServiceTypeIdentifier", cfg["svc_type"])
            named(si, "ServiceName", s["name"])
            sdi = sub(si, "ServiceDigitalIdentity")
            for v in s["x509"]:
                sub(sub(sdi, "DigitalId"), "X509Certificate", v)
            sub(si, "ServiceStatus", cfg["svc_status"])
            sub(si, "StatusStartingTime", s["start"])
            if s["supply"]:
                ssp = sub(si, "ServiceSupplyPoints")
                for u in s["supply"]:
                    sub(ssp, "ServiceSupplyPoint", u)
    return etree.tostring(root, encoding="UTF-8", xml_declaration=True,
                          pretty_print=True)


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def resolve_key_cert(args: argparse.Namespace) -> tuple[bytes | None, bytes | None]:
    if args.no_sign:
        return None, None
    if args.signing_key and args.signing_cert:
        return (Path(args.signing_key).read_bytes(),
                Path(args.signing_cert).read_bytes())
    env_key = os.environ.get("NXD_TL_SIGNING_KEY")
    env_cert = os.environ.get("NXD_TL_SIGNING_CERT")
    if env_key and env_cert:
        return env_key.encode(), env_cert.encode()
    key_path = REPO / "certs/nxd-tl-signing-key.pem"
    cert_path = REPO / "certs/nxd-tl-signing-cert.pem"
    if key_path.exists() and cert_path.exists():
        return key_path.read_bytes(), cert_path.read_bytes()
    raise SystemExit("No signing key/cert found (use --no-sign for unsigned output)")


def submission_entry(cfg: dict[str, str], cert_text: str) -> dict[str, Any]:
    urls = {"tl_url": f"{PAGES}/{LIST_DIR}/{cfg.get('json', cfg['xml'])}",
            "tl_url_xml": f"{PAGES}/{LIST_DIR}/{cfg['xml']}"}
    if "json" in cfg:
        urls["tl_url_json"] = f"{PAGES}/{LIST_DIR}/{cfg['json']}"
    return {
        **urls,
        "trust_anchor": cert_text,
        "metadata": {"operator_name": OPERATOR["name"],
                     "country": OPERATOR["country"]},
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--onboarding-dir", default=str(REPO / "onboarding"))
    parser.add_argument("--output-dir", default=str(REPO))
    parser.add_argument("--signing-key")
    parser.add_argument("--signing-cert")
    parser.add_argument("--no-sign", action="store_true")
    parser.add_argument("--sequence", type=int,
                        default=int(os.environ.get("NXD_TL_SEQUENCE", "1")))
    parser.add_argument("--issue-date", default=None,
                        help="UTC, YYYY-MM-DDThh:mm:ssZ (default: now)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out = Path(args.output_dir)
    (out / LIST_DIR).mkdir(parents=True, exist_ok=True)

    if args.issue_date:
        issue_dt = datetime.strptime(
            args.issue_date, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    else:
        issue_dt = datetime.now(UTC).replace(microsecond=0)
    issue = issue_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    nxt = add_six_months(issue_dt).strftime("%Y-%m-%dT%H:%M:%SZ")

    key, cert = resolve_key_cert(args)
    participants = load_participants(Path(args.onboarding_dir))
    print(f"participants: {len(participants)}; "
          f"issue={issue} next={nxt} seq={args.sequence}")

    xsd = etree.XMLSchema(etree.parse(str(SCHEMAS / "19612_xsd.xsd")))
    lote_schema = json.loads((SCHEMAS / "1960201_json_schema.json").read_text())
    lote_validator = jsonschema.Draft202012Validator(
        lote_schema, format_checker=jsonschema.FormatChecker())
    signed_note = " (signed, verified)" if key else " (UNSIGNED)"

    # QEAA TSL
    tsl = build_qeaa_tsl(participants, issue, nxt, args.sequence)
    if key and cert:
        tsl = sign_xml(tsl, key, cert)
        verify_xml(tsl, cert)
    if not xsd.validate(etree.fromstring(tsl)):
        for e in cast("Iterable[Any]", xsd.error_log):
            print("XSD:", e.line, e.message[:160], file=sys.stderr)
        return 1
    (out / LIST_DIR / LISTS["qeaa"]["xml"]).write_bytes(tsl)
    n_tsps = tsl.count(b"<TrustServiceProvider>")
    print(f"qeaa: {n_tsps} TSPs -> {LISTS['qeaa']['xml']}{signed_note}, XSD valid")

    # LoTE lists
    for list_key, cfg in LISTS.items():
        if list_key == "qeaa":
            continue
        ents = entity_dicts(participants, list_key, issue)

        doc = build_lote_json(cfg, ents, issue, nxt, args.sequence)
        errors = list(lote_validator.iter_errors(doc))
        if errors:
            for e in errors[:10]:
                print(f"JSON schema ({cfg['json']}):",
                      "/".join(map(str, e.absolute_path)),
                      e.message[:160], file=sys.stderr)
            return 1
        if key and cert:
            doc = sign_json(doc, key, cert)
            verify_json(doc)
        (out / LIST_DIR / cfg["json"]).write_text(
            json.dumps(doc, indent=2, ensure_ascii=False) + "\n")

        lote_xml = build_lote_xml(cfg, ents, issue, nxt, args.sequence)
        if key and cert:
            lote_xml = sign_xml(lote_xml, key, cert)
            verify_xml(lote_xml, cert)
        (out / LIST_DIR / cfg["xml"]).write_bytes(lote_xml)

        n_svcs = sum(len(e["services"]) for e in ents)
        print(f"{list_key}: {len(ents)} entities, {n_svcs} services "
              f"-> {cfg['xml']} + {cfg['json']}{signed_note}")

    # LoTL tl_entries submission files (need the public cert as trust anchor)
    if cert:
        for cfg in LISTS.values():
            dest = out / "lotl-submission" / cfg["tl_type"] / "nxd-foundation.json"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(json.dumps(
                submission_entry(cfg, cert.decode()), indent=2) + "\n")
        print(f"lotl-submission entries: "
              f"{sorted(c['tl_type'] for c in LISTS.values())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
