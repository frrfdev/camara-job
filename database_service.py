import os
from dotenv import load_dotenv
from pymongo import MongoClient
from bson import ObjectId
from pymongo.errors import ConnectionFailure

# Load environment variables
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
            
            # Create a MongoDB client with increased timeouts
            self.client = MongoClient(mongodb_uri, 
                                      serverSelectionTimeoutMS=30000,
                                      connectTimeoutMS=30000,
                                      socketTimeoutMS=30000)
            
            # Check if the connection is successful by calling server_info
            self.client.server_info()  # This will raise an exception if connection fails
            
            # Connect to the database (let's call it 'resume_db')
            self.db = self.client['resume_db']
            
            print("Connected to MongoDB successfully!")
        except ConnectionFailure as e:
            print(f"Error connecting to MongoDB: {e}")

    def store_resume(self, resume_data):
        try:
            # Create a collection called 'resumes' if it doesn't exist
            resumes_collection = self.db['resumes']
            
            # Insert the resume data into the collection
            result = resumes_collection.insert_one(resume_data)
            
            # Return the inserted document's ID
            return str(result.inserted_id)
        except Exception as e:
            print(f"Error storing resume: {e}")
            return None

    def get_resume_by_proposition_number(self, proposition_number):
        try:
            resumes_collection = self.db['resumes']
            resume = resumes_collection.find_one({'proposition_number': proposition_number})
            if resume is None:
                print(f"No resume found for proposition number: {proposition_number}")
                return None
            return resume
        except Exception as e:
            print(f"Error retrieving resume: {e}")
            return None

    def close_connection(self):
        if self.client:
            self.client.close()
            print("MongoDB connection closed.")
