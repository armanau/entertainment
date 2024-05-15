from flask import Flask, request, jsonify
import os
from datetime import datetime
from moviepy.editor import *
from moviepy.config import change_settings

# Configure ImageMagick binary location for Windows
change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"})

app = Flask(__name__)

# Directory for saved videos
videos_dir = os.path.join(os.getcwd(), 'videos')
os.makedirs(videos_dir, exist_ok=True)

def parse_chat_story_from_request():
    # Retrieve JSON payload from the request
    request_data = request.get_json()
    if not request_data or "Dialogue" not in request_data:
        print("Invalid or missing 'Dialogue' in request")  # Debugging statement
        return None

    # Parse the 'Dialogue' part of the JSON payload
    chat_story = request_data["Dialogue"]
    formatted_story_data = []
    for entry in chat_story:
        character = entry.get("Character")
        line = entry.get("Line")
        if character and line:  # Ensure both character and line are present
            formatted_story_data.append({character: line})
    
    return formatted_story_data

def create_video_clips(story_data, background_image_path):
    clips = []
    for item in story_data:
        for character, sentence in item.items():
            text = f"{character}: {sentence}"
            try:
                # Ensure you have a background image at the specified path
                text_clip = TextClip(text, fontsize=24, color='white', bg_color='black').set_position('center').set_duration(2)
                background_clip = ImageClip(background_image_path).set_duration(2)
                combined_clip = CompositeVideoClip([background_clip, text_clip])
                clips.append(combined_clip)
            except Exception as e:
                print(f"Error creating clip: {e}")
    
    if clips:
        return concatenate_videoclips(clips)
    else:
        print("No clips to concatenate.")
        return None

@app.route('/generate-video', methods=['POST'])  # Changed to POST to accept JSON payload
def generate_video():
    chat_story = parse_chat_story_from_request()
    if not chat_story:
        return jsonify(message="Invalid request. Please provide a valid 'Dialogue' JSON.", status=400)
    background_image_path = 'default.png'  # Ensure this path exists
    final_video = create_video_clips(chat_story, background_image_path)
    if final_video is None:
        return jsonify(message="Failed to create video.", status=500)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_file_name = f'video_{timestamp}.mp4'
    video_file_path = os.path.join(videos_dir, video_file_name)
    final_video.write_videofile(video_file_path, fps=24)

    # Return just the video file name in the JSON response
    return jsonify(video_file_name=video_file_name, status=200)

if __name__ == '__main__':
    app.run(debug=True)
