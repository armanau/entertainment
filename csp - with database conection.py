from flask import Flask, send_file, request, jsonify
import os
from datetime import datetime
import mysql.connector
from moviepy.editor import *
from moviepy.config import change_settings
import json  # For parsing the JSON-like chat story

# Configure ImageMagick binary location for Windows
change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"})

app = Flask(__name__)

# Directory for saved videos
videos_dir = os.path.join(os.getcwd(), 'videos')
os.makedirs(videos_dir, exist_ok=True)

def fetch_chat_story(id):
    # Update db_config with your database credentials
    db_config = {
        'user': 'admin',
        'password': 'entertainment_admin',
        'host': '3.27.125.190',
        'database': 'entertainment_db',
        'port': 3306
    }
    db = None
    cursor = None
    try:
        db = mysql.connector.connect(**db_config)
        cursor = db.cursor()
        query = "SELECT chat_story FROM content WHERE id = %s"
        cursor.execute(query, (id,))
        result = cursor.fetchone()
        if result:
            # Assuming the data is in JSON format, directly parse it
            chat_story = json.loads(result[0])
            # Convert to the expected format
            formatted_story_data = []
            for entry in chat_story:
                formatted_story_data.append({entry["character"]: entry["line"]})
            return formatted_story_data
        else:
            print(f"No chat story found for id: {id}")  # Debugging statement
            return None
    except Exception as e:
        print(f"Error fetching chat story: {e}")  # Debugging statement
        return None
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()

def create_video_clips(story_data, background_image_path):
    clips = []
    for item in story_data:
        for character, sentence in item.items():
            text = f"{character}: {sentence}"
            try:
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

@app.route('/generate-video', methods=['GET', 'POST'])
def generate_video():
    id = request.args.get('id', default="42")
    chat_story = fetch_chat_story(id)
    if not chat_story:
        return jsonify(message="No chat story found for id: {}".format(id), status=404)
    background_image_path = 'default.png'  # Ensure this path is correct
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
