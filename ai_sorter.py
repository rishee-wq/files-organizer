"""
RishFlow v2.0 - AI Smart File Sorter
Advanced classification using Computer Vision + OCR + Rules
100% Python 3.13 compatible - No ML dependencies
"""

import cv2
import numpy as np
import os
import pytesseract
from PIL import Image, ImageEnhance
from pathlib import Path
from datetime import datetime
import hashlib
import re
from collections import defaultdict

class AISmartSorter:
    def __init__(self):
        # Load OpenCV cascades for face/screenshot detection
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.profile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_profileface.xml')
        
    def classify_file(self, file_path):
        """Main classification entry point - returns folder path"""
        file_path = Path(file_path)
        ext = file_path.suffix.lower()
        
        # Extension-based quick classification
        if ext in self.IMAGE_EXTS:
            return self.classify_image(file_path)
        elif ext in self.DOC_EXTS:
            return self.classify_document(file_path)
        elif ext in self.CODE_EXTS:
            return self.classify_code(file_path)
        elif ext in self.VIDEO_EXTS:
            return 'Videos'
        elif ext in self.AUDIO_EXTS:
            return 'Audio'
        elif ext in self.ARCHIVE_EXTS:
            return 'Archives'
        elif ext in self.EXECUTABLE_EXTS:
            return 'Executables'
        else:
            return self.classify_generic(file_path)
    
    def classify_image(self, image_path):
        """AI-powered image classification"""
        try:
            img = cv2.imread(str(image_path))
            if img is None:
                return 'Images/Others'
                
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # 1. FACE DETECTION → Family Photos
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
            profiles = self.profile_cascade.detectMultiScale(gray, 1.1, 4)
            
            if len(faces) > 0 or len(profiles) > 0:
                return f'Images/Family/{image_path.stem[:20]}'  # Truncate long names
                
            # 2. SCREENSHOT DETECTION (high contrast + edges)
            edges = cv2.Canny(gray, 100, 200)
            edge_density = np.sum(edges > 0) / (gray.shape[0] * gray.shape[1])
            
            if edge_density > 0.08:
                return 'Images/Screenshots'
            
            # 3. RECEIPT/INVOICE DETECTION (text-heavy)
            text_score = self.estimate_text_density(gray)
            if text_score > 0.15:
                return f'Images/Receipts/{datetime.now().strftime("%Y/%m/%d")}_{image_path.stem}'
            
            # 4. MEMES (colorful + text overlay)
            if self.is_colorful(img) and text_score > 0.05:
                return 'Images/Memes'
                
            return 'Images/Photos'
            
        except Exception:
            return 'Images/Others'
    
    def classify_document(self, doc_path):
        """OCR-powered document classification"""
        try:
            # Quick OCR for receipts/invoices
            text = pytesseract.image_to_string(
                Image.open(doc_path), 
                config='--psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz .,-/()'
            )
            
            text_lower = text.lower()
            
            # Keywords → Category
            if any(word in text_lower for word in ['invoice', 'receipt', 'bill', 'payment']):
                date_str = self.extract_date(text)
                return f'Documents/Receipts/{date_str}/{doc_path.stem}'
            elif any(word in text_lower for word in ['report', 'proposal', 'project']):
                return f'Documents/Reports/{doc_path.stem}'
            elif 'resume' in text_lower or 'cv' in text_lower:
                return 'Documents/Resume'
            else:
                return f'Documents/{doc_path.parent.name}/{doc_path.stem}'
                
        except Exception:
            return f'Documents/{doc_path.stem}'
    
    def classify_code(self, code_path):
        """Programming language detection"""
        try:
            with open(code_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(2048)  # First 2KB
                
            lang = self.detect_language(content)
            return f'Code/{lang}/{code_path.stem}'
            
        except Exception:
            return f'Code/{code_path.stem}'
    
    def classify_generic(self, file_path):
        """File size + age based classification"""
        stat = file_path.stat()
        size_mb = stat.st_size / (1024 * 1024)
        age_days = (datetime.now().timestamp() - stat.st_ctime) / 86400
        
        if size_mb > 100:
            return 'Large_Files'
        elif age_days > 365:
            return 'Old_Files'
        else:
            return 'Misc'
    
    def extract_date(self, text):
        """Extract YYYY-MM-DD from text"""
        patterns = [
            r'\b(\d{4}-\d{2}-\d{2})\b',
            r'\b(\d{2}[-/]\d{2}[-/]\d{4})\b',
            r'\b(\d{2}/\d{2}/\d{4})\b'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).replace('/', '-')
        return datetime.now().strftime('%Y-%m-%d')
    
    def estimate_text_density(self, gray_image):
        """Estimate text presence in image"""
        # Enhance contrast for better OCR detection
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray_image)
        
        # OCR confidence as text density proxy
        data = pytesseract.image_to_data(enhanced, output_type=pytesseract.Output.DICT)
        text_conf = [int(conf) for conf in data['conf'] if int(conf) > 30]
        
        return len(text_conf) / max(len(data['text']), 1)
    
    def is_colorful(self, img):
        """Detect colorful images (memes vs photos)"""
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        saturation = hsv[:,:,1]
        return np.mean(saturation) > 80  # High saturation = colorful
    
    def detect_language(self, content):
        """Detect programming language from code"""
        keywords = {
            'python': ['def ', 'import ', 'class ', 'print('],
            'javascript': ['function', 'const ', 'let ', '=>'],
            'cpp': ['#include', 'cout', 'cin', 'int main'],
            'java': ['public class', 'System.out', 'import '],
            'html': ['<html', '<div', '<script'],
            'css': ['selector', ':hover', 'display:', 'background']
        }
        
        scores = defaultdict(int)
        content_lower = content.lower()
        
        for lang, words in keywords.items():
            for word in words:
                if word in content_lower:
                    scores[lang] += 1
        
        return max(scores, key=scores.get) if scores else 'unknown'

# File extension mappings
AISmartSorter.IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg'}
AISmartSorter.DOC_EXTS = {'.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt'}
AISmartSorter.CODE_EXTS = {'.py', '.js', '.ts', '.cpp', '.c', '.h', '.java', '.html', '.css', '.scss', '.json', '.xml'}
AISmartSorter.VIDEO_EXTS = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'}
AISmartSorter.AUDIO_EXTS = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a'}
AISmartSorter.ARCHIVE_EXTS = {'.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'}
AISmartSorter.EXECUTABLE_EXTS = {'.exe', '.msi', '.deb', '.rpm', '.dmg', '.app'}

# Usage example
if __name__ == "__main__":
    sorter = AISmartSorter()
    
    # Test classifications
    test_files = [
        "photo.jpg",
        "invoice.pdf", 
        "script.py",
        "screenshot.png",
        "family_photo.jpg"
    ]
    
    for test_file in test_files:
        category = sorter.classify_file(test_file)
        print(f"{test_file} → {category}")
