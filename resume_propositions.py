from dotenv import load_dotenv
import os
from pdf_converter import PDFConverter
from image_extractor import ImageExtractor
from proposition_agent import PropositionAgent
from stream_data_to_array import parse_stream_to_json_array
from database_service import DatabaseService
import asyncio

load_dotenv(override=True)

TOKEN = os.getenv('TOKEN')

# Create a global queue
resume_queue = asyncio.Queue()

# Set to keep track of propositions in the queue
propositions_in_queue = set()

# Flag to track if workers are running
workers_running = False

async def process_resume(proposition_agent):
    while True:
        proposition_file = await resume_queue.get()
        try:
            # transform pdf to images
            pdf_converter = PDFConverter()
            images = pdf_converter.pdf_to_images(proposition_file['file'])
            
            # extract text from images
            full_text = ''
            for image in images:
                image_extraction = ImageExtractor()
                full_text += image_extraction.extract_text_from_image(image)
            
            # resume proposition text
            resume = await proposition_agent.resume_proposition(TOKEN, full_text)
            
            if resume:
                resume_json = parse_stream_to_json_array(resume)
                full_resume = ''
                for item in resume_json:
                    full_resume += item['response']
                
                # Initialize the database service
                db_service = DatabaseService()
                
                # Store the resume
                resume_id = await db_service.store_resume({
                    "resume": full_resume,
                    "url": proposition_file['url'],
                    "proposition_number": proposition_agent.get_proposition_number(proposition_file['id']),
                })
                if resume_id:
                    print(f"Resume stored successfully with ID: {resume_id}")
                else:
                    print("Failed to store resume")
                
                # Don't forget to close the connection when you're done
                db_service.close_connection()
            else:
                print("No file content to upload.")
            
            # After processing, remove the proposition from the tracking set
            propositions_in_queue.remove(proposition_file['id'])
        except Exception as e:
            print(f"Error processing resume: {e}")
        finally:
            resume_queue.task_done()

async def start_workers(num_workers=5):
    global workers_running
    if not workers_running:
        workers_running = True
        proposition_agent = PropositionAgent()
        workers = [asyncio.create_task(process_resume(proposition_agent)) for _ in range(num_workers)]
        print(f"Started {num_workers} worker(s)")

async def add_propositions_to_queue():
    proposition_agent = PropositionAgent()
    propositions = await proposition_agent.get_last_propositions()
    propositions_files = await proposition_agent.get_propositions_documents(propositions)
    print(f'Found {len(propositions_files)} propositions to resume')
    
    added_count = 0
    skipped_count = 0
    
    for proposition_file in propositions_files:
        if proposition_file['id'] not in propositions_in_queue:
            await resume_queue.put(proposition_file)
            propositions_in_queue.add(proposition_file['id'])
            added_count += 1
        else:
            skipped_count += 1
    
    print(f'Added {added_count} propositions to the queue')
    print(f'Skipped {skipped_count} propositions already in the queue')

async def start_resume_process():
    await start_workers()  # Ensure workers are running
    await add_propositions_to_queue()  # Add new propositions to the queue

# If you want to run this script directly
if __name__ == "__main__":
    asyncio.run(start_resume_process(1))  # Start with count=1 for testing
