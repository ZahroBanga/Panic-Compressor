import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
import cv2
from PIL import Image

app = FastAPI()

UPLOAD_DIR = "/tmp/temp_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def main():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Instant Panic Compressor</title>
        <style>
            body { font-family: sans-serif; text-align: center; background: #121212; color: white; padding: 50px; }
            .box { border: 2px dashed #00ff88; padding: 40px; border-radius: 10px; max-width: 500px; margin: auto; }
            input[type="file"] { margin: 20px 0; display: block; width: 100%; text-align: center; }
            button { background: #00ff88; color: black; border: none; padding: 12px 24px; font-weight: bold; border-radius: 5px; cursor: pointer; font-size: 16px; }
            button:hover { background: #00cc6e; }
        </style>
    </head>
    <body>
        <h1>File Too Big for TikTok / YouTube?</h1>
        <p>Compress it instantly and cleanly. No ads. No watermark.</p>
        <div class="box">
            <form action="/compress" method="post" enctype="multipart/form-data">
                <input type="file" name="file" required><br>
                <button type="submit">Compress Now ($1)</button>
            </form>
        </div>
    </body>
    </html>
    """

@app.post("/compress")
async def compress_file(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded.")
        
    input_path = os.path.join(UPLOAD_DIR, file.filename)
    output_path = os.path.join(UPLOAD_DIR, f"compressed_{file.filename}")
    
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    file_extension = file.filename.split(".")[-1].lower()
    
    try:
        if file_extension in ["jpg", "jpeg", "png"]:
            img = Image.open(input_path)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.save(output_path, "JPEG", quality=60)
            
        elif file_extension in ["mp4", "avi", "mov", "webm"]:
            cap = cv2.VideoCapture(input_path)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            if width == 0 or height == 0:
                raise Exception("Could not read video dimensions.")
            
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                out.write(frame)
                
            cap.release()
            out.release()
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type.")
            
        if not os.path.exists(output_path):
            raise Exception("Compression failed to generate output file.")
            
        return FileResponse(output_path, media_type='application/octet-stream', filename=f"compressed_{file.filename}")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(input_path):
            os.remove(input_path)
