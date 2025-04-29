import json
import os
from datetime import datetime
from typing import List, Dict, Any
import aiofiles

class JSONStorage:
    def __init__(self, storage_dir: str = "message_storage"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)

    async def save_message(self, message: Dict[str, Any]) -> None:
        timestamp = datetime.now().strftime("%Y%m%d")
        filename = f"{self.storage_dir}/messages_{timestamp}.json"
        
        try:
            async with aiofiles.open(filename, 'a') as f:
                await f.write(json.dumps(message) + "\n")
        except Exception as e:
            print(f"Error saving message: {e}")

    async def get_messages(self, group_id: str = None, user_id: str = None, 
                          start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        messages = []
        files = os.listdir(self.storage_dir)
        if start_date and end_date:
            files = [f for f in files if start_date <= f.split('_')[1].split('.')[0] <= end_date]
        
        for file in files:
            try:
                async with aiofiles.open(os.path.join(self.storage_dir, file), 'r') as f:
                    async for line in f:
                        msg = json.loads(line)
                        if group_id and msg.get('group_id') != group_id:
                            continue
                        if user_id and msg.get('user_id') != user_id:
                            continue
                        messages.append(msg)
            except Exception as e:
                print(f"Error reading messages from {file}: {e}")
        
        return messages

    async def delete_messages(self, group_id: str = None, user_id: str = None) -> None:
        files = os.listdir(self.storage_dir)
        for file in files:
            try:
                async with aiofiles.open(os.path.join(self.storage_dir, file), 'r') as f:
                    lines = []
                    async for line in f:
                        msg = json.loads(line)
                        if group_id and msg.get('group_id') == group_id:
                            continue
                        if user_id and msg.get('user_id') == user_id:
                            continue
                        lines.append(line)
                
                async with aiofiles.open(os.path.join(self.storage_dir, file), 'w') as f:
                    await f.writelines(lines)
            except Exception as e:
                print(f"Error deleting messages from {file}: {e}")

# Create a global instance
json_storage = JSONStorage() 