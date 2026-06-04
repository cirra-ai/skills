# Sandbox Types Guide

Comparison matrix for Salesforce sandbox types and scratch orgs.

## Sandbox Types

| Property        | Developer                 | Developer Pro                         | Partial Copy                      | Full Copy                              |
| --------------- | ------------------------- | ------------------------------------- | --------------------------------- | -------------------------------------- |
| **Data**        | Schema only               | Schema only                           | Schema + sample data              | Full production clone                  |
| **Storage**     | 200 MB                    | 1 GB                                  | 5 GB                              | Same as production                     |
| **Refresh**     | 1 day                     | 1 day                                 | 5 days                            | 29 days                                |
| **Create Time** | 5–30 minutes              | 5–30 minutes                          | 1–6 hours                         | 2–24 hours                             |
| **Best For**    | Feature dev, unit testing | Performance testing, larger data sets | UAT with realistic data, training | Staging, migration testing, compliance |
| **Limits (EE)** | 25                        | 5                                     | 5                                 | 1                                      |
| **Limits (UE)** | 100                       | 10                                    | 5                                 | 1                                      |

## Scratch Orgs

| Property        | Scratch Org                                             |
| --------------- | ------------------------------------------------------- |
| **Data**        | Empty (schema from definition file)                     |
| **Storage**     | 200 MB                                                  |
| **Duration**    | 1–30 days (default 7)                                   |
| **Create Time** | 1–5 minutes                                             |
| **Best For**    | Short-lived feature development, CI/CD, package testing |
| **Limits**      | 40 active (Enterprise), 80 active (Unlimited)           |
| **Requires**    | Dev Hub enabled, Salesforce CLI                         |

## When to Use Each

### Developer Sandbox

- Quick feature development
- Unit testing
- Isolated changes that don't need production data
- When you need installed packages from production

### Developer Pro Sandbox

- Performance testing with larger datasets
- Integration testing with moderate data volumes
- When 200 MB is too small but you don't need production data

### Partial Copy Sandbox

- User acceptance testing (UAT) with realistic data
- Training environments
- When testers need to see real (sampled) records
- Sandbox template controls which records are copied

### Full Copy Sandbox

- Staging / pre-production validation
- Data migration testing (need to verify against real volumes)
- Compliance testing
- Disaster recovery rehearsals

### Scratch Org

- Source-driven development (2GP / unlocked packages)
- CI/CD pipelines (ephemeral, reproducible)
- Quick prototyping (spin up in minutes, throw away)
- When you need a clean slate without production config baggage

## Sandbox vs Scratch Org — Quick Decision

| Question                               | Sandbox | Scratch Org |
| -------------------------------------- | ------- | ----------- |
| Need production data?                  | ✓       | ✗           |
| Need installed managed packages?       | ✓       | Depends     |
| Need it for more than 30 days?         | ✓       | ✗           |
| Need it in under 5 minutes?            | ✗       | ✓           |
| Need a fully reproducible environment? | ✗       | ✓           |
| Using source-driven development?       | Either  | ✓ Preferred |
| Non-technical user / no CLI?           | ✓       | ✗           |

## LicenseType Mapping

The `SandboxInfo.LicenseType` field uses these values (used by the Tooling API):

| Display Name  | LicenseType Value |
| ------------- | ----------------- |
| Developer     | `DEVELOPER`       |
| Developer Pro | `DEVELOPER_PRO`   |
| Partial Copy  | `PARTIAL`         |
| Full Copy     | `FULL`            |
