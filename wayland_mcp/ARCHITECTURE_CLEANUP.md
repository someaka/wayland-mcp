# Clean MCP Server Architecture for uvx Compatibility

## Objective

- Make the MCP server fully compatible with `uvx` and PyPI.
- Remove the Node.js bridge and npm-related files from the main path.
- Follow the pattern of the DuckDuckGo MCP server (pure Python, PyPI).

## Target Architecture

```mermaid
flowchart TD
    subgraph PyPI
        A[wayland-mcp (Python MCP server)]
    end
    User1(uvx, Claude, etc) -->|PyPI| A
```

- **uvx and all MCP-native clients use the PyPI package directly.**
- **No Node.js bridge or npm wrapper in the mainline.**

## Steps

1. **Refactor Python MCP server as a PyPI package**
    - Add `pyproject.toml` with metadata, dependencies, and entry point.
    - Move all MCP logic to `wayland_mcp/server/app.py` (or similar).
    - Ensure `requirements.txt` matches `pyproject.toml` dependencies.

2. **Remove Node.js bridge**
    - Delete `wayland_mcp.js` and any npm-related files from the main path.

3. **Entry point**
    - Provide a CLI entry point (e.g. `wayland-mcp-server`) that launches the Flask MCP server.

4. **Testing**
    - Test locally with `uv run` and `uvx wayland-mcp`.

5. **Publish**
    - Publish to PyPI as `wayland-mcp`.

6. **Documentation**
    - Update README and architecture docs.

## Migration Notes

- If npm support is needed in the future, provide a thin wrapper as a separate, optional package.
- This approach matches the DuckDuckGo MCP server, which is known to work with `uvx`.

---