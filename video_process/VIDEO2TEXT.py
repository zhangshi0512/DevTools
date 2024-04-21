import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import moviepy.editor as mp
import speech_recognition as sr
import traceback
import os


class TranscriptExtractorApp:
    def __init__(self, master):
        self.master = master
        master.title("Transcript Extractor")

        # Layout configuration
        self.label = tk.Label(
            master, text="Select a video file and output format:")
        self.label.grid(columnspan=3, row=0)

        self.browse_button = tk.Button(
            master, text="Browse Video", command=self.load_video)
        self.browse_button.grid(row=1, column=0)

        self.save_button = tk.Button(
            master, text="Save As", command=self.save_file)
        self.save_button.grid(row=1, column=1)

        self.format_var = tk.StringVar(master)
        self.format_var.set("txt")  # default value
        self.format_dropdown = tk.OptionMenu(
            master, self.format_var, "txt", "srt")
        self.format_dropdown.grid(row=1, column=2)

        self.progress = ttk.Progressbar(
            master, orient='horizontal', length=200, mode='determinate')
        self.progress.grid(columnspan=3, row=2)

        self.video_path = None
        self.output_path = None

    def load_video(self):
        self.video_path = filedialog.askopenfilename(
            filetypes=[("Video files", "*.mp4;*.mkv;*.avi;*.mov")])

    def save_file(self):
        if not self.video_path:
            messagebox.showinfo("Error", "Please select a video file first.")
            return

        self.output_path = filedialog.asksaveasfilename(defaultextension="." + self.format_var.get(),
                                                        filetypes=[("Text files", "*.txt"), ("SRT files", "*.srt")])
        if self.output_path:
            self.extract_transcript()

    def extract_transcript(self):
        try:
            # Extracting audio from video
            clip = mp.VideoFileClip(self.video_path)
            audio_path = "temp_audio.wav"
            clip.audio.write_audiofile(audio_path)
            clip.close()

            # Speech to text conversion
            r = sr.Recognizer()
            with sr.AudioFile(audio_path) as source:
                audio = r.record(source)  # read the entire audio file
                try:
                    text = r.recognize_google(audio)
                except sr.UnknownValueError:
                    messagebox.showerror(
                        "Error", "Google Speech Recognition could not understand the audio.")
                    return
                except sr.RequestError as e:
                    messagebox.showerror(
                        "Error", f"Could not request results from Google Speech Recognition service; {e}")
                    return

            # Saving the transcript
            if self.format_var.get() == "txt":
                with open(self.output_path, "w") as f:
                    f.write(text)
            elif self.format_var.get() == "srt":
                import pysrt
                subs = pysrt.SubRipFile()
                subs.append(pysrt.SubRipItem(
                    1, start='00:00:00', end='23:59:59', text=text))
                subs.save(self.output_path)

            messagebox.showinfo(
                "Success", "Transcript has been successfully extracted.")
        except Exception as e:
            traceback.print_exc()
            messagebox.showerror("Error", str(e))
        finally:
            if os.path.exists(audio_path):
                os.remove(audio_path)


if __name__ == "__main__":
    root = tk.Tk()
    app = TranscriptExtractorApp(root)
    root.mainloop()
