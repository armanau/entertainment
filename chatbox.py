import json
from datetime import datetime
import os
from flask import Flask, request, jsonify
from PIL import Image, ImageDraw, ImageFont
import cv2
import random

app = Flask(__name__)

def adjust_color(color, adjustment):
    return tuple(max(0, min(255, c + adjustment)) for c in color)

def create_whatsapp_chat_image(dialogs, filename, background_colors, bubble_colors):
    width, height = 800, 600
    font_path = "arial.ttf"  # Path to a suitable font
    bold_font_path = "arialbd.ttf"  # Path to Arial Bold font
    font_size = 16
    font = ImageFont.truetype(font_path, font_size)
    bold_font = ImageFont.truetype(bold_font_path, font_size)
    padding = 40
    name_text_gap = 25
    circle_radius = 15  # Radius for the circle

    rendered_texts = []
    existing_names = {}  # Keep track of existing names and alignments
    last_name_displayed = None  # Track the last displayed name
    current_background_color = (230, 230, 230)  # Initial background color, neutral light gray

    image = Image.new('RGB', (width, height), current_background_color)
    draw = ImageDraw.Draw(image)
    y_text = 10

    for dialog in dialogs:
        name, text = dialog['name'], dialog['text']
        text_color = (0, 0, 0)

        if name not in existing_names:
            # Generate a new random light color for the background and bubble if the name is new
            current_background_color = background_colors[name]
            bubble_color = bubble_colors[name]
            name_color = adjust_color(current_background_color, -60)  # Make the name color a bit deeper than the background color
            existing_names[name] = ('left', name_color, bubble_color) if last_name_displayed is None or existing_names[last_name_displayed][0] == 'right' else ('right', name_color, bubble_color)
            last_name_displayed = name

        current_alignment, name_color, bubble_color = existing_names[name]
        x_text = width - 300 if current_alignment == 'right' else 50

        rendered_texts.append((name, text, bubble_color, x_text, current_alignment))

        # Reset drawing and y-coordinate position
        draw.rectangle(((0, 0), (width, height)), fill=current_background_color)
        y_text = 10

        last_name_displayed = None  # Reset the last name displayed

        for r_name, r_text, r_bubble_color, r_x_text, r_alignment in rendered_texts:
            r_name_alignment, r_name_color, r_bubble_color = existing_names[r_name]
            if last_name_displayed != r_name:
                # Draw a circle with the first letter of the name
                circle_center = (r_x_text - circle_radius - 10, y_text + font_size // 2)
                draw.ellipse((circle_center[0] - circle_radius, circle_center[1] - circle_radius,
                              circle_center[0] + circle_radius, circle_center[1] + circle_radius), fill=r_name_color)
                draw.text((circle_center[0] - circle_radius // 2, circle_center[1] - font_size // 2),
                          r_name[0], font=bold_font, fill=(255, 255, 255))

                draw.text((r_x_text, y_text), r_name, font=bold_font, fill=r_name_color)
                y_text += font_size + name_text_gap
                last_name_displayed = r_name

            text_width = draw.textlength(r_text, font=font)
            text_rectangle = [r_x_text, y_text, r_x_text + text_width + 20, y_text + font_size + 20]
            draw.rounded_rectangle(text_rectangle, radius=10, fill=r_bubble_color, outline=(200, 200, 200), width=2)
            draw.text((r_x_text + 10, y_text + 10), r_text, font=font, fill=text_color)
            y_text += font_size + padding

            if y_text > height - font_size - padding:
                rendered_texts.pop(0)
                break

    image.save(filename)
    print(f"Saved image {filename}")

def create_video_from_images(image_files, output_path):
    sample_img = cv2.imread(image_files[0], cv2.IMREAD_UNCHANGED)
    if sample_img is None:
        raise ValueError("Unable to read the first image.")

    height, width, layers = sample_img.shape
    frame_rate = 1
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, frame_rate, (width, height))

    for image_filename in image_files:
        frame = cv2.imread(image_filename)
        if frame is None:
            print(f"Warning: Unable to read image {image_filename}. Skipping.")
            continue
        frame = cv2.resize(frame, (width, height))
        out.write(frame)

    out.release()
    print("Video processing complete. Video saved at:", output_path)

@app.route('/create_video', methods=['POST'])
def generate_chat_images():
    data = request.json
    dialogs = data['dialogs']

    image_files = []
    background_colors = {}
    bubble_colors = {}
    for name in {d['name'] for d in dialogs}:
        background_colors[name] = (random.randint(200, 255), random.randint(200, 255), random.randint(200, 255))
        bubble_colors[name] = (random.randint(100, 200), random.randint(100, 200), random.randint(100, 200))  # Slightly darker bubble color

    for i in range(1, len(dialogs) + 1):
        filename = f"scenario{i}.png"
        create_whatsapp_chat_image(dialogs[:i], filename, background_colors, bubble_colors)
        image_files.append(filename)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_file_name = f'video_{timestamp}.mp4'
    video_path = os.path.join('videos', video_file_name)
    os.makedirs('videos', exist_ok=True)

    create_video_from_images(image_files, video_path)

    for image_file in image_files:
        os.remove(image_file)

    return jsonify(video_file_name=video_file_name, status=200)

if __name__ == "__main__":
    app.run(debug=True)
