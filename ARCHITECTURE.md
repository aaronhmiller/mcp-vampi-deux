```
                  ┌──────────────────────────────────────────────────┐
                  │ Claude Desktop                                                                                                                                                         │
                  │   (MCP client)                                                                                                                                                             │
                  └────────────────────────┴─────────────────────────┘
                                           │
                                           │
                  MCP over streamable-http  (json_response=True)
                  stateless — no `mcp-session-id` header returned
                                           │
   ════════════════════════════════════════╪════════════════════════════
              🌐  P U B L I C   I N T E R N E T   B O U N D A R Y
   ════════════════════════════════════════╪════════════════════════════
                                           ▼
                  ┌────────────────────────┬─────────────────────────┐
                  │ HOST · AWS EC2 (Amazon Linux)                                                                                                                           │
                  ├──────────────────────────────────────────────────┤
                  │ mcp-vampi-deux · FastMCP (MCP Server)                                                                                                             │
                  │     stateless_http = True                                                                                                                                           │
                  │     json_response  = True                                                                                                                                         │
                  │     transport via $MCP_TRANSPORT                                                                                                                      │
                  │      (streamable-http | stdio)                                                                                                                                     │
                  ├──────────────────────────────────────────────────┤
                  │ 14 tools / 4 groups                                                                                                                                                   │
                  │   service/db  home · create_db                                                                                                                                │
                  │   auth        register_user · login                                                                                                                                 │
                  │   users       get_all_users · debug_users                                                                                                                   │
                  │                get_user_by_username                                                                                                                             │
                  │                delete_user · update_email                                                                                                                       │
                  │                update_password                                                                                                                                     │
                  │                get_current_user                                                                                                                                       │
                  │   books       get_all_books · add_book                                                                                                                    │
                  │                get_book_by_title                                                                                                                                     │
                  ├──────────────────────────────────────────────────┤
                  │ auth tools carry a `token` param                                                                                                                              │
                  │ → no server-side JWT cache                                                                                                                                   │
                  └────────────────────────┴─────────────────────────┘
                                           │
                  httpx  →  $VAMPI_BASE_URL
                  (default http://172.31.43.19:5000)
                                           │
   ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄╪┄┄┄┄┄┄┄┄┄┄┄┄┄┄
              🔒  I N T E R N A L   ( V P C )   N E T W O R K
   ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄╪┄┄┄┄┄┄┄┄┄┄┄┄┄┄
                                           ▼
                  ┌────────────────────────┬─────────────────────────┐
                  │ VAmPI · REST API                                                                                                                                                    │
                  │ http://172.31.43.19:5000                                                                                                                                         │
                  │                                                                                                                                                                                  │
                  │ deliberately vulnerable target                                                                                                                                   │
                  │ — security-training use only —                                                                                                                                 │
                  └──────────────────────────────────────────────────┘
```
