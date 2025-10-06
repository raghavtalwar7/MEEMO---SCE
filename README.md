# MEEMO---SCE

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up API Key
Add the api key in `.env` file in the project folder:
```
PERPLEXITY_API_KEY=api_key_here
```

### 3. Add Patient Images
Add photos toh the ```patient_images``` folder

### 4. Run the Application
```bash
python test.py
```

## 🧪 How to Test

1. **Enter patient name** (e.g., "your name")
2. **Select an image** from the list
3. **Click "🎤 Start Conversation"**
4. **Speak when prompted**
5. **Try different photo types**:
   - Family photos
   - Pet photos  
   - Travel memories
   - Childhood pictures
6. **Test memory recall** with "Recall Memory Button"

## 🎯 Features Implemented

✅ **Natural conversation flow** - Asks one question at a time \
✅ **Patient-controlled** - Choose when to stop sharing memories \
✅ **Universal** - Works with ANY photo topic \
✅ **AI-powered summaries** - Creates natural memory notes \
✅ **Easy recall** - Listen to saved memories

## 🛠️ Troubleshooting

- **Microphone not working?** Check system audio settings
- **API errors?** Verify your PERPLEXITY_API_KEY is correct
- **No images showing?** Ensure patient_images/ has JPG/PNG files
- **Installation issues?** Make sure all packages are installed

## 📂 Project Structure

- `test.py` - Main application
- `requirements.txt` - Dependencies
- `.env` - API key storage
- `patient_images/` - Folder for patient photos
- `patient_memories.xlsx` - Saved memories (auto-created)