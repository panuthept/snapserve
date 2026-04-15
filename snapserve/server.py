import os
import uuid
import time
import json
import atexit
import uvicorn
import asyncio
import threading
import contextlib
from typing import Any
from snapserve.dataclasses import Attribute
from concurrent.futures import ThreadPoolExecutor
from fastapi import Request, FastAPI, HTTPException
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
        cachable: bool = False,
        cache_size: int = 1024,
    ):
        self.attributes = attributes
        self.host = host
        self.port = port

        self.app = create_app(
            attributes=self.attributes,
            workers=workers,
            max_concurrency=max_concurrency,
            timeout=timeout,
            cachable=cachable,
            cache_size=cache_size,
        )

    def run(self):
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

        print("🌐 SnapServe is live:")
        for attr_name, attribute in self.attributes.items():
            if attribute.type == "function" or attribute.type == "class":
                print(f"({attribute.type}) {attr_name}{attribute.signature}")
            else:
                print(f"({attribute.type}) {attr_name}: {attribute.signature}")
        
        print()
        print("🛑 Press Ctrl+C to stop")
        # --------------------------------------------------------------------------------------
        # Shutdown handling
        # --------------------------------------------------------------------------------------
        def shutdown():
            if server.should_exit:
                return
            server.should_exit = True
            thread.join()
            print("✅ Shutdown complete")
        atexit.register(shutdown)

        # while thread.is_alive():
        #     thread.join(timeout=1)
        thread.join()

def create_app(
    attributes: dict[str, Attribute],
    workers: int = None,
    max_concurrency: int = None,
    timeout: int = None,
    cachable: bool = False,
    cache_size: int = 1024,
):
    app = FastAPI()
    thread_executor = ThreadPoolExecutor(max_workers=workers or (2 * os.cpu_count() + 1))
    semaphore = asyncio.Semaphore(max_concurrency) if max_concurrency else contextlib.nullcontext()
    cache_manager = CacheManager(max_size=cache_size) if cachable else None
    # ------------------------------------------------------------------------------------------
    # Attribute handlers
    # ------------------------------------------------------------------------------------------
    def execute_function(attribute: Attribute, payload: dict) -> Any:
        args = payload.get("args", [])
        kwargs = payload.get("kwargs", {})
        # Run function
        return attribute.attr(*args, **kwargs)

    def execute_class(attribute: Attribute, payload: dict) -> Any:
        args = payload.get("args", [])
        kwargs = payload.get("kwargs", {})
        # Instantiate class
        obj = attribute.attr(*args, **kwargs)
        obj_id = uuid.uuid4().hex
        # Create new attribute for the object instance
        attributes[obj_id] = Attribute(obj)
        return obj_id
    
    def execute_object(attribute: Attribute, payload: dict) -> Any:
        args = payload.get("args", [])
        kwargs = payload.get("kwargs", {})
        method_or_attribute_name = payload["method_or_attribute_name"]
        if method_or_attribute_name in attribute.methods:
            method = getattr(attribute.attr, method_or_attribute_name)
            return method(*args, **kwargs)
        elif method_or_attribute_name in attribute.attributes:
            attribute_value = getattr(attribute.attr, method_or_attribute_name)
            return attribute_value
        else:
            raise HTTPException(status_code=400, detail=f"Object does not have a method or attribute named '{method_or_attribute_name}'.")
    
    def execute_attribute(attr_name: str, payload: dict) -> Any:
        if payload.get("id"):
            obj_id = payload["id"]
            if obj_id not in attributes:
                raise HTTPException(status_code=400, detail=f"Object with id '{obj_id}' not found.")
            attribute: Attribute = attributes[obj_id]
        else:
            attribute: Attribute = attributes[attr_name]

        if attribute.type == "function":
            result = execute_function(attribute, payload)
        elif attribute.type == "class":
            result = execute_class(attribute, payload)
        else:
            result = execute_object(attribute, payload)
        
        # Update cache if enabled
        if cache_manager:
            with threading.Lock():
                cache_key = f"{attr_name}:{json.dumps(payload, sort_keys=True)}"
                cache_manager.set(cache_key, result)
        return result

    async def handle_request(attr_name: str, payload: dict) -> Any:
        loop = asyncio.get_running_loop()
        # Use cache if enabled
        if cache_manager:
            cache_key = f"{attr_name}:{json.dumps(payload, sort_keys=True)}"
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
        # Execute the attribute in a thread to avoid blocking the event loop
        async with semaphore:
            return await loop.run_in_executor(
                thread_executor, 
                execute_attribute,
                attr_name,
                payload
            )
    # ------------------------------------------------------------------------------------------
    # Endpoints
    # ------------------------------------------------------------------------------------------
    @app.get("/")
    async def root():
        return {
            "status": "online",
            "workload": thread_executor._work_queue.qsize(),
            "message": "Welcome to PyServe!",
            "attributes": {
                attr_name: {
                    "type": attribute.type,
                    "signature": attribute.signature,
                    "methods": attribute.methods,
                    "attributes": attribute.attributes,
                } for attr_name, attribute in attributes.items()
            }
        }
    
    for attr_name in attributes.keys():
        @app.get(f"/{attr_name}")
        async def get_attribute(attr_name=attr_name):
            attribute = attributes[attr_name]
            return {
                "name": attr_name,
                "type": attribute.type,
                "signature": attribute.signature,
                "methods": attribute.methods,
                "attributes": attribute.attributes,
            }

        @app.post(f"/{attr_name}")
        async def call_attribute(request: Request, attr_name=attr_name):
            try:
                payload = await request.json()
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid JSON payload.")
            try:
                coro = handle_request(attr_name, payload)
                if timeout:
                    result = await asyncio.wait_for(coro, timeout=timeout)
                else:
                    result = await coro
                return {"result": result}
            except asyncio.TimeoutError:
                raise HTTPException(status_code=504, detail="Request timed out.")
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
            
        @app.options(f"/{attr_name}")
        async def options_attribute(attr_name=attr_name):
            return {"allowed_methods": ["GET", "POST", "OPTIONS"]}
    # ------------------------------------------------------------------------------------------
    # Shutdown handling
    # ------------------------------------------------------------------------------------------
    def shutdown():
        thread_executor.shutdown(wait=True)
    atexit.register(shutdown)

    return app