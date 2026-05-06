from mcp.server.fastmcp import FastMCP
from mcp_laravel.tools import repositories, controller

mcp = FastMCP("mcp-laravel-python")

repositories.register(mcp)
controller.register(mcp)

def main():
    mcp.run()

if __name__ == "__main__":
    mcp.run()