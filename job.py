import asyncio
from datetime import datetime
import schedule
from resume_propositions import start_resume_process
import requests

class JobManager:
    def __init__(self):
        self.count = 1

    async def resume_propositions_job(self):
        print(f"Running job #{self.count}")
        await start_resume_process()
        self.count += 1

async def run_scheduler():
    job_manager = JobManager()
    schedule.every(30).minutes.do(lambda: asyncio.create_task(job_manager.resume_propositions_job()))
    
    while True:
        schedule.run_pending()
        await asyncio.sleep(1)

async def main():
    # check if has internet connection
    def has_internet_connection():
        try:
            requests.get('https://www.google.com', timeout=5)
            return True
        except requests.ConnectionError:
            return False

    has_connection = has_internet_connection()
    print(f'Has connection: {has_connection}')

    if not has_connection:
        print("No internet connection. Exiting...")
        return

    print('Jobs started. Running every 30 minutes.')

    # Run the scheduler
    await run_scheduler()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down...")
