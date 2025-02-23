Discord Bot Template
This is a Discord bot template that uses AI for conversation, web scraping, and page analysis. It is designed to be easily customizable, allowing users to define their own bot personalities.

Features
✅ AI Chatbot – Responds to user messages using an AI model.
✅ Customizable Personality – Modify the system prompt to give your bot a unique character.
✅ Web Scraping – Retrieve and analyze webpage content directly from Discord.
✅ User Chat History – Maintains per-user message history for more natural conversations.
✅ Basic Commands – Includes commands like !ping and !clear for convenience.

Setup
Prerequisites
Python 3.11+
A Discord bot token (stored in .env)
Required dependencies (requirements.txt)
Installation
Clone the repository:

git clone https://github.com/your-repo/discord_bot.git
cd discord_bot
Create and activate a virtual environment:

python3 -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
Install dependencies:

pip install -r requirements.txt
Set up environment variables:
Create a .env file in the root directory and add your Discord bot token:

env
DISCORD_TOKEN=your_discord_bot_token
Run the bot:

python discord_bot.py
Customization
Modify discord_bot.py to set a unique system prompt for your bot’s personality.
By default, the chatbot operates without a system prompt, allowing full customization.
Users can integrate any AI model by changing the fallback API URL and model name.
Commands
Command	Description
!ping	Responds with "Pong!"
!clear	Clears the user's chat history
!web_scrape <url>	Scrapes text content from a webpage
!analyze <url>	Retrieves and displays webpage text for analysis
Contributing
Feel free to submit pull requests with improvements or bug fixes.

License
This project is licensed under the MIT License.

