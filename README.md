# vLLM + MCP Environment

This folder manages a local AI inference stack using **vLLM** for LLM serving and **MCP** (Model Context Protocol) for database tool access.

---

## Directory Structure

```
.vllm_env/
├── pixi.toml / pixi.lock
├── requirements.txt
├── gradio.log / mcp.log / openwebui.log / vllm.log
├── environments/
│   └── vllm.env
├── gradio_chatbot_ui/
│   └── app.py
├── mcp/
│   ├── duckdb_tools_server.py
│   ├── metadata.json
│   └── metrics.json
├── models/
│   └── Qwen3.6-35B-A3B-NVFP4/
└── .webui_secret_key
```

---

## Components

### 1. vLLM (OpenAI-compatible LLM Server)

Serves the Qwen3.6 model family with GPU acceleration.

| Parameter | Qwen3.6-27B (Remote) | Qwen3.6-35B-A3B (Local) |
|---|---|---|
| **Model** | `sakamakismile/Qwen3.6-27B-Text-NVFP4-MTP` | `models/Qwen3.6-35B-A3B-NVFP4` |
| **Host** | `172.21.0.76` | `172.21.0.76` |
| **Port** | `5850` | `5850` |
| **Max Context** | 188,416 tokens | 188,416 tokens |
| **Quantization** | ModelOpt NVFP4 | Compressed-Tensors NVFP4 |
| **Reasoning** | `qwen3` parser, MTP speculative decode | `qwen3` parser |
| **Tool Calling** | `qwen3_coder` parser | `qwen3_coder` parser |
| **KV Cache** | FP8 E4M3 | FP8 E4M3 |
| **GPU Memory** | 91.15% utilization | 91.15% utilization |
| **Max Sequences** | 4 | 4 |
| **Bat. Tokens** | 8,192 | 8,192 |

Configuration files:
- **Default**: `environments/vllm.env`
- **27B variant**: `.custom_scripts/.environments/vllm_Qwen36_27B.env`
- **35B variant**: `.custom_scripts/.environments/vllm_Qwen35_35BA3B.env`

Key runtime parameters:
```
--max-model-len 188416
--gpu-memory-utilization 0.9115
--attention-backend flashinfer
--performance-mode interactivity
--language-model-only
--kv-cache-dtype fp8_e4m3
--trust-remote-code
--max-num-seqs 4
--max-num-batched-tokens 8192
--skip-mm-profiling
--enable-prefix-caching
--enable-auto-tool-choice
```

### 2. DuckDB MCP Server

A **FastMCP** server that exposes your gaming analytics DuckDB database as tools.

- **Endpoint**: `http://127.0.0.1:8000/mcp`
- **Transport**: Streamable HTTP
- **Database**: `.local_env/Optimove/Database/players.duckdb`
- **Implementation**: `mcp/duckdb_tools_server.py`

**Available Tools**:

| Tool | Description |
|---|---|
| `list_tables` | List all tables in DuckDB |
| `list_columns` | List columns for every table |
| `get_table_info(table)` | Metadata + columns for a table |
| `search_schema(query)` | Full-text search of columns, tables, and business metrics |
| `sample_rows(table, limit)` | Preview N rows from a table |
| `execute_sql(sql)` | Run read-only SQL (SELECT/WITH/SHOW/DESCRIBE/EXPLAIN only) |

**Database Schema** (described in `mcp/metadata.json`):

| Table | Business Name | Description |
|---|---|---|
| `player_transactions` | Player Transactions Summary | Deposits and withdrawals |
| `wagers` | Wager Summary | Sports + game bets grouped by player, product, date |
| `bets` | Sports Bet Transactions | Individual sports bet records |
| `bet_details` | Sports Bet Transaction Details | Detailed bet info (join on Ticket_ID) |
| `games` | Games Transactions | Casino/slots/poker bets |
| `game_types` | Game Types | Game descriptions |
| `players` | Players | Player master table |
| `first_deposits` | First Deposits | First deposit records |

**Business Metrics** (defined in `mcp/metrics.json`):

| Metric | Formula | Columns |
|---|---|---|
| **GGR** (Gross Gaming Revenue) | `Bet_Amount - Win_Amount` | `bets.Bet_Amount`, `bets.Win_Amount`, `games.Real_Bet_Amount`, etc. |
| **Turnover** | `SUM(Bet_Amount)` | `bets.Bet_Amount` |
| **Win Amount** | `SUM(Win_Amount)` | `bets.Win_Amount` |

All queries are **read-only** — the `execute_sql` tool encodes an allowlist check (`SELECT`, `WITH`, `SHOW`, `DESCRIBE`, `EXPLAIN`) before execution.

### 3. Gradio Chatbot UI

A local chat interface powered by the vLLM server.

- **App**: `gradio_chatbot_ui/app.py`
- **Port**: `5860`
- **Host**: `172.21.0.76`
- **Backend**: `openai` Python client pointing to `http://172.21.0.76:5850/v1`

The interface uses `gr.ChatInterface` with 30-message history window.

### 4. OpenWebUI

Serves on port **5860** (same as Gradio in some configs — adjust if overlapping). The OpenWebUI in your setup connects to the vLLM OpenAI-compatible endpoint at `http://172.21.0.76:5850/v1`.

---

## Quick Start

### Start all services

```bash
cd ~/.custom_scripts
bash start_vllm.sh
```

This script:
1. Sources environment vars from `.environments/vllm.env`
2. Starts vLLM on port **5850** (if not already running)
3. Starts the DuckDB MCP server on port **8000**
4. Starts OpenWebUI on port **5860**
5. Opens the browser to `http://172.21.0.76:5860`

### Start services individually

```bash
# vLLM
cd ~/.vllm_env
pixi run vllm serve $VLLM_MODEL \
  --host 172.21.0.76 --port 5850 \
  $VLLM_ARGS \
  >> vllm.log 2>&1 &

# DuckDB MCP Server
pixi run python mcp/duckdb_tools_server.py \
  >> mcp.log 2>&1 &
```

---

## Port Reference

| Service | Port | URL |
|---|---|---|
| vLLM API | `5850` | `http://172.21.0.76:5850/v1` |
| DuckDB MCP | `8000` | `http://127.0.0.1:8000` |
| Gradio Chat UI | `5860` | `http://172.21.0.76:5860` |
| OpenWebUI | `5860` | `http://172.21.0.76:5860` |

---

## Dependencies

Managed with **pixi** (`python 3.11`, conda-forge channel):

| Package | Room |
|---|---|
| `vllm` = 0.22.1 | LLM inference engine |
| `mcp` = 1.27.2 | Model Context Protocol server toolkit |
| `duckdb` = 1.5.3+ | Embedded analytical database |
| `gradio` = 6.17.3+ | Chat UI framework |
| `openai` = 2.41.0+ | OpenAI-compatible client |
| `torch` = 2.11.0 | PyTorch runtime |
| `flashinfer` | Flash attention backend |

---

## Environment Variables

Set in `environments/vllm.env` or the equivalent `.custom_scripts/.environments/` file:

| Variable | Purpose |
|---|---|
| `VLLM_MODEL` | Model identifier (HF repo or local path) |
| `VLLM_ARGS` | vLLM server CLI arguments |
| `VLLM_URL` | OpenAI-compatible API base URL |
| `VLLM_API_KEY` | API key for vLLM (often `none` for local) |
| `OPENAI_API_BASE_URL` | Same as VLLM_URL for client compatibility |
| `GAMING_DATA_ANALYTICS_DB_PATH` | Path to DuckDB database |
| `GAMING_DATA_ANALYTICS_METADATA` | Path to `mcp/metadata.json` |
| `GAMING_DATA_ANALYTICS_METRICS` | Path to `mcp/metrics.json` |

---

## Logs

| File | Content |
|---|---|
| `vllm.log` | vLLM server startup, model loading, compilation |
| `mcp.log` | MCP HTTP session requests/responses |
| `gradio.log` | Gradio interface events |
| `openwebui.log` | OpenWebUI server events |

---

## Notes

- The `.pixi/` env is gitignored except `config.toml` — run `pixi install` to recreate environments from `pixi.lock`
- `.webui_secret_key` and all `*.log` files are gitignored
- `pixi.lock` has binary merge strategy configured in `.gitattributes`
- MCP server runs in **read-only** mode — no data modification is possible through the tool interface
