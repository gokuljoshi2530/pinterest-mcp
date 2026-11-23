"""Pinterest MCP server (remote, streamable HTTP) for Claude custom connectors.

Env vars:
  PINTEREST_TOKEN  - Pinterest API v5 access token (required)
  MCP_SECRET       - random string; server is served at /<MCP_SECRET>/mcp (required)
  PORT             - port to listen on (hosts like Render/Railway set this)
"""
import os
import httpx
from mcp.server.fastmcp import FastMCP

TOKEN = os.environ["PINTEREST_TOKEN"]
SECRET = os.environ["MCP_SECRET"]
PORT = int(os.environ.get("PORT", "8000"))
API = "https://api.pinterest.com/v5"

mcp = FastMCP(
    "pinterest",
    host="0.0.0.0",
    port=PORT,
    streamable_http_path=f"/{SECRET}/mcp",
)


def _req(method: str, path: str, params: dict | None = None, json: dict | None = None):
    r = httpx.request(
        method,
        f"{API}{path}",
        headers={"Authorization": f"Bearer {TOKEN}"},
        params={k: v for k, v in (params or {}).items() if v is not None},
        json=json,
        timeout=30,
    )
    if r.status_code >= 400:
        return {"error": r.status_code, "detail": r.text}
    return r.json() if r.content else {"ok": True}


def _slim_pin(p: dict) -> dict:
    images = (p.get("media") or {}).get("images") or {}
    img = (images.get("1200x") or images.get("600x") or images.get("400x300") or {}).get("url")
    return {
        "id": p.get("id"),
        "title": p.get("title"),
        "description": p.get("description"),
        "link": p.get("link"),
        "board_id": p.get("board_id"),
        "image": img,
        "created_at": p.get("created_at"),
    }


@mcp.tool()
def get_account() -> dict:
    """Get the connected Pinterest account's profile (username, follower count, etc.)."""
    return _req("GET", "/user_account")


@mcp.tool()
def list_boards(page_size: int = 25, bookmark: str | None = None) -> dict:
    """List your Pinterest boards. Use the returned bookmark to get the next page."""
    data = _req("GET", "/boards", {"page_size": page_size, "bookmark": bookmark})
    if "items" in data:
        data["items"] = [
            {k: b.get(k) for k in ("id", "name", "description", "privacy", "pin_count")}
            for b in data["items"]
        ]
    return data


@mcp.tool()
def list_board_pins(board_id: str, page_size: int = 25, bookmark: str | None = None) -> dict:
    """List pins saved on one board."""
    data = _req("GET", f"/boards/{board_id}/pins", {"page_size": page_size, "bookmark": bookmark})
    if "items" in data:
        data["items"] = [_slim_pin(p) for p in data["items"]]
    return data


@mcp.tool()
def search_my_pins(query: str, bookmark: str | None = None) -> dict:
    """Search pins saved in your own account by keyword (Pinterest API only allows searching your own pins)."""
    data = _req("GET", "/search/pins", {"query": query, "bookmark": bookmark})
    if "items" in data:
        data["items"] = [_slim_pin(p) for p in data["items"]]
    return data


@mcp.tool()
def get_pin(pin_id: str) -> dict:
    """Get details of a single pin."""
    data = _req("GET", f"/pins/{pin_id}")
    return data if "error" in data else _slim_pin(data)


@mcp.tool()
def create_board(name: str, description: str = "", privacy: str = "PUBLIC") -> dict:
    """Create a new board. privacy: PUBLIC, PROTECTED or SECRET."""
    return _req("POST", "/boards", json={"name": name, "description": description, "privacy": privacy})


@mcp.tool()
def create_pin(
    board_id: str,
    image_url: str,
    title: str = "",
    description: str = "",
    link: str | None = None,
) -> dict:
    """Create (publish) a new image pin on a board from a public image URL."""
    body = {
        "board_id": board_id,
        "title": title,
        "description": description,
        "media_source": {"source_type": "image_url", "url": image_url},
    }
    if link:
        body["link"] = link
    return _req("POST", "/pins", json=body)


@mcp.tool()
def save_pin_to_board(pin_id: str, board_id: str) -> dict:
    """Save (repin) an existing pin to one of your boards."""
    return _req("POST", f"/pins/{pin_id}/save", json={"board_id": board_id})


@mcp.tool()
def delete_pin(pin_id: str) -> dict:
    """Delete one of your pins. Permanent."""
    return _req("DELETE", f"/pins/{pin_id}")


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
