# Validation Framework — sf-ai-agentforce-testing

TDD validation suite for the Agent Runtime API client and multi-turn test runner.

## Quick Start

```bash
# Install dependencies
pip3 install -r validation/requirements.txt

# Run all offline tests (T1–T4)
pytest validation/scenarios -v --offline

# Run specific tier
pytest validation/scenarios -v -m tier1

# Scoring runner
python3 validation/scripts/run_validation.py --offline
```

## Tier Breakdown (100 points)

| Tier | Name                   | Points | Offline | Tests |
| ---- | ---------------------- | ------ | ------- | ----- |
| T1   | API Client Unit Tests  | 25     | ✅      | ~10   |
| T2   | Test Runner Unit Tests | 25     | ✅      | ~12   |
| T3   | Template Validation    | 15     | ✅      | ~4    |
| T4   | Negative & Error Tests | 15     | ✅      | ~6    |
| T5   | Live API Tests         | 20     | ❌      | ~5    |

**Pass**: ≥80 pts | **Warn**: ≥70 pts

## Running Live Tests (T5)

```bash
pytest validation/scenarios -v \
  --my-domain your-domain.my.salesforce.com \
  --consumer-key YOUR_KEY \
  --consumer-secret YOUR_SECRET \
  --agent-id 0XxRM0000004ABC
```

Or via environment variables:

```bash
export SF_MY_DOMAIN=your-domain.my.salesforce.com
export SF_CONSUMER_KEY=YOUR_KEY
export SF_CONSUMER_SECRET=YOUR_SECRET
export SF_AGENT_ID=0XxRM0000004ABC
pytest validation/scenarios -v
```

## Key Fixtures

| Fixture                 | Scope    | Description                                    |
| ----------------------- | -------- | ---------------------------------------------- |
| `mock_urlopen`          | function | Patches `urllib.request.urlopen`               |
| `mock_client`           | function | `AgentAPIClient` with pre-set token            |
| `mock_session`          | function | `AgentSession` with fake session_id            |
| `sample_turn_result`    | function | Factory for `TurnResult` objects               |
| `sample_agent_messages` | function | Factory for `AgentMessage` lists               |
| `mock_yaml_scenario`    | function | Factory for YAML scenario dicts                |
| `live_credentials`      | session  | SF credentials from CLI/env (skips if missing) |
| `live_client`           | session  | Authenticated `AgentAPIClient` for T5          |

## Custom CLI Options

| Flag                | Description                 |
| ------------------- | --------------------------- |
| `--offline`         | Skip T5 live API tests      |
| `--tier T1`         | Run only specified tier     |
| `--my-domain`       | Salesforce My Domain for T5 |
| `--consumer-key`    | ECA Consumer Key for T5     |
| `--consumer-secret` | ECA Consumer Secret for T5  |
| `--agent-id`        | BotDefinition ID for T5     |
