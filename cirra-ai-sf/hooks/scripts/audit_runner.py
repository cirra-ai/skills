#!/usr/bin/env python3
"""
Salesforce Org Audit Orchestrator
Coordinates the full audit workflow: collection, scoring, and report generation.

Usage:
    python3 audit_runner.py --output-dir ./output

This is the main entry point for running a complete Salesforce org audit.
All intermediate and output files are written to the specified output directory.

Designed to work with Cirra AI MCP Server for data collection.
"""

import json
import argparse
from pathlib import Path
from datetime import datetime


# ============================================================================
# CONFIGURATION
# ============================================================================

AUDIT_VERSION = "2.0.0"

PHASES = [
    "Phase 0: Plugin Discovery",
    "Phase 1: Initialize Cirra AI",
    "Phase 2: Count Components",
    "Phase 3: Collect Apex Data",
    "Phase 4: Collect Flow Data",
    "Phase 5: Score Apex Classes",
    "Phase 6: Score Flows",
    "Phase 7: Generate Word Report",
    "Phase 8: Generate Excel Report",
    "Phase 9: Generate HTML Report",
    "Phase 10: Validate Reports",
]


# ============================================================================
# OUTPUT MANAGER
# ============================================================================

class AuditOutputManager:
    """Centralised output manager - all files go to the output directory."""

    def __init__(self, output_dir: str):
        self.root = Path(output_dir)
        self.intermediate = self.root / 'intermediate'
        self.scripts = self.root / 'scripts'
        self.reports = self.root

        # Create directory structure
        self.intermediate.mkdir(parents=True, exist_ok=True)
        self.scripts.mkdir(parents=True, exist_ok=True)

    def path(self, filename: str, subdir: str = 'root') -> Path:
        """Get path for a file in the specified subdirectory."""
        dirs = {
            'root': self.root,
            'intermediate': self.intermediate,
            'scripts': self.scripts,
            'reports': self.reports,
        }
        return dirs.get(subdir, self.root) / filename

    def save_json(self, data, filename: str, subdir: str = 'intermediate') -> Path:
        path = self.path(filename, subdir)
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        return path

    def load_json(self, filename: str, subdir: str = 'intermediate') -> dict | None:
        path = self.path(filename, subdir)
        if path.exists():
            with open(path) as f:
                return json.load(f)
        return None

    def save_state(self, state: dict) -> None:
        """Save audit state for resume capability."""
        state['last_updated'] = datetime.now().isoformat()
        self.save_json(state, 'audit_state.json')

    def load_state(self) -> dict | None:
        """Load audit state for resume."""
        return self.load_json('audit_state.json')


# ============================================================================
# AUDIT STATE TRACKER
# ============================================================================

class AuditState:
    """Tracks audit progress across phases for resume capability."""

    def __init__(self, output: AuditOutputManager):
        self.output = output
        self.state = self._load_or_create()

    @staticmethod
    def _default_state() -> dict:
        return {
            'version': AUDIT_VERSION,
            'started': datetime.now().isoformat(),
            'current_phase': 0,
            'phases': {str(i): {'status': 'pending', 'result': None} for i in range(len(PHASES))},
            'org_info': {},
            'counts': {'apex_classes': 0, 'flows': 0},
        }

    def _load_or_create(self) -> dict:
        existing = self.output.load_state()
        return existing if existing else self._default_state()

    def get_phase_status(self, phase: int) -> str:
        return self.state['phases'].get(str(phase), {}).get('status', 'pending')

    @property
    def current_phase(self) -> int:
        return self.state.get('current_phase', 0)


# ============================================================================
# MCP DATA COLLECTION HELPERS
# ============================================================================

def build_mcp_collection_queries(batch_size: int = 200) -> dict:
    """
    Generate the MCP tooling_api_query parameters needed for data collection.
    Returns query configurations that can be passed to Cirra AI MCP tools.
    """
    return {
        'apex_count': {
            'tool': 'tooling_api_query',
            'params': {
                'sObject': 'ApexClass',
                'fields': ['COUNT(Id) cnt'],
                'whereClause': "NamespacePrefix = null",
            }
        },
        'flow_count': {
            'tool': 'tooling_api_query',
            'params': {
                'sObject': 'FlowDefinition',
                'fields': ['COUNT(Id) cnt'],
                'whereClause': "ActiveVersionId != null AND NamespacePrefix = null",
            }
        },
        'apex_metadata': {
            'tool': 'tooling_api_query',
            'params': {
                'sObject': 'ApexClass',
                'fields': ['Id', 'Name', 'LengthWithoutComments', 'ApiVersion'],
                'whereClause': "NamespacePrefix = null ORDER BY Id",
                'limit': batch_size,
            },
            'pagination': {
                'strategy': 'id_cursor',
                'id_field': 'Id',
                'batch_size': batch_size,
            }
        },
        'apex_body': {
            'tool': 'tooling_api_query',
            'params': {
                'sObject': 'ApexClass',
                'fields': ['Id', 'Body'],
                'whereClause': "Id = '{class_id}'",
            },
            'note': 'Fetch one class at a time to avoid response size limits',
        },
        'flow_metadata': {
            'tool': 'tooling_api_query',
            'params': {
                'sObject': 'FlowDefinition',
                'fields': ['Id', 'DeveloperName', 'MasterLabel', 'Description',
                           'ActiveVersionId', 'NamespacePrefix'],
                'whereClause': "ActiveVersionId != null AND NamespacePrefix = null ORDER BY Id",
                'limit': batch_size,
            },
            'pagination': {
                'strategy': 'id_cursor',
                'id_field': 'Id',
                'batch_size': batch_size,
            }
        },
        'flow_xml': {
            'tool': 'metadata_read',
            'params': {
                'type': 'Flow',
                'fullNames': ['{flow_developer_name}'],
            },
            'note': 'Fetch one flow XML at a time for detailed analysis',
        },
    }


# ============================================================================
# MAIN ORCHESTRATOR
# ============================================================================

def print_phase_status(state: AuditState) -> None:
    """Print current audit progress."""
    print("\n" + "=" * 70)
    print("SALESFORCE ORG AUDIT - PROGRESS")
    print("=" * 70)
    for i, phase_name in enumerate(PHASES):
        status = state.get_phase_status(i)
        icon = {'completed': '✅', 'in_progress': '🔄', 'pending': '⬜'}.get(status, '⬜')
        marker = ' ◀ CURRENT' if i == state.current_phase and status != 'completed' else ''
        print(f"  {icon} {phase_name}{marker}")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description='Salesforce Org Audit Orchestrator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full audit with output to specific directory
  python3 audit_runner.py --output-dir /path/to/audit/output

  # Show current audit progress
  python3 audit_runner.py --output-dir /path/to/output --status

  # Generate MCP query configurations
  python3 audit_runner.py --output-dir /path/to/output --generate-queries
        """,
    )
    parser.add_argument('--output-dir', default='.', help='Output directory for ALL audit files')
    parser.add_argument('--batch-size', type=int, default=200, help='Batch size for pagination')
    parser.add_argument('--status', action='store_true', help='Show current audit progress')
    parser.add_argument('--generate-queries', action='store_true', help='Generate MCP query configs')
    parser.add_argument('--reset', action='store_true', help='Reset audit state and start fresh')
    args = parser.parse_args()

    output = AuditOutputManager(args.output_dir)
    state = AuditState(output)

    print(f"🔍 Salesforce Org Audit Orchestrator v{AUDIT_VERSION}")
    print(f"📁 Output directory: {output.root}")
    print(f"   Intermediate files: {output.intermediate}")
    print(f"   Scripts: {output.scripts}")
    print()

    if args.reset:
        print("🔄 Resetting audit state...")
        state_file = output.path('audit_state.json', 'intermediate')
        if state_file.exists():
            state_file.unlink()
        state = AuditState(output)
        print("✅ Audit state reset.")
        return

    if args.status:
        print_phase_status(state)
        return

    if args.generate_queries:
        queries = build_mcp_collection_queries(args.batch_size)
        path = output.save_json(queries, 'mcp_query_configs.json')
        print(f"✅ MCP query configurations saved to: {path}")
        print("\nUse these configurations with Cirra AI MCP Server tools:")
        for name, config in queries.items():
            print(f"  - {name}: {config['tool']}")
        return

    # Show current status
    print_phase_status(state)

    # Provide guidance
    print("\n📋 USAGE GUIDE:")
    print("=" * 70)
    print(f"""
This orchestrator manages audit state and file organization.
Data collection and scoring should be run through Claude with Cirra AI MCP.

Workflow:
  1. Run this script with --generate-queries to get MCP query configs
  2. Use Claude + Cirra AI MCP to execute queries and save results
  3. All intermediate files should be saved to: {output.intermediate}
  4. Run score_apex_classes.py --output-dir {output.root} to score Apex classes
  5. Run score_flows.py --output-dir {output.root} to score Flows
  6. Use Claude to generate Word/Excel/HTML reports in {output.root}

Key Principle: ALL files go to the output directory.
  - Intermediate data: {output.intermediate}/
  - Scripts: {output.scripts}/
  - Final reports: {output.root}/
""")


if __name__ == '__main__':
    main()
