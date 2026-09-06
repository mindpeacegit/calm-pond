"""
Claude API를 이용해 채널별 맞춤 쇼츠 대본을 생성합니다.
config.CHANNEL 에 있는 카테고리 설정을 프롬프트에 그대로 반영합니다.

narration/search_keywords가 영어가 아닌 경우 자동으로 최대 3회까지 재시도합니다.
이미 사용한 주제는 채널별 data/<channel>/used_topics.json에 저장해 중복을 피합니다.
"""
import json
import os
import re
import anthropic
import config

MAX_RETRIES = 3


def _load_used_topics():
    if os.path.exists(config.USED_TOPICS_PATH):
        with open(config.USED_TOPICS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _save_used_topic(topic):
    used = _load_used_topics()
    used.append(topic)
    with open(config.USED_TOPICS_PATH, "w", encoding="utf-8") as f:
        json.dump(used[-500:], f, ensure_ascii=False, indent=2)


def _contains_non_english(text: str) -> bool:
    return bool(re.search(r"[\uac00-\ud7a3\u3040-\u30ff\u4e00-\u9fff]", text))


def _extract_text(response) -> str:
    return "".join(b.text for b in response.content if b.type == "text").strip()


def _call_claude(client, prompt: str) -> dict:
    response = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}],
    )
    raw_text = _extract_text(response)
    raw_text = re.sub(r"^```json|```$", "", raw_text, flags=re.MULTILINE).strip()
    return json.loads(raw_text)


def _build_prompt(avoid_list: str) -> str:
    channel = config.CHANNEL
    avoid_topics_line = ""
    if channel.get("avoid_topics"):
        avoid_topics_line = f"9. Avoid: {channel['avoid_topics']}.\n"

    return f"""You are a scriptwriter for a YouTube Shorts channel about
{channel['category_description']}.

Each short must deliver {channel['content_style']}.

Rules:
1. Never repeat a topic already covered. Already-covered topics: {avoid_list}
2. Pick ONE specific, concrete sub-topic within the channel's subject area (not a vague
   generality).
3. Do not just list facts. End with 1-2 sentences of the narrator's own short insight,
   practical takeaway, or commentary on why it matters.
4. The narration must be 90-110 words (about 35-45 seconds spoken aloud).
5. Start with a hooking first sentence.
6. IMPORTANT LANGUAGE RULE: Every field in your JSON output (narration, title,
   search_keywords, description, tags) MUST be written ONLY in English, using the Latin
   alphabet. Do NOT use Korean, Japanese, Chinese, or any non-English script anywhere,
   except the "topic" field which should be a short Korean label for internal duplicate
   tracking only.
7. search_keywords must be simple, common English nouns suitable for generic stock
   footage search (e.g. "brain closeup", "circuit board", "person thinking"). Never
   non-English words, never overly specific/obscure terms.
8. Respond with ONLY the following JSON. No other text, no markdown fences.
{avoid_topics_line}
{{
  "topic": "short topic label in Korean, for internal duplicate-tracking only",
  "title": "YouTube Shorts title in ENGLISH, under 60 characters, hooky",
  "narration": "full narration in ENGLISH, one string",
  "search_keywords": ["simple ENGLISH stock-footage keyword 1", "keyword 2"],
  "description": "YouTube description in ENGLISH, 2-3 sentences",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
}}"""


def generate_script():
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    used_topics = _load_used_topics()
    avoid_list = ", ".join(used_topics[-40:]) if used_topics else "(none)"
    prompt = _build_prompt(avoid_list)

    last_data = None
    for attempt in range(1, MAX_RETRIES + 1):
        data = _call_claude(client, prompt)
        problem_fields = [
            field
            for field in ("narration", "title", "description")
            if _contains_non_english(data.get(field, ""))
        ]
        problem_fields += [
            "search_keywords"
            for kw in data.get("search_keywords", [])
            if _contains_non_english(kw)
        ]

        if not problem_fields:
            last_data = data
            break

        print(f"[재시도 {attempt}/{MAX_RETRIES}] 비영어 텍스트 감지됨: {problem_fields}")
        last_data = data
    else:
        print("경고: 여러 번 재시도했지만 완전히 영어로만 된 결과를 못 받았습니다. "
              "마지막 결과로 계속 진행합니다.")

    data = last_data
    sentences = re.split(r"(?<=[.!?])\s+", data["narration"].strip())
    data["sentences"] = [s.strip() for s in sentences if s.strip()]

    _save_used_topic(data["topic"])
    return data


if __name__ == "__main__":
    result = generate_script()
    print(json.dumps(result, ensure_ascii=False, indent=2))
