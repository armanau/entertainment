import json
from PIL import Image, ImageDraw, ImageFont
import cv2
import os
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

def create_chat_image(dialogs, filename):
    # Image dimensions
    width, height = 500, (len(dialogs) * 100 + 50)
    image = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()

    y_text = 50
    for dialog in dialogs:
        text = f"{dialog['name']}: {dialog['text']}"
        draw.rectangle([50, y_text, width - 50, y_text + 80], fill=(232, 240, 254), outline=(0, 0, 0))
        draw.text((60, y_text + 10), text, font=font, fill=(0, 0, 0))
        y_text += 100

    image.save(filename)
    print(f"Saved image {filename}")

def create_video_from_images(image_files, output_path):
    # Assuming all images are the same size, get dimensions from the first image
    sample_img = cv2.imread(image_files[0], cv2.IMREAD_UNCHANGED)
    if sample_img is None:
        raise ValueError("Unable to read the first image. Check the file format and path.")

    height, width, layers = sample_img.shape
    frame_rate = 1  # One images per second
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, frame_rate, (width, height))

    if not out.isOpened():
        raise ValueError("Could not open the video for writing. Check the codec or file path.")

    for image_filename in image_files:
        frame = cv2.imread(image_filename)
        if frame is None:
            print(f"Warning: Unable to read image {image_filename}. Skipping.")
            continue

        if frame.shape[1] != width or frame.shape[0] != height:
            print(f"Warning: Image {image_filename} has different dimensions. Resizing.")
            frame = cv2.resize(frame, (width, height))

        out.write(frame)
    
    out.release()
    print("Video processing complete. Video saved at:", output_path)

@app.route('/create_video', methods=['POST'])
def generate_chat_images():
    data = request.json
    dialogs = data['dialogs']

    image_files = []
    for i in range(1, len(dialogs) + 1):
        filename = f"scenario{i}.png"
        create_chat_image(dialogs[:i], filename)
        image_files.append(filename)

    # Adding timestamp to video file name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_file_name = f'video_{timestamp}.mp4'
    video_path = os.path.join('videos', video_file_name)
    os.makedirs('videos', exist_ok=True)  # Ensure the video directory exists

    create_video_from_images(image_files, video_path)

    # Optionally, clean up image files if not needed
    for image_file in image_files:
        os.remove(image_file)
        print(f"Deleted {image_file}")

    
    return jsonify(video_file_name=video_file_name, status=200)

if __name__ == "__main__":
    app.run(debug=True)
