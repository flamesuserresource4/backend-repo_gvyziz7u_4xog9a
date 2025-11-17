import os
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from schemas import PortfolioItem, ContactMessage
from database import db, create_document, get_documents
import smtplib
from email.message import EmailMessage

app = FastAPI(title="Property Portfolio API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Backend running", "endpoints": ["/api/portfolio", "/api/portfolio/bulk", "/api/contact", "/test"]}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = getattr(db, 'name', None) or "Unknown"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
                response["connection_status"] = "Connected"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response

# ---------------- Portfolio Endpoints ----------------

class PortfolioQuery(BaseModel):
  	category: Optional[str] = None
  	page: int = 1
  	limit: int = 18

@app.get("/api/portfolio")
def list_portfolio(category: Optional[str] = None, page: int = 1, limit: int = 18):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    filter_dict = {}
    if category:
        filter_dict["category"] = category
    skip = max(0, (page - 1) * limit)
    coll = db["portfolioitem"]
    total = coll.count_documents(filter_dict)
    cursor = coll.find(filter_dict).sort("created_at", -1).skip(skip).limit(limit)
    items = []
    for doc in cursor:
        doc["id"] = str(doc.pop("_id"))
        items.append(doc)
    return {"items": items, "total": total, "page": page, "limit": limit}

@app.get("/api/portfolio/categories")
def portfolio_categories():
    return {
        "categories": [
            "Interiors",
            "Exteriors",
            "Drone / Aerial",
            "Architectural Details",
            "Commercial Spaces",
            "Short-Let & Airbnb",
        ]
    }

@app.post("/api/portfolio")
def add_portfolio_item(item: PortfolioItem):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    inserted_id = create_document("portfolioitem", item)
    return {"id": inserted_id}

@app.post("/api/portfolio/bulk")
def add_portfolio_bulk(items: List[PortfolioItem]):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    ids = []
    for it in items:
        ids.append(create_document("portfolioitem", it))
    return {"inserted": len(ids), "ids": ids}

# ---------------- Contact Endpoint ----------------

def send_email_via_smtp(subject: str, body: str, from_email: str):
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASS")
    to_email = os.getenv("CONTACT_TO_EMAIL") or os.getenv("TO_EMAIL")
    if not (host and to_email):
        return False, "SMTP not configured"
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email
    msg.set_content(body)
    try:
        with smtplib.SMTP(host, port, timeout=15) as server:
            server.starttls()
            if user and password:
                server.login(user, password)
            server.send_message(msg)
        return True, "sent"
    except Exception as e:
        return False, str(e)

@app.post("/api/contact")
def submit_contact(payload: ContactMessage):
    # Always persist the message
    try:
        saved_id = create_document("contactmessage", payload)
    except Exception:
        saved_id = None

    subject = "New portfolio inquiry"
    body = (
        f"Name: {payload.name}\n"
        f"Email: {payload.email}\n"
        f"Phone: {payload.phone or '-'}\n\n"
        f"Message:\n{payload.message}\n"
    )
    ok, info = send_email_via_smtp(subject, body, str(payload.email))

    status = "emailed" if ok else "stored"
    detail = "Message emailed successfully" if ok else f"Email not sent: {info}. Saved to database." if saved_id else "Email not sent and could not save."

    return {"status": status, "id": saved_id, "detail": detail}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
