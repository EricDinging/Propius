import asyncio

async def my_coroutine():
    try:
        while True:
            await asyncio.sleep(1)
            print("Working...")
    except asyncio.CancelledError:
        print("Coroutine was cancelled.")

async def main():
    task = asyncio.create_task(my_coroutine())
    
    # Let the coroutine run for a while
    await asyncio.sleep(5)
    
    # Explicitly cancel the task
    task.cancel()

    # Wait for the task to finish
    await task

asyncio.run(main())