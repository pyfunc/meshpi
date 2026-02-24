"""
meshpi v0.2.0 – Zero-touch Raspberry Pi fleet management
=========================================================
Apache License 2.0 © 2024 Softreck

Quick start
-----------
HOST:
    pip install meshpi
    meshpi config          # interactive config wizard
    meshpi host            # start host service + REST API + WebSocket
    meshpi host --agent    # + LLM NLP agent

CLIENT (fresh RPi):
    pip install meshpi
    meshpi scan            # discover host, download & apply config
    meshpi daemon          # persistent WS connection (diagnostics + live commands)

Hardware:
    meshpi hw list
    meshpi hw apply oled_ssd1306_i2c sensor_bme280

LLM Agent (requires litellm):
    pip install "meshpi[llm]"
    OPENAI_API_KEY=sk-... meshpi agent
    # or local: LITELLM_MODEL=ollama/llama3.2 meshpi agent
"""

__version__ = "0.1.6"
__author__ = "Softreck"
__license__ = "Apache-2.0"
