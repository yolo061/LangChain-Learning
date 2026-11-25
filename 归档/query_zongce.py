#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
综测规则智能检索系统
使用方法：python query_zongce.py
"""

from app.answer_question import query_zongce


def main():
    print("=" * 60)
    print("📚 综测规则智能检索系统")
    print("=" * 60)
    print("\n使用说明：")
    print("  - 输入问题查询综测规则")
    print("  - 输入 'q' 或 'quit' 退出")
    print("  - 支持自然语言提问\n")
    print("-" * 60)
    
    while True:
        try:
            # 获取用户输入
            question = input("\n🔍 请输入查询问题：").strip()
            
            # 检查退出命令
            if question.lower() in ['q', 'quit', 'exit', '退出']:
                print("\n👋 感谢使用，再见！")
                break
            
            # 检查空输入
            if not question:
                print("⚠️ 请输入有效问题")
                continue
            
            # 执行查询
            print("\n⏳ 正在检索综测规则...\n")
            print("=" * 60)
            
            result = query_zongce(question)

            # 输出结果
            print("\n" + "=" * 60)
            print("📋 查询结果：\n")
            print(result)
            print("\n" + "=" * 60)

        except KeyboardInterrupt:
            print("\n\n👋 检测到中断，退出程序")
            break
        except Exception as e:
            print(f"\n❌ 查询出错：{e}")
            print("请检查文档路径和 API 配置是否正确")


if __name__ == '__main__':
    main()
