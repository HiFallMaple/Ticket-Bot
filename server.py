import asyncio
import logging
import os
from contextlib import asynccontextmanager
from multiprocessing import Process, Queue

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import FileResponse, HTMLResponse

from config import CONFIG, FRONTEND_PATH, get_stored_config, load_config, save_config
from type import ActionRequest, BotStatus, ProgramStatusEnum, ConfigSchema, SessionInfo
import tixcraft


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(send_logs())
    yield
    task.cancel()


app = FastAPI(lifespan=lifespan)
process = None
log_queue = Queue()

# Store all connected WebSocket clients
connected_websockets: list[WebSocket] = []


async def send_logs():
    while True:
        logs: logging.LogRecord = await asyncio.to_thread(
            log_queue.get
        )  # Get log messages from the queue
        logs: str = logs.getMessage()
        # Send logs to all connected WebSocket clients
        for websocket in connected_websockets:
            try:
                await websocket.send_text(logs)
            except Exception as e:
                print(f"Error sending log to websocket: {e}")


@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await websocket.accept()
    connected_websockets.append(websocket)  # Add to the connected list
    try:
        while True:
            # Wait for the client to send any message to keep the connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        print("WebSocket disconnected")
    finally:
        connected_websockets.remove(websocket)  # Remove from the connected list
        await websocket.close()  # Attempt to close the WebSocket


@app.put("/api/bot/tixcraft", response_model=BotStatus)
async def control_tixcraft_bot(action_request: ActionRequest):
    global process

    if action_request.action == "run":
        if not process or not process.is_alive():
            process = Process(target=tixcraft.main, args=(log_queue,))
            process.start()
        return BotStatus(status=ProgramStatusEnum.RUNNING)

    elif action_request.action == "stop":
        if process and process.is_alive():
            process.terminate()
            process.join()
        return BotStatus(status=ProgramStatusEnum.STOPPED)


@app.get("/api/bot/tixcraft", response_model=BotStatus)
async def get_tixcraft_status():
    global process
    if process and process.is_alive():
        return BotStatus(status=ProgramStatusEnum.RUNNING)
    else:
        return BotStatus(status=ProgramStatusEnum.STOPPED)


@app.get("/api/config", response_model=ConfigSchema)
async def get_config():
    load_config()
    return ConfigSchema(**get_stored_config())


@app.put("/api/config", response_model=ConfigSchema)
async def update_config(config: ConfigSchema):
    for key, value in config:
        print(key, value)
        if value is not None:
            CONFIG[key] = value
    save_config()
    return ConfigSchema(**get_stored_config())


@app.get("/api/event/tixcraft", response_model=list[SessionInfo])
async def get_tixcraft_event_info():
    info = tixcraft.Tixcraft.get_session_info(CONFIG["TIXCRAFT_EVENT_URL"])
    for i, session in enumerate(info):
        session["id"] = i
    return info


@app.get("/{full_path:path}")
async def catch_all(request: Request, full_path: str):
    if not full_path:
        full_path = "index.html"
    file_path = os.path.join(FRONTEND_PATH, full_path)
    print("full_path", full_path)
    print("file_path", file_path)
    print("exists", os.path.exists(file_path))
    if os.path.exists(file_path):
        print("return file")
        return FileResponse(file_path)
    else:
        return HTMLResponse(content="404 Not Found", status_code=404)
