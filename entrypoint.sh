#!/bin/bash
set -e

# ── MeshPi Host entrypoint ────────────────────────────────────────────────────
# Supports two modes:
#   CMD=host        → run meshpi host (default)
#   CMD=config      → run interactive config wizard
#   CMD=shell       → drop to bash (debug)
#   CMD=agent       → run meshpi agent (LLM REPL)
# ─────────────────────────────────────────────────────────────────────────────

CONFIG_FILE="/root/.meshpi/config.env"

# If config.env doesn't exist, try to generate from environment variables
if [ ! -f "$CONFIG_FILE" ]; then
    echo "[meshpi] No config.env found — generating from environment variables..."
    mkdir -p /root/.meshpi && chmod 700 /root/.meshpi

    # Build config.env from ENV vars (any MESHPI_CFG_* variable)
    # e.g. MESHPI_CFG_WIFI_SSID=MyNet → WIFI_SSID="MyNet"
    touch "$CONFIG_FILE" && chmod 600 "$CONFIG_FILE"
    echo "# meshpi config — auto-generated from Docker environment" >> "$CONFIG_FILE"

    # Iterate all env vars matching MESHPI_CFG_*
    while IFS='=' read -r key value; do
        if [[ "$key" == MESHPI_CFG_* ]]; then
            cfg_key="${key#MESHPI_CFG_}"
            echo "${cfg_key}=\"${value}\"" >> "$CONFIG_FILE"
            echo "[meshpi]   ${cfg_key} = ***"
        fi
    done < <(env)

    # If still empty after scanning, warn
    line_count=$(wc -l < "$CONFIG_FILE")
    if [ "$line_count" -le 1 ]; then
        echo "[meshpi] WARNING: config.env is empty."
        echo "[meshpi] Mount a config.env at /root/.meshpi/config.env"
        echo "[meshpi] or set MESHPI_CFG_* environment variables."
        echo "[meshpi] Example: -e MESHPI_CFG_WIFI_SSID=MyNetwork"
    else
        echo "[meshpi] Generated config.env with $((line_count - 1)) fields."
    fi
fi

echo "[meshpi] Host starting — port ${MESHPI_PORT:-7422}"

case "${1:-host}" in
    host)
        exec meshpi host \
            --port "${MESHPI_PORT:-7422}" \
            --bind "${MESHPI_BIND:-0.0.0.0}"
        ;;
    host-agent)
        exec meshpi host \
            --port "${MESHPI_PORT:-7422}" \
            --bind "${MESHPI_BIND:-0.0.0.0}" \
            --agent
        ;;
    config)
        exec meshpi config
        ;;
    agent)
        exec meshpi agent
        ;;
    shell|bash)
        exec /bin/bash
        ;;
    *)
        exec "$@"
        ;;
esac
