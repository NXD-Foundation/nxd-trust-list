# Pull Request

## Type of change

- [ ] Participant onboarding (new `onboarding/<participant_id>.json`)
- [ ] Participant update (service added/changed/withdrawn)
- [ ] Participant removal
- [ ] Tooling / documentation / other

## Description

<!-- Who is the participant, what services are being registered, and in which
lists (qeaa, eaa, pub-eaa, pid, wallet, wrpac, wrprc, registrars)? -->

## Onboarding checklist

<!-- Delete this section for non-onboarding changes. -->

- [ ] File is `onboarding/<participant_id>.json` and `participant_id` matches the file name
- [ ] Entry validates against [`onboarding/schema/participant.schema.json`](../onboarding/schema/participant.schema.json)
- [ ] Every service carries at least one X.509 certificate (base64 DER, no PEM header/footer lines)
- [ ] Certificates belong to the participant and correspond to the keys used by the listed services
- [ ] Contact details (address, electronic addresses, information URI) are accurate
- [ ] I am authorized to register this organisation in the NXD Foundation trust lists

## Notes for reviewers

<!-- Anything the NXD Foundation reviewers should verify out-of-band, e.g. how
to confirm the certificate belongs to the participant. -->
