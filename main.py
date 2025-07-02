from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os

app = FastAPI()

# ✅ Enable CORS (open for testing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Chat backend is running."}

# 📁 File & Data Storage
DATA_FILE = "data.txt"
user_passwords = {}
chat_history = []  # Stores (username, type, content)

MAX_MESSAGES = 500  # Only keep last 500 messages in memory and file

# ✅ Load existing data
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        for line in f:
            parts = line.strip().split(" ", 3)
            if not parts:
                continue
            if parts[0] == "U" and len(parts) == 3:
                user_passwords[parts[1]] = parts[2]
            elif parts[0] == "C" and len(parts) == 4:
                chat_history.append((parts[1], parts[2], parts[3]))

# ⛔ Trim to last MAX_MESSAGES
if len(chat_history) > MAX_MESSAGES:
    chat_history = chat_history[-MAX_MESSAGES:]

# 💾 Save everything back to file
def save_data():
    with open(DATA_FILE, "w") as f:
        for u, p in user_passwords.items():
            f.write(f"U {u} {p}\n")
        for u, t, c in chat_history[-MAX_MESSAGES:]:  # Always trim to last 500
            f.write(f"C {u} {t} {c}\n")

# 🛠️ Request schema
class UserInput(BaseModel):
    action: str
    username: str
    password: str = ""
    msg_type: str = ""   # text, image, video
    content: str = ""    # message body or media URL

@app.post("/")
async def handle(req: UserInput):
    u = req.username.strip()
    p = req.password.strip()
    t = req.msg_type.strip()
    c = req.content.strip()

    if req.action == "register":
        if not u or not p:
            return {"success": False, "message": "Username and password are required."}
        if u in user_passwords:
            return {"success": False, "exists": True, "message": f"User '{u}' already exists."}
        user_passwords[u] = p
        save_data()
        return {"success": True, "message": f"User '{u}' registered successfully."}

    if req.action == "login":
        if user_passwords.get(u) == p:
            return {"success": True, "message": f"Welcome, {u}!"}
        return {"success": False, "message": "Incorrect username or password."}

    if req.action == "send":
        if u not in user_passwords:
            return {"success": False, "message": "User not registered."}
        if t not in ["text", "image", "video"]:
            return {"success": False, "message": "Invalid message type."}
        if not c:
            return {"success": False, "message": "Empty message."}
        chat_history.append((u, t, c))
        if len(chat_history) > MAX_MESSAGES:
            chat_history.pop(0)  # Keep only latest messages
        save_data()
        return {"success": True, "message": "Message sent."}

    if req.action == "get":
        return {
            "success": True,
            "messages": [
                {"username": user, "type": msg_type, "content": content}
                for user, msg_type, content in chat_history
            ]
        }

    return {"success": False, "message": "Unknown action."}
