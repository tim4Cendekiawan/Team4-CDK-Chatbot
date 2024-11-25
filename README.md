# Project Setup for Team4-CDK-Chatbot

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Setup Python Environment on Windows

1. **Clone the repository:**

  ```sh
  git clone https://github.com/tim4Cendekiawan/Team4-CDK-Chatbot.git
  cd Team4-CDK-Chatbot
  ```

2. **Create a virtual environment:**

  ```sh
  python -m venv env
  ```

3. **Activate the virtual environment in Powershell:**

  ```sh
  .\env\Scripts\Activate.ps1
  ```

4. **Install the required packages:**

  ```sh
  pip install -r requirements.txt
  ```

## Running the Streamlit App

1. **Copy the example environment file:**

  ```sh
  copy env.example .env
  ```

2. **Run the Streamlit app:**

  ```sh
  streamlit run main.py
  ```
