from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import json
import asyncio

from core.schemas import ExecuteRequest
from agent.bridge import bridge

router = APIRouter()


@router.post("/execute")
async def execute(request: ExecuteRequest):
    """Execute a command and stream back the results."""

    async def event_generator():
        try:
            async for event in bridge.execute_streaming(request.command):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'data': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )