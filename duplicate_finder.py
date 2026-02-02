import hashlib
import os
from pathlib import Path
from PIL import Image
import imagehash

class DuplicateFinder:
    def __init__(self):
        self.hashes = {}
        
    def hash_file(self, file_path, block_size=65536):
        """MD5 hash for exact duplicates"""
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            buf = f.read(block_size)
            while buf:
                hasher.update(buf)
                buf = f.read(block_size)
        return hasher.hexdigest()
        
    def perceptual_hash(self, image_path):
        """Perceptual hash for similar images"""
        try:
            hash_val = imagehash.average_hash(Image.open(image_path))
            return str(hash_val)
        except:
            return None
            
    def find_duplicates(self, folder_path):
        duplicates = []
        
        for file_path in Path(folder_path).rglob('*'):
            if file_path.is_file():
                file_hash = self.hash_file(str(file_path))
                
                if file_hash in self.hashes:
                    self.hashes[file_hash].append(str(file_path))
                else:
                    self.hashes[file_hash] = [str(file_path)]
        
        # Find groups with more than 1 file
        for hash_val, files in self.hashes.items():
            if len(files) > 1:
                duplicates.append({
                    'hash': hash_val,
                    'files': files,
                    'size': os.path.getsize(files[0])
                })
                
        return sorted(duplicates, key=lambda x: x['size'], reverse=True)