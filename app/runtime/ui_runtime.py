import os

import requests
import streamlit as st


api_base_override = os.getenv("API_BASE_URL", "").strip()
api_hostport = os.getenv("API_HOSTPORT", "").strip()

if api_base_override:
    API_BASE = api_base_override.rstrip("/")
elif api_hostport:
    if api_hostport.startswith(("http://", "https://")):
        API_BASE = api_hostport.rstrip("/")
    else:
        API_BASE = f"http://{api_hostport}".rstrip("/")
else:
    API_BASE = "http://127.0.0.1:8000"

API_URL = f"{API_BASE}/fraud"
LOGIN_URL = f"{API_BASE}/login"

GLOBAL_STYLES = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&family=Space+Grotesk:wght@400;600;700&display=swap');

html, body, [class*="css"]  {
  font-family: "Manrope", "Space Grotesk", sans-serif;
}

.stApp {
  background: radial-gradient(1200px 800px at 10% 10%, #e6f7f2 0%, #f7fbff 45%, #ffffff 100%);
}

.app-title { font-size: 36px; font-weight: 800; letter-spacing: 0.2px; margin-bottom: 6px; color: #0f2a3a; }
.app-subtitle { font-size: 15px; color: #4b6b7a; margin-bottom: 18px; }
.section-title { font-size: 20px; font-weight: 700; margin-top: 16px; color: #143347; }
.section-title { margin-bottom: 6px; }

.glass-card {
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(15, 42, 58, 0.08);
  box-shadow: 0 12px 30px rgba(15, 42, 58, 0.08);
  border-radius: 16px;
  padding: 22px;
  backdrop-filter: blur(8px);
}

.login-card {
  padding: 22px;
  border: 1px solid rgba(15, 42, 58, 0.08);
  border-radius: 16px;
  background: linear-gradient(180deg, #ffffff 0%, #f7fbff 100%);
  box-shadow: 0 18px 40px rgba(15, 42, 58, 0.12);
}

.center-wrap { display: flex; justify-content: center; }
.center-card { width: 100%; max-width: 420px; }

@keyframes floatIn {
  0% { opacity: 0; transform: translateY(10px); }
  100% { opacity: 1; transform: translateY(0); }
}

.fade-in { animation: floatIn 0.6s ease-out; }

div.stButton > button {
  background: linear-gradient(90deg, #2457c5 0%, #2e7be8 100%);
  color: #ffffff;
  border: none;
  border-radius: 10px;
  padding: 10px 16px;
  font-weight: 700;
  transition: transform 0.12s ease, box-shadow 0.12s ease;
}

div.stButton > button:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 20px rgba(36, 87, 197, 0.25);
}

div.stDownloadButton > button {
  background: linear-gradient(90deg, #0b5cab 0%, #2a7de1 100%);
  color: #ffffff;
  border: none;
  border-radius: 10px;
  padding: 8px 14px;
  font-weight: 700;
}

div.stTextInput > div > div > input {
  border-radius: 10px;
  border: 1px solid rgba(15, 42, 58, 0.15);
  padding: 10px 12px;
  background: #ffffff;
}

div[data-testid="stTextInput"] small {
  display: none;
}

div[data-testid="InputInstructions"] {
  display: none;
}

div[data-testid="stTextInput"] [data-testid="InputInstructions"] {
  display: none;
}

div[data-testid="stInfo"] {
  border-radius: 12px;
  border: 1px solid rgba(11, 92, 171, 0.15);
  background: rgba(219, 236, 255, 0.7);
}

.topbar {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-bottom: 10px;
}

.chat-row {
  display: flex;
  margin: 8px 0;
}

.chat-tight {
  margin-top: 2px;
}

.chat-left {
  justify-content: flex-start;
}

.chat-right {
  justify-content: flex-end;
}

.bubble {
  max-width: 70%;
  padding: 10px 14px;
  border-radius: 16px;
  line-height: 1.4;
  font-size: 15px;
  box-shadow: 0 8px 20px rgba(15, 42, 58, 0.08);
}

.bubble-ai {
  background: #ffffff;
  border: 1px solid rgba(15, 42, 58, 0.08);
  color: #0f2a3a;
}

.bubble-prompt {
  background: rgba(219, 236, 255, 0.7);
  border: 1px solid rgba(11, 92, 171, 0.15);
  color: #0f2a3a;
}

.bubble-user {
  background: #e8f1ff;
  border: 1px solid rgba(36, 87, 197, 0.18);
  color: #173255;
}

.input-wrap {
  display: none;
}

.chat-space {
  padding-top: 0;
  padding-bottom: 2px;
  margin-top: 0px;
}
</style>
"""


def call_fraud_api(user_id, query, session_id):
    try:
        params = {
            "userId": user_id,
            "query": query,
        }
        if session_id:
            params["sessionId"] = session_id
        response = requests.get(API_URL, params=params)
        return response.json()
    except Exception as exc:
        return {"chatbot_response": f"API Error: {str(exc)}"}


def extract_prompt(text):
    if not text:
        return "", ""

    lines = [line.strip() for line in text.split("\n") if line.strip()]
    prompt = ""

    for line in reversed(lines):
        lower_line = line.lower()
        if (
            "(Yes/No)" in line
            or line.endswith("?")
            or "provide details about the case" in lower_line
            or "describe the new fraud case" in lower_line
            or "thank you for using the sbi fraud investigation assistant" in lower_line
        ):
            prompt = line
            break

    if prompt:
        cleaned = text.replace(prompt, "").strip()
        return cleaned, prompt

    return text, ""


def initialize_session_state():
    defaults = {
        "chat_history": [],
        "user_id": "",
        "fraud_category": "",
        "session_id": "",
        "latest_documents": [],
        "next_prompt": "",
        "documents_followup_prompt": "",
        "logged_in": False,
        "login_error": "",
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_login():
    col_left, col_mid, col_right = st.columns([2, 3, 2])
    with col_mid:
        st.markdown('<div class="section-title">Login</div>', unsafe_allow_html=True)
        with st.form("login_form"):
            user_id_input = st.text_input("User ID", value=st.session_state.user_id, placeholder="Enter your user ID")
            password_input = st.text_input("Password", value="", type="password", placeholder="Enter your password")
            submit_login = st.form_submit_button("Continue")

        if submit_login:
            user_id_input = user_id_input.strip()
            password_input = password_input.strip()
            if not user_id_input or not password_input:
                st.session_state.login_error = "User ID and password are required."
            else:
                response = requests.post(
                    LOGIN_URL,
                    json={"userId": user_id_input, "password": password_input},
                )
                if response.status_code == 200:
                    st.session_state.user_id = user_id_input
                    st.session_state.logged_in = True
                    st.session_state.login_error = ""
                    st.rerun()
                else:
                    st.session_state.login_error = "Invalid user ID or password."

        if st.session_state.login_error:
            st.error(st.session_state.login_error)

    st.stop()


def render_chat_history():
    if st.session_state.next_prompt:
        last_item = st.session_state.chat_history[-1] if st.session_state.chat_history else None
        if not last_item or last_item.get("role") != "prompt" or last_item.get("content") != st.session_state.next_prompt:
            st.session_state.chat_history.append(
                {
                    "role": "prompt",
                    "content": st.session_state.next_prompt,
                }
            )
        st.session_state.next_prompt = ""

    for index, chat in enumerate(st.session_state.chat_history):
        if chat["role"] == "user":
            user_text = str(chat["content"]).replace("\n", "<br>")
            st.markdown(
                f'<div class="chat-row chat-right"><div class="bubble bubble-user">{user_text}</div></div>',
                unsafe_allow_html=True,
            )
        elif chat["role"] == "documents":
            extra_class = " chat-tight" if index == 0 else ""
            st.markdown(
                f'<div class="chat-row chat-left{extra_class}"><div class="bubble bubble-ai">Relevant SOP Documents</div></div>',
                unsafe_allow_html=True,
            )
            for document in chat.get("items", []):
                doc_name = document.get("name", "Document")
                doc_path = document.get("path", "")
                file_id = document.get("fileId", "")
                file_name = os.path.basename(doc_path) if doc_path else f"{doc_name}.pdf"

                st.markdown(f"**{doc_name}**")

                if doc_path and os.path.exists(doc_path):
                    with open(doc_path, "rb") as file_obj:
                        st.download_button(
                            label=f"Download {doc_name}",
                            data=file_obj.read(),
                            file_name=file_name,
                            mime="application/pdf",
                            key=f"download_{index}_{doc_name}",
                        )
                elif file_id:
                    response = requests.get(f"{API_BASE}/documents/{file_id}")
                    if response.status_code == 200:
                        st.download_button(
                            label=f"Download {doc_name}",
                            data=response.content,
                            file_name=file_name,
                            mime="application/pdf",
                            key=f"download_{index}_{doc_name}",
                        )
                    else:
                        st.warning(f"Unable to fetch document: {doc_name}")
                else:
                    st.warning(f"Missing file path and fileId for: {doc_name}")
        elif chat["role"] == "prompt":
            prompt_text = str(chat["content"]).replace("\n", "<br>")
            extra_class = " chat-tight" if index == 0 else ""
            st.markdown(
                f'<div class="chat-row chat-left{extra_class}"><div class="bubble bubble-prompt">{prompt_text}</div></div>',
                unsafe_allow_html=True,
            )
        else:
            bot_text = str(chat["content"]).replace("\n", "<br>")
            extra_class = " chat-tight" if index == 0 else ""
            st.markdown(
                f'<div class="chat-row chat-left{extra_class}"><div class="bubble bubble-ai">{bot_text}</div></div>',
                unsafe_allow_html=True,
            )


def handle_user_query(user_query):
    normalized_query = user_query.strip().lower()
    followup_answers = {"yes", "y", "yeah", "yep", "sure", "ok", "okay", "no", "n", "nope", "nah", "nothing"}

    if normalized_query not in followup_answers:
        st.session_state.latest_documents = []
        st.session_state.documents_followup_prompt = ""

    st.session_state.chat_history.append(
        {
            "role": "user",
            "content": user_query,
        }
    )

    data = call_fraud_api(st.session_state.user_id, user_query, st.session_state.session_id)

    chatbot_response = data.get("chatbot_response", "")
    fraud_category = data.get("fraud_category", "")
    returned_session_id = data.get("sessionId", "")
    documents = data.get("documents", [])

    st.session_state.next_prompt = ""

    if fraud_category:
        st.session_state.fraud_category = fraud_category

    if returned_session_id:
        st.session_state.session_id = returned_session_id

    if documents:
        st.session_state.latest_documents = documents
        st.session_state.chat_history.append(
            {
                "role": "documents",
                "items": documents,
            }
        )

    cleaned, prompt = extract_prompt(chatbot_response)
    if prompt:
        st.session_state.next_prompt = prompt

    full_response = cleaned or chatbot_response

    if prompt and full_response.strip() == prompt.strip():
        full_response = ""

    if documents:
        full_response = full_response.replace("Relevant SOP Documents:", "").strip()
        for document in documents:
            doc_name = document.get("name", "")
            if doc_name:
                full_response = full_response.replace(doc_name, "").strip()

    cleaned_response = full_response.strip()
    if cleaned_response:
        st.session_state.chat_history.append(
            {
                "role": "bot",
                "content": cleaned_response,
            }
        )

    st.rerun()


def run_app():
    st.set_page_config(page_title="SBI Fraud Investigation Assistant", layout="wide")
    st.markdown(GLOBAL_STYLES, unsafe_allow_html=True)
    st.markdown('<div class="app-title fade-in">SBI Fraud Investigation Assistant</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="app-subtitle fade-in">Secure, guided fraud investigation for State Bank of India</div>',
        unsafe_allow_html=True,
    )

    initialize_session_state()

    if not st.session_state.logged_in:
        render_login()

    if st.session_state.logged_in and not st.session_state.chat_history:
        st.session_state.next_prompt = "Hello😊 Please provide details about the SBI fraud case."

    col_spacer, col_reset, col_logout = st.columns([6, 1, 1])
    with col_reset:
        if st.button("Reset Conversation"):
            st.session_state.chat_history = []
            st.session_state.fraud_category = ""
            st.session_state.session_id = ""
            st.session_state.latest_documents = []
            st.session_state.next_prompt = ""
            st.session_state.documents_followup_prompt = ""
            st.rerun()
    with col_logout:
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.chat_history = []
            st.session_state.fraud_category = ""
            st.session_state.session_id = ""
            st.session_state.latest_documents = []
            st.session_state.next_prompt = ""
            st.session_state.documents_followup_prompt = ""
            st.rerun()

    st.markdown('<div class="section-title fade-in">SBI Fraud Investigation Chat</div>', unsafe_allow_html=True)
    st.markdown('<div class="chat-space">', unsafe_allow_html=True)
    render_chat_history()
    st.markdown("</div>", unsafe_allow_html=True)

    user_query = st.chat_input("Describe the SBI fraud case or reply Yes / No when asked")
    if user_query:
        handle_user_query(user_query)
