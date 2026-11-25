import os
import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_classic.output_parsers import ResponseSchema, StructuredOutputParser


def chat_init():
    """创建聊天模型对象（第一步：建模型）。

    ChatOpenAI 是 LangChain 对"OpenAI 兼容接口"聊天模型的通用封装。
    DeepSeek 的 API 兼容 OpenAI 协议，所以只要把 base_url 指向 DeepSeek
    的服务地址，就能复用这同一个类，不必换成 DeepSeek 专用的类。
    """
    return ChatOpenAI(
        base_url="https://api.deepseek.com",         # 模型服务地址（不填默认连 OpenAI 官方）
        model="deepseek-v4-flash",                   # 要调用的具体模型名
        api_key=os.environ.get("DEEPSEEK_API_KEY"),  # 密钥从环境变量读取，避免硬编码进代码泄露
        temperature=0.0                              # 采样温度：0 输出最稳定，适合信息提取类任务
    )


def get_messages(chat: ChatOpenAI, template_string, text, format_instructions):
    """组装提示词消息列表（第二步：拼提示词，此时还没联网）。

    ChatPromptTemplate.from_template() 把含 {占位符} 的字符串转成模板对象；
    format_messages() 用关键字参数填充占位符，返回聊天模型所需的消息列表。
    本质只是本地字符串替换，不产生任何网络请求。
    """
    template = ChatPromptTemplate.from_template(template_string)  # 构建模板
    messages = template.format_messages(
        text=text,                                     # 填充 {text}：待分析的评论原文
        format_instructions=format_instructions        # 填充 {format_instructions}：输出格式说明
    )
    return messages


def get_response(chat, messages):
    """调用大模型（第三步：真正发起 API 请求）。

    invoke() 是 LangChain 统一的调用接口（替代已废弃的 chat(messages) 写法），
    模型、提示词、链等所有组件都用它。返回 AIMessage 对象，
    通过 .content 取出模型的回复文本。
    """
    return chat.invoke(messages)


def get_output_parsers():
    """创建结构化输出解析器（贯穿二、四步：发说明书 + 阅卷）。

    ResponseSchema 逐个声明输出字段：name 是字段名，description 描述
    该字段要提取什么内容（这段描述也会出现在给模型的格式说明里）。
    StructuredOutputParser.from_response_schemas() 是工厂方法（类方法），
    把 schema 列表包装成解析器实例，不能直接在类上调 get_format_instructions()。
    同一个实例承担两个职责：
      - get_format_instructions()：生成 JSON 格式说明书，注入提示词给模型看
      - parse(模型回复)：把模型输出的 JSON 文本解析成 Python 字典
    两者必须出自同一个实例，"谁发说明书谁来阅卷"，格式才能对得上。
    """
    gift_schema = ResponseSchema(name="gift",
                                 description="Was the item purchased as a gift for someone else? Answer True if yes, False if not or unknown.")
    delivery_days_schema = ResponseSchema(name="delivery_days",
                                          description="How many days did it take for the product to arrive?")
    price_value_schema = ResponseSchema(name="price_value",
                                        description="Extract any sentences about the value or price")
    response_schema = [gift_schema, delivery_days_schema, price_value_schema]
    output_parsers = StructuredOutputParser.from_response_schemas(response_schema)
    return output_parsers


if __name__ == '__main__':
    template_string = """\
                        For the following text, extract the following information:
                        gift: Was the item purchased as a gift for someone else? Answer \
                        with 'yes' or 'no'.
                        delivery_days: How many days did it take for the product to arrive?\
                         If this information is not found, output 'no information found.'
                        price_value: Extract any sentences about the value or price,\
                         and output them as a comma separated Python list.
                        text: {text}
                        {format_instructions}
                      """
    text = """
        This leaf blower is pretty amazing.  It has four settings:\
        candle blower, gentle breeze, windy city, and tornado. \
        It arrived in two days, just in time for my wife's \
        anniversary present. \
        I think my wife liked it so much she was speechless. \
        So far I've been the only one using it, and I've been \
        using it every other morning to clear the leaves on our lawn.\
        It's slightly more expensive than the other leaf blowers \
        out there, but I think it's worth it for the extra features.
    """

    # 整体流程：建模型 -> 拼提示词 -> 调用模型 -> 解析输出
    chat = chat_init()

    output_parsers = get_output_parsers()
    messages = get_messages(chat, template_string, text, output_parsers.get_format_instructions())
    response = get_response(chat, messages)
    output_dict = output_parsers.parse(response.content)  # JSON 文本 -> Python 字典

    print(output_dict)

    # 写入文件
    with open("LangChain/01.json", "w", encoding="utf-8") as f:
        json.dump(output_dict, f)  # dump（无s）写入文件；dumps（有s）只转成字符串
