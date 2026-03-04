import torch
import numpy as np
import cv2
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
from config import CLIP_MODEL_NAME, PROMPTS

class ActivityClassifier:
    def __init__(self):
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model = CLIPModel.from_pretrained(CLIP_MODEL_NAME).to(self.device)
        self.processor = CLIPProcessor.from_pretrained(CLIP_MODEL_NAME)

    def classify(self, frame, bbox):
        x1, y1, x2, y2 = map(int,bbox)
        crop = frame[y1:y2, x1:x2]

        if crop.size == 0:
            return "unknown"
        
        crop_pil = Image.fromarray(
            cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
        )

        inputs = self.processor(
            text = PROMPTS,
            images = crop_pil,
            return_tensors = 'pt',
            padding = True
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = outputs.logits_per_image.softmax(dim=1).cpu().numpy()[0]

            return PROMPTS[np.argmax(probs)]