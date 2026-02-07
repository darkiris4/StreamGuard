from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from services.ws_manager import manager


router = APIRouter(tags=["ws"])


@router.websocket("/ws/audit/{job_id}")
async def ws_audit(websocket: WebSocket, job_id: str):
    await manager.connect(job_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(job_id, websocket)


@router.websocket("/ws/mitigate/{job_id}")
async def ws_mitigate(websocket: WebSocket, job_id: str):
    await manager.connect(job_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(job_id, websocket)
