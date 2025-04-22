import asyncio
import threading


def start_thread_async_task(coroutine) -> threading.Thread:
    thread = threading.Thread(target=lambda: asyncio.run(coroutine))
    thread.start()
    return thread