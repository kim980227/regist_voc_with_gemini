import asyncio
import sys
import os
from pathlib import Path
from typing import List
from mcp import Tool
from mcp.server import Server
from mcp.types import TextContent

BASE_DIR = Path(__file__).resolve().parent.parent  # 프로젝트 루트 추정
MAIN_SCRIPT = BASE_DIR / "main.py"
DATA_DIR = BASE_DIR / "data"

app = Server("voc_agent_server")

@app.list_tools()
async def list_tools() -> List[Tool]:
    return [
        Tool(
            name="run_main_py",
            description="main.py 실행 (data 폴더 안 CSV 파일 처리). csv_name은 파일명만 주어도 됨 (확장자 생략 가능).",
            inputSchema={
                "type": "object",
                "properties": {
                    "csv_name": {"type": "string", "description": "처리할 CSV 파일명 (예: VOC_일괄등록(8월) 또는 VOC_일괄등록(8월).csv)"}
                },
                "required": ["csv_name"],
                "additionalProperties": False
            }
        ),
        Tool(
            name="list_csv_files",
            description="data 폴더 내 CSV 파일 목록 반환",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        )
    ]

def _find_csv(csv_name: str) -> tuple[Path | None, str | None]:
    """파일명만 받아 data 폴더에서 CSV 찾기 (대소문자 구분 안함, 확장자 생략 지원)."""
    if not DATA_DIR.exists():
        return None, f"❌ data 폴더가 없습니다: {DATA_DIR}"

    name = csv_name.strip()
    if not name:
        return None, "❌ csv_name이 비어있습니다."

    # 절대/상대 경로 형태면 그대로 사용 (단, 존재 검사)
    if any(sep in name for sep in ("/", os.sep)):
        p = Path(name)
        if not p.is_absolute():
            p = (BASE_DIR / p).resolve()
        if p.exists():
            return p, None
        return None, f"❌ 경로가 존재하지 않습니다: {p}"

    # 확장자 붙이기 시나리오 준비
    candidates = []
    base = name[:-4] if name.lower().endswith('.csv') else name

    # data 디렉토리 내 검색 (대소문자 무시)
    for f in DATA_DIR.glob('*.csv'):
        fname_lower = f.name.lower()
        if name.lower() == f.name.lower():  # 완전 일치
            return f.resolve(), None
        if base.lower() == fname_lower[:-4]:  # 확장자 제외 매칭
            candidates.append(f.resolve())
        elif base.lower() in fname_lower:  # 부분 포함 (느슨한 매칭)
            candidates.append(f.resolve())

    # 후보 정리
    unique = list(dict.fromkeys(candidates))
    if len(unique) == 1:
        return unique[0], None
    if len(unique) > 1:
        listing = "\n".join(f" - {p.name}" for p in unique[:20])
        return None, f"❌ 다의적 매칭(여러 파일 후보):\n{listing}\n구체적으로 입력하세요."

    # 아무것도 못 찾음 -> 목록 제공
    existing = [p.name for p in DATA_DIR.glob('*.csv')]
    hint = ", ".join(existing) if existing else "(data 폴더 비어있음)"
    return None, f"❌ '{csv_name}'에 해당하는 CSV를 찾지 못했습니다. 존재 목록: {hint}"

async def _exec_main(csv_path: Path) -> TextContent:
    if not MAIN_SCRIPT.exists():
        return TextContent(type="text", text=f"❌ main.py를 찾을 수 없습니다: {MAIN_SCRIPT}")

    cmd = [sys.executable, str(MAIN_SCRIPT), str(csv_path)]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(BASE_DIR)
        )
        stdout_b, stderr_b = await proc.communicate()
        stdout = stdout_b.decode(errors='ignore').strip() or '<empty>'
        stderr = stderr_b.decode(errors='ignore').strip() or '<empty>'
        return TextContent(
            type="text",
            text=(
                f"▶️ 실행: {' '.join(cmd)}\n"
                f"📂 작업디렉토리: {BASE_DIR}\n"
                f"� CSV: {csv_path}\n"
                f"STDOUT:\n{stdout}\n\nSTDERR:\n{stderr}"
            )
        )
    except Exception as e:
        return TextContent(type="text", text=f"❌ 실행 실패: {e}")

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> List[TextContent]:
    if name == "list_csv_files":
        if not DATA_DIR.exists():
            return [TextContent(type="text", text=f"data 폴더가 없습니다: {DATA_DIR}")]
        files = sorted([p for p in DATA_DIR.glob('*.csv')])
        if not files:
            return [TextContent(type="text", text="(CSV 없음)")]
        listing = "\n".join(f" - {p.name}" for p in files[:200])
        return [TextContent(type="text", text=f"총 {len(files)}개 CSV:\n{listing}")]

    if name == "run_main_py":
        csv_name = arguments.get("csv_name")
        if not csv_name:
            return [TextContent(type="text", text="csv_name은 필수입니다.")]
        resolved, err = _find_csv(csv_name)
        if err:
            return [TextContent(type="text", text=err)]
        result = await _exec_main(resolved)
        return [result]

    return [TextContent(type="text", text="Unknown tool name")]

async def main():
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())