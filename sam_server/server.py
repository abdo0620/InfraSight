"""SAM 3.1 segmentation server for InfraSight: outlines the damage on a citizen's photo.

Run it on a machine with an NVIDIA GPU (CPU works, but takes tens of seconds per photo):
    pip install -r requirements.txt
    hf auth login                      # if the model asks you to accept its licence on huggingface.co first
    uvicorn server:app --host 0.0.0.0 --port 8100
Then in InfraSight's backend/.env: SAM_URL=http://<this machine>:8100

SAM_MODEL picks the checkpoint (default facebook/sam3.1; unsloth/sam3.1 is an ungated copy).
"""
import io, os
import cv2
import numpy as np
import torch
from fastapi import FastAPI, File, Form, UploadFile
from PIL import Image
from transformers import Sam3Model, Sam3Processor

MODEL = os.environ.get("SAM_MODEL", "facebook/sam3.1")
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
DTYPE = torch.bfloat16 if DEVICE == "cuda" else torch.float32
model = Sam3Model.from_pretrained(MODEL, dtype=DTYPE).to(DEVICE).eval()
processor = Sam3Processor.from_pretrained(MODEL)
app = FastAPI(title="InfraSight SAM server")


@app.get("/health")
def health():
    return {"ok": True, "model": MODEL, "device": DEVICE}


@app.post("/segment")
async def segment(image: UploadFile = File(...), text: str = Form(...), threshold: float = Form(0.4)):
    """Every instance of `text` (e.g. "pothole") in the photo. Coordinates are fractions of the photo size."""
    img = Image.open(io.BytesIO(await image.read())).convert("RGB")
    w, h = img.size
    inputs = processor(images=img, text=text, return_tensors="pt").to(DEVICE, DTYPE)
    with torch.inference_mode():
        outputs = model(**inputs)
    res = processor.post_process_instance_segmentation(
        outputs, threshold=threshold, mask_threshold=0.5, target_sizes=inputs.get("original_sizes").tolist())[0]
    objects = []
    for score, box, mask in zip(res["scores"].tolist(), res["boxes"].tolist(), res["masks"]):
        m = mask.cpu().numpy().astype(np.uint8)
        contours, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            continue
        c = max(contours, key=cv2.contourArea)
        c = cv2.approxPolyDP(c, 0.004 * cv2.arcLength(c, True), True)   # fewer points, same shape
        objects.append({"score": round(score, 3), "box": [round(box[0] / w, 4), round(box[1] / h, 4),
                                                            round(box[2] / w, 4), round(box[3] / h, 4)],
                        "polygon": [[round(x / w, 4), round(y / h, 4)] for x, y in c.reshape(-1, 2).tolist()],
                        "area": round(float(m.sum()) / (w * h), 4)})
    objects.sort(key=lambda o: -o["score"])
    return {"text": text, "width": w, "height": h, "objects": objects[:5]}
