import os
from moviepy import TextClip, AudioFileClip, CompositeVideoClip, ColorClip
import textwrap
import random

def create_text_video(script, output_filename, duration=30, 
                      complexity_level="medium", music_file=None):
    """
    Creates a video with text appearing on screen with background music.
    """
    # Video settings
    width, height = 1280, 720
    background_color = (20, 20, 20)  # Dark background
    
    # Create background
    background = ColorClip(size=(width, height), color=background_color, duration=duration)
    
    # Adjust text display based on complexity
    if complexity_level == "low":
        font_size = 60
        words_per_screen = 10
        display_time = 5.0
    elif complexity_level == "medium":
        font_size = 48
        words_per_screen = 15
        display_time = 4.0
    else:  # high
        font_size = 36
        words_per_screen = 25
        display_time = 3.0
    
    # Split text into chunks
    words = script.split()
    chunks = []
    for i in range(0, len(words), words_per_screen):
        chunk = ' '.join(words[i:i+words_per_screen])
        chunks.append(chunk)
    
    # Create text clips
    text_clips = []
    current_time = 0
    
    for chunk in chunks:
        # Wrap text to fit screen width
        wrapped_text = textwrap.fill(chunk, width=40)
        
        # Create text clip with proper parameters
        txt_clip = TextClip(
            text=wrapped_text, 
            font_size=font_size, 
            color='white',
            bg_color=None,
            size=(width-100, None),
            method='caption',
            text_align='center'
        )
        
        txt_clip = txt_clip.with_position('center').with_start(current_time).with_duration(display_time)
        text_clips.append(txt_clip)
        current_time += display_time - 0.5  # Slight overlap for smoother transition
    
    # Add background music
    if music_file and os.path.exists(music_file):
        audio = AudioFileClip(music_file)
        audio = audio.with_duration(min(audio.duration, duration))
        background = background.set_audio(audio)
    
    # Combine all clips
    video = CompositeVideoClip([background] + text_clips, size=(width, height))
    video = video.with_duration(min(duration, current_time + display_time))
    
    # Write output file
    video.write_videofile(output_filename, fps=24, codec='libx264', 
                         audio_codec='aac', threads=4)
    print(f"Video saved as {output_filename}")

def generate_videos(scripts, complexity_levels, output_dir="./webserver/static/videos"):
    """Generate multiple videos from scripts with different complexity levels"""
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    music_files = [
        "ambient1.mp3",
    ]
    
    # Generate each video
    for i, (script, level) in enumerate(zip(scripts, complexity_levels)):
        output_file = os.path.join(output_dir, f"text_video_{i+1}_{level}.mp4")
        music = random.choice(music_files) if music_files and os.path.exists(music_files[0]) else None
        create_text_video(script, output_file, complexity_level=level, music_file=music)

# Example usage
if __name__ == "__main__":
    scripts = [
        "Photosynthesis is the process by which plants convert light energy into chemical energy. This energy is used to produce glucose from carbon dioxide and water. Oxygen is released as a byproduct.",
        "The Pythagorean theorem states that in a right triangle, the square of the length of the hypotenuse equals the sum of the squares of the other two sides. This can be written as a² + b² = c².",
        "Climate change refers to long-term shifts in temperatures and weather patterns. Human activities have been the main driver of climate change since the 1800s, primarily due to burning fossil fuels like coal, oil, and gas.",
        "Quantum computing uses quantum bits or qubits that can exist in multiple states simultaneously, unlike classical bits. This property, called superposition, allows quantum computers to process complex problems exponentially faster.",
        "The human immune system is a complex network of cells, tissues, and organs that work together to defend the body against harmful pathogens. It recognizes foreign substances and destroys or neutralizes them."
    ]
    
    complexity_levels = ["low", "medium", "high", "high", "medium"]
    generate_videos(scripts, complexity_levels)
