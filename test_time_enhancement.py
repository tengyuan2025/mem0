#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试时间增强功能
"""

import re
from datetime import datetime, timedelta

def enhance_memory_with_time(text: str) -> str:
    """
    增强记忆文本，将相对时间表达转换为具体时间
    """
    now = datetime.now()
    enhanced_text = text
    
    # 时间模式匹配和替换规则
    time_patterns = [
        # 今天相关
        (r'今天([上下]午|早上|晚上|中午)?', lambda m: f"今天{m.group(1) if m.group(1) else ''}({now.strftime('%Y年%m月%d日')})"),
        (r'今日([上下]午|早上|晚上|中午)?', lambda m: f"今日{m.group(1) if m.group(1) else ''}({now.strftime('%Y年%m月%d日')})"),
        
        # 昨天相关  
        (r'昨天([上下]午|早上|晚上|中午)?', lambda m: f"昨天{m.group(1) if m.group(1) else ''}({(now - timedelta(days=1)).strftime('%Y年%m月%d日')})"),
        (r'昨日([上下]午|早上|晚上|中午)?', lambda m: f"昨日{m.group(1) if m.group(1) else ''}({(now - timedelta(days=1)).strftime('%Y年%m月%d日')})"),
        
        # 明天相关
        (r'明天([上下]午|早上|晚上|中午)?', lambda m: f"明天{m.group(1) if m.group(1) else ''}({(now + timedelta(days=1)).strftime('%Y年%m月%d日')})"),
        (r'明日([上下]午|早上|晚上|中午)?', lambda m: f"明日{m.group(1) if m.group(1) else ''}({(now + timedelta(days=1)).strftime('%Y年%m月%d日')})"),
        
        # 前天、后天
        (r'前天([上下]午|早上|晚上|中午)?', lambda m: f"前天{m.group(1) if m.group(1) else ''}({(now - timedelta(days=2)).strftime('%Y年%m月%d日')})"),
        (r'后天([上下]午|早上|晚上|中午)?', lambda m: f"后天{m.group(1) if m.group(1) else ''}({(now + timedelta(days=2)).strftime('%Y年%m月%d日')})"),
        
        # 本周、上周、下周
        (r'本周', lambda m: f"本周({now.strftime('%Y年第%U周')})"),
        (r'这周', lambda m: f"这周({now.strftime('%Y年第%U周')})"),
        (r'上周', lambda m: f"上周({(now - timedelta(days=7)).strftime('%Y年第%U周')})"),
        (r'下周', lambda m: f"下周({(now + timedelta(days=7)).strftime('%Y年第%U周')})"),
        
        # 现在、刚才
        (r'现在', lambda m: f"现在({now.strftime('%Y年%m月%d日 %H:%M')})"),
        (r'刚才', lambda m: f"刚才({now.strftime('%Y年%m月%d日 %H:%M')})"),
        (r'刚刚', lambda m: f"刚刚({now.strftime('%Y年%m月%d日 %H:%M')})"),
    ]
    
    # 应用所有时间模式
    changes_made = []
    for pattern, replacement in time_patterns:
        matches = list(re.finditer(pattern, enhanced_text))
        if matches:
            for match in reversed(matches):  # 从后往前替换避免索引问题
                original = match.group(0)
                new_text = replacement(match)
                enhanced_text = enhanced_text[:match.start()] + new_text + enhanced_text[match.end():]
                changes_made.append(f"'{original}' → '{new_text}'")
    
    return enhanced_text, changes_made

def test_time_enhancement():
    """测试时间增强功能"""
    test_cases = [
        "我今天中午吃了肉沫茄子盖饭",
        "昨天晚上看了一部电影",
        "明天上午有一个重要会议", 
        "前天去了公园散步",
        "刚才和朋友聊天",
        "本周计划完成项目",
        "上周买了一本书",
        "今日天气不错",
        "现在正在工作",
        "这是一个普通的句子，没有时间词汇"
    ]
    
    print("🧪 时间增强功能测试")
    print("=" * 60)
    
    for i, text in enumerate(test_cases, 1):
        enhanced, changes = enhance_memory_with_time(text)
        print(f"\n测试 {i}:")
        print(f"原文本: {text}")
        print(f"增强后: {enhanced}")
        if changes:
            print(f"变更: {' | '.join(changes)}")
        else:
            print("变更: 无")
        print("-" * 40)

if __name__ == "__main__":
    test_time_enhancement()