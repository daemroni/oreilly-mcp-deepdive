from mcp.server import MCPServer

mcp = MCPServer("greeting")

@mcp.tool()
def greeting(name: str) -> str:
    """Greet a user by name."""
    return f"Hello, {name}!"

if __name__ == "__main__":
    mcp.run(transport="streamable-http")