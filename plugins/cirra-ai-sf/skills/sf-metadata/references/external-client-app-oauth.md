<!-- Parent: sf-metadata/SKILL.md -->

# External Client Apps (ECA) — OAuth policies

External Client Apps (ECAs) are the modern replacement for Connected Apps. The
moment OAuth is enabled on an ECA, Salesforce **auto-generates a separate
`ExtlClntAppOauthConfigurablePolicies` record** that holds everything an admin
thinks of as "the app's OAuth policies": who may authorize the app, refresh-token
lifetime, IP relaxation, required session level. None of that lives on
`ExternalClientApplication` itself, and the policy record's name is not surfaced
anywhere obvious in Setup.

Type facts, from the Metadata API Developer Guide
([ExtlClntAppOauthConfigurablePolicies](https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_extlclntappoauthconfigurablepolicies.htm)):

| Fact                   | Value                                                        |
| ---------------------- | ------------------------------------------------------------ |
| Metadata type          | `ExtlClntAppOauthConfigurablePolicies`                       |
| File suffix / folder   | `.ecaOauthPlcy` in `extlClntAppOauthPolicies`                |
| Available since        | API v59.0                                                    |
| Required field         | `externalClientApplication` — the ECA's developer name       |
| Related settings types | `ExtlClntAppOauthSettings`, `ExtlClntAppGlobalOauthSettings` |

---

## 1. Find the policy record — do NOT guess its fullName

**This is the step most likely to trip you up.** The policy record exists as soon
as OAuth is enabled on the ECA, but nothing in Setup or in the
`ExternalClientApplication` metadata shows its name, and **its `fullName` is not
the same as the ECA's own developer name**.

❌ **Do not assume `fullName` = `{ECA_DeveloperName}`.** It either matches nothing
on `metadata_read`, or — if you upsert with it — fails with a duplicate-value
error.

✅ **The convention observed in practice is `{ECA_DeveloperName}_oauthPlcy`**
(corroborated by community deployment guides, which ship the component as
`MyApp_oauthPlcy.ecaOauthPlcy-meta.xml`). Treat it as a strong hint to verify,
never as a fact to write against blind.

### Discovery ladder — cheapest first

1. **`metadata_list`** for the type. Free when it works, but `listMetadata` does
   not return every type in every org/connector — if it comes back empty, that is
   not proof the record is absent.

   ```
   metadata_list(
     type="ExtlClntAppOauthConfigurablePolicies",
     sf_user="{sf_user}"
   )
   ```

2. **`metadata_read` the conventional name.** If it reads back a populated
   object, you have the record and its current state in one call.

   ```
   metadata_read(
     type="ExtlClntAppOauthConfigurablePolicies",
     fullNames=["{ECA_DeveloperName}_oauthPlcy"],
     sf_user="{sf_user}"
   )
   ```

3. **Provoke the duplicate-value error.** If neither of the above resolves the
   name, deliberately upsert with a throwaway name. Salesforce enforces one
   policy record per OAuth settings record, so the collision names the real
   record for you — the error message is a gift:

   ```
   DUPLICATE_VALUE: ExtlClntAppOauthSettingsId duplicates value on {ECA_DeveloperName}_oauthPlcy
   ```

   Re-run against the name in that message.

   **Safety note:** the collision is on `ExtlClntAppOauthSettingsId`, so a
   throwaway upsert that _succeeds_ instead of erroring means the ECA had no
   policy record at all — you just created one under a junk name. Use an
   obviously disposable name (e.g. `{ECA_DeveloperName}_probe_tmp`), and
   `metadata_delete` it if the call succeeds.

A Tooling/Connect REST lookup is preferable when available; provoking the error
is the fastest reliable fallback when it is not.

---

## 2. Read before you write — an upsert replaces the whole record

Once you know the real `fullName`, **`metadata_read` it first and merge your
changes into the full existing object before writing back.** An upsert that
passes `metadata` replaces the entire record: omitted fields (refresh-token
policy, IP relaxation, session level, flow toggles) can silently reset to
defaults — a policy downgrade nobody asked for and nobody notices until an
integration breaks.

Lower-risk alternative once the `fullName` is known: use `metadata_update`'s
**`patch` mode** (JSON Patch plus `fullName`) instead of `metadata`. The current
object is fetched and patched server-side, so untouched fields cannot be dropped.

---

## 3. Update the policy: pre-authorize by Permission Set

Key fields:

| Field                         | Notes                                                                                                                                    |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `permittedUsersPolicyType`    | `AdminApprovedPreAuthorized` (pre-authorized users only) or `AllSelfAuthorized` (any user may self-authorize — the default on a new ECA) |
| `commaSeparatedPermissionSet` | Comma-separated Permission Set **Names**, not IDs — see the warning below                                                                |
| `commaSeparatedProfile`       | Same idea, for Profiles, when pre-authorizing by profile instead                                                                         |
| `refreshTokenPolicyType`      | `Infinite` \| `SpecificInactivity` \| `SpecificLifetime` \| `Zero`                                                                       |
| `ipRelaxationPolicyType`      | `Enforce` \| `Bypass` \| `Bypass_2factor` \| `Enforce_RelaxRefresh`                                                                      |
| `requiredSessionLevel`        | `HIGH_ASSURANCE` \| `STANDARD` \| `LOW`                                                                                                  |

⚠️ **Names, not IDs — the Salesforce docs are misleading here.** The Metadata API
Developer Guide describes `commaSeparatedPermissionSet` as "Permission set IDs in
a comma-separated list", but passing a Salesforce record ID fails with:

```
INVALID_FIELD: We couldn't find permission sets called {id}
```

Use the Permission Set `Name`/`fullName` (e.g. `MCP_Client_User`), never `0PS…`.

Full-object upsert (every field carried over from the preceding `metadata_read`;
only `permittedUsersPolicyType` and `commaSeparatedPermissionSet` are being
changed here):

```
metadata_update(
  type="ExtlClntAppOauthConfigurablePolicies",
  upsert=true,
  metadata=[{
    "fullName": "Workshop_MCP_Client_oauthPlcy",
    "externalClientApplication": "Workshop_MCP_Client",
    "label": "Workshop_MCP_Client_oauthPlcy",
    "permittedUsersPolicyType": "AdminApprovedPreAuthorized",
    "commaSeparatedPermissionSet": "MCP_Client_User",
    "ipRelaxationPolicyType": "Enforce",
    "isClientCredentialsFlowEnabled": false,
    "isGuestCodeCredFlowEnabled": false,
    "isTokenExchangeFlowEnabled": false,
    "refreshTokenPolicyType": "SpecificInactivity",
    "refreshTokenValidityPeriod": 30,
    "refreshTokenValidityUnit": "Days",
    "requiredSessionLevel": "STANDARD"
  }],
  sf_user="{sf_user}"
)
```

Pre-authorizing does not by itself grant a user the app: the named permission
set(s) still have to be **assigned** to the users who will authorize it.

---

## 4. Verify after writing

Always `metadata_read` the record back and confirm the fields landed. It is cheap
insurance against a silent field reset, and it is the evidence you need if the
Setup UI misbehaves next (below).

```
metadata_read(
  type="ExtlClntAppOauthConfigurablePolicies",
  fullNames=["Workshop_MCP_Client_oauthPlcy"],
  sf_user="{sf_user}"
)
```

---

## 5. Expect a possible Setup UI glitch after an API-driven policy change

After changing an ECA's OAuth policy through the Metadata API, the **External
Client App Manager** detail page in Setup can intermittently fail to load —
"We couldn't load the external client app" / "Something went wrong". This has
been observed while a `metadata_read` immediately afterwards confirms the record
is intact and correctly updated.

Before assuming something broke:

1. **Re-verify via `metadata_read`.** If it reads back clean, the data is fine
   and the problem is in the Setup UI, not in the org.
2. **Tell the user to re-enter from the list**: go back to the External Client App
   Manager list and click into the record fresh, rather than reloading or using
   the back button on the broken page.
3. **Give it a minute or two.** Salesforce documents that ECA changes can take a
   short time to propagate through Setup UI caching.

Do not "fix" this by rewriting the policy record — a second write against a
partially cached Setup view is how a good record gets clobbered.

---

## Error → cause → fix

| Error                                                                    | Cause                                                       | Fix                                                                                       |
| ------------------------------------------------------------------------ | ----------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| `metadata_read` returns nothing for the policy                           | Guessed `fullName` — likely the bare ECA developer name     | Work the discovery ladder in §1; the real name is usually `{ECA_DeveloperName}_oauthPlcy` |
| `DUPLICATE_VALUE: ExtlClntAppOauthSettingsId duplicates value on {name}` | Upserting a second policy for an ECA that already has one   | Read the real `fullName` out of the error message and re-run against it                   |
| `INVALID_FIELD: We couldn't find permission sets called {id}`            | Passed a `0PS…` record ID in `commaSeparatedPermissionSet`  | Use the Permission Set `Name`, comma-separated                                            |
| Policy fields reset to defaults after an update                          | Upsert with `metadata` replaced the whole record            | `metadata_read` → merge → write the full object, or use `patch` mode                      |
| Setup shows "We couldn't load the external client app"                   | Setup UI caching after an API-driven change, record is fine | Verify with `metadata_read`, re-enter from the ECA list, wait a minute — see §5           |

---

## Sources

- [ExtlClntAppOauthConfigurablePolicies | Metadata API Developer Guide](https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_extlclntappoauthconfigurablepolicies.htm)
- [ExtlClntAppOauthSettings | Metadata API Developer Guide](https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_extlclntappoauthsettings.htm)
- [ExtlClntAppGlobalOauthSettings | Metadata API Developer Guide](https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_extlclntappglobaloauthsettings.htm)
- [External Client Apps (ECA) deployment patterns — flxbl-io/external-client-apps-guide](https://github.com/flxbl-io/external-client-apps-guide) (source of the `MyApp_oauthPlcy.ecaOauthPlcy-meta.xml` naming example)
