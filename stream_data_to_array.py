import json

def parse_stream_to_json_array(stream_data):
    json_array = []
    full_response = ""
    
    for line in stream_data.split('\n'):
        if line.strip():
            try:
                json_obj = json.loads(line)
                if 'response' in json_obj:
                    full_response += json_obj['response']
                    json_array.append({
                        'model': json_obj.get('model', ''),
                        'created_at': json_obj.get('created_at', ''),
                        'response': json_obj['response'],
                        'done': json_obj.get('done', False)
                    })
            except json.JSONDecodeError:
                print(f"Error parsing line: {line}")
    
    # Add a final object with the complete response
    json_array.append({
        'model': json_array[-1]['model'] if json_array else '',
        'created_at': json_array[-1]['created_at'] if json_array else '',
        'response': full_response,
        'done': True
    })
    
    return json_array
