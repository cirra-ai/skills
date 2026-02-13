# cirra-ai-sf

Salesforce orchestrator plugin for Claude Cowork. Coordinates the individual Salesforce plugins (Apex, Flow, Data, and others) into a unified admin suite.

When installed, this plugin routes tasks to the appropriate sub-plugin based on context — e.g., Apex code reviews go to `cirra-ai-sf-apex`, data operations go to `cirra-ai-sf-data`.

Each sub-plugin also works independently without the orchestrator.

## Sample Prompts

- "Perform a thorough audit of the Apex classes and Flows in my Salesforce org. Use Cirra AI and the cirra-ai-sf plugin. Use the default org for Cirra AI. Please generate Word, HTML and Excel versions of the report."
- "I need a new custom object called Inspection\_\_c with fields for Status, Inspector, and Date. Then create an Apex trigger that auto-assigns inspectors based on region, a Screen Flow for field technicians to submit inspection results, and seed 50 test records so I can demo it. Do this in the default org for Cirra AI."
- "Review all Apex triggers in my org for bulkification issues and governor limit risks. For each issue found, suggest a fix and score the code. Do this in the default org for Cirra AI."

## Model choice

For reports, analysis and simple metadata task the Sonnet model is a good and cost effective choice. For deeper thinking about how to best build new features or debug existing issues, the Opus model may be needed.

## Installation

For installation instructions and the full plugin catalog, see the [root README](../README.md).
