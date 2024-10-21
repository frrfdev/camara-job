import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from pymongo.errors import ConnectionFailure

load_dotenv()

class DatabaseService:
    def __init__(self):
        self.client = None
        self.db = None
        self.connect()

    def connect(self):
        try:
            # Get the MongoDB URI from the environment variables
            mongodb_uri = os.getenv('DB_URL')
            print(f'MongoDB URI: {mongodb_uri}')
            
            # Create an AsyncIOMotorClient
            self.client = AsyncIOMotorClient(mongodb_uri)
            
            # Connect to the database (let's call it 'resume_db')
            self.db = self.client['resume_db']
            
            print("Connected to MongoDB successfully!")
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")

    async def store_resume(self, resume_data):
        try:
            # Create a collection called 'resumes' if it doesn't exist
            resumes_collection = self.db['resumes']
            
            # Insert the resume data into the collection
            result = await resumes_collection.insert_one(resume_data)
            
            # Return the inserted document's ID
            return str(result.inserted_id)
        except Exception as e:
            print(f"Error storing resume: {e}")
            return None

    async def get_resume_by_proposition_number(self, proposition_number):
        try:
            resumes_collection = self.db['resumes']
            resume = await resumes_collection.find_one({'proposition_number': proposition_number})
            return resume
        except Exception as e:
            print(f"Error retrieving resume: {e}")
            return None

    async def store_proposition_in_queue(self, propositionNumber):
        try:
            queue_collection = self.db['queue']
            await queue_collection.insert_one({'proposition_number': propositionNumber, 'status': 'pending'})
        except Exception as e:
            print(f"Error storing proposition in queue: {e}")
            return None
          
    async def get_proposition_from_queue(self, proposition_number):
        try:
            queue_collection = self.db['queue']
            proposition = await queue_collection.find_one({'proposition_number': proposition_number})
            return proposition
        except Exception as e:
            print(f"Error getting proposition from queue: {e}")
            return None
          
    async def get_all_propositions_from_queue(self):
        try:
            queue_collection = self.db['queue']
            propositions = await queue_collection.find().to_list(length=None)
            return propositions
        except Exception as e:
            print(f"Error getting all propositions from queue: {e}")
            return None
          
    async def delete_proposition_from_queue(self, proposition_number):
        try:
            queue_collection = self.db['queue']
            await queue_collection.delete_one({'proposition_number': proposition_number})
        except Exception as e:
            print(f"Error deleting proposition from queue: {e}")

  
    async def update_proposition_status(self, proposition_number, status):
        try:
            queue_collection = self.db['queue']
            await queue_collection.update_one({'proposition_number': proposition_number}, {'$set': {'status': status}})
        except Exception as e:
            print(f"Error updating proposition status: {e}")

    def close_connection(self):
        if self.client:
            self.client.close()
            print("MongoDB connection closed.")
