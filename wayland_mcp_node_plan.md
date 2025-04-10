# Plan: Node.js MCP Entrypoint for wayland_mcp

## Objective
Create a Node.js/JSX file named `wayland_mcp` at the project root, executable by `uvx`, that implements the MCP stdio protocol and bridges to the Python Flask server running on localhost:5000.

## Steps
1. **Create `wayland_mcp` Node.js/JSX Entrypoint**
    - Listens for MCP stdio requests.
    - Forwards tool invocations to the Python Flask server via HTTP.
    - Returns results in MCP protocol format.
2. **Supported Tools**
    - `execute_task` → POST /execute
    - `capture_screenshot` → (implement if Flask server exposes this)
    - `compare_images` → (implement if Flask server exposes this)
3. **Error Handling**
    - If the Python server is not running, return an error.
    - If the HTTP request fails, return an error.

## Mermaid Diagram
```mermaid
flowchart TD
    A[MCP Client] -- stdio --> B[wayland_mcp (Node.js/JSX)]
    B -- HTTP (localhost:5000) --> C[Python Flask Server]
    C -- result --> B
    B -- stdio --> A
```

## Next Steps
- Confirm this plan with the user.
- Implement the Node.js/JSX entrypoint as described.