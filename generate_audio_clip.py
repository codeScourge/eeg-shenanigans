import os
import textwrap
from pathlib import Path
import numpy as np
from gtts import gTTS
from moviepy import vfx, AudioFileClip, ImageClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont
import tempfile

def create_narration_video(text, complexity, output_filename, duration=30):
    """
    Create a narration video with adjustable speed based on complexity.
    
    Args:
        text (str): The text to narrate
        complexity (str): "low", "medium", or "high" to control speed
        output_filename (str): Filename for the output video
        duration (int): Target duration in seconds
    """
    # Create temp directory for intermediate files
    temp_dir = tempfile.mkdtemp()
    
    # Adjust speech rate based on complexity
    if complexity == "low":
        speech_rate = False  # Normal speed
        text_size = 36
        words_per_frame = 6
    elif complexity == "medium":
        speech_rate = True  # Slightly faster
        text_size = 32
        words_per_frame = 9
    else:  # high
        speech_rate = True  # Fast
        text_size = 28
        words_per_frame = 12
    
    # Create audio narration
    audio_file = os.path.join(temp_dir, "narration.mp3")
    tts = gTTS(text=text, lang='en', slow=not speech_rate)
    tts.save(audio_file)
    
    # Load audio to get its duration
    audio = AudioFileClip(audio_file)
    audio_duration = audio.duration
    
    # Create background (plain color)
    width, height = 1280, 720
    color = (240, 240, 240)  # Light gray
    
    # Create frames with text
    frames_folder = os.path.join(temp_dir, "frames")
    os.makedirs(frames_folder, exist_ok=True)
    
    # Split text into chunks for progressive display
    words = text.split()
    total_frames = int(duration * 30)  # 30fps
    
    # Determine how many words to show per frame
    words_per_frame = max(1, len(words) // total_frames)
    
    # Create a blank frame
    def create_frame(frame_text, frame_number):
        img = Image.new('RGB', (width, height), color)
        draw = ImageDraw.Draw(img)
        
        # Use a nicer font if available, otherwise use default
        try:
            font = ImageFont.truetype("Arial", text_size)
        except IOError:
            font = ImageFont.load_default()
        
        # Wrap text to fit width
        margin = 100
        wrapped_text = textwrap.fill(frame_text, width=40)
        
        # Draw text centered
        left, top, right, bottom = draw.textbbox((0, 0), wrapped_text, font=font)
        text_width = right - left
        text_height = bottom - top

        position = ((width - text_width) // 2, (height - text_height) // 2)
        draw.text(position, wrapped_text, fill=(0, 0, 0), font=font)
        
        # Save the frame
        frame_path = os.path.join(frames_folder, f"frame_{frame_number:04d}.png")
        img.save(frame_path)
        return frame_path
    
    # Generate frames with progressively more text
    frame_files = []
    for i in range(total_frames):
        # Calculate how many words to show in this frame
        words_to_show = min(len(words), int((i / total_frames) * len(words)) + 1)
        frame_text = ' '.join(words[:words_to_show])
        frame_path = create_frame(frame_text, i)
        frame_files.append(frame_path)
    
    # Create video from frames
    clips = [ImageClip(f).with_duration(1/30) for f in frame_files]
    video = concatenate_videoclips(clips, method="compose")
    
    # Combine audio and video
    final_clip = video.with_audio(audio)
    final_clip.write_videofile(output_filename, fps=30)
    
    # Clean up temporary files
    import shutil
    shutil.rmtree(temp_dir)
    
    print(f"Video saved as {output_filename}")

# --- main
if __name__ == "__main__":
    scripts = [
        "The sun is a star. It gives us light and heat. Plants need sunlight to grow. Without the sun, Earth would be very cold and dark. The sun is very important for all life on Earth.",
        "Photosynthesis is the process used by plants to convert light energy into chemical energy. This chemical energy is stored in carbohydrate molecules, such as sugars, which are synthesized from carbon dioxide and water. Oxygen is released as a waste product during this process.",
        "Quantum entanglement occurs when particles such as photons, electrons, or molecules interact physically and then become separated while continuing to share quantum states. This phenomenon leads to correlations between observable physical properties of the systems that cannot be explained by classical physics. The mathematical formulation of quantum mechanics allows for precise calculations of these correlations, which have been confirmed experimentally."
    ]
    
    complexity_levels = [
        "low",
        "medium",
        "high"
    ]
    
    # Create narration videos
    for i, text, complexity in zip(range(len(scripts)), scripts, complexity_levels):
        create_narration_video(
            text, 
            complexity=complexity,
            output_filename=f"./webserver/static/videos/audio_video_{i}_{complexity}.mp4"
        )
        
