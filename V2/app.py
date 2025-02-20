import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from ttkbootstrap import Style
from pydub import AudioSegment
import numpy as np
import os

# Set ffmpeg path manually (optional)
# AudioSegment.converter = r"C:\ffmpeg\bin\ffmpeg.exe"

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
    
    output_path = filedialog.asksaveasfilename(defaultextension=".wav", filetypes=[("WAV files", "*.wav")])
    if not output_path:
        return  # User canceled the dialog
    
    # Loading the audio file
    audio = AudioSegment.from_file(file_path)
    sample_rate = audio.frame_rate

    # Ensure audio is in stereo format
    samples = np.array(audio.get_array_of_samples())

    if audio.channels == 2:
        samples = samples.reshape((-1, 2))  # Stereo
    else:
        samples = np.column_stack((samples, samples))  # Convert mono to stereo

    # Normalize samples
    samples = samples.astype(np.float64) / np.iinfo(np.int16).max

    # Get selected pattern
    pattern = pattern_var.get()
    speed = speed_scale.get()
    
    # Apply effect based on the selected pattern
    duration = len(audio) / 1000.0
    t = np.linspace(0, duration, len(samples))

    if pattern == "Circular":
        angle = 2.0 * np.pi * t * speed
        left_channel = samples[:, 0] * (0.5 * (1 + np.cos(angle)))
        right_channel = samples[:, 1] * (0.5 * (1 + np.sin(angle)))

    elif pattern == "Sine":
        angle = 2.0 * np.pi * t * speed
        left_channel = samples[:, 0] * (0.5 * (1 + np.sin(angle)))
        right_channel = samples[:, 1] * (0.5 * (1 - np.sin(angle)))

    elif pattern == "Random Pan":
        panning = np.random.uniform(-1, 1, len(samples))
        left_channel = samples[:, 0] * (0.5 * (1 + panning))
        right_channel = samples[:, 1] * (0.5 * (1 - panning))

    elif pattern == "Echo Effect":
        echo_delay = 0.3
        echo_samples = int(sample_rate * echo_delay)
        echo = np.pad(samples, ((echo_samples, 0), (0, 0)), mode='constant', constant_values=0)[:len(samples)]
        left_channel = samples[:, 0] + 0.5 * echo[:, 0]
        right_channel = samples[:, 1] + 0.5 * echo[:, 1]

    else:  # Default to Circular
        angle = 2.0 * np.pi * t * speed
        left_channel = samples[:, 0] * (0.5 * (1 + np.cos(angle)))
        right_channel = samples[:, 1] * (0.5 * (1 + np.sin(angle)))

    # Convert back to int16 and prevent clipping
    processed_samples = np.clip(np.array([left_channel, right_channel]).T * np.iinfo(np.int16).max, 
                                np.iinfo(np.int16).min, np.iinfo(np.int16).max).astype(np.int16)

    # Create output audio segment
    converted_audio = AudioSegment(
        processed_samples.tobytes(),
        frame_rate=sample_rate,
        sample_width=2,  # 16-bit PCM
        channels=2
    )

    # Save converted audio
    converted_audio.export(output_path, format="wav")
    messagebox.showinfo("Success", f"Audio converted and saved as {output_path}")

# GUI setup
root = tk.Tk()
root.title("Audio Converter")

# Handle missing favicon.ico
try:
    root.iconbitmap(os.path.join(os.path.dirname(__file__), "favicon.ico"))
except tk.TclError:
    print("Warning: Icon file not found! Using default Tkinter icon.")

# Apply the theme
style = Style(theme='cyborg')

frame = ttk.Frame(root, padding="10")
frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

# File selection
label = ttk.Label(frame, text="Upload Audio File:")
label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

entry_file_path = ttk.Entry(frame, width=50)
entry_file_path.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

btn_upload = ttk.Button(frame, text="Browse", command=upload_file)
btn_upload.grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)

# Convert Button
btn_convert = ttk.Button(frame, text="Convert to 3D/8D", command=convert_audio)
btn_convert.grid(row=1, column=0, columnspan=3, pady=20, sticky=tk.W)

# Speed control
speed_label_var = tk.StringVar()
speed_label_var.set("Speed: 1")

label_speed = ttk.Label(frame, text="Adjust Speed:")
label_speed.grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)

speed_scale = ttk.Scale(frame, from_=0.01, to=1.5, orient='horizontal', length=300, command=update_speed_label)
speed_scale.set(0.1)
speed_scale.grid(row=2, column=1, columnspan=2, padx=5, pady=5, sticky=tk.W)

speed_label = ttk.Label(frame, textvariable=speed_label_var)
speed_label.grid(row=3, column=0, columnspan=3, sticky=tk.W, padx=5)

# Pattern selection
label_pattern = ttk.Label(frame, text="Select Pattern:")
label_pattern.grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)

pattern_var = tk.StringVar()
pattern_combobox = ttk.Combobox(frame, textvariable=pattern_var)
pattern_combobox['values'] = (
    "Circular", "Sine", "Random Pan", "Echo Effect"
)
pattern_combobox.current(0)
pattern_combobox.grid(row=4, column=1, columnspan=2, padx=5, pady=5, sticky=tk.W)

root.mainloop()
