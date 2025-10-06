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
import re

# Load environment variables
load_dotenv()

class GeneralizedDementiaCareAgent:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("PERPLEXITY_API_KEY")
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.model = "sonar-pro"

        # Initialize pygame for audio playback
        pygame.mixer.init()
        self.temp_dir = tempfile.mkdtemp()

        # Speech recognition setup
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self._calibrate_microphone()

        # Setup folders and files
        self.images_folder = "patient_images"
        Path(self.images_folder).mkdir(exist_ok=True)

        self.memories_file = "patient_memories.xlsx"
        self._init_memory_file()

        print("🎤 System ready! Put JPG/PNG images in 'patient_images' folder")
        print("🌟 Works with ANY photo topic: family, pets, travel, celebrations!")

    def _calibrate_microphone(self):
        """Calibrate microphone for ambient noise"""
        print("🎤 Calibrating microphone...")
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
            print("✅ Microphone ready")
        except Exception as e:
            print(f"⚠️ Microphone issue: {e}")

    def _init_memory_file(self):
        """Initialize Excel file for memories"""
        if not Path(self.memories_file).exists():
            df = pd.DataFrame(columns=[
                'image_filename', 'patient_name', 'memory_note', 
                'created_date', 'conversation_id'
            ])
            df.to_excel(self.memories_file, index=False)
            print("📊 Memory file created: patient_memories.xlsx")

    def speak(self, text):
        """Speak using Google Text-to-Speech"""
        print(f"🔊 AI: {text}")

        try:
            # Generate speech using gTTS
            tts = gTTS(text=text, lang='en', slow=False)

            # Save to temporary file
            temp_file = os.path.join(self.temp_dir, f"speech_{uuid.uuid4().hex[:8]}.mp3")
            tts.save(temp_file)

            # Play audio using pygame
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()

            # Wait for playback to finish
            while pygame.mixer.music.get_busy():
                pygame.time.wait(100)

            # Clean up temporary file
            try:
                os.remove(temp_file)
            except:
                pass

        except Exception as e:
            print(f"🔊 TTS Error: {e}")
            print("(AI would speak this text)")

    def listen(self, timeout=25):
        """Listen to patient speech with longer timeout for elderly patients"""
        try:
            print("🎤 Listening... (speak now - take your time)")
            with self.microphone as source:
                # Longer phrase time limit for complete sentences
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
        """Get list of images in the patient_images folder"""
        extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
        images = []

        for file in Path(self.images_folder).iterdir():
            if file.suffix.lower() in extensions:
                images.append(file.name)

        return sorted(images)

    def start_conversation(self, patient_name, image_filename):
        """Start interactive conversation about an image - GENERALIZED for ANY topic"""

        print(f"\n🖼️ Starting conversation about: {image_filename}")
        print(f"👤 Patient: {patient_name}")

        # Check if there's already a memory for this image
        memories_df = pd.read_excel(self.memories_file)
        existing_memory = memories_df[
            (memories_df['image_filename'] == image_filename) & 
            (memories_df['patient_name'] == patient_name)
        ]

        if not existing_memory.empty:
            existing_note = existing_memory.iloc[0]['memory_note']
            self.speak(f"I remember we talked about this photo before. {existing_note}")
            self.speak("Would you like to share anything new about this photo?")

        # Start the conversation
        image_display_name = image_filename.replace('_', ' ').replace('.jpg', '').replace('.png', '').replace('.jpeg', '')
        self.speak(f"I'd love to hear about this photo")

        conversation_id = str(uuid.uuid4())[:8]

        # Store patient responses for memory creation
        patient_responses = []

        # GENERALIZED conversation flow
        conversation_questions = [
            "Tell me, what do you see in this photo? Take your time.",
            "That's wonderful. Can you tell me more about what you remember from this moment?",
            "Thank you for sharing that. What feelings does this photo bring up for you?"
        ]

        question_index = 0
        meaningful_responses = 0
        max_responses = 3

        # Start with first question
        self.speak(conversation_questions[0])
        question_index += 1

        # Conversation loop with better timing
        while meaningful_responses < max_responses:
            # Listen to patient with longer timeout
            patient_response = self.listen(timeout=30)  # 30 seconds for elderly patients

            if patient_response == "TIMEOUT":
                self.speak("I'm here whenever you're ready. Take all the time you need.")
                continue
            elif patient_response == "UNCLEAR":
                self.speak("I didn't quite catch that. Could you repeat it for me?")
                continue
            elif patient_response == "ERROR":
                self.speak("Let me try listening again. Please go ahead.")
                continue

            # Store patient response for memory creation
            patient_responses.append(patient_response)
            meaningful_responses += 1
            print(f"📊 Meaningful responses collected: {meaningful_responses}/{max_responses}")

            # Check if patient wants to stop early
            stop_words = ["done", "finished", "stop", "enough", "that's all", "no more", "bye", "goodbye"]
            if any(word in patient_response.lower() for word in stop_words):
                print("🛑 Patient wants to end conversation")
                break

            # Ask next question if available and not at limit
            if question_index < len(conversation_questions) and meaningful_responses < max_responses:
                self.speak(conversation_questions[question_index])
                question_index += 1

        if meaningful_responses >= max_responses:
            self.speak("You've shared some beautiful memories with me. Would you like to tell me more about this photo, or should I save what you've shared?")

            # Listen for their choice
            choice_response = self.listen(timeout=20)

            if choice_response not in ["TIMEOUT", "UNCLEAR", "ERROR"]:
                continue_words = ["more", "continue", "tell", "talk", "yes", "keep going", "another"]
                if any(word in choice_response.lower() for word in continue_words):
                    # IMPROVED: Dynamic continuation loop
                    self.speak("I'd love to hear more. What else can you tell me about this photo?")

                    # Keep asking until patient decides to stop
                    while True:
                        additional_response = self.listen(timeout=30)

                        # Handle speech recognition issues
                        if additional_response == "TIMEOUT":
                            self.speak("Take your time, I'm here when you're ready.")
                            continue
                        elif additional_response == "UNCLEAR":
                            self.speak("I didn't quite catch that. Could you repeat it?")
                            continue
                        elif additional_response == "ERROR":
                            self.speak("Let me try listening again.")
                            continue

                        # Add their meaningful response
                        patient_responses.append(additional_response)
                        print(f"📊 Added response: {additional_response}")

                        # Check if they explicitly want to stop
                        stop_words = ["done", "finished", "stop", "enough", "that's all", "no more", "bye", "goodbye", "save"]
                        if any(word in additional_response.lower() for word in stop_words):
                            self.speak("Thank you for sharing all those wonderful memories with me.")
                            break

                        # Thank them and ask if they want to continue
                        self.speak("That's wonderful, thank you for sharing.")
                        self.speak("Would you like to tell me more about this photo, or are you ready for me to save these memories?")

                        # Listen for their decision
                        continue_decision = self.listen(timeout=20)

                        if continue_decision in ["TIMEOUT", "UNCLEAR", "ERROR"]:
                            # If unclear, default to saving
                            self.speak("I'll save what you've shared with me.")
                            break

                        # Check if they want to continue or stop
                        if any(word in continue_decision.lower() for word in continue_words):
                            self.speak("Wonderful! What else would you like to share about this photo?")
                            # Continue the loop for another response
                        else:
                            # They want to stop/save
                            self.speak("Thank you for sharing all those beautiful memories.")
                            break

        print("🔄 Creating generalized memory from conversation...")
        memory_text = self._create_generalized_memory(patient_responses, image_filename, patient_name)

        # Save memory
        self.speak("Thank you for sharing those wonderful memories with me. I'll save them so we can remember together.")
        success = self._save_memory(patient_name, image_filename, memory_text, conversation_id)

        if success:
            print("💾 Memory successfully saved!")
        else:
            print("❌ Failed to save memory")

        print("✅ Conversation completed!")
        return conversation_id

    def _create_generalized_memory(self, responses, image_filename, patient_name):
        """AI-powered natural memory creation - works for ANY topic"""
        if not responses:
            return "We looked at this photo together."

        print(f"📝 Creating AI-powered memory from: {responses}")

        # Filter meaningful responses
        meaningful_responses = []
        for response in responses:
            cleaned = response.strip()
            control_phrases = ['save', 'done', 'finished', 'want to save', 'now i want']
            is_control = any(phrase in cleaned.lower() for phrase in control_phrases)

            if not is_control and len(cleaned) > 3:
                meaningful_responses.append(cleaned)

        if not meaningful_responses:
            return "We had a conversation about this photo."

        # Prepare patient responses for AI
        patient_text = " | ".join(meaningful_responses)

        # Prompt for natural memory creation  
        prompt = f"""Create a natural, conversational summary of what this patient shared about their photo.

    Patient said: {patient_text}

    Write a warm summary as if gently telling the patient what they shared. Use "you" and make it flow naturally. Don't use bullet points or formal language.

    Examples:
    - "I was happy in Austria, it was cold, I made snowman" → "You were happy in Austria even though it was cold. You had fun making a snowman."
    - "My dog Max loved playing" → "You have wonderful memories of your dog Max who loved playing."

    Keep it natural and caring, 2-3 sentences maximum."""

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            data = {
                "model": "sonar-pro",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 150
            }

            response = requests.post(self.base_url, headers=headers, json=data)
            response.raise_for_status()

            ai_summary = response.json()["choices"][0]["message"]["content"].strip()

            # Clean up response
            if ai_summary.startswith('"') and ai_summary.endswith('"'):
                ai_summary = ai_summary[1:-1]
            if not ai_summary.endswith('.'):
                ai_summary += '.'

            print(f"📝 AI created: {ai_summary}")
            return ai_summary

        except Exception as e:
            print(f"❌ AI failed ({e}), using fallback")
            # Simple fallback
            if len(meaningful_responses) == 1:
                return f"You shared: {meaningful_responses[0]}"
            else:
                return f"You told me about {meaningful_responses[0].lower()} and {meaningful_responses[1].lower()}"

    def _save_memory(self, patient_name, image_filename, memory_note, conversation_id):
        """Save memory to Excel file"""
        try:
            print(f"💾 Attempting to save memory...")
            print(f"   Patient: {patient_name}")
            print(f"   Image: {image_filename}")
            print(f"   Memory: {memory_note[:100]}...")

            memories_df = pd.read_excel(self.memories_file)
            print(f"   Current memories count: {len(memories_df)}")

            # Remove any existing memory for same patient/image
            before_count = len(memories_df)
            memories_df = memories_df[~(
                (memories_df['image_filename'] == image_filename) & 
                (memories_df['patient_name'] == patient_name)
            )]
            after_count = len(memories_df)
            if before_count != after_count:
                print(f"   Replaced existing memory: {before_count} -> {after_count}")

            # Add new memory
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
        """Recall and speak a saved memory in natural, conversational way"""
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

            # NATURAL RECALL - speak directly to patient in conversational way
            image_display_name = image_filename.replace('_', ' ').replace('.jpg', '').replace('.png', '').replace('.jpeg', '')
            self.speak(f"I remember when we talked about this photo on {created_date[:10]}.")
            self.speak(memory_note)

            return memory_note

        except Exception as e:
            print(f"❌ Error recalling memory: {e}")
            self.speak("I'm having trouble accessing the memories right now.")
            return None

# GUI Application
class DementiaCareGUI:
    def __init__(self):
        self.agent = GeneralizedDementiaCareAgent()

        # Create main window
        self.root = tk.Tk()
        self.root.title("Dementia Memory Assistant - Universal System")
        self.root.geometry("800x600")

        # Set window icon and styling
        try:
            self.root.configure(bg='#f0f0f0')
        except:
            pass

        self.create_widgets()

    def create_widgets(self):
        # Title
        title_label = tk.Label(self.root, text="Dementia Memory Assistant", 
                font=("Arial", 18, "bold"), bg='#f0f0f0', fg='#2c3e50')
        title_label.pack(pady=15)

        subtitle_label = tk.Label(self.root, text="Universal System - Works with ANY photo topic", 
                font=("Arial", 10, "italic"), bg='#f0f0f0', fg='#7f8c8d')
        subtitle_label.pack(pady=(0,10))

        # Patient name input
        patient_frame = tk.Frame(self.root, bg='#f0f0f0')
        patient_frame.pack(pady=15)

        tk.Label(patient_frame, text="Patient Name:", font=("Arial", 12, "bold"), 
                bg='#f0f0f0').pack(side=tk.LEFT)
        self.patient_var = tk.StringVar()
        self.patient_entry = tk.Entry(patient_frame, textvariable=self.patient_var, 
                                    width=25, font=("Arial", 12))
        self.patient_entry.pack(side=tk.LEFT, padx=10)

        # Instructions
        instructions_frame = tk.Frame(self.root, bg='#e8f4f8', relief=tk.RAISED, bd=1)
        instructions_frame.pack(pady=10, padx=20, fill=tk.X)

        instructions = tk.Label(instructions_frame, 
                               text="📁 Put JPG/PNG images in 'patient_images' folder\n" +
                                    "🌟 Works with: Family photos, pets, vacations, celebrations, school memories, etc.\n" +
                                    "🖼️ Select image below and start conversation",
                               font=("Arial", 10), fg="#2c3e50", bg='#e8f4f8')
        instructions.pack(pady=10)

        # Images list
        tk.Label(self.root, text="Available Images:", font=("Arial", 12, "bold"), 
                bg='#f0f0f0').pack(pady=(15,5))

        images_frame = tk.Frame(self.root)
        images_frame.pack(fill=tk.BOTH, expand=True, padx=20)

        # Listbox with scrollbar
        scrollbar = tk.Scrollbar(images_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.images_listbox = tk.Listbox(images_frame, yscrollcommand=scrollbar.set,
                                       font=("Arial", 11), height=12,
                                       selectbackground='#3498db', selectforeground='white')
        self.images_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.images_listbox.yview)

        # Buttons
        button_frame = tk.Frame(self.root, bg='#f0f0f0')
        button_frame.pack(pady=20)

        tk.Button(button_frame, text="🔄 Refresh Images", 
                 command=self.refresh_images, font=("Arial", 10),
                 bg='#95a5a6', fg='white', padx=10).pack(side=tk.LEFT, padx=8)

        tk.Button(button_frame, text="🎤 Start Conversation", 
                 command=self.start_conversation, 
                 bg="#27ae60", fg="white", font=("Arial", 11, "bold"),
                 padx=15).pack(side=tk.LEFT, padx=8)

        tk.Button(button_frame, text="🧠 Recall Memory", 
                 command=self.recall_memory,
                 bg="#3498db", fg="white", font=("Arial", 11, "bold"),
                 padx=15).pack(side=tk.LEFT, padx=8)

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready! Enter patient name, select image, and start conversation.")
        status_bar = tk.Label(self.root, textvariable=self.status_var, 
                            relief=tk.SUNKEN, anchor=tk.W, font=("Arial", 9),
                            bg='#ecf0f1', fg='#2c3e50')
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Load images initially
        self.refresh_images()

    def refresh_images(self):
        """Refresh the images list"""
        self.images_listbox.delete(0, tk.END)
        images = self.agent.get_images()

        if not images:
            self.images_listbox.insert(tk.END, "No images found - add JPG/PNG files to 'patient_images' folder")
            self.status_var.set("No images found. Add JPG/PNG files to 'patient_images' folder.")
        else:
            for img in images:
                self.images_listbox.insert(tk.END, img)
            self.status_var.set(f"Found {len(images)} images. Works with any topic: family, pets, travel, celebrations!")

    def start_conversation(self):
        """Start conversation with selected image"""
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

        self.status_var.set(f"Starting conversation about {image_filename}...")
        self.root.update()

        # Run conversation in separate thread to avoid blocking GUI
        def run_conversation():
            try:
                self.agent.start_conversation(patient_name, image_filename)
                self.status_var.set("✅ Conversation completed and memory saved!")
            except Exception as e:
                self.status_var.set(f"❌ Error: {str(e)}")
                print(f"Conversation error: {e}")

        thread = threading.Thread(target=run_conversation, daemon=True)
        thread.start()

    def recall_memory(self):
        """Recall memory for selected image"""
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
        """Start the GUI"""
        self.root.mainloop()

# Main execution
if __name__ == "__main__":
    print("MEEMO")
    print("=" * 60)

    try:
        # Check if API key is set
        if not os.getenv("PERPLEXITY_API_KEY"):
            print("⚠️  WARNING: PERPLEXITY_API_KEY not set!")
            print("   Create a .env file with: PERPLEXITY_API_KEY=your_key_here")
            print("   Or set environment variable: export PERPLEXITY_API_KEY='your_key_here'")
            print()

        # Start GUI
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