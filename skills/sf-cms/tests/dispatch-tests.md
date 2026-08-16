# sf-cms dispatch tests

Each test case describes a user input and expected behavior.
Phase 1 (static) validates dispatch routing and tool references against SKILL.md.
Phase 2 (prompt) constructs the full prompt and validates its structure.

---

## create a news article

- **Input**: `/sf-cms create a news article "Q3 launch" in the Marketing workspace`
- **Dispatch**: Create and Publish
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Tool params**: `(no parameters)`
- **Should call**: `cirra_ai_init`, `cms_content`, `metadata_list`, `cms_delivery`
- **Should NOT call**: `sobject_dml`, `metadata_delete`
- **Should ask user**: yes (must present the authoring plan for approval, then ask separately before publishing)
- **Follow-up skills**: `sf-metadata`, `sf-connect-rest`

**Notes**: Discovery must run before authoring — `cms_content` `list_spaces` to resolve the workspace, `metadata_list` / `metadata_read` on `ManagedContentType` to resolve the content type, and `list_channels` for the connected channels. The body should be modelled on an existing item of the same type via `search` then `get`. `create` does NOT publish; publishing requires a second, explicitly separate approval that names the channels the workspace is connected to — `publish` itself takes no channel field and goes live on all of them. Verification must go through `cms_delivery` `get_content`, not the authoring response.

---

## update existing content

- **Input**: `/sf-cms update the "Q3 launch" article headline`
- **Dispatch**: Update Content
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Tool params**: `(no parameters)`
- **Should call**: `cirra_ai_init`, `cms_content`
- **Should NOT call**: `metadata_create`, `sobject_dml`
- **Should ask user**: yes (must show before/after of changed fields and get approval; must ask separately about re-publishing)
- **Follow-up skills**: `sf-cms`

**Notes**: CRITICAL variant behavior — `update` takes a `variantId`, not a `contentKeyOrId`. The skill must call `cms_content` `get` first to read the variant ID out of the response. An update to already-published content does not automatically republish; the skill must ask before calling `publish`.

---

## publish content to a channel

- **Input**: `/sf-cms publish the Q3 launch article to the Partner Portal channel`
- **Dispatch**: Publish
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Tool params**: `(no parameters)`
- **Should call**: `cirra_ai_init`, `cms_content`, `cms_delivery`
- **Should NOT call**: `metadata_create`, `metadata_delete`
- **Should ask user**: yes (must state the blast radius — content becomes visible to everyone with channel access — and get explicit approval)
- **Follow-up skills**: `sf-cms`

**Notes**: Publishing is a separately-approved step even when the content change was already approved. `publish` takes `contentIds` or `variantIds` and has no channel field — it makes the content live on every channel the workspace is connected to, so the plan must name those channels from `list_channels` (and if there are none, say the publish will not make anything visible). `unpublish` must send `variantIds`, not `contentIds`, in enhanced workspaces. After publishing, verification goes through `cms_delivery` `get_content` — a deployment ID / `status: Published` is not proof the content is live.

---

## check what is live on the site

- **Input**: `/sf-cms delivery what content is live on the customer portal`
- **Dispatch**: Verify Delivery
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: fast
- **First tool**: `cirra_ai_init`
- **Tool params**: `(no parameters)`
- **Should call**: `cirra_ai_init`, `cms_delivery`
- **Should NOT call**: `cms_content`, `sobject_dml`
- **Should ask user**: no (read-only)
- **Follow-up skills**: `sf-cms`

**Notes**: Read-only path using `cms_delivery` only. Must start with `list_channels` to resolve the delivery channel ID — delivery channel IDs are a different ID space from the authoring channel IDs returned by `cms_content`.

---

## content not showing on the site

- **Input**: `/sf-cms why isn't the Q3 launch article showing on the site`
- **Dispatch**: Verify Delivery
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Tool params**: `(no parameters)`
- **Should call**: `cirra_ai_init`, `cms_delivery`, `cms_content`
- **Should NOT call**: `metadata_delete`
- **Should ask user**: no (diagnostic, read-only)
- **Follow-up skills**: `sf-connect-rest`, `sf-permissions`

**Notes**: Must work the four-step diagnosis in order rather than retrying: (1) published at all, (2) workspace connected to this channel — `publish` takes no channel, so content is live only on connected channels, (3) channel visible to the context user, (4) content type searchable and indexed. Steps 1 and 2 use `cms_content`; step 4 is `connect_rest` territory (`cms/channels/{channelId}/searchable-content-types`, `cms/channels/{channelId}/search/indexes`). The report must name which of the four applies rather than saying "not found".

---

## search for content

- **Input**: `/sf-cms search for content mentioning "pricing"`
- **Dispatch**: Find Content
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: fast
- **First tool**: `cirra_ai_init`
- **Tool params**: `(no parameters)`
- **Should call**: `cirra_ai_init`, `cms_content`
- **Should NOT call**: `sobject_dml`, `metadata_create`
- **Should ask user**: no (read-only)
- **Follow-up skills**: `sf-cms`

**Notes**: `cms_content` `search` requires BOTH `contentSpaceOrFolderIds` and `queryTerm` in `queryParams`. If no space or folder ID is known, `list_spaces` must run first. Results should be reported with content keys so follow-up operations have the correct ID.

---

## delete a CMS channel

- **Input**: `/sf-cms channel delete the retired Partner Portal channel`
- **Dispatch**: Workspace and Channel
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Tool params**: `(no parameters)`
- **Should call**: `cirra_ai_init`, `cms_content`
- **Should NOT call**: `metadata_delete`, `sobject_dml`
- **Should ask user**: yes (must call out that deleting a channel affects everything published to it, and get explicit approval)
- **Follow-up skills**: `sf-connect-rest`

**Notes**: `list_channels` must run first to resolve the channel ID and confirm the right channel. `delete_channel` is destructive — the plan must state the effect on published content explicitly before approval.

---

## unclear workspace — must ask

- **Input**: `/sf-cms create a banner`
- **Dispatch**: Create and Publish
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Tool params**: `(no parameters)`
- **Should call**: `cirra_ai_init`, `cms_content`
- **Should NOT call**: `cms_delivery`, `metadata_create`
- **Should ask user**: yes (must use `AskUserQuestion` to resolve which workspace and content type before authoring)
- **Follow-up skills**: `sf-metadata`

**Notes**: Workspace and content type are ambiguous. Per SKILL.md the skill MUST call `AskUserQuestion` rather than guessing a `spaceId` or content type. `list_spaces` may run first to offer the real options.
