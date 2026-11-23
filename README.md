# Pinterest MCP for Claude

Tools: get_account, list_boards, list_board_pins, search_my_pins, get_pin,
create_board, create_pin, save_pin_to_board, delete_pin.

## 1. Get a Pinterest token
1. Go to https://developers.pinterest.com/apps/ → Connect app / Create app.
2. In the app, generate an access token with scopes:
   `user_accounts:read, boards:read, boards:write, pins:read, pins:write`.
   (New apps start with "Trial" access — enough for your own account. Request
   "Standard" access later if you need it.)

## 2. Deploy (Render, free tier)
1. Put these 3 files in a new GitHub repo.
2. Render → New → Web Service → pick the repo.
   - Build command: `pip install -r requirements.txt`
   - Start command: `python server.py`
3. Environment variables:
   - `PINTEREST_TOKEN` = your token
   - `MCP_SECRET` = any long random string (e.g. from https://www.uuidgenerator.net)
4. Deploy. You get a URL like `https://pinterest-mcp.onrender.com`.

(Railway works the same way: new project from GitHub repo, add the 2 variables.)

## 3. Add to Claude
Settings → Connectors → Add custom connector
- Name: Pinterest
- URL: `https://<your-app>.onrender.com/<MCP_SECRET>/mcp`

Keep that URL private — the secret in it is what protects your account.

## Notes
- Pinterest's API only lets you search **your own** pins, not all of Pinterest.
  For browsing public Pinterest, use Claude in Chrome.
- Render free tier sleeps when idle; the first call may take ~30 s.
