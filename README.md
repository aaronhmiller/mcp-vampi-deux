# VAmPI MCP Server (stateless)

An [MCP](https://modelcontextprotocol.io) server that exposes the
[VAmPI](https://github.com/erev0s/VAmPI) (intentionally Vulnerable API) as tools,
talking to a running VAmPI instance at `http://172.31.43.19:5000` by default.

## Why "stateless"

- **Transport** runs with `stateless_http=True` + `json_response=True`. No MCP
  session is created or tracked — every HTTP request is independent, so the
  server is safe to horizontally scale / load-balance.
- **Auth** is never cached. `login` returns the `auth_token`; the caller passes
  that token back into any tool that needs authentication. Nothing is stored
  server-side between calls.

## Install

```bash
python3 -m venv venv
. venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run

Streamable-HTTP (default), endpoint served at `/mcp`:

```bash
python vampi_mcp_server.py
# serves on http://127.0.0.1:8000/mcp
```

Local stdio (e.g. for Claude Desktop):

```bash
MCP_TRANSPORT=stdio python vampi_mcp_server.py
```

## Configuration

| Variable         | Default                     | Purpose                          |
|------------------|-----------------------------|----------------------------------|
| `VAMPI_BASE_URL` | `http://172.31.43.19:5000`  | VAmPI instance base URL          |
| `VAMPI_TIMEOUT`  | `15`                        | Per-request timeout (seconds)    |
| `MCP_TRANSPORT`  | `streamable-http`           | `streamable-http` or `stdio`     |
| `MCP_HOST`       | `127.0.0.1`                 | HTTP bind host                   |
| `MCP_PORT`       | `8000`                      | HTTP bind port                   |

## Tools

Service: `home`, `create_db` ·
Auth: `register_user`, `login` ·
Users: `get_all_users`, `debug_users`, `get_user_by_username`, `delete_user`,
`update_email`, `update_password`, `get_current_user` ·
Books: `get_all_books`, `add_book`, `get_book_by_title`

Authenticated tools (`delete_user`, `update_email`, `update_password`,
`get_current_user`, `add_book`, `get_book_by_title`) take a `token` argument —
obtain it from `login`'s `auth_token`.

## Typical flow

1. `create_db` — seed the database.
2. `login(username, password)` → grab `auth_token` from the result.
3. Call authenticated tools, passing that `token`.

> VAmPI is deliberately insecure and intended only for security training in a
> controlled environment. The `debug_users` endpoint, for example, returns
> plaintext passwords by design.
