"""WebSocket endpoints for real-time data streaming."""

import asyncio
import json
from datetime import datetime

from fastapi import Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from solar_analyzer.data.database import get_db
from solar_analyzer.data.models import SolarReading
from solar_analyzer.logging_config import get_logger

logger = get_logger("solar_analyzer.websockets")


class ConnectionManager:
    """Manages WebSocket connections for real-time data streaming."""

    def __init__(self):
        self.active_connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)
        logger.info("WebSocket client connected", total_connections=len(self.active_connections))

    async def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        async with self._lock:
            self.active_connections.discard(websocket)
        logger.info("WebSocket client disconnected", total_connections=len(self.active_connections))

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific client."""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error("Failed to send WebSocket message", error=str(e))
            await self.disconnect(websocket)

    async def broadcast(self, message: dict):
        """Broadcast a message to all connected clients."""
        if not self.active_connections:
            return

        message_text = json.dumps(message)
        disconnected = set()

        async with self._lock:
            connections = self.active_connections.copy()

        for connection in connections:
            try:
                await connection.send_text(message_text)
            except Exception as e:
                logger.warning("WebSocket connection failed during broadcast", error=str(e))
                disconnected.add(connection)

        # Clean up disconnected clients
        if disconnected:
            async with self._lock:
                self.active_connections -= disconnected
            logger.info("Cleaned up disconnected clients",
                       removed=len(disconnected),
                       remaining=len(self.active_connections))


# Global connection manager
manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, db: AsyncSession = Depends(get_db)):
    """WebSocket endpoint for real-time solar data."""
    await manager.connect(websocket)

    try:
        while True:
            # Wait for client message (keepalive or request)
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                message = json.loads(data)

                if message.get("type") == "request_data":
                    # Send current data immediately
                    current_data = await get_current_solar_data(db)
                    await manager.send_personal_message({
                        "type": "current_data",
                        "data": current_data
                    }, websocket)

                elif message.get("type") == "ping":
                    # Respond to ping with pong
                    await manager.send_personal_message({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }, websocket)

            except TimeoutError:
                # Send periodic data update every 30 seconds
                current_data = await get_current_solar_data(db)
                await manager.send_personal_message({
                    "type": "current_data",
                    "data": current_data
                }, websocket)

    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception as e:
        logger.error("WebSocket error", error=str(e))
        await manager.disconnect(websocket)


async def get_current_solar_data(db: AsyncSession) -> dict:
    """Get current solar data for WebSocket transmission."""
    try:
        # Get most recent reading
        result = await db.execute(
            select(SolarReading).order_by(SolarReading.timestamp.desc()).limit(1)
        )
        reading = result.scalar_one_or_none()

        if not reading:
            return {
                "timestamp": datetime.now().isoformat(),
                "production_kw": 0.0,
                "consumption_kw": 0.0,
                "grid_kw": 0.0,
                "battery_kw": None,
                "battery_soc": None,
                "status": "no_data"
            }

        return {
            "timestamp": reading.timestamp.isoformat(),
            "production_kw": reading.production_kw,
            "consumption_kw": reading.consumption_kw,
            "grid_kw": reading.grid_kw,
            "battery_kw": reading.battery_kw,
            "battery_soc": reading.battery_soc,
            "status": "active"
        }

    except Exception as e:
        logger.error("Failed to get current solar data", error=str(e))
        return {
            "timestamp": datetime.now().isoformat(),
            "production_kw": 0.0,
            "consumption_kw": 0.0,
            "grid_kw": 0.0,
            "battery_kw": None,
            "battery_soc": None,
            "status": "error",
            "error": str(e)
        }


async def broadcast_solar_update(data: dict):
    """Broadcast solar data update to all connected clients."""
    await manager.broadcast({
        "type": "solar_update",
        "data": data,
        "timestamp": datetime.now().isoformat()
    })


async def broadcast_system_alert(alert: dict):
    """Broadcast system alert to all connected clients."""
    await manager.broadcast({
        "type": "system_alert",
        "alert": alert,
        "timestamp": datetime.now().isoformat()
    })
