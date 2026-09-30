"""创建对话模型"""
from langchain.chat_models import init_chat_model
from email_agent.config import settings

def get_llm():
    llm = init_chat_model(
        model = settings.model_name,
        api_key =  settings.deepseek_api_key,
        temperature = settings.temperature,
        extra_body={
            "thinking": {
                "type": "disabled"
            }
        }
    )
    return llm

if __name__ == '__main__':
    llm = get_llm()
    print(llm.invoke("whats the weather like in sichuan"))