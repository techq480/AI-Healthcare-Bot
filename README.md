# Healthcare AI Chatbot

A web-based healthcare chatbot powered by DeepSeek AI that provides medical information and advice through an intuitive chat interface.

## Features

- 💬 Interactive chat interface with conversation history
- 🤖 AI-powered responses using DeepSeek API
- 💾 SQLite database for persistent chat storage
- 🔄 Multiple chat sessions support
- 🎨 Clean, modern UI

## Prerequisites

- Python 3.7+
- DeepSeek API key

## Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd "all new cb"
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # or
   venv\Scripts\activate  # On Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   
   Create a `.env` file in the root directory or export the variable:
   ```bash
   export DEEPSEEK_API_KEY='your-deepseek-api-key-here'
   ```

   Or on Windows:
   ```cmd
   set DEEPSEEK_API_KEY=your-deepseek-api-key-here
   ```

## Running the Application

1. **Navigate to the backend directory**
   ```bash
   cd backend
   ```

2. **Run the Flask server**
   ```bash
   python app.py
   ```

3. **Access the application**
   
   Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

## Project Structure

```
.
├── backend/
│   ├── app.py          # Flask application and API endpoints
│   └── schema.sql      # Database schema
├── healthcare-bot.html # Frontend interface
├── requirements.txt    # Python dependencies
├── .gitignore         # Git ignore rules
└── README.md          # This file
```

## API Endpoints

- `GET /` - Serves the main HTML interface
- `GET /api/chats` - Retrieves all chat sessions
- `POST /api/chats` - Creates a new chat session
- `GET /api/chats/<chat_id>/messages` - Gets messages for a specific chat
- `POST /api/chats/<chat_id>/messages` - Sends a message and receives AI response
- `DELETE /api/chats` - Clears all conversations

## Database

The application uses SQLite with the following tables:
- `chats` - Stores chat session metadata
- `messages` - Stores individual messages with timestamps

The database file (`healthcare_bot.db`) is automatically created on first run.

## Important Notes

⚠️ **Disclaimer**: This chatbot is for informational purposes only and should not replace professional medical advice. Always consult with a qualified healthcare provider for medical concerns.

## License

MIT License
