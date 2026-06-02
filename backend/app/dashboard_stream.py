import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.events import subscribe

router = APIRouter()


@router.websocket("/ws/events")
async def events_stream(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        async for event in subscribe("*"):
            await websocket.send_text(json.dumps(event))
    except WebSocketDisconnect:
        pass
