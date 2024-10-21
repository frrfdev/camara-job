import json
import aiohttp
import asyncio
import os
from dotenv import load_dotenv
from database_service import DatabaseService
import requests
import re
import xmltodict

load_dotenv(override=True)

OLLAMA_URL = os.getenv('OLLAMA_URL')
BASE_CAMARA_URL = os.getenv('BASE_CAMARA_URL')

class PropositionAgent:
    async def resume_proposition(self, token, file_text):
        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json'
        }
        
        gbnf_grammar = """
        root ::= <json>
       <json> ::= "[" <entry> { "," <entry> } "]"

<entry> ::= "{" 
              "\"title\"" ":" <valid_title> "," 
              "\"description\"" ":" <description> 
            "}"

<valid_title> ::= "\"Qual é o nome do projeto?\"" 
                | "\"Quem criou o projeto?\"" 
                | "\"O que esse projeto quer mudar?\"" 
                | "\"Por que isso é importante?\"" 
                | "\"Quem vai decidir se esse projeto é bom?\"" 
                | "\"O que essas comissões disseram?\"" 
                | "\"O que acontece se esse projeto virar lei?\"" 
                | "\"Quando essa lei começa a valer?\"" 
                | "\"Por que essa lei é legal?\""

<description> ::= "\"" <text> "\"" 
                | "\"Informação não disponível\""

<text> ::= { <char> }

<char> ::= any printable UTF-8 character except \" or \\
        """
        
        payload = {
            "model": "llama3.2:latest",
            "prompt": f"""

Conteúdo do projeto:

{file_text}

Analise o conteúdo do projeto fornecido e crie um resumo estruturado no formato JSON especificado abaixo. Responda APENAS com o array JSON, sem texto adicional.

[
  {{"title": "Qual é o nome do projeto?", "description": "Insira o nome completo do projeto aqui"}},
  {{"title": "Quem criou o projeto?", "description": "Liste o(s) autor(es) do projeto"}},
  {{"title": "O que esse projeto quer mudar?", "description": "Resuma o objetivo principal do projeto em uma frase"}},
  {{"title": "Por que isso é importante?", "description": "Explique brevemente a relevância do projeto"}},
  {{"title": "Quem vai decidir se esse projeto é bom?", "description": "Mencione as comissões ou órgãos responsáveis pela avaliação"}},
  {{"title": "O que essas comissões disseram?", "description": "Resuma as opiniões das comissões, se disponíveis"}},
  {{"title": "O que acontece se esse projeto virar lei?", "description": "Descreva as principais mudanças que ocorrerão"}},
  {{"title": "Quando essa lei começa a valer?", "description": "Indique a data ou condição de início da lei"}},
  {{"title": "Por que essa lei é legal?", "description": "Explique o principal benefício do projeto para a sociedade"}}
]

Se alguma informação não estiver disponível no texto, use "Informação não disponível" como descrição.

""",
            "stream": False,
        }
        
        json_payload = json.dumps(payload)
        
        async with aiohttp.ClientSession() as session:
            try:   	
                async with session.post(OLLAMA_URL, headers=headers, data=json_payload) as response:
                    response_json = await response.json()
                    response.raise_for_status()
                    if 'response' in response_json:
                        try:
                            # First, try to parse the response as is
                            parsed_response = json.loads(response_json['response'])
                        except json.JSONDecodeError:
                            # If that fails, clean the response and try again
                            cleaned_response = self.clean_json_string(response_json['response'])
                            try:
                                parsed_response = json.loads(cleaned_response)
                            except json.JSONDecodeError as e:
                                print(f"Error decoding JSON: {e}")
                                print(f"Raw response: {response_json['response']}")
                                print(f"Cleaned response: {cleaned_response}")
                                return None
                        
                        # Ensure all entries have the correct structure
                        structured_response = []
                        for item in parsed_response:
                            if isinstance(item, dict) and 'title' in item and 'description' in item:
                                structured_response.append({
                                    'title': item['title'],
                                    'description': item['description'] if item['description'] else "Informação não disponível"
                                })
                        
                        return structured_response
                    return None
            except aiohttp.ClientResponseError as http_err:
                print(f"HTTP error occurred: {http_err}")
            except aiohttp.ClientError as req_err:
                print(f"Request error occurred: {req_err}")
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
        return None
    
    def get_proposition_number(self, url):
        return url.split('=')[-1]
    
    async def get_last_propositions(self):
        url = f"{BASE_CAMARA_URL}/api/v2/proposicoes?pagina=1&ordem=DESC&ordenarPor=id&itens=20"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
                return data['dados']
    
    async def get_proposition_details(self, proposition_id):
        url = f"{BASE_CAMARA_URL}/api/v2/proposicoes/{proposition_id}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'application/json;charset=UTF-8'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                content_type = response.headers.get('Content-Type', '')
                text = await response.text()
                
                print(f"Content-Type: {content_type}")
                print(f"Response text: {text[:200]}...")  # Print first 200 characters
                
                try:
                  if content_type.startswith('application/json'):
                    data = json.loads(text)
                  else:
                    data = xmltodict.parse(text)
                except json.JSONDecodeError as e:
                        print(f"Failed to parse response: {e}")
                        raise ValueError(f"Unable to parse response as JSON or XML. Content-Type: {content_type}")
                      
                if 'dados' in data:
                    return data['dados']
                elif 'proposicao' in data:
                    return data['proposicao']
                else:
                    raise ValueError(f"Unexpected data structure: {data.keys()}")
    
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
            
            details = await self.get_proposition_details(proposition_id)
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

    def clean_json_string(self, json_string):
        # Remove newlines and extra whitespace
        json_string = ' '.join(json_string.split())
        
        # Decode Unicode escape sequences
        json_string = json.loads(f'"{json_string}"')
        
        # Replace Portuguese characters
        replacements = {
            'ç': 'c', 'ã': 'a', 'õ': 'o', 'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
            'â': 'a', 'ê': 'e', 'î': 'i', 'ô': 'o', 'û': 'u', 'à': 'a', 'è': 'e', 'ì': 'i', 'ò': 'o', 'ù': 'u',
            'Ç': 'C', 'Ã': 'A', 'Õ': 'O', 'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
            'Â': 'A', 'Ê': 'E', 'Î': 'I', 'Ô': 'O', 'Û': 'U', 'À': 'A', 'È': 'E', 'Ì': 'I', 'Ò': 'O', 'Ù': 'U'
        }
        for char, replacement in replacements.items():
            json_string = json_string.replace(char, replacement)
        
        # Remove any remaining non-ASCII characters
        json_string = ''.join(char for char in json_string if ord(char) < 128)
        
        return json_string
