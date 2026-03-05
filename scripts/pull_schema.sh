#!/usr/bin/env bash
#
# Pull JSON Schema for a Salesforce metadata type from an authenticated org.
#
# Usage:
#   ./scripts/pull_schema.sh --type all myOrg          # ALL schemas at once
#   ./scripts/pull_schema.sh                           # Flow schema, default org
#   ./scripts/pull_schema.sh myDevOrg                  # Flow schema, specific org
#   ./scripts/pull_schema.sh --type CustomObject        # CustomObject, default org
#   ./scripts/pull_schema.sh --type PermissionSet myOrg # PermissionSet, specific org
#
# Supported types:
#   all, Flow (default), PermissionSet, Profile, Layout, FlexiPage,
#   CustomObject, CustomField, ValidationRule, RecordType,
#   QuickAction, PermissionSetGroup, SharingRules
#
# Hand-curated "description" fields in existing schema files are preserved.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

python3 "$SCRIPT_DIR/pull_schema.py" "$@"
