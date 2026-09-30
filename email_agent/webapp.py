import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from email_agent.server.connect import list_inbox, to_email_input

app = FastAPI(title="Email Agent")

@app.get("/", response_class=HTMLResponse)
def home():
    return "<h1>Email Agent</h1><p>服务已启动</p>"

@app.get("/api/emails")
def emails():
    msgs = list_inbox(top=5)
    return [{"index": i, "subject": m["subject"],
             "from": m["from"]["emailAddress"]["address"], "id": m["id"]}
            for i, m in enumerate(msgs)]

if __name__ == '__main__':
    uvicorn.run("email_agent.webapp:app", host="localhost", port=9999, reload=True)