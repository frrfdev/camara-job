from dotenv import load_dotenv
import os
from pdf_converter import PDFConverter
from image_extractor import ImageExtractor
from proposition_agent import PropositionAgent
from stream_data_to_array import parse_stream_to_json_array
from database_service import DatabaseService
import asyncio
import time
from datetime import datetime, timezone

load_dotenv(override=True)

TOKEN = os.getenv('TOKEN')

# Global variables
propositions_to_process = asyncio.Queue()
_is_processing = False
_background_task = None

def is_processing():
    return _is_processing

async def resume_with_timer(proposition_agent, token, full_text, proposition_id):
    start_time = time.time()
    
    async def timer():
        elapsed_time = 0
        while True:
            print(f'Resuming proposition {proposition_id} - Elapsed time: {elapsed_time} seconds')
            await asyncio.sleep(1)
            elapsed_time += 1

    timer_task = asyncio.create_task(timer())
    resume = await proposition_agent.resume_proposition(token, full_text)
    timer_task.cancel()

    end_time = time.time()
    duration = end_time - start_time
    print(f'Resuming proposition {proposition_id} completed in {duration:.2f} seconds')
    return resume

async def process_resume(proposition_agent, proposition_file):
    try:
        # transform pdf to images
        pdf_converter = PDFConverter()
        print(f'Converting PDF to images for proposition {proposition_file["id"]}')
        images = pdf_converter.pdf_to_images(proposition_file['file'])
        
        # extract text from images
        full_text = ''
        for index, image in enumerate(images):
            image_extraction = ImageExtractor()
            print(f'Extracting text from image {index} for proposition {proposition_file["id"]}')
            full_text += image_extraction.extract_text_from_image(image)
        
        # resume proposition text
        print(f'Starting to resume proposition {proposition_file["id"]}')
        resume = await resume_with_timer(proposition_agent, TOKEN, full_text, proposition_file["id"])
        
        if resume:
            print(f'Parsing resume for proposition {proposition_file["id"]}')
            resume_json = parse_stream_to_json_array(resume)
            full_resume = ''
            for item in resume_json:
                full_resume += item['response']
            
            # Initialize the database service
            db_service = DatabaseService()
            
            print(f'Storing resume for proposition {proposition_file["id"]}')
            resume_id = await db_service.store_resume({
                "resume": full_resume,
                "url": proposition_file['url'],
                "proposition_number": proposition_agent.get_proposition_number(proposition_file['id']),
                "created_at": datetime.now(timezone.utc)
            })
            if resume_id:
                print(f"Resume stored successfully with ID: {resume_id}")
            else:
                print("Failed to store resume")
            
            # Don't forget to close the connection when you're done
            db_service.close_connection()
        else:
            print("No file content to upload.")
    except Exception as e:
        print(f"Error processing resume: {e}")

async def process_propositions():
    global _is_processing
    proposition_agent = PropositionAgent()
    while True:
        proposition_file = await propositions_to_process.get()
        _is_processing = True
        await process_resume(proposition_agent, proposition_file)
        propositions_to_process.task_done()
        _is_processing = False

async def add_propositions_to_process():
    proposition_agent = PropositionAgent()
    propositions = await proposition_agent.get_last_propositions()
    propositions_files = await proposition_agent.get_propositions_documents(propositions)
    print(f'Found {len(propositions_files)} propositions to resume')
    
    added_count = 0
    skipped_count = 0
    
    database_service = DatabaseService()
    
    for proposition_file in propositions_files:
        proposition_number = proposition_agent.get_proposition_number(proposition_file['id'])
        resume = await database_service.get_resume_by_proposition_number(proposition_number)
        
        if resume is not None:
            print(f"Resume already exists for proposition {proposition_number}")
            skipped_count += 1
        else:
            await propositions_to_process.put(proposition_file)
            added_count += 1
    
    database_service.close_connection()
    print(f'Added {added_count} propositions to process')
    print(f'Skipped {skipped_count} propositions already in the database')

async def start_resume_process():
    global _background_task
    await add_propositions_to_process()
    if not is_processing() and (_background_task is None or _background_task.done()):
        _background_task = asyncio.create_task(process_propositions())
