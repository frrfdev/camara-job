from datetime import datetime
import schedule
import time

def hello_world():
    print("hello world")

# Get current time
now = datetime.now()

# Schedule the job every day at 21:10
schedule.every().day.at("21:10").do(hello_world)

# If the current time is past 21:10, run the job immediately
if now.hour >= 21 and now.minute >= 10:
    hello_world()

print('jobs started')

while True:
    schedule.run_pending()
    time.sleep(1)  # wait one second
