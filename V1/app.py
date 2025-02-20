import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from ttkbootstrap import Style
from pydub import AudioSegment
import numpy as np
import os
import random

# Function to upload file
def upload_file():
    file_path = filedialog.askopenfilename(filetypes=[("Audio Files", "*.mp3 *.wav")])
    if file_path:
        entry_file_path.delete(0, tk.END)
        entry_file_path.insert(0, file_path)

# Function to update speed label
def update_speed_label(val):
    speed_label_var.set(f"Speed: {float(val):.2f}")

# Function to convert audio to 3D/8D
def convert_audio():
    file_path = entry_file_path.get()
    if not file_path:
        messagebox.showerror("Error", "Please upload an audio file")
        return
    
    # Open a Save As dialog to choose the output file location and name
    output_path = filedialog.asksaveasfilename(defaultextension=".wav", filetypes=[("WAV files", "*.wav")])
    if not output_path:
        return  # User cancelled the dialog
    
    # Loading the audio file
    audio = AudioSegment.from_file(file_path)
    
    # Apply 3D effect
    sample_rate = audio.frame_rate
    samples = np.array(audio.get_array_of_samples()).reshape((-1, 2))
    
    # Get selected pattern
    pattern = pattern_var.get()
    
    # Get speed from the scale
    speed = speed_scale.get()
    
    # Ensure samples are float for processing
    samples = samples.astype(np.float64)
    
    # Apply effect based on the selected pattern
    duration = len(audio) / 1000.0
    t = np.linspace(0, duration, len(samples))
    
    if pattern == "Circular":
        angle = 2.0 * np.pi * t * speed  # Circular pattern
        left_channel = samples[:, 0] * (0.5 * (1 + np.cos(angle)))
        right_channel = samples[:, 1] * (0.5 * (1 + np.sin(angle)))
    
    elif pattern == "Sine":
        angle = 2.0 * np.pi * t * speed  # Sine pattern
        left_channel = samples[:, 0] * (0.5 * (1 + np.sin(angle)))
        right_channel = samples[:, 1] * (0.5 * (1 - np.sin(angle)))
    
    elif pattern == "Smooth Right-Left":
        transition_time = 5.0  # Time in seconds for the transition
        transition_frames = int(sample_rate * transition_time)
        
        # Create a transition effect
        fade_in = np.linspace(0, 1, transition_frames)
        fade_out = np.linspace(1, 0, transition_frames)
        
        left_channel = np.copy(samples[:, 0])
        right_channel = np.copy(samples[:, 1])
        
        num_cycles = len(samples) // (2 * transition_frames)
        
        for cycle in range(num_cycles):
            start_idx = cycle * 2 * transition_frames
            end_idx = start_idx + transition_frames
            
            right_channel[start_idx:end_idx] *= fade_in * 0.95  # 100% to 5%
            right_channel[end_idx:2*transition_frames + start_idx] *= fade_out * 0.95
            
            left_channel[start_idx:end_idx] *= fade_out * 0.95  # 5% to 100%
            left_channel[end_idx:2*transition_frames + start_idx] *= fade_in * 0.95
        
        left_channel = np.clip(left_channel, -32768, 32767)
        right_channel = np.clip(right_channel, -32768, 32767)
    
    elif pattern == "Random Pan":
        panning = np.random.uniform(-1, 1, len(samples))  # Random panning values between -1 and 1
        left_channel = samples[:, 0] * (0.5 * (1 + panning))
        right_channel = samples[:, 1] * (0.5 * (1 - panning))
    
    elif pattern == "Delay Effect":
        delay_time = 0.2  # Delay in seconds
        delay_samples = int(sample_rate * delay_time)
        left_channel = np.pad(samples[:, 0], (delay_samples, 0))[:len(samples)]
        right_channel = np.pad(samples[:, 1], (0, delay_samples))[:len(samples)]
    
    elif pattern == "Random Delay":
        delay_time = np.random.uniform(0, 0.5)  # Random delay between 0 and 0.5 seconds
        delay_samples = int(sample_rate * delay_time)
        right_channel = np.pad(samples[:, 1], (delay_samples, 0))[:len(samples)]
        left_channel = samples[:, 0]
    
    elif pattern == "Pulse Effect":
        pulse_duration = 0.5  # Duration of the pulse in seconds
        pulse_samples = int(sample_rate * pulse_duration)
        pulse = np.concatenate([
            np.ones(pulse_samples),
            np.zeros(pulse_samples)
        ])
        pulse = np.tile(pulse, len(samples) // (2 * pulse_samples) + 1)[:len(samples)]
        left_channel = samples[:, 0] * pulse
        right_channel = samples[:, 1] * np.flip(pulse)
    
    elif pattern == "Echo Effect":
        echo_delay = 0.3  # Echo delay in seconds
        echo_samples = int(sample_rate * echo_delay)
        echo = np.pad(samples, ((echo_samples, 0), (0, 0)), mode='constant', constant_values=0)[:len(samples)]
        left_channel = samples[:, 0] + 0.5 * echo[:, 0]
        right_channel = samples[:, 1] + 0.5 * echo[:, 1]
    
    else:  # Default to Circular
        angle = 2.0 * np.pi * t * speed
        left_channel = samples[:, 0] * (0.5 * (1 + np.cos(angle)))
        right_channel = samples[:, 1] * (0.5 * (1 + np.sin(angle)))
    
    processed_samples = np.array([left_channel, right_channel]).T.astype(np.int16)
    
    converted_audio = AudioSegment(
        processed_samples.tobytes(),
        frame_rate=sample_rate,
        sample_width=audio.sample_width,
        channels=2
    )
    
    # Save converted audio to the selected file path
    converted_audio.export(output_path, format="wav")
    messagebox.showinfo("Success", f"Audio converted and saved as {output_path}")

# GUI setup
root = tk.Tk()
root.title("Audio Converter")

# Set the window icon
root.iconbitmap('favicon.ico')  # Ensure 'favicon.ico' is in the same directory as your script

# Apply the theme
style = Style(theme='cosmo')  # Choose a theme such as 'darkly', 'cyborg', etc.

# Customize widget styles
style.configure('TButton',
                font=('ubuntu', 12),
                padding=6,
                relief='flat')

style.map('TButton',
          background=[('active', '#007bff')],
          foreground=[('active', 'white')])

style.configure('TLabel',
                font=('ubuntu', 10),  # Set label font to regular (not bold)
                background='white',
                foreground='#333',)

style.configure('TScale',
                background='white',
                troughcolor='#f0f0f0',
                slidercolor='#007bff')

style.configure('TCombobox',
                font=('ubuntu', 12),
                padding=6)

# Main labels customization
style.configure('Bold.TLabel',
                font=('ubuntu', 12, 'bold'),  # Set main labels font to bold
                background='white',
                foreground='#333')

frame = ttk.Frame(root, padding="10")
frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

# Layout and alignment for widgets
label = ttk.Label(frame, text="Upload Audio File:", style='Bold.TLabel')
label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

entry_file_path = ttk.Entry(frame, width=50)
entry_file_path.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

btn_upload = ttk.Button(frame, text="Browse", command=upload_file)
btn_upload.grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)

btn_convert = ttk.Button(frame, text="Convert to 3D/8D", command=convert_audio)
btn_convert.grid(row=1, column=0, columnspan=3, pady=20, sticky=tk.W)

# Add scale for speed control
label_speed = ttk.Label(frame, text="Adjust Speed:", style='Bold.TLabel')
label_speed.grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)

speed_scale = ttk.Scale(frame, from_=0.01, to=1.5, orient='horizontal', length=300, command=update_speed_label)
speed_scale.set(0.1)  # Default speed
speed_scale.grid(row=2, column=1, columnspan=2, padx=5, pady=5, sticky=tk.W)

# Add label to display current speed
speed_label_var = tk.StringVar()
speed_label_var.set("Speed: 1")
speed_label = ttk.Label(frame, textvariable=speed_label_var)
speed_label.grid(row=3, column=0, columnspan=3, sticky=tk.W, padx=5)

# Add pattern selection
label_pattern = ttk.Label(frame, text="Select Pattern:", style='Bold.TLabel')
label_pattern.grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)

pattern_var = tk.StringVar()
pattern_combobox = ttk.Combobox(frame, textvariable=pattern_var)
pattern_combobox['values'] = (
    "Circular", "Sine", "Smooth Right-Left", 
    "Random Pan", "Delay Effect", 
    "Random Delay", "Pulse Effect", 
    "Echo Effect"
)
pattern_combobox.current(0)
pattern_combobox.grid(row=4, column=1, columnspan=2, padx=5, pady=5, sticky=tk.W)

root.mainloop()
