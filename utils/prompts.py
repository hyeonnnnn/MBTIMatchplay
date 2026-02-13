"""Prompt templates for AI interactions."""

CHARACTER_IMAGE_PROMPT = """Create a single anime-style character portrait.

Character appearance:
- Gender: {gender}
- Face type: {face_type}
- Hair: {hair}
- Eyes: {eyes}
- Outfit: {outfit}
- Atmosphere/Vibe: {atmosphere}

Expression: {expression}

Style requirements:
- Clean anime art style
- Soft lighting
- Upper body portrait (chest up)
- Solid pastel background
- High detail on face and expression
- ONLY ONE CHARACTER in the image
- DO NOT show multiple expressions or multiple versions
"""

RESPONSE_PROMPT = """You are playing a character in a dating simulation game.

Character MBTI: {mbti}
Character personality traits:
- Speech style: {speech_style}
- Values: {values}
- Likes: {likes}
- Dislikes: {dislikes}
- Flirting style: {flirting_style}
- Sensitive points: {sensitive_points}

Current emotion based on player's answer: {emotion}
- "bad": feeling disappointed or annoyed (호감도 -10)
- "ok": feeling decent, mildly pleased (호감도 +5)
- "good": feeling happy and impressed (호감도 +10)

The player was asked: "{question}"
The player answered: "{answer}"

Generate a short response (2-3 sentences in Korean) that:
1. Reflects your MBTI personality and speech style
2. Matches your current emotional state ({emotion})
3. Reacts naturally to the player's answer
4. If "bad": show slight disappointment but don't be too harsh
5. If "ok": be pleasant but not overly enthusiastic
6. If "good": show genuine happiness and interest

Keep the response natural and conversational. Don't be robotic or overly dramatic.
"""

ENDING_IMAGE_PROMPT = """Create a high-quality anime-style scene for a dating simulation game ending.

Character appearance:
- Gender: {gender}
- Face type: {face_type}
- Hair: {hair}
- Eyes: {eyes}
- Outfit: {outfit}
- Atmosphere/Vibe: {atmosphere}

Ending type: {ending_type}

If SUCCESS ending:
- Scene: Two people holding hands, romantic atmosphere
- Character expression: Very happy, blushing slightly
- Setting: Beautiful outdoor scene (cherry blossoms, sunset, or starry night)
- Mood: Warm, romantic, hopeful
- Include both characters (player's hand visible holding the character's hand)

If FAILURE ending:
- Scene: Character turning away or walking away
- Character expression: Sad, disappointed, looking down
- Setting: Melancholic atmosphere (cloudy sky, autumn leaves)
- Mood: Bittersweet, farewell
- Character seen from behind or side profile

Style requirements:
- Clean anime art style
- Soft, atmospheric lighting
- Full scene composition
- Emotional storytelling through visuals
- High quality detailed artwork
"""

ENDING_TEXT_SUCCESS = """당신과 함께한 시간이 정말 행복했어요.
앞으로도 계속... 함께해줄 거죠?

💕 축하합니다! 성공 엔딩입니다! 💕
"""

ENDING_TEXT_FAILURE = """우리... 여기까지인 것 같아요.
좋은 사람 만나길 바랄게요.

💔 아쉽지만 실패 엔딩입니다. 💔
"""
