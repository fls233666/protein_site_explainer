#!/usr/bin/env python3

import re

# 当前的正则表达式
MUTATION_PATTERN = re.compile(r'^([A-Z])(\d+)([A-Z*])$')

test_cases = [
    "A123T",       # 有效格式
    "123AT",       # 错误顺序
    "A123456T",    # 长位置（应该有效）
    "AA123T",      # 两个野生型氨基酸
    "A123TT",      # 两个突变型氨基酸
    "A123*",       # 终止突变
    "a123t",       # 小写字母
]

print("Testing mutation pattern regex:")
print("Pattern:", MUTATION_PATTERN.pattern)
print()

for test in test_cases:
    match = MUTATION_PATTERN.match(test)
    if match:
        print(f"✓ '{test}' matches")
        print(f"  Groups: {match.groups()}")
    else:
        print(f"✗ '{test}' does not match")
    print()