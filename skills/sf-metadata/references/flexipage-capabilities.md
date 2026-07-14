# FlexiPage Capabilities Reference

Catalogues every `FlexiPage` page type the Salesforce Metadata API recognizes
(API v66), grouped by surface, with the per-type rules the validator and the
skill workflow rely on. Pair this with `flexipage-metadata-schema.json` for
shape validation.

The page type is set in the `type` element of the FlexiPage payload. It drives
which template names are valid, whether `sobjectType` is required or forbidden,
and which components / regions the renderer accepts.

## Quick contract table

| `type`                        | `sobjectType` | `template.name` (typical)                           | Regions required? | Notes                                                  |
| ----------------------------- | ------------- | --------------------------------------------------- | ----------------- | ------------------------------------------------------ |
| `RecordPage`                  | **Required**  | `flexipage:recordHomeTemplateDesktop`               | Yes               | Mobile uses `flexipage:recordHomeTemplateMobile`       |
| `ObjectPage`                  | **Required**  | `flexipage:objectHomeTemplateDesktop`               | Yes               | Object Home (list-view container)                      |
| `AppPage`                     | Must NOT set  | `flexipage:defaultAppHomeTemplate`                  | Yes               | Custom Lightning App tab                               |
| `HomePage`                    | Must NOT set  | `home:desktopTemplate`                              | Yes               | Regions: `top`, `bottomLeft`, `bottomRight`, `sidebar` |
| `EasyHomePage`                | Must NOT set  | `flexipage:easyHomeTemplate`                        | Yes               | Easy-mode home (Spring '24+)                           |
| `ApplicationLayout`           | Must NOT set  | `forceApp:applicationLayoutTemplate`                | Yes               | Lightning App container shell                          |
| `UtilityBar`                  | Must NOT set  | (no template / `flexipage:utilityBar`)              | Optional          | Utility bar items definition                           |
| `MobileAppPage`               | Must NOT set  | `flexipage:mobileAppHomeTemplate`                   | Yes               | Mobile App Home                                        |
| `RecordPreview`               | Optional      | `flexipage:recordPreviewTemplate`                   | Optional          | Hover-card / preview panel for a record                |
| `ForecastingPage`             | Must NOT set  | `forecasting:forecastingTemplate`                   | Yes               | Forecasting (Collaborative Forecasts)                  |
| `OmniSupervisorPage`          | Must NOT set  | `runtime_omnichannel_supervisor:supervisorTemplate` | Yes               | Omni-Channel Supervisor                                |
| `EmbeddedServicePage`         | Must NOT set  | `embeddedService:flowTemplate` or chat              | Yes               | Embedded Service / Chat / Messaging                    |
| `ServiceDocument`             | Must NOT set  | varies                                              | Yes               | Service Document (Field Service)                       |
| `LandingPage`                 | Must NOT set  | `flexipage:landingPageTemplate`                     | Yes               | Marketing / Pardot landing page                        |
| `CardPage`                    | Must NOT set  | `flexipage:cardPageTemplate`                        | Yes               | Reusable card (Spring '23+)                            |
| `CdpRecordPage`               | **Required**  | `flexipage:recordHomeTemplateDesktop`               | Yes               | CDP / Data Cloud DMO record page                       |
| `ConfiguratorAppPage`         | Must NOT set  | (varies)                                            | Yes               | Configurator (Revenue Cloud / CPQ+)                    |
| `VoiceExtension`              | Must NOT set  | (varies)                                            | Optional          | Service Cloud Voice extension                          |
| `MailAppAppPage`              | Must NOT set  | `flexipage:mailAppHomeTemplate`                     | Yes               | Lightning for Outlook / Gmail App tab                  |
| `EmailContentPage`            | Must NOT set  | `flexipage:emailContentTemplate`                    | Yes               | Email Content Builder body                             |
| `EmailTemplatePage`           | Must NOT set  | `flexipage:emailTemplatePage`                       | Yes               | Lightning Email Template editor                        |
| `SlackAppHome`                | Must NOT set  | `slack:appHomeTemplate`                             | Yes               | Slack app home tab                                     |
| `SlackMessage`                | Must NOT set  | `slack:messageTemplate`                             | Yes               | Slack message blocks                                   |
| `SlackModal`                  | Must NOT set  | `slack:modalTemplate`                               | Yes               | Slack modal blocks                                     |
| `SlackNotification`           | Must NOT set  | `slack:notificationTemplate`                        | Optional          | Slack notification payload                             |
| `CommAppPage`                 | Must NOT set  | `comm:appHomeTemplate`                              | Yes               | Experience Cloud App page                              |
| `CommObjectPage`              | **Required**  | `comm:objectHomeTemplate`                           | Yes               | Experience Cloud object list view                      |
| `CommRecordPage`              | **Required**  | `comm:recordHomeTemplate`                           | Yes               | Experience Cloud record page                           |
| `CommRelatedListPage`         | **Required**  | `comm:relatedListTemplate`                          | Yes               | Experience Cloud related list                          |
| `CommQuickActionCreatePage`   | **Required**  | varies                                              | Yes               | Experience Cloud quick action create form              |
| `CommThemeLayoutPage`         | Must NOT set  | `comm:themeLayoutTemplate`                          | Yes               | Experience Cloud theme layout                          |
| `CommLoginPage`               | Must NOT set  | `comm:loginTemplate`                                | Yes               | Experience Cloud login page                            |
| `CommForgotPasswordPage`      | Must NOT set  | `comm:forgotPasswordTemplate`                       | Yes               | Experience Cloud forgot-password                       |
| `CommSelfRegisterPage`        | Must NOT set  | `comm:selfRegisterTemplate`                         | Yes               | Experience Cloud self-register                         |
| `CommSearchResultPage`        | Must NOT set  | `comm:searchResultTemplate`                         | Yes               | Experience Cloud search results                        |
| `CommGlobalSearchResultPage`  | Must NOT set  | `comm:globalSearchResultTemplate`                   | Yes               | Experience Cloud global search                         |
| `CommNoSearchResultsPage`     | Must NOT set  | `comm:noSearchResultsTemplate`                      | Yes               | Experience Cloud "no results" page                     |
| `CommFlowPage`                | Must NOT set  | `comm:flowTemplate`                                 | Yes               | Experience Cloud Flow page                             |
| `CommCheckoutPage`            | Must NOT set  | `comm:checkoutTemplate`                             | Yes               | B2B / B2C Commerce checkout                            |
| `CommOrderConfirmationPage`   | Must NOT set  | `comm:orderConfirmationTemplate`                    | Yes               | Commerce order confirmation                            |
| `CommElectronicSignaturePage` | Must NOT set  | `comm:electronicSignatureTemplate`                  | Yes               | Contract e-signature page                              |
| `CommContractDocumentsPage`   | Must NOT set  | `comm:contractDocumentsTemplate`                    | Yes               | Contract documents page                                |
| `CommContractDetailViewPage`  | Must NOT set  | `comm:contractDetailViewTemplate`                   | Yes               | Contract detail view                                   |

"Must NOT set" means including `sobjectType` may be silently ignored or rejected
depending on type — keep the payload clean. "Optional" templates mean Salesforce
will accept different templates; the names listed are the most common defaults.

## Page-type categories

### 1. Standard Lightning App pages

Used in Lightning Experience for the main desktop / mobile app:

- **`RecordPage`** — the page that replaces a Classic record page layout. Requires
  `sobjectType`. Highlights panel, detail panel, related lists, etc. The desktop
  template (`flexipage:recordHomeTemplateDesktop`) has three regions: `header`,
  `main`, `sidebar`. The mobile template (`flexipage:recordHomeTemplateMobile`)
  uses a single `main` region.
- **`ObjectPage`** — Object Home (the page you land on when you click the tab,
  before opening a specific record). Requires `sobjectType`.
- **`AppPage`** — generic tab inside a Lightning App. Must NOT specify
  `sobjectType`. Used for dashboards, custom landing tabs, etc.
- **`HomePage`** — replaces the Lightning Home tab. Must NOT specify
  `sobjectType`. Template provides exactly four regions: `top`, `bottomLeft`,
  `bottomRight`, `sidebar` — there is no native three-column layout.
- **`EasyHomePage`** — Spring '24+ simplified Home for new orgs / "Easy" setup.
  Must NOT specify `sobjectType`.
- **`ApplicationLayout`** — defines the App-level layout shell (utility bar
  region, etc.). Must NOT specify `sobjectType`.
- **`UtilityBar`** — utility bar configuration (phone, history, notes, custom
  LWCs). Items are declared via component instances; regions may be empty.
- **`MobileAppPage`** — mobile App Home, distinct from desktop AppPage.
- **`RecordPreview`** — hover / preview card configuration; renders a subset of
  the record. Regions are optional (single-region templates).
- **`CardPage`** — reusable card definition referenced from other pages
  (`parentFlexiPage` is often used).

### 2. Experience Cloud (Communities)

Every `Comm*` type belongs to an Experience Cloud (LWR / Aura) site.
`CommRecordPage`, `CommObjectPage`, `CommRelatedListPage`, and
`CommQuickActionCreatePage` are object-bound and **require `sobjectType`**.
All other `Comm*` types must NOT specify `sobjectType`.

Use `comm:*` templates. Components are typically from the
`forceCommunity:*` and `community_layout:*` namespaces.

### 3. Slack pages

Native Salesforce-built Slack apps render Lightning components via the
`slack:*` template family. None of the Slack page types take `sobjectType`.

- **`SlackAppHome`** — the App Home tab content for a Slack app.
- **`SlackMessage`** — Slack message blocks (rich content posted into channels).
- **`SlackModal`** — modal dialog opened from a Slack interaction.
- **`SlackNotification`** — notification payload; regions are often empty.

Slack pages do not support browser-based visibility rules in the same way as
desktop pages — keep `visibilityRule` simple or omit it.

### 4. Email pages

- **`EmailContentPage`** — body of an Email Content record (drag-and-drop
  Email Content Builder).
- **`EmailTemplatePage`** — Lightning Email Template editor surface.

Neither accepts `sobjectType`. They use the `flexipage:richText` and
related email-specific components.

### 5. Forecasting & Service

- **`ForecastingPage`** — Collaborative Forecasts page. Must NOT specify
  `sobjectType`.
- **`OmniSupervisorPage`** — Omni-Channel Supervisor configuration. Must NOT
  specify `sobjectType`.
- **`EmbeddedServicePage`** — Embedded Service deployments (chat / messaging /
  Service Cloud Voice flows).
- **`ServiceDocument`** — Service Document layout (Field Service / Industries).
- **`VoiceExtension`** — Service Cloud Voice phone extension layout.

### 6. Mail / Outlook / Gmail

- **`MailAppAppPage`** — Lightning for Outlook / Gmail integration App page.
  Must NOT specify `sobjectType`.

### 7. Marketing / Data Cloud / Configurator

- **`LandingPage`** — Marketing Cloud Account Engagement (Pardot) landing page
  built as a FlexiPage.
- **`CdpRecordPage`** — Data Cloud (CDP) DMO record page. Requires
  `sobjectType` (the DMO API name).
- **`ConfiguratorAppPage`** — Revenue Cloud / Configurator app surface.

## Per-type field rules (validator-relevant)

The validator (`scripts/validate_metadata_operation.py`) enforces:

1. **`type` must be one of the enum values.** The list is kept in sync with
   `flexipage-metadata-schema.json`. Unknown types are flagged `critical`.
2. **`sobjectType` required when the type is in the required set:**
   `RecordPage`, `ObjectPage`, `CommRecordPage`, `CommObjectPage`,
   `CommRelatedListPage`, `CommQuickActionCreatePage`, `CdpRecordPage`.
3. **`sobjectType` must be absent when the type is in the forbidden set:**
   `AppPage`, `HomePage`, `EasyHomePage`, `ApplicationLayout`, `UtilityBar`,
   `MobileAppPage`, `ForecastingPage`, `OmniSupervisorPage`,
   `EmbeddedServicePage`, `ServiceDocument`, `LandingPage`, `CardPage`,
   `ConfiguratorAppPage`, `VoiceExtension`, `MailAppAppPage`,
   `EmailContentPage`, `EmailTemplatePage`, all `Slack*`,
   `CommAppPage`, `CommThemeLayoutPage`, `CommLoginPage`,
   `CommForgotPasswordPage`, `CommSelfRegisterPage`,
   `CommSearchResultPage`, `CommGlobalSearchResultPage`,
   `CommNoSearchResultsPage`, `CommFlowPage`, `CommCheckoutPage`,
   `CommOrderConfirmationPage`, `CommElectronicSignaturePage`,
   `CommContractDocumentsPage`, `CommContractDetailViewPage`.
4. **`template.name` should match the known default** for `RecordPage`,
   `ObjectPage`, `AppPage`, `HomePage` (warning if it doesn't). For other types
   the template field is enforced as present but not checked against a specific
   string — too much variance in the field.
5. **`flexiPageRegions` required** for almost every type. The exceptions
   (`UtilityBar`, `RecordPreview`, `SlackNotification`, `VoiceExtension`)
   downgrade the "no regions" finding to a warning instead of critical.
6. **`visibilityRule.criteria[*].operator` must be `EQUAL`** on every page
   type. All other operators are rejected with `FIELD_INTEGRITY_EXCEPTION`.

## Visibility rules — common to all page types

- `operator` must be `EQUAL`. `NOT_EQUAL`, `GREATER_THAN`, `LESS_THAN` etc. are
  rejected with `FIELD_INTEGRITY_EXCEPTION` at deploy time.
- Supported `leftValue` prefixes: `Record.<FieldApiName>`, `$User.<FieldName>`.
- `$Permission.PermissionSetName` is NOT supported as a leftValue — use a
  `$User` field-based check or assign visibility via a parent component.

## Components and regions cheat-sheet

| Region target          | Common componentName(s)                                                                                    |
| ---------------------- | ---------------------------------------------------------------------------------------------------------- |
| Header (RecordPage)    | `force:highlightsPanel`                                                                                    |
| Main (RecordPage)      | `force:detailPanel`, `flexipage:tabset`, `runtime_sales_pathassistant:pathAssistant`                       |
| Sidebar (RecordPage)   | `force:relatedListContainer`, `forceChatter:recordFeedContainer`, `runtime_sales_activities:activityPanel` |
| AppPage / HomePage     | `flexipage:richText`, `flexipage:tabset`, `flexipage:reportChart`                                          |
| Slack pages            | `slack:section`, `slack:divider`, `slack:input`, `slack:actions`                                           |
| Email pages            | `flexipage:richText`, `flexipage:emailContent`                                                             |
| Experience Cloud pages | `forceCommunity:*`, `community_layout:*`                                                                   |

Properties on `flexipage:richText` use `richTextValue` (not `markup`).

## Cross-references

- Schema: `references/flexipage-metadata-schema.json`
- Validator: `scripts/validate_metadata_operation.py` (`_check_flexipage_*`)
- Tests: `tests/test_flexipage_validation.py` and fixtures under
  `tests/fixtures/good-flexipage-*.json` / `bad-flexipage-*.json`
- Top-level skill notes: see "Lightning Page (FlexiPage) Reference" in
  `SKILL.md`
