from mcp.server import MCPServer

mcp = MCPServer("Addition")

@mcp.tool(description="Add two numbers.")
def add(a: int, b: int) -> int:
    """Add two numbers.
    Args:
        a: The first number.
        b: The second number.
    Returns:
        The sum of the two numbers.
    """
    return a + b

if __name__ == "__main__":
    mcp.run()