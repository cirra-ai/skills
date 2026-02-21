---
name: create-diagram
description: Create a Salesforce architecture diagram using Mermaid. Supports OAuth flows, data models (ERDs), integration sequences, system landscapes, role hierarchies, and Agentforce flows.
---

Create a Salesforce architecture diagram in Mermaid format with ASCII fallback.

## Parsing the request

| Input after `/create-diagram` | Interpretation |
| ----------------------------- | ------------------------------------------------------------ |
| `JWT Bearer` | OAuth flow diagram - JWT Bearer |
| `Account Contact Opportunity` | ERD with those objects |
| `integration with SAP` | Integration sequence diagram |
| `role hierarchy` | Role/permission hierarchy |
| _(no argument)_ | Ask what type of diagram to create |

## Workflow

### 1. Gather requirements

Use AskUserQuestion to determine:

- **Diagram type**: OAuth Flow, ERD/Data Model, Integration Sequence, System Landscape, Role Hierarchy, Agentforce Flow
- **Scope**: Which objects/systems/flows to include
- **Output preference**: Mermaid + ASCII (default), or one format only

### 2. Collect data

**For ERD diagrams with org connection**:

Describe each object to discover real relationships:

```
sobject_describe(sObject="Account", sf_user="<sf_user>")
sobject_describe(sObject="Contact", sf_user="<sf_user>")
```

Optionally get record counts for LDV indicators:

```
soql_query(sObject="Account", fields=["COUNT(Id)"], sf_user="<sf_user>")
```

**For OAuth/integration/landscape diagrams**: Use the built-in templates from `assets/`.

### 3. Select and load template

Read the appropriate template from the skill's `assets/` directory to use as a starting point.

### 4. Generate the diagram

**Mermaid**:
- Apply the color scheme (Standard=Blue `#bae6fd`, Custom=Orange `#fed7aa`, External=Green `#a7f3d0`)
- Use `autonumber` for sequence diagrams
- For ERDs: Use `flowchart LR` with object-type color coding
- Keep ERD objects simple: name + record count only (no fields)
- Use `-->` for Lookup, `==>` for Master-Detail relationships

**ASCII**:
- Use box-drawing characters for terminal compatibility
- Keep width under 80 characters
- Add step numbers for sequences

### 5. Score and deliver

Score the diagram against the 80-point rubric:
- Accuracy (20): Correct actors, flow steps, relationships
- Clarity (20): Easy to read, proper labeling
- Completeness (15): All relevant steps/entities included
- Styling (15): Color scheme, theming, annotations
- Best Practices (10): Proper notation, conventions

Present both Mermaid and ASCII versions with key points and the score.
