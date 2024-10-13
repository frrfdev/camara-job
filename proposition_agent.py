import json
import aiohttp
import asyncio
import os
from dotenv import load_dotenv
from database_service import DatabaseService
import requests

load_dotenv(override=True)

OLLAMA_URL = os.getenv('OLLAMA_URL')
BASE_CAMARA_URL = os.getenv('BASE_CAMARA_URL')

class PropositionAgent:
    async def resume_proposition(self, token, file_text):
        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json'
        }
        
        payload = {
            "model": "llama3.2:latest",
            "prompt": f"Leia o arquivo e retorne um resumo conciso e completo que até uma criança de 10 anos consegue entender. \n\n {file_text}",
            "stream": False
        }
        
        json_payload = json.dumps(payload)
        
        async with aiohttp.ClientSession() as session:
            try:   	
                async with session.post(OLLAMA_URL, headers=headers, data=json_payload) as response:
                    response_text = await response.text()

                    response.raise_for_status()
                    return response_text
            except aiohttp.ClientResponseError as http_err:
                print(f"HTTP error occurred: {http_err}")
                print("Response Text:", response_text)
            except aiohttp.ClientError as req_err:
                print(f"Request error occurred: {req_err}")
            except ValueError as json_err:
                print(f"JSON decode error: {json_err}")
                print("Response Text:", response_text)
        return None
    
    def get_proposition_number(self, url):
        return url.split('=')[-1]
    
    async def get_last_propositions(self):
        url = f"{BASE_CAMARA_URL}/api/v2/proposicoes?ordem=DESC&ordenarPor=id&itens=20"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
                return data['dados']
    
    async def get_proposition_details(self, proposition):
        url = f"{BASE_CAMARA_URL}/api/v2/proposicoes/{proposition['id']}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}) as response:
                data = await response.json()
                return data['dados']
    
    async def get_propositions_documents(self, propositions):
        documents = []        
        database_service = DatabaseService()
        
        for proposition in propositions:
            # Convert the id to a string if necessary
            proposition_id = str(proposition['id'])
            
            # Check if this is a synchronous or asynchronous method
            if asyncio.iscoroutinefunction(database_service.get_resume_by_proposition_number):
                resume = await database_service.get_resume_by_proposition_number(proposition_id)
            else:
                resume = database_service.get_resume_by_proposition_number(proposition_id)
            
            if resume:
                continue
            
            details = await self.get_proposition_details(proposition)
            file_content = await self.download_proposition(details['urlInteiroTeor'])
            documents.append({
                'file': file_content,
                'id': proposition_id,
                'url': details['urlInteiroTeor']
            })
        
        return documents
    
    async def download_proposition(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers={'User-Agent': 'Mozilla/5.0'}) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    print(f"Failed to download file. Status code: {response.status}")
                    print(await response.text())
                    return None
