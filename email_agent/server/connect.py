import requests

from .auth import get_token

BASE = "https://graph.microsoft.com/v1.0"
def graph_get(url, header_extra=None):
    headers={"Authorization": f"Bearer {get_token()}"}
    if header_extra:
        headers.update(header_extra)
    response = requests.get(url, headers=headers)
    response.raise_for_status() # 异常抛出
    return response.json()

def graph_post(url, payload=None):
    response = requests.post(url, headers={"Authorization": f"Bearer {get_token()}"}, json=payload)
    response.raise_for_status()
    return response.json() if response.content else None

def list_inbox(top=5):
    url = (f"{BASE}/me/mailFolders/inbox/messages"
           f"?$top={top}"
           f"&$select=subject,from,toRecipients,body,receivedDateTime,id"
           f"&$orderby=receivedDateTime desc")
    return graph_get(url, header_extra={"Prefer": 'outlook.body-content-type="Text"'})["value"]


def to_email_input(m: dict) -> dict:                         # Graph 格式 → agent 格式
    """把 Graph 的 message JSON 转成 State.email_input 需要的四键 dict"""
    frm = m["from"]["emailAddress"]
    tos = "; ".join(r["emailAddress"]["address"] for r in m.get("toRecipients", []))
    return {
        "id" : m["id"],
        "author": f'{frm["name"]} <{frm["address"]}>',
        "to": tos,
        "subject": m["subject"],
        "email_thread": m["body"]["content"],                # 纯文本正文(Prefer 生效时)
    }
"""回复邮件"""
def create_reply_draft(message_id : str, reply_body : str) -> dict:
    """对指定邮件建一封回复草稿,返回草稿 JSON(含草稿的 id)"""
    url = f"{BASE}/me/messages/{message_id}/createReply"
    draft = graph_post(url)  # createReply 会自动带上 Re: 主题和原收件人
    update_draft_body(draft["id"], reply_body)
    return draft


def update_draft_body(draft_id: str, body: str):
    url = f"{BASE}/me/messages/{draft_id}"
    requests.patch(url, headers={"Authorization": f"Bearer {get_token()}"},
                   json={"body": {"contentType": "Text", "content": body}})
    # graph_patch 版本:requests.patch + raise_for_status,顺手补上


def send_draft(draft_id: str):
    url = f"{BASE}/me/messages/{draft_id}/send"
    requests.post(url, headers={"Authorization": f"Bearer {get_token()}"})
    # 同理加 raise_for_status;send 返回 202 无 body

if __name__ == "__main__":
    msgs = list_inbox(3)          # 回到这个,文件夹清单那种调试代码先注释掉
    print(f"拿到了 {len(msgs)} 封邮件")
    for m in msgs:
        print("-" * 40)
        print(to_email_input(m))