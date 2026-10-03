"""Minimal client for Palmier Pro's local MCP server (streamable HTTP).

Usage from Python:
    from palmier_mcp import call
    call("get_timeline", {})

CLI:
    python3 palmier_mcp.py list
    python3 palmier_mcp.py call get_timeline '{}'
"""
import json
import os
import sys
import urllib.error
import urllib.request

URL = os.environ.get("PALMIER_MCP_URL", "http://127.0.0.1:19789/mcp")
SESSION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".palmier-session")
TIMEOUT = int(os.environ.get("PALMIER_MCP_TIMEOUT", "150"))
_id = [0]


def _post(payload, sid=None):
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "MCP-Protocol-Version": "2025-06-18",
    }
    if sid:
        headers["Mcp-Session-Id"] = sid
    req = urllib.request.Request(URL, data=json.dumps(payload).encode(), headers=headers, method="POST")
    resp = urllib.request.urlopen(req, timeout=TIMEOUT)
    body = resp.read().decode("utf8", "ignore")
    new_sid = resp.headers.get("Mcp-Session-Id")
    msgs = []
    if "event-stream" in resp.headers.get("content-type", ""):
        for block in body.split("\n\n"):
            data = "".join(line[5:].strip() for line in block.splitlines() if line.startswith("data:"))
            if data:
                msgs.append(json.loads(data))
    elif body.strip():
        msgs.append(json.loads(body))
    return msgs, new_sid


def _session():
    if os.path.exists(SESSION_FILE):
        return open(SESSION_FILE).read().strip()
    _, sid = _post({"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {
        "protocolVersion": "2025-06-18", "capabilities": {},
        "clientInfo": {"name": "orgrowth-timelapse-generator", "version": "1"}}})
    _post({"jsonrpc": "2.0", "method": "notifications/initialized"}, sid)
    open(SESSION_FILE, "w").write(sid or "")
    return sid


def rpc(method, params):
    _id[0] += 1
    payload = {"jsonrpc": "2.0", "id": _id[0], "method": method, "params": params}
    try:
        msgs, _ = _post(payload, _session())
    except urllib.error.HTTPError as err:
        if err.code in (400, 404) and os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
            msgs, _ = _post(payload, _session())
        else:
            raise
    for msg in msgs:
        if msg.get("id") == _id[0]:
            return msg
    return msgs[-1] if msgs else None


def call(name, args=None, _retry=True):
    """Call a Palmier tool. Retries once on a timeout (capture_frame occasionally stalls)."""
    try:
        msg = rpc("tools/call", {"name": name, "arguments": args or {}})
    except Exception as err:
        if _retry and "timed out" in str(err).lower():
            return call(name, args, False)
        raise
    if "error" in msg:
        raise RuntimeError(json.dumps(msg["error"]))
    result = msg["result"]
    text = "\n".join(c.get("text", "") for c in result.get("content", []) if c.get("type") == "text")
    if result.get("isError"):
        raise RuntimeError(text)
    try:
        return json.loads(text)
    except ValueError:
        return text


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    if sys.argv[1] == "list":
        for tool in rpc("tools/list", {})["result"]["tools"]:
            print(tool["name"])
    elif sys.argv[1] == "call":
        out = call(sys.argv[2], json.loads(sys.argv[3]) if len(sys.argv) > 3 else {})
        print(out if isinstance(out, str) else json.dumps(out, indent=1))
