# Prompt templates for analysis engine
# This file contains language-specific prompt content

INITIAL_PROMPT_TEMPLATE = """
生成一个Python兼容的正则表达式，满足以下要求：

需求描述：{user_request}

主要示例输入：{sample_input}
预期匹配：{expected_matches}

"""

ADDITIONAL_EXAMPLES_SECTION = "其他参考示例：{additional_examples}\n"

NEGATIVE_EXAMPLES_SECTION = "负例（不应匹配）：{negative_examples}\n"

INITIAL_PROMPT_FOOTER = """
注意有的有空格干扰。
请仅返回正则表达式模式，不要任何解释或代码格式。

请注意，生成的正则表达式将在后台使用Python的re模块进行验证，
以确保其正确性。请确保生成的正则表达式语法正确且符合Python re模块的要求。
"""

FINAL_CHECK_TEMPLATE = """
我有一个正则表达式模式：{regex}
应用于主要输入：{sample_input}
当前匹配：{current_matches}
预期匹配：{expected_matches}

"""

FINAL_CHECK_ADDITIONAL = """
额外示例的匹配结果：
"""

FINAL_CHECK_NEGATIVE = """
负例的匹配结果（这些不应该匹配）：
"""

FINAL_CHECK_FOOTER = """
主要示例的匹配结果是正确的，但请评估额外示例和负例的匹配结果是否符合预期。
小心有的有空格干扰。

如果额外示例的匹配结果和负例的匹配结果都符合正则表达式的预期模式，
请返回原始的正则表达式模式。
否则，请提供修正的正则表达式。
注意：仅回复正则表达式，不要任何解释或代码格式。
"""

ERROR_PROMPT_HEADER = """
我们正在尝试生成一个正则表达式来满足您的需求：{user_request}

当前尝试 ({attempt}/{max_attempts}) 的结果：
- 正则表达式: {regex}
- 应用于主要输入: {sample_input}
- 当前匹配: {current_matches}
- 预期匹配: {expected_matches}

"""

ERROR_PROMPT_ADDITIONAL = "额外示例的匹配结果：\n"

ERROR_PROMPT_NEGATIVE = "\n负例的匹配结果（这些不应该匹配）：\n"

ERROR_PROMPT_MISMATCH = """
当前正则表达式没有正确匹配主要示例的预期模式。请建议修正的正则表达式。
注意有的有空格干扰。

以下是当前匹配和预期匹配的对比：
- 实际匹配: {current_matches}
- 期望匹配: {expected_matches}
- 未匹配的期望项: {unmatched_expected}
- 意外匹配项: {unexpected_matches}

请参考额外示例的匹配结果来优化正则表达式，确保它符合整体模式。
请参考负例的匹配结果来修正正则表达式，避免匹配不应匹配的内容。
"""

ERROR_PROMPT_SYNTAX = "\n特别注意：正则表达式存在语法错误，请修正后再提供。错误详情：{regex_error}"

ERROR_PROMPT_FOOTER = """
请仅返回修正的正则表达式模式，如果正则表达式准确则返回"CORRECT"。
请注意，正则表达式将在后台使用Python的re模块进行验证，
请确保生成的正则表达式语法正确且符合Python re模块的要求。
"""

FAILURE_ANALYSIS_HEADER = """
我们尝试生成一个正则表达式来满足您的需求：{user_request}
主要示例输入：{sample_input}
预期匹配：{expected_matches}

以下是 {max_attempts} 次尝试的完整历史记录：
"""

FAILURE_ANALYSIS_FOOTER = """
尽管进行了多次尝试，但仍然无法生成满足需求的正则表达式。
请分析历史记录并提供一个修正的正则表达式，或者建议如何调整需求以使其可实现。
"""
