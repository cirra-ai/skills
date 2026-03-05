#!/usr/bin/env python3
"""
Pull Metadata Schema from a Salesforce org.

Downloads the metadata WSDL from an authenticated org, extracts XSD type
definitions for a specified metadata type, and generates a JSON Schema file
that can be used for offline validation (both XML and JSON representations).

Usage:
    # Pull Flow schema (default):
    python pull_schema.py

    # Pull a different metadata type:
    python pull_schema.py --type PermissionSet
    python pull_schema.py --type Profile
    python pull_schema.py --type Layout
    python pull_schema.py --type FlexiPage
    python pull_schema.py --type CustomObject
    python pull_schema.py --type CustomField
    python pull_schema.py --type ValidationRule
    python pull_schema.py --type RecordType
    python pull_schema.py --type QuickAction
    python pull_schema.py --type PermissionSetGroup
    python pull_schema.py --type SharingRules

    # Specify a target org:
    python pull_schema.py --target-org myOrg

    # Direct URL + token (advanced):
    python pull_schema.py --instance-url https://myorg.my.salesforce.com --access-token <token>

Output:
    skills/<skill-dir>/references/<type>-metadata-schema.json  (overwrites existing)
"""

import argparse
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
SKILLS_DIR = SCRIPT_DIR.parent / "skills"  # skills/ root containing all skill dirs

XSD_NS = "http://www.w3.org/2001/XMLSchema"

# Metadata types and their XSD type prefixes. The key is the CLI-friendly
# name; the value is (type_prefix, root_type_name, skill_dir, output_filename).
METADATA_TYPES = {
    "Flow": ("Flow", "Flow", "cirra-ai-sf-flow", "flow-metadata-schema.json"),
    "PermissionSet": (
        "PermissionSet",
        "PermissionSet",
        "cirra-ai-sf-permissions",
        "permissionset-metadata-schema.json",
    ),
    "Profile": ("Profile", "Profile", "cirra-ai-sf-metadata", "profile-metadata-schema.json"),
    "Layout": ("Layout", "Layout", "cirra-ai-sf-metadata", "layout-metadata-schema.json"),
    "FlexiPage": (
        "FlexiPage",
        "FlexiPage",
        "cirra-ai-sf-metadata",
        "flexipage-metadata-schema.json",
    ),
    "CustomObject": (
        "CustomObject",
        "CustomObject",
        "cirra-ai-sf-metadata",
        "customobject-metadata-schema.json",
    ),
    "CustomField": (
        "CustomField",
        "CustomField",
        "cirra-ai-sf-metadata",
        "customfield-metadata-schema.json",
    ),
    "ValidationRule": (
        "ValidationRule",
        "ValidationRule",
        "cirra-ai-sf-metadata",
        "validationrule-metadata-schema.json",
    ),
    "RecordType": (
        "RecordType",
        "RecordType",
        "cirra-ai-sf-metadata",
        "recordtype-metadata-schema.json",
    ),
    "QuickAction": (
        "QuickAction",
        "QuickAction",
        "cirra-ai-sf-metadata",
        "quickaction-metadata-schema.json",
    ),
    "PermissionSetGroup": (
        "PermissionSetGroup",
        "PermissionSetGroup",
        "cirra-ai-sf-permissions",
        "permissionsetgroup-metadata-schema.json",
    ),
    "SharingRules": (
        "SharingRules",
        "SharingRules",
        "cirra-ai-sf-permissions",
        "sharingrules-metadata-schema.json",
    ),
}

# XSD → JSON Schema type mapping
XSD_TYPE_MAP = {
    "xsd:string": "string",
    "xsd:boolean": "boolean",
    "xsd:int": "integer",
    "xsd:integer": "integer",
    "xsd:long": "integer",
    "xsd:double": "number",
    "xsd:decimal": "number",
    "xsd:float": "number",
    "xsd:date": "string",
    "xsd:dateTime": "string",
    "xsd:base64Binary": "string",
    "tns:ID": "string",
}


def get_org_info(target_org=None):
    """Get instance URL and access token from sf CLI."""
    cmd = ["sf", "org", "display", "--json"]
    if target_org:
        cmd.extend(["--target-org", target_org])
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        info = data.get("result", {})
        return info.get("instanceUrl"), info.get("accessToken"), info.get("apiVersion")
    except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error getting org info from sf CLI: {e}", file=sys.stderr)
        return None, None, None


def download_wsdl(instance_url, access_token):
    """Download metadata WSDL from the org."""
    import urllib.request

    url = f"{instance_url}/services/wsdl/metadata"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {access_token}")
    req.add_header("Accept", "application/xml")

    print(f"Downloading metadata WSDL from {instance_url}...")
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8")


def extract_types(wsdl_content, type_prefix):
    """Extract XSD complex types from the WSDL.

    Starts with types matching ``type_prefix`` then transitively includes any
    complex types referenced via element types or extension bases so that the
    generated schema is self-contained.
    """
    root = ET.fromstring(wsdl_content)

    # Find the <types> → <schema> section
    types_el = root.find(f".//{{{XSD_NS}}}schema")
    if types_el is None:
        wsdl_ns = "http://schemas.xmlsoap.org/wsdl/"
        types_el = root.find(f".//{{{wsdl_ns}}}types/{{{XSD_NS}}}schema")
    if types_el is None:
        raise ValueError("Could not find XSD schema in WSDL")

    enum_types = {}

    # Pass 1: collect all simpleType enums
    for simple_type in types_el.findall(f"{{{XSD_NS}}}simpleType"):
        name = simple_type.get("name", "")
        restriction = simple_type.find(f"{{{XSD_NS}}}restriction")
        if restriction is not None:
            enums = [e.get("value") for e in restriction.findall(f"{{{XSD_NS}}}enumeration")]
            if enums:
                enum_types[name] = enums

    # Index all complexTypes
    all_complex_types = {}
    for complex_type in types_el.findall(f"{{{XSD_NS}}}complexType"):
        name = complex_type.get("name", "")
        if name:
            all_complex_types[name] = complex_type

    # Pass 2: seed with prefix-matched types, then resolve transitive deps
    seed_names = {
        n for n in all_complex_types if n.startswith(type_prefix) or n == type_prefix
    }
    matched_types = _resolve_transitive_types(seed_names, all_complex_types)

    return matched_types, enum_types


def _resolve_transitive_types(seed_names, all_complex_types):
    """Walk extension bases and element type refs to collect all needed types."""
    needed = set()
    queue = list(seed_names)
    while queue:
        name = queue.pop()
        if name in needed or name not in all_complex_types:
            continue
        needed.add(name)
        ct = all_complex_types[name]

        cc = ct.find(f"{{{XSD_NS}}}complexContent")
        seq = None
        if cc is not None:
            ext = cc.find(f"{{{XSD_NS}}}extension")
            if ext is not None:
                base = re.sub(r"^tns:", "", ext.get("base", ""))
                if base in all_complex_types and base != "Metadata":
                    queue.append(base)
                seq = ext.find(f"{{{XSD_NS}}}sequence")
        else:
            seq = ct.find(f"{{{XSD_NS}}}sequence")

        if seq is not None:
            for elem in seq.findall(f"{{{XSD_NS}}}element"):
                etype = re.sub(r"^tns:", "", elem.get("type", ""))
                if etype in all_complex_types:
                    queue.append(etype)

    return {n: all_complex_types[n] for n in needed}


def xsd_type_to_json_schema(type_name, enum_types, known_types):
    """Convert an XSD type reference to a JSON Schema type.

    ``known_types`` is the set of complex type names included in ``$defs``.
    """
    if type_name in XSD_TYPE_MAP:
        return {"type": XSD_TYPE_MAP[type_name]}

    clean = re.sub(r"^tns:", "", type_name)

    if clean in enum_types:
        return {"type": "string", "enum": enum_types[clean]}

    if clean in known_types:
        return {"$ref": f"#/$defs/{clean}"}

    return {"type": "string", "description": f"Mapped from XSD type: {type_name}"}


def complex_type_to_json_schema(ct_element, enum_types, known_types):
    """Convert an XSD complexType element to a JSON Schema object definition.

    ``known_types`` is the set of complex type names included in ``$defs``.
    """
    schema = {"type": "object", "properties": {}, "additionalProperties": True}
    required = []

    complex_content = ct_element.find(f"{{{XSD_NS}}}complexContent")
    if complex_content is not None:
        extension = complex_content.find(f"{{{XSD_NS}}}extension")
        if extension is not None:
            base = extension.get("base", "")
            clean_base = re.sub(r"^tns:", "", base)
            if clean_base in known_types:
                schema["allOf"] = [{"$ref": f"#/$defs/{clean_base}"}]
            sequence = extension.find(f"{{{XSD_NS}}}sequence")
        else:
            sequence = None
    else:
        sequence = ct_element.find(f"{{{XSD_NS}}}sequence")

    if sequence is not None:
        for elem in sequence.findall(f"{{{XSD_NS}}}element"):
            elem_name = elem.get("name", "")
            elem_type = elem.get("type", "xsd:string")
            min_occurs = elem.get("minOccurs", "1")
            max_occurs = elem.get("maxOccurs", "1")

            prop_schema = xsd_type_to_json_schema(elem_type, enum_types, known_types)

            if max_occurs == "unbounded":
                prop_schema = {"type": "array", "items": prop_schema}

            schema["properties"][elem_name] = prop_schema

            if min_occurs != "0":
                required.append(elem_name)

    if required:
        schema["required"] = required

    return schema


def build_json_schema(matched_types, enum_types, root_type, api_version=None):
    """Build a complete JSON Schema from extracted types."""
    known_types = set(matched_types.keys())
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"https://cirra.ai/schemas/salesforce-{root_type.lower()}-metadata.json",
        "title": f"Salesforce {root_type} Metadata",
        "description": (
            f"JSON Schema for Salesforce {root_type} metadata"
            f" (API v{api_version}). " if api_version else f"JSON Schema for Salesforce {root_type} metadata. "
        )
        + "Auto-generated from the org's metadata WSDL by pull_schema.py.",
        "type": "object",
        "$defs": {},
    }

    if api_version:
        schema["x-salesforce-api-version"] = api_version

    for name, ct_element in sorted(matched_types.items()):
        schema["$defs"][name] = complex_type_to_json_schema(ct_element, enum_types, known_types)

    if root_type in schema["$defs"]:
        schema["$ref"] = f"#/$defs/{root_type}"

    return schema


def main():
    parser = argparse.ArgumentParser(
        description="Pull metadata schema from Salesforce org"
    )
    parser.add_argument(
        "--type",
        default="Flow",
        choices=list(METADATA_TYPES.keys()),
        help="Metadata type to extract (default: Flow)",
    )
    parser.add_argument(
        "org",
        nargs="?",
        default=None,
        help="sf CLI target org alias or username (uses default org if omitted)",
    )
    parser.add_argument("--target-org", help="sf CLI target org alias (alternative to positional arg)")
    parser.add_argument("--instance-url", help="Salesforce instance URL (direct mode)")
    parser.add_argument("--access-token", help="OAuth access token (direct mode)")
    parser.add_argument("--output", help="Output JSON Schema path (overrides default)")
    args = parser.parse_args()

    # Positional org takes precedence, then --target-org
    target_org = args.org or args.target_org

    type_prefix, root_type, skill_dir, default_filename = METADATA_TYPES[args.type]

    if args.instance_url and args.access_token:
        instance_url = args.instance_url
        access_token = args.access_token
        api_version = None
    else:
        instance_url, access_token, api_version = get_org_info(target_org)
        if not instance_url or not access_token:
            print(
                "Could not get org credentials. Is sf CLI installed and authenticated?",
                file=sys.stderr,
            )
            sys.exit(1)

    wsdl_content = download_wsdl(instance_url, access_token)

    print(f"Extracting {args.type} types from WSDL...")
    matched_types, enum_types = extract_types(wsdl_content, type_prefix)
    print(f"Found {len(matched_types)} {args.type} complex types and {len(enum_types)} enum types")

    schema = build_json_schema(matched_types, enum_types, root_type, api_version)

    default_refs_dir = SKILLS_DIR / skill_dir / "references"
    output_path = Path(args.output) if args.output else default_refs_dir / default_filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(schema, f, indent=2)
    print(f"Wrote JSON Schema to {output_path}")
    print(f"  Types: {len(schema.get('$defs', {}))}")
    if api_version:
        print(f"  API version: {api_version}")


if __name__ == "__main__":
    main()
