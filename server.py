import asyncio
import logging
import os
import threading
from contextlib import asynccontextmanager
from queue import Queue
from threading import Event, Thread
from typing import Optional

from fastapi import FastAPI, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.websockets import WebSocketState

import tixcraft
from config import CONFIG, FRONTEND_PATH, get_stored_config, load_config, save_config
from type import ActionRequest, BotStatus, ConfigSchema, ProgramStatusEnum, SessionInfo
from utils import raise_SystemExit_in_thread


@asynccontextmanager
async def lifespan(app: FastAPI):
    task_logs = asyncio.create_task(send_logs())
    task_status = asyncio.create_task(send_status())
    yield
    log_queue.put("END")
    logger.info(f"send_logs.cancel: {task_logs.cancel()}")
    logger.info(f"send_status.cancel: {task_status.cancel()}")
    logger.info(f"thread: {thread}")
    if thread:
        raise_SystemExit_in_thread(thread)


app = FastAPI(lifespan=lifespan)
thread = None
# multiprocessing event
continue_event = Event()
pause_flag = Event()
end_flag = Event()
log_queue = Queue()
logger = logging.getLogger("uvicorn")

# Store all connected WebSocket clients
logs_websockets: list[WebSocket] = []
thread_status_websockets: list[WebSocket] = []


async def get_thread_status() -> ProgramStatusEnum:
    global thread
    if thread and thread.is_alive():
        if pause_flag.is_set():
            return ProgramStatusEnum.PAUSED
        if end_flag.is_set():
            return ProgramStatusEnum.ENDED
        return ProgramStatusEnum.RUNNING
    else:
        return ProgramStatusEnum.STOPPED


async def send_logs():
    while True:
        logs: logging.LogRecord = await asyncio.to_thread(
            log_queue.get
        )  # Get log messages from the queue
        if logs == "END":
            return
        logs: str = logs.getMessage()
        logger.debug("log from queue:", logs)
        # Send logs to all connected WebSocket clients
        for websocket in logs_websockets:
            try:
                await websocket.send_text(logs)
            except Exception as e:
                logger.warning(f"Error sending log to websocket: {e}")


async def send_status():
    while True:
        status = await get_thread_status()
        for websocket in thread_status_websockets:
            try:
                await websocket.send_text(status.value)
            except Exception as e:
                logger.warning(f"Error sending status to websocket: {e}")
        await asyncio.sleep(0.5)


@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await websocket.accept()
    logs_websockets.append(websocket)  # Add to the connected list
    try:
        while True:
            # Wait for the client to send any message to keep the connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    finally:
        logs_websockets.remove(websocket)  # Remove from the connected list
        if not WebSocketState.DISCONNECTED:
            await websocket.close()  # Attempt to close the WebSocket


@app.websocket("/ws/thread/status")
async def websocket_thread_status(websocket: WebSocket):
    await websocket.accept()
    thread_status_websockets.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    finally:
        thread_status_websockets.remove(websocket)
        if not WebSocketState.DISCONNECTED:
            await websocket.close()


@app.put("/api/bot/tixcraft", response_model=BotStatus)
async def control_tixcraft_bot(action_request: ActionRequest):
    global thread, continue_event, pause_flag, end_flag, log_queue
    logger.info(f"action_request: {action_request}, thread: {thread}")
    if thread:
        logger.info(f"thread is alive: {thread.is_alive()}")
    logger.info(f"pause_flag.is_set(): {pause_flag.is_set()}")
    logger.info(f"continue_event.is_set(): {continue_event.is_set()}")
    logger.info(f"threading.enumerate() {threading.enumerate()}")
    if action_request.action == "run":
        if not thread or not thread.is_alive():
            thread = Thread(
                target=tixcraft.main,
                args=(
                    continue_event,
                    pause_flag,
                    end_flag,
                    log_queue,
                ),
                daemon=True,
            )
            thread.start()
        return BotStatus(status=ProgramStatusEnum.RUNNING)

    elif action_request.action == "stop":
        if thread and thread.is_alive():
            continue_event.set()
            raise_SystemExit_in_thread(thread)
            logger.info("thread.join()")
            thread.join()
            logger.info("thread.join finished")
            thread = None
        return BotStatus(status=ProgramStatusEnum.STOPPED)

    elif action_request.action == "pause":
        logger.info(f"pause_flag.is_set(): {pause_flag.is_set()}")
        logger.info(f"continue_event.is_set(): {continue_event.is_set()}")
        if pause_flag.is_set():
            return BotStatus(status=ProgramStatusEnum.PAUSED)
        if thread and thread.is_alive():
            logger.info("pause_flag.set()")
            pause_flag.set()
        return BotStatus(status=ProgramStatusEnum.PAUSED)

    elif action_request.action == "continue":
        if thread and thread.is_alive():
            continue_event.set()
            return BotStatus(status=ProgramStatusEnum.RUNNING)
        else:
            return BotStatus(status=ProgramStatusEnum.STOPPED)


@app.get("/api/bot/tixcraft", response_model=BotStatus)
async def get_tixcraft_status():
    return BotStatus(status=await get_thread_status())


@app.get("/api/config", response_model=ConfigSchema)
async def get_config():
    load_config()
    return ConfigSchema(**get_stored_config())


@app.put("/api/config", response_model=ConfigSchema)
async def update_config(config: ConfigSchema):
    for key, value in config:
        if value is not None:
            CONFIG[key] = value
    save_config()
    return ConfigSchema(**get_stored_config())


@app.get("/api/event/tixcraft", response_model=list[SessionInfo])
async def get_tixcraft_event_info(event_url: Optional[str] = Query(None)):
    url = event_url if event_url else CONFIG["TIXCRAFT_EVENT_URL"]
    info = tixcraft.Tixcraft.get_session_info(url)
    for i, session in enumerate(info):
        session["id"] = i
    return info


@app.get("/{full_path:path}")
async def catch_all(request: Request, full_path: str):
    if not full_path:
        full_path = "index.html"
    file_path = os.path.join(FRONTEND_PATH, full_path)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    else:
        return HTMLResponse(content="404 Not Found", status_code=404)
