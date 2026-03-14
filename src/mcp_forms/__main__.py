"""Точка входа: python -m mcp_forms."""

from __future__ import annotations


def main() -> None:
    from mcp_forms.config import PORT, TRANSPORT
    from mcp_forms.server import mcp

    mcp.run(transport=TRANSPORT, host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    main()
