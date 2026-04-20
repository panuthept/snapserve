import os
import uuid
import time
import json
import atexit
import logging
import uvicorn
import asyncio
import threading
import contextlib
from typing import Any
from concurrent.futures import ThreadPoolExecutor
from snapserve.utils.inspect import get_attr_type
from fastapi import Request, FastAPI, HTTPException
from snapserve.dataclasses import Attribute, AutoAttribute
from snapserve.utils.connections import wait_for_connection


class CacheManager:
    def __init__(self, max_size: int = 1024):
        self.max_size = max_size
        self.cache: dict[str, Any] = {}
        self.access_times: dict[str, float] = {}

    def get(self, key: str) -> Any:
        if key in self.cache:
            self.access_times[key] = time.time()
            return self.cache[key]
        else:
            return None

    def set(self, key: str, value: Any) -> None:
        if len(self.cache) >= self.max_size:
            # Evict least recently used item
            oldest_key = min(self.access_times, key=lambda k: self.access_times[k])
            del self.cache[oldest_key]
            del self.access_times[oldest_key]
        self.cache[key] = value
        self.access_times[key] = time.time()

class Server:
    def __init__(
        self, 
        attributes: dict[str, Attribute],
        host: str = "localhost",
        port: int = 8000,
        workers: int = None,
        max_concurrency: int = None,
        timeout: int = None,
        allow_cache: bool = False,
        cache_size: int = 1024,
    ):
        logging.info(f"Configuring server with host={host}, port={port}, workers={workers}, max_concurrency={max_concurrency}, timeout={timeout}, allow_cache={allow_cache}, cache_size={cache_size}")

        self.attributes = attributes
        self.host = host
        self.port = port

        self.app = create_app(
            attributes=self.attributes,
            workers=workers,
            max_concurrency=max_concurrency,
            timeout=timeout,
            allow_cache=allow_cache,
            cache_size=cache_size,
        )

    def run(self):
        logging.info("Starting server...")

        config = uvicorn.Config(
            self.app,
            host=self.host,
            port=self.port,
            log_level="warning",
        )
        server = uvicorn.Server(config)
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()

        if not wait_for_connection(f"http://{self.host}:{self.port}"):
            raise RuntimeError(f"❌ Failed to start server at port {self.port}")

        logging.info(f"Server is running at: http://{self.host}:{self.port}")
        for attr_name, attribute in self.attributes.items():
            if attribute.type == "function" or attribute.type == "class":
                logging.info(f"({attribute.type}) {attr_name}{attribute.signature}")
            else:
                logging.info(f"({attribute.type}) {attr_name}: {attribute.signature}")
        # --------------------------------------------------------------------------------------
        # Shutdown handling
        # --------------------------------------------------------------------------------------
        def shutdown():
            if server.should_exit:
                return
            server.should_exit = True
            thread.join()
            logging.info("Server shutdown complete")
        atexit.register(shutdown)

        thread.join()

def create_app(
    attributes: dict[str, Attribute],
    workers: int = None,
    max_concurrency: int = None,
    timeout: int = None,
    allow_cache: bool = False,
    cache_size: int = 1024,
):
    app = FastAPI()
    thread_executor = ThreadPoolExecutor(max_workers=workers or (2 * os.cpu_count() + 1))
    semaphore = asyncio.Semaphore(max_concurrency) if max_concurrency else contextlib.nullcontext()
    cache_manager = CacheManager(max_size=cache_size) if allow_cache else None
    
    # ------------------------------------------------------------------------------------------
    # Attribute handlers
    # ------------------------------------------------------------------------------------------
    def execute_attribute(payload: dict) -> Any:
        args = payload.get("args", [])
        kwargs = payload.get("kwargs", {})
        attr_name = payload.get("attr_name", attr_name)

        output = attributes[attr_name].call(*args, **kwargs)
        output_type = get_attr_type(output)
        if output_type == "variable":
            result = {"value": output}
        else:
            new_attr_name = f"{attr_name}_{uuid.uuid4().hex[:8]}"
            attributes[new_attr_name] = AutoAttribute.from_attr(output)
            result = {"new_attr_name": new_attr_name}

        # Update cache if enabled
        if cache_manager:
            with threading.Lock():
                cache_key = json.dumps(payload, sort_keys=True)
                cache_manager.set(cache_key, result)
        return result

    async def handle_request(payload: dict) -> Any:
        loop = asyncio.get_running_loop()
        # Execute the attribute in a thread to avoid blocking the event loop
        async with semaphore:
            return await loop.run_in_executor(
                thread_executor, 
                execute_attribute,
                payload
            )
        
    # ------------------------------------------------------------------------------------------
    # Endpoints
    # ------------------------------------------------------------------------------------------
    @app.get("/")
    async def root():
        request_id = uuid.uuid4().hex
        logging.info(f"Request {request_id}: Received GET request at '/' endpoint")
        return {
            "status": "online",
            "workload": thread_executor._work_queue.qsize(),
            "attributes": list(attributes.keys()),
        }
    
    @app.get("/attribute")
    async def get_attribute(request: Request):
        request_id = uuid.uuid4().hex
        try:
            payload = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON payload.")
        logging.info(f"Request {request_id}: Received GET request at '/attribute' endpoint with payload: {payload}")
        
        if "attr_name" not in payload:
            raise HTTPException(status_code=400, detail="Missing 'attr_name' field in payload.")
        
        attr_name = payload.get("attr_name")
        if attr_name not in attributes:
            raise HTTPException(status_code=400, detail=f"Attribute '{attr_name}' not found.")
        
        return attributes[attr_name].to_dict()
    
    @app.post("/attribute")
    async def post_attribute(request: Request):
        request_id = uuid.uuid4().hex
        try:
            payload = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON payload.")
        logging.info(f"Request {request_id}: Received POST request at '/attribute' endpoint with payload: {payload}")

        start_time = time.monotonic()

        # Use cache if enabled
        if cache_manager:
            cache_key = json.dumps(payload, sort_keys=True)
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                logging.info(f"Request {request_id}: Completed POST request for '/attribute' in {time.monotonic() - start_time:.2f} seconds (Cache Hit)")
                return cached_result
        
        # Execute the attribute and return the result
        try:
            coro = handle_request(payload)
            if timeout:
                result = await asyncio.wait_for(coro, timeout=timeout)
            else:
                result = await coro
            logging.info(f"Request {request_id}: Completed POST request for '/attribute' in {time.monotonic() - start_time:.2f} seconds")
            return result
        except asyncio.TimeoutError:
            logging.error(f"Request {request_id}: POST Request for '/attribute' timed out after {timeout} seconds")
            raise HTTPException(status_code=504, detail="Request timed out.")
        except HTTPException:
            logging.error(f"Request {request_id}: HTTPException occurred while handling POST request for '/attribute'")
            raise
        except Exception as e:
            logging.error(f"Request {request_id}: Error occurred while handling POST request for '/attribute': {e}")
            raise HTTPException(status_code=500, detail=str(e))
        
    # ------------------------------------------------------------------------------------------
    # Shutdown handling
    # ------------------------------------------------------------------------------------------
    def shutdown():
        thread_executor.shutdown(wait=True)
    atexit.register(shutdown)

    return app