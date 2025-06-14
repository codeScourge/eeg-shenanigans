from moviepy import TextClip, AudioFileClip, CompositeVideoClip, ColorClip
import textwrap

from gtts import gTTS

import tempfile
import os


DURATION = 30 # in seconds
FPS = 16

def create_text_video(text, output_filename, complexity, duration=DURATION, fps=FPS):
    """
    Creates a video with text appearing on screen with background music.
    
    for the average human, reading wpm:
    - low: 200-250 => 250
    - high: 300-450 => 350
    
    we will always show 10 words per screen, this means, we will adapt the display_time in seconds to fit that value
    - 250/10 => need a 25th of a minute => 60/25 = 2.5sec
    - 350/10 => 60/35 = 1.7sec
    using the wpm and this speed, we can predict if the text will fit in the duration or will be done before the end
    """
    width, height = 1280, 720
    background_color = (20, 20, 20)
    background = ColorClip(size=(width, height), color=background_color, duration=duration)
    
    font_size = 40
    font_color = "white"
    
    
    words = text.split()
    n_words = len(words)
    words_per_screen = 10
    
    
    if complexity == "low":
        wpm = 250
    elif complexity == "high":
        wpm = 350
    else:
        raise ValueError("complexity must be 'low', or 'high'")
    
    display_time = 60 / (wpm / words_per_screen)


    words_displayed = (duration / display_time) * words_per_screen
    if words_displayed < n_words:
        print(f"--- warning: words to be displayed {n_words} is bigger than the displayable {words_displayed} - some will be cutoff ---")
    if words_displayed > n_words:
        print(f"--- warning: words to be displayed {n_words} is smaller than the displayable {words_displayed}- might have empty screen at the end---")
    

    text_clips = []
    current_time = 0
    

    for i in range(0, len(words), words_per_screen):
        chunk = ' '.join(words[i:i+words_per_screen])
        
        wrapped_text = textwrap.fill(chunk, width=40)
        
        txt_clip = TextClip(
            text=wrapped_text, 
            font_size=font_size, 
            color=font_color,
            bg_color=None,
            size=(width-100, None),
            method='caption',
            text_align='center'
        )
        
        txt_clip = txt_clip.with_position('center').with_start(current_time).with_duration(display_time)
        text_clips.append(txt_clip)
        current_time += display_time

    video = CompositeVideoClip([background] + text_clips, size=(width, height)).with_duration(duration)
    video.write_videofile(output_filename, fps=fps, codec='libx264', audio_codec='aac', threads=4)
    print(f"Video saved as {output_filename}")


def create_audio_video(text, output_filename, complexity, duration=DURATION, fps=FPS):
    """
    Create a narration video with adjustable speed based on complexity.
    
    uses gtts, wpm up to:
    - low: 110
    - high: 160
    this means that in order to match the duration, the text must have as close to but not more than wpm/duration words - will throw a warning if it does
    """
    width, height = 1280, 720
    background_color = (20, 20, 20)
    background = ColorClip(size=(width, height), color=background_color, duration=duration)
    
    n_words = len(text.split())
    
    if complexity == "low":
        slow_speech = True
        wpm = 110
        
    elif complexity == "high":
        slow_speech = False
        wpm = 160
    else:
        raise ValueError("complexity must be 'low', or 'high'")
    
    
    minutes_needed = n_words / wpm 
    if minutes_needed * 60 > duration:
        print(f"--- warning: minutes_needed {minutes_needed}m is larger than duration {duration}s - speech might be cutoff ---")
    if minutes_needed * 60 < duration:
        print(f"--- warning: minutes_needed {minutes_needed}m is smaller than duration {duration} s- might have empty audio at the end ---")
    
    
    
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
        temp_filename = temp_file.name
        
    tts = gTTS(text=text, lang='en', slow=slow_speech)
    tts.save(temp_filename)
    audio = AudioFileClip(temp_filename)
    
    
    print(f"==> audio {audio} while clip is {duration}")


    video = CompositeVideoClip([background], size=(width, height)).with_duration(duration)
    video = video.with_audio(audio)
    video.write_videofile(output_filename, fps=fps, codec='libx264', audio_codec='aac', threads=4)
    print(f"Video saved as {output_filename}")
    
    audio.close()
    os.remove(temp_filename)

# --- main
if __name__ == "__main__":
    # --- filling content
    # scripts = [
    #     "Photosynthesis is the process by which plants convert light energy into chemical energy. This energy is used to produce glucose from carbon dioxide and water. Oxygen is released as a byproduct.",
    #     "The Pythagorean theorem states that in a right triangle, the square of the length of the hypotenuse equals the sum of the squares of the other two sides. This can be written as a² + b² = c².",
    #     "Climate change refers to long-term shifts in temperatures and weather patterns. Human activities have been the main driver of climate change since the 1800s, primarily due to burning fossil fuels like coal, oil, and gas.",
    #     "Quantum computing uses quantum bits or qubits that can exist in multiple states simultaneously, unlike classical bits. This property, called superposition, allows quantum computers to process complex problems exponentially faster.",
    # ]
    
    # complexity_levels = [
    #     "low", 
    #     "low", 
    #     "high", 
    #     "high", 
    # ]
    
    # video_types = [
    #     0,
    #     1,
    #     0,
    #     1,
    # ]
    
    scripts = [
        # Easy Content, Low Speed (Audio)
        "The water cycle is how water moves around Earth. It starts when the sun heats water in oceans and lakes. This water turns into vapor and rises into the air. As it cools, it forms clouds. When clouds get heavy, rain or snow falls back to Earth. Water flows into rivers and back to oceans. Then the cycle begins again.",
        
        # Easy Content, Low Speed (Text)
        "Plants need sunlight to grow. Through a process called photosynthesis, plants use light energy from the sun to make food. Leaves contain a green substance called chlorophyll that captures sunlight. The plant combines this light energy with water from the soil and carbon dioxide from the air. This creates sugar for the plant to use as energy. During this process, plants release oxygen into the air, which animals and humans breathe. Without plants producing oxygen, most life on Earth could not exist. This is why forests and other plant-rich areas are so important for our planet's health. Plants also provide food, shelter, and materials for many living things.",
        
        # Medium Content, Low Speed (Audio)
        "Renewable energy comes from natural sources that don't run out. Solar panels convert sunlight directly into electricity using photovoltaic cells. Wind turbines generate power when their blades are turned by moving air. Unlike fossil fuels, these energy sources produce minimal pollution and help reduce climate change impacts.",
        
        # Medium Content, High Speed (Text)
        "The human immune system is a complex network of cells, tissues, and organs that work together to defend the body against harmful pathogens. When a virus or bacteria enters the body, specialized white blood cells called lymphocytes identify these foreign invaders. B lymphocytes produce antibodies that target specific pathogens, while T lymphocytes directly attack infected cells. Macrophages engulf and digest cellular debris and pathogens. The complement system enhances the ability of antibodies to clear microbes. Dendritic cells present antigens to T cells, activating the adaptive immune response. This sophisticated defense mechanism can remember previous infections, allowing for faster response to repeated exposure. Vaccines work by training the immune system to recognize specific pathogens without causing disease. Autoimmune disorders occur when this system mistakenly attacks healthy cells.",
        
        # Hard Content, Low Speed (Audio)
        "Quantum entanglement occurs when particles interact in ways that their quantum states cannot be described independently. Einstein called this 'spooky action at a distance' because measuring one particle instantly affects its entangled partner, regardless of separation distance. This phenomenon challenges our understanding of local realism in physics.",
        
        # Hard Content, High Speed (Text)
        "Blockchain technology functions as a distributed ledger system implementing cryptographic principles to ensure data immutability and transparency. Each block contains a cryptographic hash of the previous block, transaction data, and a timestamp. The decentralized consensus mechanism eliminates the need for trusted third parties by requiring network participants to validate transactions through complex mathematical algorithms. Proof-of-work systems demand computational resources to solve cryptographic puzzles, while proof-of-stake systems allocate validation rights based on cryptocurrency holdings. Smart contracts enable self-executing agreements with terms directly written into code. The immutable nature of blockchain prevents retroactive data modification without consensus from the network majority. Public key infrastructure ensures secure transactions through asymmetric cryptography, where users possess private keys to authorize transfers and public keys visible to the network. This technology has applications beyond cryptocurrency, including supply chain management, digital identity verification, and decentralized finance protocols.",
        
        # Medium Content, High Speed (Audio)
        "Neural networks consist of interconnected artificial neurons organized in layers. Input data passes through hidden layers where weighted connections determine signal strength. Each neuron applies an activation function to determine its output. Through backpropagation, the network adjusts weights to minimize prediction errors and improve accuracy over time.",
        
        # Medium Content, Low Speed (Text)
        "Climate change refers to long-term shifts in temperatures and weather patterns. These changes may be natural, but since the 1800s, human activities have been the main driver of climate change, primarily due to burning fossil fuels like coal, oil, and gas, which produces heat-trapping gases. As these gases accumulate in our atmosphere, they act like a blanket, trapping the sun's heat and causing Earth's temperature to rise. This warming leads to more frequent and intense weather events, changing precipitation patterns, rising sea levels, and ecosystem disruptions. Scientists have observed these changes through careful measurement of global temperatures, ocean conditions, ice sheet volumes, and atmospheric composition over many decades. The effects of climate change impact every region on Earth, though some areas experience more dramatic consequences than others.",
        
        # Easy Content, High Speed (Audio)
        "Healthy eating involves choosing a variety of foods from all food groups. Fruits and vegetables provide essential vitamins. Whole grains offer fiber and energy. Lean proteins help build muscles. Dairy products strengthen bones. Limiting processed foods and sugar improves overall health. Drinking plenty of water keeps your body functioning properly.",
        
        # Hard Content, Low Speed (Text)
        "Neuroplasticity refers to the brain's remarkable ability to reorganize itself by forming new neural connections throughout life. This dynamic property allows neurons to compensate for injury and disease and to adjust their activities in response to new situations or environmental changes. The process occurs at multiple levels, from microscopic changes in individual neurons to large-scale changes visible on brain imaging. During development, neuroplasticity is particularly abundant as the immature brain organizes itself. Later in life, it remains essential for learning, memory formation, and adaptation to new experiences. Neuroplasticity works through several mechanisms including axonal sprouting, where undamaged axons grow new nerve endings to reconnect with neurons that have lost their connections. Synaptic pruning eliminates weaker neural connections while preserving stronger ones. Long-term potentiation occurs when communication between two neurons strengthens over time, facilitating learning and memory formation. Environmental enrichment studies demonstrate that rich, stimulating environments can enhance neuroplasticity even in adult brains."
    ]

    complexity_levels = [
        "low",   # Easy Content, Low Speed (Audio)
        "low",   # Easy Content, Low Speed (Text)
        "low",   # Medium Content, Low Speed (Audio)
        "high",  # Medium Content, High Speed (Text)
        "low",   # Hard Content, Low Speed (Audio)
        "high",  # Hard Content, High Speed (Text)
        "high",  # Medium Content, High Speed (Audio)
        "low",   # Medium Content, Low Speed (Text)
        "high",  # Easy Content, High Speed (Audio)
        "low"    # Hard Content, Low Speed (Text)
    ]

    video_types = [
        0,  # Audio
        1,  # Text
        0,  # Audio
        1,  # Text
        0,  # Audio
        1,  # Text
        0,  # Audio
        1,  # Text
        0,  # Audio
        1   # Text
    ]
    
    # --- keep the same
    for i, (script, level, type) in enumerate(zip(scripts, complexity_levels, video_types)):
        output_file = f"./webserver/static/videos/clip_{i+1}.mp4"   # matching what we have in `cogload_calibration.js`
        if type == 1:
            # output_file = f"./webserver/static/videos/{i+1}_{level}_text.mp4"
            create_text_video(script, output_file, level)

        elif type == 0:
            # output_file = f"./webserver/static/videos/{i+1}_{level}_audio.mp4"
            create_audio_video(script, output_file, level)
            
            
    # TODO: generate three python arrays `scripts` (containing strings), `complexity_levels` ("high" or "low" - determines the speed), and `video_types` (0 for audio, 1 for text) - all of the same length obviously
    # for our duration of 30seconds, 
    # - our audio clips, need to be 55 words for slow speech or 80 word for fast speech
    # - our text clips, need 120 words for slow read or 176 for fast read
    # now: based on this information, create easy (easy content and low speed), hard (hard content and high speed), and medium (everything inbetween) content. give me the code with no comments
    
