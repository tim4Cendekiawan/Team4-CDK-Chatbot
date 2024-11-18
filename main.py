from openai import OpenAI
import tiktoken
import requests
import os
import streamlit as st

# DEFAULT_API_KEY = os.environ.get("TOGETHER_API_KEY")
DEFAULT_API_KEY = "1eda623d114fb46016f9dabdebe008383ae343c9d03f2411db22469cab5f1585"
DEFAULT_BASE_URL = "https://api.together.xyz/v1"
DEFAULT_MODEL = "meta-llama/Llama-Vision-Free"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 512
DEFAULT_TOKEN_BUDGET = 4096
DEFAULT_TOP_P = 0.7
DEFAULT_TOP_K = 50
DEFAULT_RP = "Normal"

class ConversationManager:
    def __init__(self, api_key=None, base_url=None, model=None, temperature=None, max_tokens=None, token_budget=None, top_p=None, top_k=None, rp_style=None):
        if not api_key:
            api_key = DEFAULT_API_KEY
        if not base_url:
            base_url = DEFAULT_BASE_URL
            
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.rp_style = rp_style if rp_style else DEFAULT_RP
        self.rp_add = ""
        self.top_p = top_p if top_p else DEFAULT_TOP_P
        self.top_k = top_k if top_k else DEFAULT_TOP_K
        self.model = model if model else DEFAULT_MODEL
        self.temperature = temperature if temperature else DEFAULT_TEMPERATURE
        self.max_tokens = max_tokens if max_tokens else DEFAULT_MAX_TOKENS
        self.token_budget = token_budget if token_budget else DEFAULT_TOKEN_BUDGET

        self.update_system_message()

    def update_system_message(self):
        self.system_message = f"Kamu adalah seorang dokter profesional yang dapat mendiagnosa penyakit dengan gejala yang sesuai. Kamu akan memberikan diagnosa kepada pengguna mengenai gejala yang akan ia berikan, mengurutkan penyakit penyakit yang relevan sesuai dengan jumlah gejala yang sesuai. Kamu juga akan memberikan teks bold atau tebal kepada gejala yang sesuai tersebut. Gaya kamu dalam menjawab pasien adalah {self.rp_style}. {self.rp_add}"
        self.conversation_history = [{"role": "system", "content": self.system_message}]

    

    def count_tokens(self, text):
        try:
            encoding = tiktoken.encoding_for_model(self.model)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")
        tokens = encoding.encode(text)
        return len(tokens)

    def total_tokens_used(self):
        try:
            return sum(self.count_tokens(message['content']) for message in self.conversation_history)
        except Exception as e:
            print(f"Error calculating total tokens used: {e}")
            return None
    
    def enforce_token_budget(self):
        try:
            while self.total_tokens_used() > self.token_budget:
                if len(self.conversation_history) <= 1:
                    break
                self.conversation_history.pop(1)
        except Exception as e:
            print(f"Error enforcing token budget: {e}")

    def chat_completion(self, prompt, temperature=None, max_tokens=None, model=None, top_p=None):
        temperature = temperature if temperature is not None else self.temperature
        max_tokens = max_tokens if max_tokens is not None else self.max_tokens
        top_p = top_p if top_p is not None else self.top_p
        model = model if model is not None else self.model

        self.conversation_history.append({"role": "user", "content": prompt})
        self.enforce_token_budget()

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=self.conversation_history,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=0.7,
            )
        except Exception as e:
            print(f"Error generating response: {e}")
            return None

        ai_response = response.choices[0].message.content
        self.conversation_history.append({"role": "assistant", "content": ai_response})

        return ai_response
    
    def reset_conversation_history(self):
        self.conversation_history = [{"role": "system", "content": self.system_message}]

def get_instance_id():
    """Retrieve the EC2 instance ID from AWS metadata using IMDSv2."""
    try:
        # Step 1: Get the token
        token = requests.put(
            "http://169.254.169.254/latest/api/token",
            headers={"X-aws-ec2-metadata-token-ttl-seconds": "21600"},
            timeout=1
        ).text

        # Step 2: Use the token to get the instance ID
        instance_id = requests.get(
            "http://169.254.169.254/latest/meta-data/instance-id",
            headers={"X-aws-ec2-metadata-token": token},
            timeout=1
        ).text
        return instance_id
    except requests.exceptions.RequestException:
        return "Instance ID not available (running locally or error in retrieval)"

### Streamlit code ###
st.title("Ask Doctor")

# Display EC2 Instance ID
instance_id = get_instance_id()
st.write(f"**EC2 Instance ID**: {instance_id}")

# Initialize the ConversationManager object
if 'chat_manager' not in st.session_state:
    st.session_state['chat_manager'] = ConversationManager()

chat_manager = st.session_state['chat_manager']

if 'conversation_history' not in st.session_state:
    st.session_state['conversation_history'] = chat_manager.conversation_history

conversation_history = st.session_state['conversation_history']

# Chat input from the user
user_input = st.chat_input("Write a message")

# Call the chat manager to get a response from the AI
if user_input:
    response = chat_manager.chat_completion(user_input)

# Display the conversation history
for message in conversation_history:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.write(message["content"])


sidebar_page = st.sidebar

sidebar_title = sidebar_page.write("## Chat Customization")

with sidebar_page.form("Chat Customization"):
    temp_slider = st.slider("Temperature", min_value=0.0, max_value=1.0, value=chat_manager.temperature, step=0.1)
    max_token_message = st.slider("Max Token Per Message", min_value= 0, max_value= 1500, value=chat_manager.max_tokens, step=1)
    top_p = st.slider("Top P", min_value=0.0, max_value=1.0, value=chat_manager.top_p, step=0.1)
    # top_k = st.slider("Top K", min_value=0, max_value=100, value=chat_manager.top_k, step=1)
    rp_style = st.text_input("AI Persona", placeholder="Contoh : Galak, Lemah lembut, Normal")
    rp_add = st.text_area("Additional Role Play", value=chat_manager.rp_add)
    done = st.form_submit_button("Done")
    if done:
        chat_manager.rp_style = rp_style
        chat_manager.temperature = temp_slider
        chat_manager.max_tokens = max_token_message
        chat_manager.top_p = top_p
        chat_manager.rp_add = rp_add
        
        chat_manager.update_system_message()

        st.session_state['chat_manager'] = chat_manager
        st.session_state['conversation_history'] = chat_manager.conversation_history

        st.success(f'''
        Top P = {chat_manager.top_p}\n
        Temperature = {chat_manager.temperature}\n
        Max Tokens = {chat_manager.max_tokens}
        ''')
        
