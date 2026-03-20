from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import Request
import requests
from app.db.mongodb import chat_collection  # new collection for conversation state
import datetime

router = APIRouter()


# Conversation steps
STEPS = [
    "sop_analysis",
    "ask_sop_docs",
    "ask_report",
    "ask_historical_docs",
    "final_assistance",
    "end"
]


def get_next_step(current_step):
    idx = STEPS.index(current_step)
    if idx + 1 < len(STEPS):
        return STEPS[idx + 1]
    return "end"


@router.post("/chat-step")
async def chat_step(request: Request):
    """
    Step-by-step chatbot endpoint.
    Expects JSON:
    {
        "userId": "hdfc001",
        "query": "User's current input",
        "sessionId": "optional, to continue existing conversation"
    }
    """
    data = await request.json()
    user_id = data.get("userId")
    user_query = data.get("query")
    session_id = data.get("sessionId")  # optional

    if not user_id or not user_query:
        raise HTTPException(status_code=400, detail="userId and query are required")

    # Load existing session or create new
    if session_id:
        session = chat_collection.find_one({"sessionId": session_id, "userId": user_id})
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        current_step = session.get("current_step", "sop_analysis")
        conversation_history = session.get("history", [])
    else:
        session_id = f"{user_id}_{datetime.datetime.utcnow().timestamp()}"
        current_step = "sop_analysis"
        conversation_history = []

    response_text = ""
    next_step = get_next_step(current_step)

    # Step logic
    if current_step == "sop_analysis":
        # Call /fraud API internally
        r = requests.get(
            "http://127.0.0.1:8000/fraud",
            params={"userId": user_id, "query": user_query}
        )
        analysis = r.json().get("analysis", "No analysis found")
        response_text = f"📄 SOP-Based Analysis:\n{analysis}\n\nDo you want the relevant documentation for the detected/classified fraud? (Yes/No)"
    elif current_step == "ask_sop_docs":
        if user_query.strip().lower() == "yes":
            response_text = "Fetching the relevant SOP PDF documents for the detected fraud..."
        else:
            response_text = "Skipping SOP documents."
        response_text += "\n\nDo you want an automated report generated for the analysis? (Yes/No)"
    elif current_step == "ask_report":
        if user_query.strip().lower() == "yes":
            response_text = "Generating automated report with all analysis details, risk levels, indicators, and recommendations..."
        else:
            response_text = "Skipping automated report generation."
        response_text += "\n\nDo you want historical reference documents from past similar fraud cases? (Yes/No)"
    elif current_step == "ask_historical_docs":
        if user_query.strip().lower() == "yes":
            response_text = "Fetching historical reference documents..."
        else:
            response_text = "Skipping historical reference documents."
        response_text += "\n\nIs there anything else I can help you with?"
    elif current_step == "final_assistance":
        if user_query.strip().lower() in ["no", "nothing"]:
            response_text = "✅ Thank you! The conversation has ended."
            next_step = "end"
        else:
            response_text = f"You asked: {user_query}\nI will respond accordingly."
            next_step = "final_assistance"
    else:
        response_text = "Conversation ended."

    # Update session in DB
    chat_collection.update_one(
        {"sessionId": session_id, "userId": user_id},
        {"$set": {
            "current_step": next_step,
            "last_query": user_query,
            "history": conversation_history + [{"step": current_step, "user": user_query, "bot": response_text}],
            "updated_at": datetime.datetime.utcnow()
        }},
        upsert=True
    )

    return {
        "sessionId": session_id,
        "step": current_step,
        "bot": response_text
    }