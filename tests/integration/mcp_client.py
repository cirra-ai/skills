"""
Minimal MCP HTTP client for the Cirra AI MCP Server.
Supports the Streamable HTTP transport (MCP 2025-03-26 spec).
"""

import json
import uuid
import time
import requests


class MCPClient:
    """Stateful MCP client that talks to a Streamable HTTP endpoint."""

    def __init__(self, url: str, sf_user: str | None = None):
        self.url = url
        self.sf_user = sf_user
        self.session_id: str | None = None
        self._request_session = requests.Session()
        self._request_session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        })

    # ------------------------------------------------------------------
    # Low-level JSON-RPC helpers
    # ------------------------------------------------------------------

    def _jsonrpc(self, method: str, params: dict | None = None) -> dict:
        """Send a JSON-RPC request and return the result (or raise on error)."""
        msg = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": method,
        }
        if params is not None:
            msg["params"] = params

        headers = {}
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id

        resp = self._request_session.post(self.url, json=msg, headers=headers, timeout=120)

        # Capture session id from response header
        if "Mcp-Session-Id" in resp.headers:
            self.session_id = resp.headers["Mcp-Session-Id"]

        # Handle SSE response
        content_type = resp.headers.get("Content-Type", "")
        if "text/event-stream" in content_type:
            return self._parse_sse(resp.text)

        # Standard JSON response
        body = resp.json()
        if "error" in body:
            raise MCPError(body["error"])
        return body.get("result", body)

    def _parse_sse(self, text: str) -> dict:
        """Parse SSE stream and extract the final JSON-RPC result."""
        last_data = None
        for line in text.split("\n"):
            if line.startswith("data: "):
                last_data = line[6:]
        if last_data:
            body = json.loads(last_data)
            if "error" in body:
                raise MCPError(body["error"])
            return body.get("result", body)
        raise MCPError({"code": -1, "message": "No data in SSE stream"})

    # ------------------------------------------------------------------
    # MCP lifecycle
    # ------------------------------------------------------------------

    def initialize(self) -> dict:
        """Perform MCP initialize handshake."""
        result = self._jsonrpc("initialize", {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "cirra-integration-test", "version": "1.0.0"},
        })
        # Send initialized notification
        self._send_notification("notifications/initialized")
        return result

    def _send_notification(self, method: str, params: dict | None = None):
        """Send a JSON-RPC notification (no id, no response expected)."""
        msg = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        headers = {}
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        self._request_session.post(self.url, json=msg, headers=headers, timeout=30)

    def list_tools(self) -> list[dict]:
        """List available MCP tools."""
        result = self._jsonrpc("tools/list")
        return result.get("tools", [])

    # ------------------------------------------------------------------
    # Tool invocation
    # ------------------------------------------------------------------

    def call_tool(self, name: str, arguments: dict | None = None) -> dict:
        """Call an MCP tool and return the result."""
        params = {"name": name}
        if arguments is not None:
            params["arguments"] = arguments
        return self._jsonrpc("tools/call", params)

    # ------------------------------------------------------------------
    # Convenience wrappers for Cirra AI tools
    # ------------------------------------------------------------------

    def cirra_ai_init(self) -> dict:
        args = {}
        if self.sf_user:
            args["sf_user"] = self.sf_user
        return self.call_tool("cirra_ai_init", args)

    def sobject_describe(self, sobject: str) -> dict:
        args = {"sObject": sobject}
        if self.sf_user:
            args["sf_user"] = self.sf_user
        return self.call_tool("sobject_describe", args)

    def soql_query(self, query: str) -> dict:
        args = {"query": query}
        if self.sf_user:
            args["sf_user"] = self.sf_user
        return self.call_tool("soql_query", args)

    def sobject_dml(self, operation: str, sobject: str, records: list[dict],
                    external_id_field: str | None = None) -> dict:
        args = {
            "operation": operation,
            "sObject": sobject,
            "records": records,
        }
        if external_id_field:
            args["externalIdField"] = external_id_field
        if self.sf_user:
            args["sf_user"] = self.sf_user
        return self.call_tool("sobject_dml", args)

    def tooling_api_query(self, sobject: str, where_clause: str,
                          fields: list[str] | None = None) -> dict:
        args = {"sObject": sobject, "whereClause": where_clause}
        if fields:
            args["fields"] = fields
        if self.sf_user:
            args["sf_user"] = self.sf_user
        return self.call_tool("tooling_api_query", args)

    def tooling_api_dml(self, operation: str, sobject: str,
                        records: list[dict]) -> dict:
        args = {
            "operation": operation,
            "sObject": sobject,
            "records": records,
        }
        if self.sf_user:
            args["sf_user"] = self.sf_user
        return self.call_tool("tooling_api_dml", args)

    def metadata_create(self, metadata_type: str, metadata: list[dict]) -> dict:
        args = {"type": metadata_type, "metadata": metadata}
        if self.sf_user:
            args["sf_user"] = self.sf_user
        return self.call_tool("metadata_create", args)

    def metadata_update(self, metadata_type: str, metadata: list[dict]) -> dict:
        args = {"type": metadata_type, "metadata": metadata}
        if self.sf_user:
            args["sf_user"] = self.sf_user
        return self.call_tool("metadata_update", args)

    def metadata_read(self, metadata_type: str, full_names: list[str]) -> dict:
        args = {"type": metadata_type, "fullNames": full_names}
        if self.sf_user:
            args["sf_user"] = self.sf_user
        return self.call_tool("metadata_read", args)

    def metadata_list(self, metadata_type: str) -> dict:
        args = {"type": metadata_type}
        if self.sf_user:
            args["sf_user"] = self.sf_user
        return self.call_tool("metadata_list", args)

    def metadata_delete(self, metadata_type: str, full_names: list[str]) -> dict:
        args = {"type": metadata_type, "fullNames": full_names}
        if self.sf_user:
            args["sf_user"] = self.sf_user
        return self.call_tool("metadata_delete", args)


class MCPError(Exception):
    """Raised when the MCP server returns a JSON-RPC error."""

    def __init__(self, error_dict: dict):
        self.code = error_dict.get("code", -1)
        self.message = error_dict.get("message", "Unknown MCP error")
        self.data = error_dict.get("data")
        super().__init__(f"MCP error {self.code}: {self.message}")
