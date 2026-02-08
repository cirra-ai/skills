# cirra-ai-sf

Salesforce orchestrator plugin for Claude Cowork. Coordinates the individual Salesforce plugins (Apex, Flow, Data, and others) into a unified admin suite.

When installed, this plugin routes tasks to the appropriate sub-plugin based on context — e.g., Apex code reviews go to `cirra-ai-sf-apex`, data operations go to `cirra-ai-sf-data`.

Each sub-plugin also works independently without the orchestrator.

For installation instructions and the full plugin catalog, see the [root README](../README.md).
