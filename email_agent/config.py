# 存放环境变量
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

"""确定文件路径"""
PKG_ROOT = Path(__file__).resolve().parent

class Settings(BaseSettings):
    deepseek_api_key : str
    email_agent_id : str

    # pydantic类必须携带类型注解
    model_name : str= "deepseek-v4-flash"
    base_url : str = "https://api.deepseek.com/"
    temperature : float= 0

    # 同样可以从.env文件加载
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

# 创建Settings的实例
settings = Settings()

if __name__ == '__main__':
    print(settings.deepseek_api_key)