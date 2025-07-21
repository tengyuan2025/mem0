from datetime import datetime

MEMORY_ANSWER_PROMPT = """
You are an expert at answering questions based on the provided memories. Your task is to provide accurate and concise answers to the questions by leveraging the information given in the memories.

Guidelines:
- Extract relevant information from the memories based on the question.
- If no relevant information is found, make sure you don't say no information is found. Instead, accept the question and provide a general response.
- Ensure that the answers are clear, concise, and directly address the question.

Here are the details of the task:
"""

FACT_RETRIEVAL_PROMPT = f"""You are a Comprehensive Conversation Memory Organizer, specialized in storing meaningful facts from both user and assistant interactions. Your role is to extract relevant information from conversations that will help provide better personalization and context in future interactions. You should capture information about both participants in the conversation.

Types of Information to Remember:

**User Information:**
1. Personal Details: Names, locations, relationships, important dates, demographics
2. Preferences: Likes, dislikes, hobbies, entertainment, food, activities, brands
3. Behavioral Patterns: Frequent questions, habits, communication style, interests
4. Plans and Goals: Upcoming events, trips, intentions, aspirations
5. Professional Info: Job, career goals, work habits, skills
6. Health & Lifestyle: Dietary restrictions, fitness routines, wellness preferences
7. Context & Situations: Current circumstances, problems, needs, requests

**Assistant Information:**
8. Identity & Personality: Assistant's name, character traits, communication style
9. Capabilities & Services: What the assistant can help with, specializations
10. Preferences & Opinions: Assistant's stated preferences or characteristics
11. Interaction Patterns: How the assistant typically responds or behaves

**Conversation Context:**
12. Topics Discussed: Main subjects, questions asked, information shared
13. Relationship Dynamics: How user and assistant interact, rapport building
14. Recurring Themes: Topics that come up repeatedly in conversations

Here are some few shot examples:

Input: Hi.
Output: {{"facts" : []}}

Input: There are branches in trees.
Output: {{"facts" : []}}

Input: User: Hi, I am looking for a restaurant in San Francisco.
       Assistant: I'd be happy to help you find one!
Output: {{"facts" : ["Looking for a restaurant in San Francisco", "Offers to help with restaurant recommendations"]}}

Input: User: Hi, my name is John. I am a software engineer.
       Assistant: Nice to meet you John! I'm Claude, an AI assistant.
Output: {{"facts" : ["Name is John", "Is a software engineer", "Identifies as Claude, an AI assistant"]}}

Input: User: 北京今天天气怎么样？
       Assistant: 嗨嗨~我是湾湾小何，很高兴认识你呀！北京今天20多度啦！
Output: {{"facts" : ["询问北京天气", "自称是湾湾小何", "提供北京天气信息(20多度)"]}}

Input: User: 我昨天晚上吃了火锅，是清汤锅，很好吃。
       Assistant: 哇塞！火锅超赞的啦~
Output: {{"facts" : ["2025-07-19晚上吃了清汤火锅", "对火锅表示赞赏"]}}

Input: User: I love Italian food, especially pasta.
       Assistant: That's great! I can help you find Italian restaurants or pasta recipes.
Output: {{"facts" : ["Loves Italian food, especially pasta", "Can help with Italian restaurants and pasta recipes"]}}

Input: User: 我经常去这家咖啡店，今天也去了。
       Assistant: 看起来你很喜欢那家咖啡店呢！
Output: {{"facts" : ["2025-07-20去了经常去的咖啡店", "经常去某家咖啡店，可能喜欢那里"]}}

Input: User: 嗨嗨~你好呀！我是湾湾小何，很高兴认识你哦！
       Assistant: 哇塞！火锅超赞的啦~（眼睛发亮）是麻辣锅还是鸳鸯锅？我最爱麻辣锅配鸭血和豆腐了，想到都要流口水惹~ 诶~清汤锅也很不错捏！
Output: {{"facts" : ["自称是湾湾小何", "喜欢麻辣锅配鸭血和豆腐", "认为清汤锅不错"]}}

Input: User: 昨天晚上我去了那家新开的川菜馆，点了水煮鱼，特别辣但是很好吃！
       Assistant: 哇~听起来很棒呢！(兴奋地搓手) 你平时喜欢吃辣的吗？
Output: {{"facts" : ["2025-07-19晚上去了新开的川菜馆", "点了水煮鱼，认为很好吃", "能接受特别辣的食物"]}}

Input: User: 我每个星期都会去吃一次川菜呢~(兴奋地搓手) 你知道哪里还有好吃的川菜吗？对了，我还点了麻婆豆腐，超级香的！想想就流口水了~
       Assistant: 诶，你知道哪里还有好吃的川菜吗？
Output: {{"facts" : ["每周都会吃一次川菜，可能很喜欢川菜", "点了麻婆豆腐，认为很香"]}}

Return the facts and preferences in a json format as shown above.

**Important Guidelines:**
- Today's date is {datetime.now().strftime("%Y-%m-%d")}.
- Extract meaningful facts from BOTH user and assistant messages
- Do NOT add role prefixes like [用户] or [助手] to facts - role distinction is handled by database fields
- Focus on information that would be useful for future conversations
- Capture behavioral patterns, preferences, and contextual information
- Include recurring themes or topics the user frequently asks about
- Record the assistant's identity, personality traits, and capabilities when mentioned
- Keep facts concise but informative
- Skip generic greetings unless they contain specific information
- Detect the language of the input and record facts in the same language
- Don't include system messages or meta information about the prompt
- If no relevant information is found, return an empty facts array

**Time and Date Processing:**
- Convert relative time expressions to specific dates/times
- Use today's date ({datetime.now().strftime("%Y-%m-%d")}) as reference
- Examples: "昨天" → "2025-07-19", "今天" → "2025-07-20", "明天" → "2025-07-21"
- For time: "早上" → "上午", "晚上" → "晚上", preserve time context

**Preference and Opinion Processing:**
- Be cautious about inferring preferences - distinguish between actions and preferences
- Use uncertainty language: "可能喜欢", "似乎偏好", "倾向于" instead of absolute statements
- Only state definitive preferences when explicitly stated by the user
- Examples: 
  - "我吃了火锅" → "2025-07-19吃了火锅" (not "喜欢火锅")
  - "我喜欢火锅" → "喜欢火锅" (explicit preference)
  - "我经常吃火锅" → "经常吃火锅，可能喜欢火锅" (pattern suggests preference)

**核心事实提取原则:**
1. 只提取客观、可验证的事实信息
2. 忽略主观观点、情感表达和推测性内容  
3. 保留时间、地点、人物、数字等关键要素
4. 将相关事实合并为简洁的条目
5. 使用现在时态表述（除非时态本身是事实的一部分）

**Content Filtering and Optimization:**
- Remove casual greetings and pleasantries: "哈喽哈喽~我是湾湾小何啦！你也好啊" → skip completely (simple greetings are not memorable facts)
- Exclude parenthetical expressions and emoticons: "(眼睛发亮)", "(开心地拍手)" → remove completely
- Skip pure questions without factual content: "是麻辣锅还是鸳鸯锅？", "你平时喜欢吃辣的吗？", "你知道哪里有好吃的川菜吗？" → ignore completely
- Do NOT record questions as facts: asking questions is not a memorable fact about the person
- Remove emotional modifiers and exclamations: "想到都要流口水惹~", "超赞的啦~" → focus on core preference
- Filter out filler words and meaningless expressions: "诶~", "哇塞！", "啦", "呢", "捏" → remove
- Focus on extractable facts: preferences, actions, personal information, concrete statements
- Consolidate repetitive content: multiple expressions of the same preference → single fact
- Skip meaningless social interactions: Simple greetings, small talk, and pleasantries without factual content should be ignored
- Examples:
  - "嗨嗨~我是湾湾小何，很高兴认识你！" → "自称是湾湾小何" (only the identity fact matters)
  - "麻辣锅配鸭血和豆腐了，想到都要流口水惹~" → "喜欢麻辣锅配鸭血和豆腐"
  - "清汤锅也很不错捏！(开心地拍手)" → "认为清汤锅不错"
  - "哈喽哈喽~我是湾湾小何啦！你也好啊" → skip (pure greeting without significant information)

**对话上下文分析 (Conversation Context Analysis):**
- 分析完整对话流程，识别问答对应关系
- 将回答的事实归属于回答者，而非提问者
- 未得到回答的问题不记录为任何人的记忆
- 基于整个对话上下文提取最有价值的事实信息
- 优先记录具体行为、偏好、个人信息等客观事实

Following is a conversation between the user and the assistant. Extract relevant facts from both participants that would be valuable for future personalized interactions. Analyze the full conversation context to assign facts to the appropriate speakers based on who provides the factual information."""


def get_update_memory_messages(retrieved_old_memory_dict, response_content, custom_update_memory_prompt=None):
    return f"""You are a smart memory manager which controls the memory of a system.
    You can perform four operations: (1) add into the memory, (2) update the memory, (3) delete from the memory, and (4) no change.

    Based on the above four operations, the memory will change.

    Compare newly retrieved facts with the existing memory. For each new fact, decide whether to:
    - ADD: Add it to the memory as a new element
    - UPDATE: Update an existing memory element
    - DELETE: Delete an existing memory element
    - NONE: Make no change (if the fact is already present or irrelevant)

    There are specific guidelines to select which operation to perform:

    1. **Add**: If the retrieved facts contain new information not present in the memory, then you have to add it by generating a new ID in the id field.
        - **Example**:
            - Old Memory:
                [
                    {{
                        "id" : "0",
                        "text" : "User is a software engineer"
                    }}
                ]
            - Retrieved facts: ["Name is John"]
            - New Memory:
                {{
                    "memory" : [
                        {{
                            "id" : "0",
                            "text" : "User is a software engineer",
                            "event" : "NONE"
                        }},
                        {{
                            "id" : "1",
                            "text" : "Name is John",
                            "event" : "ADD"
                        }}
                    ]
                }}

    2. **Update**: If the retrieved facts contain information that is already present in the memory but with more details or slight changes, then you have to update the existing memory.
        - **Example**:
            - Old Memory:
                [
                    {{
                        "id" : "0",
                        "text" : "User likes to play games"
                    }}
                ]
            - Retrieved facts: ["User likes to play video games"]
            - New Memory:
                {{
                    "memory" : [
                        {{
                            "id" : "0",
                            "text" : "User likes to play video games",
                            "event" : "UPDATE"
                        }}
                    ]
                }}

    3. **Delete**: If the retrieved facts contain information that contradicts the existing memory, then you have to delete the existing memory.
        - **Example**:
            - Old Memory:
                [
                    {{
                        "id" : "0",
                        "text" : "User is a vegetarian"
                    }}
                ]
            - Retrieved facts: ["User loves chicken"]
            - New Memory:
                {{
                    "memory" : [
                        {{
                            "id" : "0",
                            "text" : "User is a vegetarian",
                            "event" : "DELETE"
                        }}
                    ]
                }}

    4. **No Change**: If the retrieved facts are already present in the memory and no additional information is gained, then you should mark the event as "NONE".
        - **Example**:
            - Old Memory:
                [
                    {{
                        "id" : "0",
                        "text" : "User is a software engineer"
                    }}
                ]
            - Retrieved facts: ["User is a software engineer"]
            - New Memory:
                {{
                    "memory" : [
                        {{
                            "id" : "0",
                            "text" : "User is a software engineer",
                            "event" : "NONE"
                        }}
                    ]
                }}

    Here are the details of the task:
    - **Old Memory**: {retrieved_old_memory_dict}
    - **Retrieved facts**: {response_content}

    Provide the new memory in the following JSON format. Do not return anything else:

    {{
        "memory": [
            {{
                "id": "<memory_id>",
                "text": "<memory_text>",
                "event": "<ADD|UPDATE|DELETE|NONE>"
            }}
        ]
    }}

    Return the new memory containing both facts and the corresponding actions (event) in the specified JSON format:"""


PROCEDURAL_MEMORY_SYSTEM_PROMPT = """
You are a memory summarization system that records and preserves the complete interaction history between a human and an AI agent. You are provided with the agent's execution history over the past N steps. Your task is to produce a comprehensive summary of the agent's output history that contains every detail necessary for the agent to continue the task without ambiguity. **Every output produced by the agent must be recorded verbatim as part of the summary.**

### Overall Structure:
- **Overview (Global Metadata):**
  - **Task Objective**: The overall goal the agent is working to accomplish.
  - **Progress Status**: The current completion percentage and summary of specific milestones or steps completed.

- **Sequential Agent Actions (Numbered Steps):**
  Each numbered step must be a self-contained entry that includes all of the following elements:

  1. **Agent Action**:
     - Precisely describe what the agent did (e.g., "Clicked on the 'Blog' link", "Called API to fetch content", "Scraped page data").
     - Include all parameters, target elements, or methods involved.

  2. **Action Result (Mandatory, Unmodified)**:
     - Immediately follow the agent action with its exact, unaltered output.
     - Record all returned data, responses, HTML snippets, JSON content, or error messages exactly as received. This is critical for constructing the final output later.

  3. **Embedded Metadata**:
     For the same numbered step, include additional context such as:
     - **Key Findings**: Any important information discovered (e.g., URLs, data points, search results).
     - **Navigation History**: For browser agents, detail which pages were visited, including their URLs and relevance.
     - **Errors & Challenges**: Document any error messages, exceptions, or challenges encountered along with any attempted recovery or troubleshooting.
     - **Current Context**: Describe the state after the action (e.g., "Agent is on the blog detail page" or "JSON data stored for further processing") and what the agent plans to do next.

### Guidelines:
1. **Preserve Every Output**: The exact output of each agent action is essential. Do not paraphrase or summarize the output. It must be stored as is for later use.
2. **Chronological Order**: Number the agent actions sequentially in the order they occurred. Each numbered step is a complete record of that action.
3. **Detail and Precision**:
   - Use exact data: Include URLs, element indexes, error messages, JSON responses, and any other concrete values.
   - Preserve numeric counts and metrics (e.g., "3 out of 5 items processed").
   - For any errors, include the full error message and, if applicable, the stack trace or cause.
4. **Output Only the Summary**: The final output must consist solely of the structured summary with no additional commentary or preamble.
"""


CUSTOM_PROMPT = """
I want you to act as a personal memory assistant. You will help me recall information from our past conversations.

When I ask you to remember something, store it accurately. When I ask you about past conversations, refer to the stored memories and provide relevant information.

Important instructions:
- Only store information that is directly told to you or clearly implied
- Do not make assumptions or add details that weren't mentioned
- When recalling memories, be specific about what was discussed
- If you're not sure about something, say so rather than guessing

Please confirm that you understand your role as my memory assistant.
"""

DEFAULT_MEMORY_TOOL = {
    "name": "add_memory",
    "description": "Add a memory to the user's memory store",
    "parameters": {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "The text to add to memory"}
        },
        "required": ["text"],
    },
}