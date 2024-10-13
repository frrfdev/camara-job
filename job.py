import asyncio
from datetime import datetime
import schedule
from resume_propositions import start_resume_process
import requests

class JobManager:
    def __init__(self):
        self.count = 1
        self.loop = asyncio.get_event_loop()

    async def resume_propositions_job(self):
        print(f"Running job #{self.count}")
        await start_resume_process()
        self.count += 1

    def run_job(self):
        self.loop.run_until_complete(self.resume_propositions_job())

now = datetime.now()

# check if has internet connection
def has_internet_connection():
    try:
        requests.get('https://www.google.com', timeout=5)
        return True
    except requests.ConnectionError:
        return False
      
if not has_internet_connection():
    print("No internet connection. Exiting...")
    exit()

job_manager = JobManager()
schedule.every(20).seconds.do(job_manager.run_job)
print('Jobs started. Running every 20 minutes.')

# Run the job immediately
job_manager.run_job()

try:
    while True:
        schedule.run_pending()
        job_manager.loop.run_until_complete(asyncio.sleep(1))
except KeyboardInterrupt:
    print("Shutting down...")
finally:
    job_manager.loop.close()
