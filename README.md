# Company Expense Tracker

A desktop application to track and analyze company expenses using OCR, voice commands, and AI insights.

## Features

- Upload and scan bills using OCR (Tesseract)
- Add/view expenses using voice commands 
- View monthly and category-wise charts
- Generate and save QR codes for any expense entry
- Get AI-powered summaries using Groq API
- CEO Dashboard with key insights

## Technologies Used

- Python (Tkinter)
- pytesseract for OCR
- speech_recognition for voice input
- matplotlib for graphs
- Groq API for AI
- dotenv for API key management
- qrcode for generating QR codes
  
## How to Run

1. Install requirements:
pip install -r requirements.txt

2. Set your environment variables in a `.env` file:
GROQ_API_KEY=your_key_here

3. Make sure Tesseract OCR is installed on your system.

4. Run the app:
python project.py

## Project Structure

- `project.py` - Main 
- `requirements.txt` - requirements
- `.env` - API's
