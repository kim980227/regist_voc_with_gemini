import asyncio
import subprocess
import sys
from mcp import Tool
from mcp.server import Server
from mcp.types import TextContent, PromptMessage

app = Server("voc_agent_server")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="run_main_py",
            description="Execute main.py script to process VOC data from a CSV file.",
            inputSchema={
                "type": "object",
                "properties": {
                    "csv_path": {"type": "string", "description": "Path to the CSV file to process."}
                },
                "required": ["csv_path"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "run_main_py":
        csv_path = arguments.get("csv_path")
        if not csv_path:
            return [TextContent(type="text", text="Error: csv_path is required.")]
        
        try:
            # main.py를 subprocess로 실행 (보안 주의: 실제 환경에서는 검증 필요)
            result = subprocess.run([sys.executable, "main.py", csv_path], capture_output=True, text=True)
            return [TextContent(type="text", text=f"Output: {result.stdout}\nErrors: {result.stderr}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Execution failed: {str(e)}")]
    
    return [TextContent(type="text", text="Unknown tool.")]

async def main():
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())