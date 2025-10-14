import os
import pandas as pd
import requests
import speech_recognition as sr
from gtts import gTTS
import pygame
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
import threading
from dotenv import load_dotenv
from PIL import Image, ImageTk


# Load environment variables
load_dotenv()


class GeneralizedDementiaCareAgent:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("PERPLEXITY_API_KEY")
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.model = "sonar-pro"

        pygame.mixer.init()
        self.temp_dir = tempfile.mkdtemp()
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self._calibrate_microphone()
        self.images_folder = "patient_images"
        Path(self.images_folder).mkdir(exist_ok=True)
        self.memories_file = "patient_memories.xlsx"
        self._init_memory_file()
        print("🎤 System ready! Put JPG/PNG images in 'patient_images' folder")
        print("🌟 Works with ANY photo topic: family, pets, travel, celebrations!")


    def _calibrate_microphone(self):
        print("🎤 Calibrating microphone...")
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
            print("✅ Microphone ready")
        except Exception as e:
            print(f"⚠️ Microphone issue: {e}")


    def _init_memory_file(self):
        if not Path(self.memories_file).exists():
            df = pd.DataFrame(columns=[
                'image_filename', 'patient_name', 'memory_note',
                'created_date', 'conversation_id'
            ])
            df.to_excel(self.memories_file, index=False)
            print("📊 Memory file created: patient_memories.xlsx")


    def speak(self, text):
        print(f"🔊 AI: {text}")
        try:
            tts = gTTS(text=text, lang='en', slow=False)
            temp_file = os.path.join(self.temp_dir, f"speech_{uuid.uuid4().hex[:8]}.mp3")
            tts.save(temp_file)
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.wait(100)
            try:
                os.remove(temp_file)
            except:
                pass
        except Exception as e:
            print(f"🔊 TTS Error: {e}")
            print("(AI would speak this text)")


    def listen(self, timeout=25):
        try:
            print("🎤 Listening... (speak now - take your time)")
            with self.microphone as source:
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=15)
            print("🔄 Processing speech...")
            text = self.recognizer.recognize_google(audio)
            print(f"👂 Patient: {text}")
            return text
        except sr.WaitTimeoutError:
            print("⏰ No speech detected (taking longer break)")
            return "TIMEOUT"
        except sr.UnknownValueError:
            print("❓ Speech unclear")
            return "UNCLEAR"
        except Exception as e:
            print(f"🎤 Speech error: {e}")
            return "ERROR"


    def get_images(self):
        extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
        images = []
        for file in Path(self.images_folder).iterdir():
            if file.suffix.lower() in extensions:
                images.append(file.name)
        return sorted(images)


    def detect_speech_emotion(self, speech_text):
        """
        Basic placeholder for speech emotion detection by keyword matching in text.
        Replace this with an actual speech emotion model for real use.
        """
        text = speech_text.lower()
        if any(word in text for word in ["sad", "unhappy", "depressed", "down", "tear"]):
            return "sad"
        elif any(word in text for word in ["happy", "joy", "glad", "delighted", "smile"]):
            return "happy"
        elif any(word in text for word in ["angry", "mad", "furious", "upset"]):
            return "angry"
        elif any(word in text for word in ["fear", "scared", "afraid", "nervous"]):
            return "fear"
        return "neutral"


    def start_conversation(self, patient_name, image_filename, on_conversation_end=None):
        try:
            save_memory = True
            sad_response_continue = False
            print(f"Starting conversation about {image_filename}")
            print(f"Patient: {patient_name}")

            self.speak(f"I'd love to hear about this photo")
            conversationid = str(uuid.uuid4())
            patientresponses = []

            conversationquestions = [
                "Tell me, what do you see in this photo? Take your time.",
                "That's wonderful. Can you tell me more about what you remember from this moment?",
                "Thank you for sharing that. What feelings does this photo bring up for you?"
            ]
            questionindex = 0
            meaningfulresponses = 0
            maxresponses = 3
            stopwords = ["done", "finished", "stop", "enough", "thats all", "no more", "bye", "goodbye", "skip", "save", "please save"]

            self.speak(conversationquestions[0])
            questionindex = 1
            while meaningfulresponses < maxresponses:
                patientresponse = self.listen(timeout=30)
                if patientresponse == "TIMEOUT":
                    self.speak("I'm here whenever you're ready. Take all the time you need.")
                    continue
                elif patientresponse == "UNCLEAR":
                    self.speak("I didn't quite catch that. Could you repeat it for me?")
                    continue
                elif patientresponse == "ERROR":
                    self.speak("Let me try listening again. Please go ahead.")
                    continue

                detectedemotion = self.detect_speech_emotion(patientresponse)
                print(f"Detected speech emotion: {detectedemotion}")

                if detectedemotion in ["sad", "angry", "fear", "frustrated"] and sad_response_continue == False:
                    self.speak("I notice this might be a difficult feeling. It's okay to take your time or skip if you want. Say 'skip' to move on or continue sharing.")
                    patience_response = self.listen(timeout=30)
                    if patience_response and any(word in patience_response.lower() for word in stopwords):
                        save_memory = False
                        self.speak("Okay, I understand. We won't save this memory. Thank you for sharing with me today. Take care!")
                        print("User chose to skip and not save")
                        print("Conversation completed!")
                        return conversationid
                    else:
                        sad_response_continue = True
                        self.speak("Thank you for continuing to share.")
                elif detectedemotion == "happy":
                    self.speak("It's lovely to hear you're feeling happy!")

                patientresponses.append(patientresponse)
                meaningfulresponses += 1
                print(f"Meaningful responses collected: {meaningfulresponses}/{maxresponses}")

                if any(word in patientresponse.lower() for word in stopwords):
                    print("Patient wants to end conversation")
                    break

                if questionindex < len(conversationquestions) and meaningfulresponses < maxresponses:
                    self.speak(conversationquestions[questionindex])
                    questionindex += 1

            if meaningfulresponses >= maxresponses and save_memory:
                self.speak("Do you want to tell me more about the photo, or should I save what you've shared?")
                final_response = self.listen(timeout=30)
                if final_response and any(word in final_response.lower() for word in stopwords):
                    self.speak("Okay, I'll save your memories now.")
                else:
                    self.speak("Okay, please go ahead and tell me more.")

                    while True:
                        more_response = self.listen(timeout=30)
                        if more_response is None:
                            self.speak("I'm here whenever you're ready.")
                            continue

                        if any(word in more_response.lower() for word in stopwords):
                            self.speak("Thanks for sharing more. I'll save your memories now.")
                            break

                        patientresponses.append(more_response)

                        self.speak("Do you want to share more or should I save?")
                        cont_resp = self.listen(timeout=30)
                        if cont_resp and any(word in cont_resp.lower() for word in stopwords):
                            self.speak("Thanks for sharing. I'll save your memories now.")
                            break
                        else:
                            self.speak("Okay, please continue.")

            if save_memory:
                print("Creating generalized memory from conversation...")
                memorytext = self._create_generalized_memory(patientresponses, image_filename, patient_name)
                self.speak("Thank you for sharing those wonderful memories with me. I'll save them so we can remember together.")
                success = self._save_memory(patient_name, image_filename, memorytext, conversationid)
                if success:
                    print("Memory successfully saved!")
                else:
                    print("Failed to save memory")

            print("Conversation completed!")
            return conversationid

        finally:
            if on_conversation_end:
                on_conversation_end()


    def _create_generalized_memory(self, responses, image_filename, patient_name, empathetic_prefix=""):
        if not responses:
            return "We looked at this photo together."
        print(f"📝 Creating AI-powered memory from: {responses}")
        meaningful_responses = []
        for response in responses:
            cleaned = response.strip()
            control_phrases = ['save', 'done', 'finished', 'want to save', 'now i want']
            is_control = any(phrase in cleaned.lower() for phrase in control_phrases)
            if not is_control and len(cleaned) > 3:
                meaningful_responses.append(cleaned)
        if not meaningful_responses:
            return "We had a conversation about this photo."
        patient_text = " | ".join(meaningful_responses)
        prompt = f"""{empathetic_prefix}

Create a natural, conversational summary of what this patient shared about their photo.

Patient said: {patient_text}

Write a warm summary as if gently telling the patient what they shared. Use "you" and make it flow naturally. Don't use bullet points or formal language.

Examples:
- "I was happy in Austria, it was cold, I made snowman" → "You were happy in Austria even though it was cold. You had fun making a snowman."
- "My dog Max loved playing" → "You have wonderful memories of your dog Max who loved playing."

Keep it natural and caring, 2-3 sentences maximum."""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            data = {
                "model": "sonar-pro",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 150
            }
            response = requests.post(self.base_url, headers=headers, json=data)
            response.raise_for_status()
            ai_summary = response.json()["choices"][0]["message"]["content"].strip()
            if ai_summary.startswith('"') and ai_summary.endswith('"'):
                ai_summary = ai_summary[1:-1]
            if not ai_summary.endswith('.'):
                ai_summary += '.'
            print(f"📝 AI created: {ai_summary}")
            return ai_summary
        except Exception as e:
            print(f"❌ AI failed ({e}), using fallback")
            if len(meaningful_responses) == 1:
                return f"You shared: {meaningful_responses[0]}"
            else:
                return f"You told me about {meaningful_responses[0].lower()} and {meaningful_responses[1].lower()}"


    def _save_memory(self, patient_name, image_filename, memory_note, conversation_id):
        try:
            print(f"💾 Attempting to save memory...")
            print(f"   Patient: {patient_name}")
            print(f"   Image: {image_filename}")
            print(f"   Memory: {memory_note[:100]}...")
            memories_df = pd.read_excel(self.memories_file)
            print(f"   Current memories count: {len(memories_df)}")
            before_count = len(memories_df)
            memories_df = memories_df[~(
                (memories_df['image_filename'] == image_filename) &
                (memories_df['patient_name'] == patient_name)
            )]
            after_count = len(memories_df)
            if before_count != after_count:
                print(f"   Replaced existing memory: {before_count} -> {after_count}")
            new_memory = {
                'image_filename': image_filename,
                'patient_name': patient_name,
                'memory_note': memory_note,
                'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'conversation_id': conversation_id
            }
            memories_df = pd.concat([memories_df, pd.DataFrame([new_memory])], ignore_index=True)
            memories_df.to_excel(self.memories_file, index=False)
            print(f"💾 Memory saved successfully! Total memories: {len(memories_df)}")
            print(f"   Saved to: {self.memories_file}")
            return True
        except Exception as e:
            print(f"❌ Error saving memory: {e}")
            return False


    def recall_memory(self, patient_name, image_filename):
        try:
            print(f"🔍 Looking for memory: {patient_name} + {image_filename}")
            memories_df = pd.read_excel(self.memories_file)
            print(f"   Total memories in file: {len(memories_df)}")
            if len(memories_df) > 0:
                print("   Existing memories:")
                for idx, row in memories_df.iterrows():
                    print(f"     {idx}: {row['patient_name']} - {row['image_filename']}")
            memory_record = memories_df[
                (memories_df['image_filename'] == image_filename) &
                (memories_df['patient_name'] == patient_name)
            ]
            if memory_record.empty:
                print("   No matching memory found")
                self.speak("We haven't talked about this photo yet. Would you like to tell me about it?")
                return None
            memory_note = memory_record.iloc[0]['memory_note']
            created_date = memory_record.iloc[0]['created_date']
            print(f"   Found memory: {memory_note[:50]}...")
            image_display_name = image_filename.replace('_', ' ').replace('.jpg', '').replace('.png', '').replace('.jpeg', '')
            self.speak(f"I remember when we talked about this photo on {created_date[:10]}.")
            self.speak(memory_note)
            return memory_note
        except Exception as e:
            print(f"❌ Error recalling memory: {e}")
            self.speak("I'm having trouble accessing the memories right now.")
            return None


class DementiaCareGUI:
    def __init__(self):
        self.agent = GeneralizedDementiaCareAgent()
        self.image_window = None
        self.root = tk.Tk()
        self.root.title("Dementia Memory Assistant - Universal System")
        self.root.geometry("800x600")
        try:
            self.root.configure(bg='#f0f0f0')
        except:
            pass
        self.create_widgets()


    def create_widgets(self):
        title_label = tk.Label(self.root, text="Dementia Memory Assistant",
                               font=("Arial", 18, "bold"), bg='#f0f0f0', fg='#2c3e50')
        title_label.pack(pady=15)
        subtitle_label = tk.Label(self.root, text="Universal System - Works with ANY photo topic",
                                 font=("Arial", 10, "italic"), bg='#f0f0f0', fg='#7f8c8d')
        subtitle_label.pack(pady=(0, 10))
        patient_frame = tk.Frame(self.root, bg='#f0f0f0')
        patient_frame.pack(pady=15)
        tk.Label(patient_frame, text="Patient Name:", font=("Arial", 12, "bold"), bg='#f0f0f0').pack(side=tk.LEFT)
        self.patient_var = tk.StringVar()
        self.patient_entry = tk.Entry(patient_frame, textvariable=self.patient_var, width=25, font=("Arial", 12))
        self.patient_entry.pack(side=tk.LEFT, padx=10)
        instructions_frame = tk.Frame(self.root, bg='#e8f4f8', relief=tk.RAISED, bd=1)
        instructions_frame.pack(pady=10, padx=20, fill=tk.X)
        instructions = tk.Label(
            instructions_frame,
            text="📁 Put JPG/PNG images in 'patient_images' folder\n"
                 "🌟 Works with: Family photos, pets, vacations, celebrations, school memories, etc.\n"
                 "🖼️ Select image below and start conversation",
            font=("Arial", 10), fg="#2c3e50", bg='#e8f4f8'
        )
        instructions.pack(pady=10)
        tk.Label(self.root, text="Available Images:", font=("Arial", 12, "bold"),
                 bg='#f0f0f0').pack(pady=(15, 5))
        images_frame = tk.Frame(self.root)
        images_frame.pack(fill=tk.BOTH, expand=True, padx=20)
        scrollbar = tk.Scrollbar(images_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.images_listbox = tk.Listbox(
            images_frame, yscrollcommand=scrollbar.set,
            font=("Arial", 11), height=12,
            selectbackground='#3498db', selectforeground='white'
        )
        self.images_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.images_listbox.yview)
        button_frame = tk.Frame(self.root, bg='#f0f0f0')
        button_frame.pack(pady=20)
        tk.Button(
            button_frame, text="🔄 Refresh Images",
            command=self.refresh_images, font=("Arial", 10),
            bg='#95a5a6', fg='white', padx=10
        ).pack(side=tk.LEFT, padx=8)
        tk.Button(
            button_frame, text="🎤 Start Conversation",
            command=self.start_conversation,
            bg="#27ae60", fg="white", font=("Arial", 11, "bold"),
            padx=15
        ).pack(side=tk.LEFT, padx=8)
        tk.Button(
            button_frame, text="🧠 Recall Memory",
            command=self.recall_memory,
            bg="#3498db", fg="white", font=("Arial", 11, "bold"),
            padx=15
        ).pack(side=tk.LEFT, padx=8)
        self.status_var = tk.StringVar()
        self.status_var.set("Ready! Enter patient name, select image, and start conversation.")
        status_bar = tk.Label(
            self.root, textvariable=self.status_var,
            relief=tk.SUNKEN, anchor=tk.W, font=("Arial", 9),
            bg='#ecf0f1', fg='#2c3e50'
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.refresh_images()


    def refresh_images(self):
        self.images_listbox.delete(0, tk.END)
        images = self.agent.get_images()
        if not images:
            self.images_listbox.insert(tk.END, "No images found - add JPG/PNG files to 'patient_images' folder")
            self.status_var.set("No images found. Add JPG/PNG files to 'patient_images' folder.")
        else:
            for img in images:
                self.images_listbox.insert(tk.END, img)
            self.status_var.set(f"Found {len(images)} images. Works with any topic: family, pets, travel, celebrations!")


    def show_image_window(self, image_filename):
        image_path = os.path.join(self.agent.images_folder, image_filename)
        try:
            img = Image.open(image_path)
            img.thumbnail((480, 380))
            self.image_window = tk.Toplevel(self.root)
            self.image_window.title(f"Viewing Image: {image_filename}")
            self.image_window.geometry("500x420")
            self.image_window.configure(bg='#fff')
            photo = ImageTk.PhotoImage(img)
            img_label = tk.Label(self.image_window, image=photo, bg='#fff')
            img_label.image = photo
            img_label.pack(expand=True, fill=tk.BOTH)
            tk.Label(self.image_window, text="Describe what you see!",
                     font=("Arial", 13), bg='#fff').pack(pady=5)
        except Exception as e:
            messagebox.showerror("Error", f"Could not display image: {e}")


    def close_image_window(self):
        if self.image_window is not None:
            try:
                self.root.after(0, self.image_window.destroy)
            except:
                pass
            self.image_window = None


    def start_conversation(self):
        patient_name = self.patient_var.get().strip()
        selection = self.images_listbox.curselection()
        if not patient_name:
            messagebox.showerror("Error", "Please enter patient name")
            return
        if not selection:
            messagebox.showerror("Error", "Please select an image")
            return
        selected_text = self.images_listbox.get(selection[0])
        if "No images found" in selected_text:
            messagebox.showerror("Error", "No images available. Add images to 'patient_images' folder.")
            return
        image_filename = selected_text
        self.show_image_window(image_filename)
        self.status_var.set(f"Starting conversation about {image_filename}...")
        self.root.update()

        def run_conversation():
            try:
                self.agent.start_conversation(patient_name, image_filename, on_conversation_end=self.close_image_window)
                self.status_var.set("✅ Conversation completed and memory saved!")
            except Exception as e:
                self.status_var.set(f"❌ Error: {str(e)}")
                print(f"Conversation error: {e}")

        thread = threading.Thread(target=run_conversation, daemon=True)
        thread.start()


    def recall_memory(self):
        patient_name = self.patient_var.get().strip()
        selection = self.images_listbox.curselection()
        if not patient_name:
            messagebox.showerror("Error", "Please enter patient name")
            return
        if not selection:
            messagebox.showerror("Error", "Please select an image")
            return
        image_filename = self.images_listbox.get(selection[0])
        if "No images found" in image_filename:
            messagebox.showerror("Error", "No images available.")
            return

        def run_recall():
            try:
                memory = self.agent.recall_memory(patient_name, image_filename)
                if memory:
                    self.status_var.set(f"✅ Recalled memory for {image_filename}")
                else:
                    self.status_var.set(f"No memory found for {image_filename}")
            except Exception as e:
                self.status_var.set(f"❌ Error: {str(e)}")
                print(f"Recall error: {e}")

        thread = threading.Thread(target=run_recall, daemon=True)
        thread.start()


    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    print("MEEMO")
    print("=" * 60)
    try:
        if not os.getenv("PERPLEXITY_API_KEY"):
            print("⚠️  WARNING: PERPLEXITY_API_KEY not set!")
            print("   Create a .env file with: PERPLEXITY_API_KEY=your_key_here")
            print("   Or set environment variable: export PERPLEXITY_API_KEY='your_key_here'")
            print()
        print("🚀 Starting MEEMO...")
        app = DementiaCareGUI()
        app.run()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Startup error: {e}")
        print("\nTroubleshooting:")
        print("   - Check if all packages are installed")
        print("   - Verify microphone/speaker setup")
        print("   - Ensure 'patient_images' folder has JPG/PNG files")