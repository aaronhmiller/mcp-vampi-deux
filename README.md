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
python3.12 -m venv .venv
. .venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run

Streamable-HTTP (default), endpoint served at `/mcp`:

```bash
python3.12 vampi_mcp_server.py
# serves on http://0.0.0.0:8000/mcp
```

Local stdio (e.g. for Claude Desktop):

```bash
MCP_TRANSPORT=stdio python3.12 vampi_mcp_server.py
```
## Connecting to Claude Desktop

You need to tell Claude Desktop how to connect to this MCP Server. To do so, in your client (Claude -> Settings -> Developer) add the JSON stanza below to your `claude_desktop_config.json` (on a Mac it'll be in `~/Library/Application Support/Claude/`), restart your Claude Desktop and it *should* just work. If not, see [Debugging](#debugging) section below.
```
  "mcpServers": {
    "mcp-vampi": {
      "command": "/opt/homebrew/bin/npx",
      "args": ["-y", "mcp-remote", "http://<your_mcp_server_ip>:8000/mcp", "--allow-http"]
    }
  },
```
To more clearly understand how the three components are wired together, please refer to [architectural view](ARCHITECTURE.md).

## Configuration

| Variable         | Default                     | Purpose                          |
|------------------|-----------------------------|----------------------------------|
| `VAMPI_BASE_URL` | `http://172.31.43.19:5000`  | VAmPI instance base URL          |
| `VAMPI_TIMEOUT`  | `15`                        | Per-request timeout (seconds)    |
| `MCP_TRANSPORT`  | `streamable-http`           | `streamable-http` or `stdio`     |
| `MCP_HOST`       | `0.0.0.0`                   | HTTP bind host                   |
| `MCP_PORT`       | `8000`                      | HTTP bind port                   |

NOTE: from my experience, the remote Claude Desktop cannot connect unless the MCP_HOST is 0.0.0.0
Please submit a PR if you have an alternative default setting that will work.

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

## Debugging

Various problems can and will happen in a networked environment (connectivity, disconnects, timeouts, latency, etc). While not exhaustive, here are some high probability places to start looking when things aren't working as designed:
* Ask Claude! Give as full a description with versions of what you're trying to do and paste in the exact errors you're getting. 
* Check the logs/stdout on the server running MCP and vAmPI and on your client (Mac or Windows running Claude Desktop)
* Test one fix at a time (i.e. restart client (if that doesn't fix); restart client and server (if that doesn't fix); make a change to MCP_HOST, restart server, restart client (you get it). Verify that changing that single setting works or does not each time. Iterate!

## Testing your understanding

* Learning: have a hypothesis...test your understanding by changing something, seeing if according to your theory, the system breaks in the way you expected. Write down what you think will happen before the test FIRST and be honest if results did or didn't match what you predicted. We have a tendency to assume we were correct and knew something all along, when in reality, we did not. Maybe just I struggle with this more than most, but it's important to not fool ourselves first. And we're the easiest one to fool. 😝
