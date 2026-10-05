# Architecture

## Conceptual model

The Homelab is organized around four responsibilities:

| Component | Responsibility |
| --- | --- |
| Cloud infrastructure | Identity, governance, security foundations, and deployment controls |
| Security analytics | Telemetry storage, normalization, investigation, and querying |
| Detection engineering | Detection content, testing, and validation |
| Operations interface | Change awareness and bounded automation |

These responsibilities describe the overall design, independent of specific tools, repository names, or implementation status.

## Engineering principles

Use least privilege and explicit security boundaries. Preserve useful evidence, validate outcomes, and keep cost and complexity proportionate to the lab.

Analytics supports reproducible investigations. Detections are tested against representative evidence. Automation uses bounded permissions and observable outcomes.

## Repository and disclosure boundaries

`homelab` contains public project documentation and architectural decisions. Component repositories own their implementation and supporting documentation. Authoritative infrastructure is maintained privately.

Public material describes generalized patterns and design rationale. Sensitive identifiers, access relationships, secrets metadata, and reconnaissance-relevant operational details remain private. Reference examples are written deliberately rather than copied from the live environment.

Roadmap, priorities, and progress are tracked in GitHub Projects, with actionable work defined in Issues.
