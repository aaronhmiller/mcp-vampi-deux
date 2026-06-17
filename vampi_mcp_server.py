"""
Stateless MCP server for VAmPI (the Vulnerable API).

This server exposes the VAmPI REST API (https://github.com/erev0s/VAmPI) as MCP
tools. It is deliberately *stateless* in two senses:

1. Transport: it runs the Streamable-HTTP transport with ``stateless_http=True``
   and ``json_response=True``. No MCP session is created or tracked between
   requests, so the server can be load-balanced / horizontally scaled and every
   HTTP request is self-contained.

2. Application: it never caches a JWT or any per-user session. Authenticated
   endpoints take the bearer ``token`` as an explicit argument. ``login`` simply
   returns the ``auth_token`` to the caller, who threads it back into subsequent
   authenticated tool calls.

Configuration (environment variables):
    VAMPI_BASE_URL   Base URL of the running VAmPI instance
                     (default: http://172.31.43.19:5000)
    VAMPI_TIMEOUT    Per-request timeout in seconds (default: 15)
    MCP_TRANSPORT    "streamable-http" (default) or "stdio"
    MCP_HOST         Bind host for HTTP transport (default: 127.0.0.1)
    MCP_PORT         Bind port for HTTP transport (default: 8000)
"""

from __future__ import annotations

import os
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

BASE_URL = os.environ.get("VAMPI_BASE_URL", "http://172.31.43.19:5000").rstrip("/")
TIMEOUT = float(os.environ.get("VAMPI_TIMEOUT", "15"))

mcp = FastMCP(
    name="vampi",
    instructions=(
        "Stateless bridge to a VAmPI (Vulnerable API) instance. VAmPI is an "
        "intentionally insecure training API. Authentication is stateless: call "
        "`login` to obtain an `auth_token`, then pass that token to any tool that "
        "requires authentication. No session or token is stored server-side."
    ),
    stateless_http=True,
    json_response=True,
    host=os.environ.get("MCP_HOST", "0.0.0.0"),
    port=int(os.environ.get("MCP_PORT", "8000")),
)


# --------------------------------------------------------------------------- #
# HTTP helper
# --------------------------------------------------------------------------- #
def _request(
    method: str,
    path: str,
    *,
    token: str | None = None,
    json_body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Make a single, self-contained request to VAmPI and return a result dict.

    A fresh client is used for every call so that no connection-level or auth
    state survives between tool invocations.
    """
    url = f"{BASE_URL}{path}"
    headers: dict[str, str] = {"Accept": "application/json"}
    if token:
        # VAmPI's token_required decorator expects: "Authorization: Bearer <jwt>"
        headers["Authorization"] = f"Bearer {token}"

    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            resp = client.request(method, url, headers=headers, json=json_body)
    except httpx.RequestError as exc:
        return {
            "ok": False,
            "error": "request_failed",
            "detail": str(exc),
            "url": url,
        }

    # VAmPI returns JSON for virtually every endpoint; fall back to text.
    try:
        payload: Any = resp.json()
    except ValueError:
        payload = resp.text

    return {
        "ok": resp.is_success,
        "status_code": resp.status_code,
        "data": payload,
    }


# --------------------------------------------------------------------------- #
# Service / database
# --------------------------------------------------------------------------- #
@mcp.tool()
def home() -> dict[str, Any]:
    """GET / — VAmPI home/help banner."""
    return _request("GET", "/")


@mcp.tool()
def create_db() -> dict[str, Any]:
    """GET /createdb — (re)create and seed the VAmPI database with dummy data."""
    return _request("GET", "/createdb")


# --------------------------------------------------------------------------- #
# Authentication / registration
# --------------------------------------------------------------------------- #
@mcp.tool()
def register_user(username: str, password: str, email: str) -> dict[str, Any]:
    """POST /users/v1/register — register a new user."""
    return _request(
        "POST",
        "/users/v1/register",
        json_body={"username": username, "password": password, "email": email},
    )


@mcp.tool()
def login(username: str, password: str) -> dict[str, Any]:
    """POST /users/v1/login — authenticate and return a JWT.

    Stateless: the returned `auth_token` is NOT cached. Pass it explicitly to
    tools that require authentication (delete_user, update_email,
    update_password, get_current_user, books endpoints).
    """
    result = _request(
        "POST",
        "/users/v1/login",
        json_body={"username": username, "password": password},
    )
    # Surface the token at the top level for convenience while staying stateless.
    data = result.get("data")
    if isinstance(data, dict) and "auth_token" in data:
        result["auth_token"] = data["auth_token"]
    return result


# --------------------------------------------------------------------------- #
# Users
# --------------------------------------------------------------------------- #
@mcp.tool()
def get_all_users() -> dict[str, Any]:
    """GET /users/v1 — list all users with basic info (username, email)."""
    return _request("GET", "/users/v1")


@mcp.tool()
def debug_users() -> dict[str, Any]:
    """GET /users/v1/_debug — list ALL user details, including passwords and admin
    flags. (This is an intentional VAmPI vulnerability used for training.)"""
    return _request("GET", "/users/v1/_debug")


@mcp.tool()
def get_user_by_username(username: str) -> dict[str, Any]:
    """GET /users/v1/{username} — retrieve a single user by username."""
    return _request("GET", f"/users/v1/{username}")


@mcp.tool()
def delete_user(username: str, token: str) -> dict[str, Any]:
    """DELETE /users/v1/{username} — delete a user by username (requires an admin
    token)."""
    return _request("DELETE", f"/users/v1/{username}", token=token)


@mcp.tool()
def update_email(username: str, email: str, token: str) -> dict[str, Any]:
    """PUT /users/v1/{username}/email — update the authenticated user's email."""
    return _request(
        "PUT",
        f"/users/v1/{username}/email",
        token=token,
        json_body={"email": email},
    )


@mcp.tool()
def update_password(username: str, password: str, token: str) -> dict[str, Any]:
    """PUT /users/v1/{username}/password — update a user's password."""
    return _request(
        "PUT",
        f"/users/v1/{username}/password",
        token=token,
        json_body={"password": password},
    )


@mcp.tool()
def get_current_user(token: str) -> dict[str, Any]:
    """GET /me — return the currently authenticated user's details."""
    return _request("GET", "/me", token=token)


# --------------------------------------------------------------------------- #
# Books
# --------------------------------------------------------------------------- #
@mcp.tool()
def get_all_books(token: str | None = None) -> dict[str, Any]:
    """GET /books/v1 — list all books (title + owning user).

    A token is included when provided; some VAmPI versions require auth here.
    """
    return _request("GET", "/books/v1", token=token)


@mcp.tool()
def add_book(book_title: str, secret: str, token: str) -> dict[str, Any]:
    """POST /books/v1 — add a new book with a secret only the owner should read."""
    return _request(
        "POST",
        "/books/v1",
        token=token,
        json_body={"book_title": book_title, "secret": secret},
    )


@mcp.tool()
def get_book_by_title(book_title: str, token: str) -> dict[str, Any]:
    """GET /books/v1/{book_title} — retrieve a book and its secret by title."""
    return _request("GET", f"/books/v1/{book_title}", token=token)


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    transport = os.environ.get("MCP_TRANSPORT", "streamable-http")
    if transport == "stdio":
        mcp.run(transport="stdio")
    else:
        # Stateless Streamable-HTTP; endpoint served at /mcp
        mcp.run(transport="streamable-http")
