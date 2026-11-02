from typing import Any, Dict, List
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

router = APIRouter(tags=["Real-Time Collaboration"])


class ElementUpdate(BaseModel):
    id: str
    title: str
    description: str = ""


class ConnectionManager:
    def __init__(self):
        # room_id -> list of active WebSockets
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # room_id -> room state dict
        self.rooms: Dict[str, Dict[str, Any]] = {}

    def get_or_create_room(self, room_id: str) -> Dict[str, Any]:
        if room_id not in self.rooms:
            self.rooms[room_id] = {
                "id": room_id,
                "elements": [
                    {
                        "id": "node-1",
                        "title": "API Gateway / Load Balancer",
                        "description": "Primary edge entrypoint",
                    }
                ],
            }
        return self.rooms[room_id]

    async def connect(self, room_id: str, websocket: WebSocket):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)

    def disconnect(self, room_id: str, websocket: WebSocket):
        if room_id in self.active_connections:
            if websocket in self.active_connections[room_id]:
                self.active_connections[room_id].remove(websocket)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    async def broadcast(self, room_id: str, message: Dict[str, Any], sender: WebSocket = None):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                if connection != sender:
                    try:
                        await connection.send_json(message)
                    except Exception:
                        pass


manager = ConnectionManager()


@router.post("/api/rooms")
def create_room():
    room_id = f"room-{uuid.uuid4().hex[:8]}"
    room = manager.get_or_create_room(room_id)
    return {
        "roomId": room_id,
        "shareUrl": f"/session?room={room_id}",
        "room": room,
    }


@router.get("/api/rooms/{room_id}")
def get_room(room_id: str):
    return manager.get_or_create_room(room_id)


@router.post("/api/rooms/{room_id}/elements")
async def update_room_element(room_id: str, update: ElementUpdate):
    room = manager.get_or_create_room(room_id)
    updated_element = None
    for el in room["elements"]:
        if el["id"] == update.id:
            el["title"] = update.title
            el["description"] = update.description
            updated_element = el
            break

    if not updated_element:
        updated_element = {
            "id": update.id,
            "title": update.title,
            "description": update.description,
        }
        room["elements"].append(updated_element)

    # Broadcast update to all room participants
    await manager.broadcast(
        room_id,
        {
            "type": "element_updated",
            "element": updated_element,
            "roomId": room_id,
        },
    )
    return {"status": "ok", "element": updated_element}


@router.websocket("/ws/rooms/{room_id}")
async def websocket_room_endpoint(websocket: WebSocket, room_id: str):
    await manager.connect(room_id, websocket)
    room = manager.get_or_create_room(room_id)
    # Send current state upon joining
    await websocket.send_json({"type": "room_state", "room": room})
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            if msg_type == "update_element":
                el_data = data.get("element", {})
                for el in room["elements"]:
                    if el["id"] == el_data.get("id"):
                        el["title"] = el_data.get("title", el["title"])
                        el["description"] = el_data.get("description", el["description"])
                # Broadcast to others
                await manager.broadcast(
                    room_id,
                    {
                        "type": "element_updated",
                        "element": el_data,
                        "roomId": room_id,
                    },
                    sender=websocket,
                )
    except WebSocketDisconnect:
        manager.disconnect(room_id, websocket)
