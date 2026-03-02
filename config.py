# config.py

INPUT_VIDEO = "input_video.mp4"
OUTPUT_VIDEO = "output_tracked.avi"

YOLO_MODEL = "yolov8n.pt"
CLIP_MODEL_NAME = "openai/clip-vit-base-patch32"

PERSON_CLASS_ID = 0

PROMPTS = [
    "The person is walking",
    "The person is standing",
    "The person placed the laptop down",
    "The person picked the laptop",
    "The man is holding a laptop"
]