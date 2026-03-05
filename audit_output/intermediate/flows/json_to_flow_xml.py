#!/usr/bin/env python3
"""Convert Salesforce Flow metadata JSON to Flow XML (.flow-meta.xml)"""
import json
import sys
import os
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

FLOW_NS = "http://soap.sforce.com/2006/04/metadata"

# Order of top-level Flow elements per Salesforce metadata spec
TOP_LEVEL_ORDER = [
    "actionCalls", "apexPluginCalls", "apiVersion", "areMetricsLoggedToDataCloud",
    "assignments", "choices", "collectionProcessors", "constants", "customErrors",
    "decisions", "description", "dynamicChoiceSets", "environments", "formulas",
    "interviewLabel", "isAdditionalPermissionRequiredToRun", "isOverridable",
    "isTemplate", "label", "loops", "orchestratedStages", "overriddenFlow",
    "processMetadataValues", "processType", "recordCreates", "recordDeletes",
    "recordLookups", "recordRollbacks", "recordUpdates", "runInMode",
    "screens", "sourceTemplate", "stages", "start", "status", "steps",
    "subflows", "textTemplates", "transforms", "triggerOrder", "variables",
    "waits"
]

def dict_to_xml(parent, data, tag=None):
    """Recursively convert a dict/list/primitive to XML elements."""
    if isinstance(data, dict):
        for key, value in data.items():
            if key == "fullName":
                continue  # fullName is not part of Flow body XML
            if isinstance(value, list):
                for item in value:
                    child = SubElement(parent, key)
                    if isinstance(item, dict):
                        dict_to_xml(child, item)
                    else:
                        child.text = str(item) if item is not None else ""
            elif isinstance(value, dict):
                child = SubElement(parent, key)
                dict_to_xml(child, value)
            else:
                child = SubElement(parent, key)
                if value is not None:
                    child.text = str(value)
                else:
                    child.text = ""
    elif isinstance(data, list):
        for item in data:
            if tag:
                child = SubElement(parent, tag)
                if isinstance(item, dict):
                    dict_to_xml(child, item)
                else:
                    child.text = str(item) if item is not None else ""
    else:
        parent.text = str(data) if data is not None else ""

def flow_json_to_xml(flow_data):
    """Convert a single flow JSON object to XML string."""
    root = Element("Flow")
    root.set("xmlns", FLOW_NS)
    
    # Add elements in spec order first, then any remaining
    added = set()
    for key in TOP_LEVEL_ORDER:
        if key in flow_data and key != "fullName":
            value = flow_data[key]
            if isinstance(value, list):
                if len(value) == 0:
                    continue
                for item in value:
                    child = SubElement(root, key)
                    if isinstance(item, dict):
                        dict_to_xml(child, item)
                    else:
                        child.text = str(item) if item is not None else ""
            elif isinstance(value, dict):
                child = SubElement(root, key)
                dict_to_xml(child, value)
            else:
                child = SubElement(root, key)
                if value is not None:
                    child.text = str(value)
            added.add(key)
    
    # Add any remaining keys not in the order list
    for key, value in flow_data.items():
        if key in added or key == "fullName":
            continue
        if isinstance(value, list):
            if len(value) == 0:
                continue
            for item in value:
                child = SubElement(root, key)
                if isinstance(item, dict):
                    dict_to_xml(child, item)
                else:
                    child.text = str(item) if item is not None else ""
        elif isinstance(value, dict):
            child = SubElement(root, key)
            dict_to_xml(child, value)
        else:
            child = SubElement(root, key)
            if value is not None:
                child.text = str(value)
    
    # Pretty print
    rough = tostring(root, encoding="unicode")
    parsed = minidom.parseString(rough)
    pretty = parsed.toprettyxml(indent="    ", encoding=None)
    # Remove the XML declaration line that minidom adds
    lines = pretty.split("\n")
    # Replace declaration with standard one
    lines[0] = '<?xml version="1.0" encoding="UTF-8"?>'
    return "\n".join(lines)

def convert_file(json_path, output_dir):
    """Read a JSON file containing flow results and convert each to XML."""
    with open(json_path) as f:
        data = json.load(f)
    
    if isinstance(data, list) and len(data) > 0 and "text" in data[0]:
        # Persisted output format
        inner = json.loads(data[0]["text"])
    elif isinstance(data, dict):
        inner = data
    else:
        inner = data
    
    results = inner.get("results", [])
    converted = []
    for result in results:
        full_name = result.get("fullName", "unknown")
        xml_str = flow_json_to_xml(result)
        out_path = os.path.join(output_dir, f"{full_name}.flow-meta.xml")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(xml_str)
        converted.append(full_name)
        print(f"Converted: {full_name}")
    return converted

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: json_to_flow_xml.py <json_file> <output_dir>")
        sys.exit(1)
    convert_file(sys.argv[1], sys.argv[2])
