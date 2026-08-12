# oreilly-mcp-deepdive

A collection of small, self-contained **MCP (Model Context Protocol)** servers built with the
Python `mcp` SDK (v2.x). Each server is a single file that can be run on its own, inspected with
the MCP Inspector, and wired into Claude Desktop.

The repo is used as a hands-on deep dive: every server demonstrates a *different* aspect of MCP —
calling an external API, returning binary content, and serving over HTTP instead of stdio.

---

## Included MCP servers

### `crypto` — [crypto.py](crypto.py)

Fetches live cryptocurrency prices from the public [CoinGecko](https://www.coingecko.com/) API.

| | |
|---|---|
| Server name | `Crypto` |
| Tool | `get_crypto_currency_price(currency: str) -> str` |
| Transport | stdio (default) |
| External dependency | `https://api.coingecko.com/api/v3/simple/price` (no API key required) |

The `currency` argument is a CoinGecko **coin id**, not a ticker symbol — use `bitcoin`,
`ethereum`, `solana` (not `BTC`, `ETH`, `SOL`). Network errors and unknown coins are caught and
returned as a readable message instead of raising.

```
> What is bitcoin trading at?
The current price of bitcoin is $64213.00 USD.
```

### `screenshot` — [screenshot.py](screenshot.py)

Captures the Windows desktop and returns it as an image, demonstrating **non-text tool results**
(the MCP `Image` content type).

| | |
|---|---|
| Server name | `ScreenshotDemo` |
| Tool | `capture_screenshot() -> Image` |
| Transport | stdio (default) |
| External dependency | `powershell.exe` (System.Windows.Forms / System.Drawing) |

The tool shells out to PowerShell, which grabs `PrimaryScreen.Bounds`, encodes the bitmap as JPEG
and prints it base64. Python decodes it and hands back an `Image` object, which Claude renders
inline.

> **Requires Windows or WSL.** Under WSL the interop binary `powershell.exe` must be on `PATH`.
> On plain Linux/macOS this tool will fail with `FileNotFoundError`. Only the primary monitor is
> captured.

### `greeting` — [greeting.py](greeting.py)

The minimal example, used to demonstrate the **streamable-http** transport instead of stdio.

| | |
|---|---|
| Server name | `greeting` |
| Tool | `greeting(name: str) -> str` |
| Transport | `streamable-http`, listening on `http://127.0.0.1:8000/mcp` |
| External dependency | none |

Unlike the other two, this server is **not** spawned by the client. You start it yourself and it
keeps running; clients connect to the HTTP endpoint:

```bash
uv run greeting.py
```

---

## Attribute comparison

Including two related servers from sibling repos for contrast:

| MCP | Repo | Transport | Launched by | Distribution | External API | Returns |
|---|---|---|---|---|---|---|
| **crypto** | this repo | stdio | client spawns `uv run crypto.py` | local file | ✅ CoinGecko REST API | text |
| **screenshot** | this repo | stdio | client spawns `uv run screenshot.py` | local file | ❌ (local PowerShell subprocess) | image (JPEG) |
| **greeting** | this repo | **streamable-http** | you start it; client connects to `:8000/mcp` | local file | ❌ | text |
| **weather** | `oreilly-mcp` | stdio | client spawns `uv run weather.py` | local file | ❌ (hardcoded stub) | text |
| **addition** | `mcp-server-deepdive` | stdio | client spawns `uvx` | **GitHub as package repo** (`uvx --from git+…`) | ❌ | number |

The `addition` server is the packaging example: it has a `[project.scripts]` entry point, so it
never needs to be cloned — `uvx` installs it straight from GitHub into a throwaway environment.

---

## Adding the servers to Claude Desktop

Edit the Claude Desktop config file:

| OS | Path |
|---|---|
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |

Add an `mcpServers` block. The snippet below is for **Claude Desktop on Windows talking to servers
inside WSL** — each entry runs `wsl --cd <project dir> -- <absolute path to uv> run <file>`:

```json
{
  "mcpServers": {
    "crypto": {
      "command": "wsl",
      "args": [
        "--cd", "/home/daemr/workspace/oreilly-mcp-deepdive",
        "--",
        "/home/daemr/.local/bin/uv", "run", "crypto.py"
      ]
    },
    "screenshotDemo": {
      "command": "wsl",
      "args": [
        "--cd", "/home/daemr/workspace/oreilly-mcp-deepdive",
        "--",
        "/home/daemr/.local/bin/uv", "run", "screenshot.py"
      ]
    },
    "greeting": {
      "command": "wsl",
      "args": [
        "--",
        "/home/daemr/.nvm/versions/node/v24.19.0/bin/npx", "-y",
        "mcp-remote", "http://127.0.0.1:8000/mcp"
      ]
    },
    "addition": {
      "command": "wsl",
      "args": [
        "--",
        "/home/daemr/.local/bin/uvx",
        "--from", "git+https://github.com/daemroni/oreilly-mcp-deepdive.git",
        "mcp-server"
      ]
    }
  }
}
```

Notes:

- **Use absolute paths.** Claude Desktop does not run a login shell, so `uv`, `uvx` and `npx` are
  not on `PATH`. Find yours with `which uv`.
- The **key** (`"crypto"`, `"screenshotDemo"`, …) is just a display label you choose; it does not
  have to match the server name in the Python file.
- **`greeting` is different**: Claude Desktop only speaks stdio, so `mcp-remote` acts as a bridge
  to the HTTP endpoint. Start `uv run greeting.py` *before* launching Claude Desktop, or the
  connection fails.
- **Restart Claude Desktop** after editing — config is read once at startup. Connected servers
  appear under the tools icon in the prompt box.

If you run Claude Desktop natively on Linux/macOS, drop the WSL wrapper:

```json
{
  "mcpServers": {
    "crypto": {
      "command": "uv",
      "args": ["--directory", "/home/daemr/workspace/oreilly-mcp-deepdive", "run", "crypto.py"]
    }
  }
}
```

---

## Setting up your own MCP repo

```bash
uv init my-mcp-server
cd my-mcp-server

uv venv
source .venv/bin/activate      

uv add mcp[cli]
```

`mcp[cli]` pulls in the SDK plus the `mcp` command line tool (needed for `mcp dev`). Add anything
else your tools need, e.g. `uv add requests pillow` for this repo.

Then create a server file:

```python
from mcp.server import MCPServer

mcp = MCPServer("my-server")

@mcp.tool(description="Add two numbers.")
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

if __name__ == "__main__":
    mcp.run()                       # stdio; use mcp.run(transport="streamable-http") for HTTP
```

Two things the model actually sees, so make them count: the **`description=`** on the decorator
and the **type hints**, which become the tool's input schema. The docstring documents the tool for
humans reading the code.

Run it with `uv run my_server.py`.

### Getting set up with *this* repo

```bash
git clone <this repo>
cd oreilly-mcp-deepdive
uv sync            # creates .venv and installs mcp[cli], requests, pillow from uv.lock
```

Requires Python ≥ 3.12 (pinned to 3.12 in [.python-version](.python-version)).

---

## Testing with the MCP Inspector

The Inspector is a browser UI that connects to a server, lists its tools, and lets you call them
by hand — much faster than restarting Claude Desktop on every change.

### stdio servers (`crypto`, `screenshot`)

```bash
mcp dev crypto.py
```

This spawns the server *and* the Inspector, and prints a pre-authenticated URL to open. Swap in
`screenshot.py` for the other one.

### HTTP servers (`greeting`)

Start the server in one terminal:

```bash
uv run greeting.py
```

Start the Inspector in a second terminal:

```bash
npx @modelcontextprotocol/inspector
```

Then in the Inspector UI, set:

- **Transport Type**: `Streamable HTTP`
- **URL**: `http://localhost:8000/mcp`

and hit **Connect** → **List Tools** → pick `greeting`, fill in `name`, **Run Tool**.

> Requires Node.js for `npx`. The Inspector prints a session token in the terminal; use the
> full URL it gives you if the UI asks for authentication.

---

## Layout

```
oreilly-mcp-deepdive/
├── crypto.py                    # external-API MCP  (stdio)
├── screenshot.py                # image-returning MCP (stdio, Windows/WSL)
├── greeting.py                  # streamable-http MCP (:8000/mcp)
├── pyproject.toml               # deps: mcp[cli], requests, pillow
├── uv.lock
└── src/oreilly_mcp_deepdive/    # package scaffold from `uv init` (unused by the demos)
```

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| Server missing in Claude Desktop | Restart the app; check absolute paths; look at the logs in `%APPDATA%\Claude\logs\` |
| `spawn uv ENOENT` | `uv` not on Claude Desktop's `PATH` — use the full path from `which uv` |
| `greeting` won't connect | The HTTP server isn't running. Start `uv run greeting.py` first |
| `Price information for X is not available.` | Wrong CoinGecko id — use `bitcoin`, not `BTC` |
| Screenshot raises `FileNotFoundError` | Not on Windows/WSL, or `powershell.exe` isn't on `PATH` |
