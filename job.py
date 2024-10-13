from datetime import datetime
import schedule
import time
import asyncio
from resume_propositions import start_resume_process

class JobManager:
    def __init__(self):
        self.count = 1

    def resume_propositions_job(self):
        print(f"Running job #{self.count}")
        asyncio.run(start_resume_process())
        self.count += 1

now = datetime.now()

job_manager = JobManager()
schedule.every(30).seconds.do(job_manager.resume_propositions_job)
print('Jobs started. Running every 20 minutes.')

# Run the job immediately
job_manager.resume_propositions_job()

while True:
    schedule.run_pending()
    time.sleep(1)  # wait one second
