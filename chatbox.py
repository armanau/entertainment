import json
from datetime import datetime
import os
from flask import Flask, request, jsonify
from PIL import Image, ImageDraw, ImageFont
import cv2
import random
from gtts import gTTS
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

app = Flask(__name__)

def adjust_color(color, adjustment):
    return tuple(max(0, min(255, c + adjustment)) for c in color)

def get_random_image_from_folder(folder_path):
    image_files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    if not image_files:
        raise ValueError("No images found in the folder.")
    random_image_file = random.choice(image_files)
    return os.path.join(folder_path, random_image_file)

def create_whatsapp_chat_image(dialogs, filename, background_images, bubble_colors):
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

    image = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(image)
    y_text = 10

    for dialog in dialogs:
        name, text = dialog['name'], dialog['text']
        text_color = (0, 0, 0)

        if name not in existing_names:
            # Get a new random image for the background if the name is new
            current_background_image = Image.open(background_images[name])
            image.paste(current_background_image.resize((width, height)), (0, 0))
            bubble_color = bubble_colors[name]
            name_color = adjust_color(bubble_color, -60)  # Make the name color a bit deeper than the bubble color
            existing_names[name] = ('left', name_color, bubble_color) if last_name_displayed is None or existing_names[last_name_displayed][0] == 'right' else ('right', name_color, bubble_color)
            last_name_displayed = name

        current_alignment, name_color, bubble_color = existing_names[name]
        x_text = width - 300 if current_alignment == 'right' else 50

        rendered_texts.append((name, text, bubble_color, x_text, current_alignment))

        # Reset drawing and y-coordinate position
        image.paste(current_background_image.resize((width, height)), (0, 0))
        draw = ImageDraw.Draw(image)
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

def create_video_from_images(image_files, audio_files, output_path):
    video_clips = []
    fps = 24  # Set the frames per second for the video
    for image_file, audio_file in zip(image_files, audio_files):
        audio_clip = AudioFileClip(audio_file)
        video_clip = ImageClip(image_file, duration=audio_clip.duration).set_fps(fps).set_audio(audio_clip)
        video_clips.append(video_clip)

    final_clip = concatenate_videoclips(video_clips, method="compose")
    final_clip.write_videofile(output_path, codec='libx264', fps=fps)

@app.route('/create_video', methods=['POST'])
def generate_chat_images():
    data = request.json
    dialogs = data['dialogs']
    image_folder = "image"

    image_files = []
    audio_files = []
    background_images = {}
    bubble_colors = {}

    for name in {d['name'] for d in dialogs}:
        background_images[name] = get_random_image_from_folder(image_folder)
        bubble_colors[name] = (random.randint(100, 200), random.randint(100, 200), random.randint(100, 200))  # Slightly darker bubble color

    for i, dialog in enumerate(dialogs):
        filename = f"scenario{i+1}.png"
        create_whatsapp_chat_image(dialogs[:i+1], filename, background_images, bubble_colors)
        image_files.append(filename)

        # Generate audio for the current dialog
        tts = gTTS(dialog['text'])
        audio_file = f"audio_{i+1}.mp3"
        tts.save(audio_file)
        audio_files.append(audio_file)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_file_name = f'video_{timestamp}.mp4'
    video_path = os.path.join('videos', video_file_name)
    os.makedirs('videos', exist_ok=True)

    create_video_from_images(image_files, audio_files, video_path)

    # Cleanup
    for image_file in image_files:
        os.remove(image_file)
    for audio_file in audio_files:
        os.remove(audio_file)

    return jsonify(video_file_name=video_file_name, status=200)

if __name__ == "__main__":
    app.run(debug=True)
