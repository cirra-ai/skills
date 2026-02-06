# Agent Script Patterns Quick Reference

> Decision trees and cheat sheets for common Agent Script patterns

---

## Pattern Selection Decision Tree

### Which Architecture Pattern?

```
What's your agent's purpose?
│
├─► Multi-purpose (sales, support, orders)?
│   └─► HUB AND SPOKE
│       Central router → Specialized topics
│
├─► Sequential workflow (onboarding, checkout)?
│   └─► LINEAR FLOW
│       A → B → C pipeline
│
├─► Tiered support with escalation?
│   └─► ESCALATION CHAIN
│       L1 → L2 → L3 → Human
│
└─► Sensitive operations (payments, PII)?
    └─► VERIFICATION GATE
        Security check → Protected topics
```

---

## Node Type Decision Tree

```
What should this topic do?
│
├─► Route based on intent?
│   └─► 🔵 ROUTING (Topic Selector)
│
├─► Security/identity check?
│   └─► 🔵 VERIFICATION
│
├─► Fetch external data?
│   └─► 🟡 DATA-LOOKUP
│
├─► Apply business rules?
│   └─► 🟢 PROCESSING
│
└─► Transfer to human?
    └─► 🔴 HANDOFF
```

---

## Variable Type Decision Tree

```
What kind of data is this?
│
├─► State that changes during conversation?
│   │   (counters, flags, accumulated data)
│   └─► MUTABLE
│       `failed_attempts: mutable number = 0`
│
└─► Data from external source?
    │   (session, context, CRM)
    └─► LINKED
        `customer_id: linked string`
        `   source: @session.customerId`
```

---

## Action Target Protocol Decision Tree

```
Where should this action go?
│
├─► Data queries, record updates?
│   └─► flow://
│
├─► Custom calculations, validation?
│   └─► apex://
│
├─► LLM-generated summaries?
│   └─► generatePromptResponse://
│
├─► Knowledge search, RAG?
│   └─► retriever://
│
├─► External REST APIs?
│   └─► externalService://
│
└─► Built-in SF actions (email, tasks)?
    └─► standardInvocableAction://
```

---

## Deterministic vs Subjective Decision Tree

```
Should this be code-enforced or LLM-flexible?
│
├─► Security/safety requirement?
│   └─► DETERMINISTIC (code)
│
├─► Financial threshold?
│   └─► DETERMINISTIC (code)
│
├─► Counter/state management?
│   └─► DETERMINISTIC (code)
│
├─► Conversational/greeting?
│   └─► SUBJECTIVE (LLM)
│
├─► Context understanding needed?
│   └─► SUBJECTIVE (LLM)
│
└─► Natural language generation?
    └─► SUBJECTIVE (LLM)
```

---

## SOMA Pattern Decision Tree

```
Does the conversation return to original agent?
│
├─► Yes, specialist handles sub-task
│   └─► DELEGATION
│       `@utils.transition to @topic.specialist`
│
└─► No, permanent transfer
    ├─► To human?
    │   └─► `@utils.escalate`
    │
    └─► To another agent?
        └─► `@agent.X` (Connections)
```

---

## Transition Type Cheat Sheet

| Syntax | Type | Control |
|--------|------|---------|
| `@utils.transition to @topic.X` | LLM-chosen | LLM decides when to use |
| `transition to @topic.X` | Deterministic | Always executes when reached |
| `@utils.escalate` | Permanent handoff | Human takeover |

---

## Instruction Resolution Order

```
instructions: ->
   # 1. POST-ACTION CHECKS (at TOP - triggers on loop)
   if @variables.action_completed == True:
      run @actions.follow_up_action
      transition to @topic.next_step

   # 2. PRE-LLM DATA LOADING
   run @actions.load_required_data
      set @variables.data = @outputs.result

   # 3. DYNAMIC INSTRUCTIONS FOR LLM
   | Here is the context: {!@variables.data}

   if @variables.condition:
      | Do this thing.
   else:
      | Do that thing.
```

**Why this order?**
1. Post-action at TOP → triggers immediately on loop
2. Data loading next → LLM needs current data
3. Instructions last → LLM sees resolved values

---

## Common Patterns Quick Reference

### Security Gate (Early Exit)

```yaml
instructions: ->
   if @variables.failed_attempts >= 3:
      | Account locked due to too many attempts.
      transition to @topic.lockout  # LLM never reasons
```

### Guarded Actions

```yaml
actions:
   process_refund: @actions.process_refund
      description: "Issue refund"
      available when @variables.customer_verified == True
```

### Post-Action Follow-Up

```yaml
instructions: ->
   if @variables.refund_status == "Approved":
      run @actions.create_crm_case
         with customer_id = @variables.customer_id
      transition to @topic.success
```

### Data-Dependent Instructions

```yaml
instructions: ->
   run @actions.get_account_tier
      set @variables.tier = @outputs.tier

   if @variables.tier == "Gold":
      | VIP treatment - offer 20% discount.
   else:
      | Standard customer service.
```

---

## Anti-Patterns to Avoid

### ❌ Data Load After LLM Text

```yaml
# WRONG - LLM sees empty values
instructions: ->
   | Customer name: {!@variables.name}  # empty!
   run @actions.load_customer
      set @variables.name = @outputs.name
```

### ❌ Post-Action Check at Bottom

```yaml
# WRONG - Never triggers
instructions: ->
   | Help with refund.
   transition to @topic.main  # Exits first!

   if @variables.refund_done:  # Never reached
      run @actions.log_refund
```

### ❌ Mixing Tabs and Spaces

```yaml
# WRONG - Compilation error
config:
   agent_name: "MyAgent"      # 3 spaces
        agent_label: "Label"  # 8 spaces - FAILS!
```

### ❌ Lowercase Booleans

```yaml
# WRONG - Agent Script uses Python-style
is_verified: mutable boolean = true   # WRONG
is_verified: mutable boolean = True   # CORRECT
```

---

## Syntax Quick Reference

| Pattern | Purpose |
|---------|---------|
| `instructions: ->` | Arrow syntax, enables expressions |
| `instructions: \|` | Pipe syntax, simple multi-line |
| `if @variables.x:` | Conditional (pre-LLM) |
| `run @actions.x` | Execute during resolution |
| `set @var = @outputs.y` | Capture action output |
| Curly-bang: {!@variables.x} | Template injection |
| `available when` | Control action visibility |
| `transition to @topic.x` | Deterministic topic change |
| `@utils.transition to` | LLM-chosen topic change |
| `@utils.escalate` | Human handoff |

---

## The 6 Deterministic Building Blocks

| # | Block | Example |
|---|-------|---------|
| 1 | Conditionals | `if @variables.failed_attempts >= 3:` |
| 2 | Topic Filters | `available when @variables.cart_items > 0` |
| 3 | Variable Checks | `if @variables.churn_risk >= 80:` |
| 4 | Inline Actions | `run @actions.load_customer` |
| 5 | Utility Actions | `@utils.transition`, `@utils.escalate` |
| 6 | Variable Injection | Curly-bang: {!@variables.customer_name} |
