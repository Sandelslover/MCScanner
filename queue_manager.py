import asyncio
import json
import logging
from typing import Optional
import redis.asyncio as redis
from config import CONFIG

class TaskQueue:
    def __init__(self, use_redis=False, host='localhost', port=6379, db=0):
        self.use_redis = use_redis
        if self.use_redis:
            self.redis = redis.Redis(host=host, port=port, db=db, decode_responses=True)
            self.queue_name = "mc_scan_tasks"
        else:
            self.local_queue = asyncio.Queue()
            logging.info("Using in-memory task queue (Local Mode).")

    async def enqueue_batch(self, targets: list[dict]):
        if not targets:
            return
        
        if self.use_redis:
            async with self.redis.pipeline() as pipe:
                for target in targets:
                    target_json = json.dumps(target)
                    await pipe.lpush(self.queue_name, target_json)
                await pipe.execute()
        else:
            for target in targets:
                await self.local_queue.put(target)
                
        logging.info(f"Enqueued {len(targets)} tasks.")

    async def dequeue(self) -> Optional[dict]:
        if self.use_redis:
            target_json = await self.redis.rpop(self.queue_name)
            if target_json:
                return json.loads(target_json)
        else:
            try:
                # Use non-blocking get or short timeout for local queue
                return await asyncio.wait_for(self.local_queue.get(), timeout=0.1)
            except (asyncio.TimeoutError, asyncio.QueueEmpty):
                return None
        return None

    async def get_queue_size(self):
        if self.use_redis:
            return await self.redis.llen(self.queue_name)
        return self.local_queue.qsize()
