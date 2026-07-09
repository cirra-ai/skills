<!-- Parent: sf-metadata/SKILL.md -->

# Access Strategy (Phase 3.5) — MANDATORY, NO GUESSWORK

Whenever you create a new **Custom Object**, **Custom Field**, or **List View**,
you MUST propose a specific, complete access strategy and get the user to
confirm the exact **profiles** and **permission sets** involved **before**
declaring the work done. **Never assume, never guess, never silently pick a
default.** If you do not yet know which profiles/permission sets should have
access, ask — do not invent one.

A newly deployed object or field is **invisible and unusable** until every
layer below is decided:

| Access layer                     | What it controls                                   | Where it is configured                                   | Permission Set? | Profile? |
| -------------------------------- | -------------------------------------------------- | -------------------------------------------------------- | --------------- | -------- |
| Object CRUD                      | Can the user access the object at all?             | `objectPermissions`                                      | ✅ Yes          | ✅ Yes   |
| Field-Level Security (FLS)       | Can the user see/edit each field?                  | `fieldPermissions`                                       | ✅ Yes          | ✅ Yes   |
| Page Layout assignment           | Which classic layout a user sees (per record type) | **Profile** `layoutAssignments`                          | ❌ No           | ✅ Yes   |
| Lightning Record Page assignment | Which Lightning (FlexiPage) a user sees            | FlexiPage **activation**: org default, or app/profile/RT | ❌ No           | ✅ Yes   |
| List View visibility             | Who can see a list view (and its Kanban)           | `ListView.sharedTo` / `filterScope`                      | n/a             | n/a      |

**Key consequence: FLS and object access can be granted via permission sets
(cheap, preferred), but page-layout and Lightning-page assignment can ONLY be
expressed against profiles.** So a truly complete access plan almost always
names specific profiles, not just permission sets. Do not paper over this — call
it out and get the exact profile names.

---

## The mandatory prompt

After a successful `metadata_create` of an object, field(s), or list view, ask
the user to specify the access plan. Use `AskUserQuestion`. Do **not** proceed
with a generic "Invoice_Access" permission set as if the audience were known.

```
AskUserQuestion:
  question: "Who should have access to <Artifact>? I need specifics — there should be no guesswork. Please confirm each layer:

    1. Object + Field access (CRUD + FLS): which PERMISSION SET(S) and/or PROFILE(S)?
       (Recommended: grant via permission sets, not profiles — see cost note.)
    2. Page Layout: which layout should each PROFILE (and record type) see?
    3. Lightning Record Page: org default, or assigned to specific apps / profiles / record types?
    4. (List views) Visibility: visible to all users, or shared only to specific groups/roles/queues?"
  header: "Access plan"
  options:
    - label: "I'll name the exact profiles & permission sets"
      description: "You provide the specific profile/permission-set names for each layer; I build them."
    - label: "Use one new permission set for object+FLS, leave layouts/pages manual"
      description: "I create <Object>_Access (object CRUD + FLS) and give you exact Setup steps for layout/page/list-view assignment (zero profile-edit credits)."
    - label: "Full strategy incl. profile layout assignment"
      description: "I also update the named profiles' layoutAssignments and activate the Lightning page (costs profile-update credits — see cost note)."
```

Never collapse this to a yes/no "generate a permission set?" question. The user
must end up naming the concrete profiles and permission sets for each layer.

---

## Layer 1 — Object CRUD + Field-Level Security

Prefer **permission sets** over profile edits (see the cost warning in
`SKILL.md`). Filter fields per the rules in `permset-auto-generation.md`
(required, Master-Detail, and Name fields are excluded; formula/roll-up fields
are read-only).

```
metadata_create(
  type="PermissionSet",
  metadata=[{
    "fullName": "Invoice_Access",
    "label": "Invoice Access",
    "description": "Grants access to Invoice__c and its fields",
    "objectPermissions": [{
      "object": "Invoice__c",
      "allowCreate": true, "allowRead": true, "allowEdit": true, "allowDelete": true,
      "viewAllRecords": false, "modifyAllRecords": false
    }],
    "fieldPermissions": [
      {"field": "Invoice__c.Amount__c", "editable": true, "readable": true}
    ]
  }],
  sf_user="<sf_user>"
)
```

If the user insists on profile-based access, confirm the **exact profile
names** first and warn about the per-profile credit cost.

---

## Layer 2 — Page Layout assignment (Profile-only)

A page layout only reaches a user through a **Profile** `layoutAssignments`
entry, optionally keyed by **record type**. There is no permission-set
equivalent. Get the exact profile name(s) and record type(s) — do not guess.

```
metadata_update(
  type="Profile",
  metadata=[{
    "fullName": "Sales User",
    "layoutAssignments": [
      {"layout": "Invoice__c-Invoice Layout", "recordType": "Invoice__c.Standard"}
    ]
  }],
  sf_user="<sf_user>"
)
```

**Cost note:** profile updates consume credits (one call per profile). If the
user prefers zero cost, provide exact Setup steps instead:
Setup → Object Manager → _Object_ → Page Layouts → **Page Layout Assignment** →
**Edit Assignment** (see [Assign Page Layouts to Profiles or Record Types](https://help.salesforce.com/s/articleView?id=platform.layouts_assigning.htm&language=en_US&type=5)).

---

## Layer 3 — Lightning Record Page (FlexiPage) assignment

Creating a FlexiPage is not enough — it must be **activated/assigned** or users
keep seeing the previous page. Confirm the intended scope explicitly:

| Assignment scope            | Effect                                                    |
| --------------------------- | --------------------------------------------------------- |
| Org Default                 | Default for the object across all apps                    |
| App Default                 | Default within specific Lightning app(s)                  |
| App + Record Type + Profile | Most specific; different page per profile/record-type/app |
| Form factor (Desktop/Phone) | Different page per device                                 |

Ask which scope and — for app/profile/record-type assignment — the **exact**
apps, profiles, and record types. Assignment steps:
Setup → Lightning App Builder → open page → **Activation** (see
[Activate Lightning Experience Record Pages](https://help.salesforce.com/s/articleView?id=sf.lightning_app_builder_customize_lex_pages_activate.htm&language=en_US&type=5)).

---

## Layer 4 — List Views (and Kanban) — NO GUESSWORK

Creating a list view has the same "who can see it?" question. Every `ListView`
needs an explicit visibility decision — never default silently.

**Visibility is set on the `ListView` itself** via `filterScope` and, for
group/role/queue sharing, `sharedTo` (see
[ListView | Metadata API Developer Guide](https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_listview.htm)
and [SharedTo](https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_sharedto.htm)):

| `filterScope` | Meaning                                                  |
| ------------- | -------------------------------------------------------- |
| `Everything`  | All records the user can see (typical "All …" list view) |
| `Mine`        | Records owned by the running user                        |
| `Queue`       | Records in the queue named by `queue`                    |

```
metadata_create(
  type="ListView",
  metadata=[{
    "fullName": "Invoice__c.Open_Invoices",
    "label": "Open Invoices",
    "filterScope": "Everything",
    "columns": ["NAME", "STATUS__C", "AMOUNT__C"],
    "filters": [{"field": "Invoice__c.Status__c", "operation": "equals", "value": "Open"}],
    "sharedTo": {                       // omit ⇒ visible to all users
      "group": ["Invoice_Team"]         // or role / roleAndSubordinates / queue
    }
  }],
  sf_user="<sf_user>"
)
```

Confirm with the user: **visible to all users**, or **shared only to specific
public groups / roles / queues** — then set `sharedTo` accordingly (omit it only
when the user explicitly wants it visible to everyone).

### Kanban view — important accuracy caveat

A **Kanban view is not its own metadata type**. It is a per-list-view **display
mode** configured in the UI, and Kanban settings are stored per list view (see
[Set Up a Kanban View](https://help.salesforce.com/s/articleView?id=sf.kanban_configuration.htm&language=en_US&type=5)).
The `ListView` metadata has **no** Kanban field, so Kanban itself cannot be
deployed via `metadata_create`. Do not claim to have created a Kanban view via
metadata.

What you MUST do so the Kanban works with no guesswork:

1. **Confirm the list view's visibility** (`sharedTo` / `filterScope`) — this is
   what governs who can open the Kanban, since the Kanban rides on the list view.
2. **Verify the grouping field exists.** Kanban groups records by a **picklist**
   (e.g. `Status__c`) — create it first if missing.
3. **Verify the summary field exists** if the user wants column sums (a
   Currency/Number field).
4. **Give exact UI steps** to switch the list view to Kanban:
   open the list view → **Display As** (gear/toggle) → **Kanban** → set
   **Group By** = the picklist and **Summarize By** = the number field
   (see [Set Up a Kanban View](https://help.salesforce.com/s/articleView?id=sf.kanban_configuration.htm&language=en_US&type=5)).

---

## Completion gate

Do not report the object/field/list-view work as "done" until, for each new
artifact, you have stated **who** has access at every applicable layer, naming
the **specific** permission sets and profiles (and, for list views, the exact
`sharedTo` audience). If any layer is intentionally left to the user, say so
explicitly and give the exact Setup navigation — never leave it implicit.
