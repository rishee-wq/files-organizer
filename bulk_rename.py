import re
from pathlib import Path
from datetime import datetime

class BulkRenamer:
    def __init__(self):
        self.patterns = {
            'sequential': self.sequential_rename,
            'date_prefix': self.date_prefix,
            'clean_name': self.clean_name,
            'camel_case': self.camel_case
        }
        
    def sequential_rename(self, files, prefix='file'):
        for i, file_path in enumerate(files):
            ext = Path(file_path).suffix
            new_name = f"{prefix}_{i:04d}{ext}"
            yield new_name
            
    def date_prefix(self, files, date_format='%Y%m%d'):
        today = datetime.now().strftime(date_format)
        for file_path in files:
            ext = Path(file_path).suffix
            new_name = f"{today}_{Path(file_path).stem}{ext}"
            yield new_name
            
    def clean_name(self, files):
        for file_path in files:
            name = re.sub(r'[^a-zA-Z0-9\s-]', '_', Path(file_path).stem)
            ext = Path(file_path).suffix
            yield f"{name}{ext}"
            
    def camel_case(self, files):
        for file_path in files:
            name = ''.join(word.capitalize() for word in Path(file_path).stem.split())
            ext = Path(file_path).suffix
            yield f"{name}{ext}"
