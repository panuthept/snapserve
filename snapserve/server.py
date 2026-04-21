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
from fastapi import Request, FastAPI, HTTPException
from snapserve.utils.connections import wait_for_connection
from snapserve.utils.inspect import get_attr_type, get_attr_info


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
        attributes: dict[str, Any],
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
            logging.info(f"{attr_name}: {get_attr_info(attribute)}")
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
    attributes: dict[str, Any],
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
    def get_nested_attribute(payload: dict) -> Any:
        attr_name = payload["attr_name"]
        attr_path = payload.get("attr_path", [])

        if attr_name not in attributes:
            return {"error": f"Attribute '{attr_name}' not found."}
        attribute = attributes[attr_name]

        for path in attr_path:
            attribute = getattr(attribute.attr, path, None)
            if attribute is None:
                return {"error": f"Attribute '{attr_name}.{'.'.join(attr_path)}' not found."}
            
        return attribute
    
    def get_attribute_info(payload: dict) -> dict:
        attribute = get_nested_attribute(payload)
        if isinstance(attribute, dict) and "error" in attribute:
            return attribute
        return get_attr_info(attribute)

    def call_attribute(payload: dict) -> Any:
        attribute = get_nested_attribute(payload)
        if isinstance(attribute, dict) and "error" in attribute:
            return attribute

        args = payload.get("args", [])
        kwargs = payload.get("kwargs", {})

        output = attribute(*args, **kwargs)

        if get_attr_type(output) == "variable":
            result = {"value": output}
        else:
            attr_name = payload["attr_name"]
            new_attr_name = f"{attr_name}_{uuid.uuid4().hex[:8]}"
            attributes[new_attr_name] = output
            result = {"new_attr_name": new_attr_name}

        # Update cache if enabled
        if cache_manager:
            with threading.Lock():
                cache_key = json.dumps(payload, sort_keys=True)
                cache_manager.set(cache_key, result)
        return result

    async def handle_get_request(payload: dict) -> Any:
        loop = asyncio.get_running_loop()
        # Execute the attribute in a thread to avoid blocking the event loop
        async with semaphore:
            return await loop.run_in_executor(
                thread_executor, 
                get_attribute_info,
                payload
            )
        
    async def handle_post_request(payload: dict) -> Any:
        loop = asyncio.get_running_loop()
        # Execute the attribute in a thread to avoid blocking the event loop
        async with semaphore:
            return await loop.run_in_executor(
                thread_executor, 
                call_attribute,
                payload
            )
        
    # ------------------------------------------------------------------------------------------
    # Endpoints
    # ------------------------------------------------------------------------------------------
    @app.get("/")
    async def root():
        request_id = uuid.uuid4().hex
        logging.info(f"Received GET request {request_id} at '/' endpoint")
        return {
            "status": "online",
            "workload": thread_executor._work_queue.qsize(),
        }
    
    @app.get("/attribute")
    async def get_attribute(request: Request):
        request_id = uuid.uuid4().hex
        try:
            payload = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON payload.")
        logging.info(f"Received GET request {request_id} at '/attribute' endpoint with payload: {payload}")
        
        if "attr_name" not in payload:
            raise HTTPException(status_code=400, detail="Missing 'attr_name' field in payload.")
        
        attr_name = payload["attr_name"]
        if attr_name not in attributes:
            raise HTTPException(status_code=400, detail=f"Attribute '{attr_name}' not found.")
        
        start_time = time.monotonic()

        # Call the attribute and return the result
        try:
            coro = handle_get_request(payload)
            if timeout:
                result = await asyncio.wait_for(coro, timeout=timeout)
            else:
                result = await coro
            logging.info(f"Completed GET request {request_id} for '/attribute' in {time.monotonic() - start_time:.2f} seconds")
            return result
        except asyncio.TimeoutError:
            logging.error(f"GET request {request_id} for '/attribute' timed out after {timeout} seconds")
            raise HTTPException(status_code=504, detail="Request timed out.")
        except HTTPException:
            logging.error(f"sHTTPException occurred while handling GET request {request_id} for '/attribute'")
            raise
        except Exception as e:
            logging.error(f"Error occurred while handling GET request {request_id} for '/attribute': {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/attribute")
    async def post_attribute(request: Request):
        request_id = uuid.uuid4().hex
        try:
            payload = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON payload.")
        logging.info(f"Received POST request {request_id} at '/attribute' endpoint with payload: {payload}")

        if "attr_name" not in payload:
            raise HTTPException(status_code=400, detail="Missing 'attr_name' field in payload.")
        
        attr_name = payload["attr_name"]
        if attr_name not in attributes:
            raise HTTPException(status_code=400, detail=f"Attribute '{attr_name}' not found.")

        start_time = time.monotonic()

        # Use cache if enabled
        if cache_manager:
            cache_key = json.dumps(payload, sort_keys=True)
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                logging.info(f"Completed POST request {request_id} for '/attribute' in {time.monotonic() - start_time:.2f} seconds (Cache Hit)")
                return cached_result
        
        # Call the attribute and return the result
        try:
            coro = handle_post_request(payload)
            if timeout:
                result = await asyncio.wait_for(coro, timeout=timeout)
            else:
                result = await coro
            logging.info(f"Completed POST request {request_id} for '/attribute' in {time.monotonic() - start_time:.2f} seconds")
            return result
        except asyncio.TimeoutError:
            logging.error(f"POST request {request_id} for '/attribute' timed out after {timeout} seconds")
            raise HTTPException(status_code=504, detail="Request timed out.")
        except HTTPException:
            logging.error(f"HTTPException occurred while handling POST request {request_id} for '/attribute'")
            raise
        except Exception as e:
            logging.error(f"Error occurred while handling POST request {request_id} for '/attribute': {e}")
            raise HTTPException(status_code=500, detail=str(e))
        
    # ------------------------------------------------------------------------------------------
    # Shutdown handling
    # ------------------------------------------------------------------------------------------
    def shutdown():
        thread_executor.shutdown(wait=True)
    atexit.register(shutdown)

    return app