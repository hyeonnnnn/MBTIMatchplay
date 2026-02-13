"""AI client for OpenAI and Google Gemini API interactions."""

import streamlit as st
from openai import OpenAI
from google import genai
import base64
import requests
from io import BytesIO
from .prompts import CHARACTER_IMAGE_PROMPT, RESPONSE_PROMPT, ENDING_IMAGE_PROMPT


def get_client() -> OpenAI:
    """Get OpenAI client with API key from Streamlit secrets."""
    return OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


def get_gemini_client():
    """Get Google Gemini client with API key from Streamlit secrets."""
    return genai.Client(api_key=st.secrets["GEMINI_API_KEY"])


def generate_response(
    mbti: str,
    mbti_traits: dict,
    question: str,
    answer: str,
    emotion: str
) -> str:
    """Generate character response based on MBTI personality and emotion.

    Args:
        mbti: Character's MBTI type (e.g., "INFP")
        mbti_traits: Dictionary containing MBTI personality traits
        question: The question that was asked
        answer: Player's answer
        emotion: Emotional state - "bad", "ok", or "good"

    Returns:
        Generated response text in Korean
    """
    client = get_client()

    traits = mbti_traits.get(mbti, {})

    prompt = RESPONSE_PROMPT.format(
        mbti=mbti,
        speech_style=traits.get("speech_style", ""),
        values=traits.get("values", ""),
        likes=traits.get("likes", ""),
        dislikes=traits.get("dislikes", ""),
        flirting_style=traits.get("flirting_style", ""),
        sensitive_points=traits.get("sensitive_points", ""),
        emotion=emotion,
        question=question,
        answer=answer
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a character in a Korean dating simulation game. Respond naturally in Korean."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=200,
        temperature=0.8
    )

    return response.choices[0].message.content.strip()


def generate_character_images(
    appearance: dict,
    mbti: str
) -> dict:
    """Generate 3 character images with different expressions using Google Gemini.

    First generates neutral image, then edits it to create pout and big_smile variants.

    Args:
        appearance: Dictionary with character appearance details
            - gender, face_type, hair, eyes, outfit, atmosphere
        mbti: Character's MBTI type

    Returns:
        Dictionary with expression keys (neutral, pout, big_smile)
        and base64 encoded image data as values. 'smile' maps to 'neutral'.
    """
    from PIL import Image

    client = get_gemini_client()
    images = {}

    # Step 1: Generate neutral image first
    neutral_prompt = CHARACTER_IMAGE_PROMPT.format(
        gender=appearance.get("gender", "female"),
        face_type=appearance.get("face_type", "cute"),
        hair=appearance.get("hair", "long black hair"),
        eyes=appearance.get("eyes", "brown eyes"),
        outfit=appearance.get("outfit", "casual clothes"),
        atmosphere=appearance.get("atmosphere", "warm and friendly"),
        expression="neutral calm friendly expression with gentle smile"
    )
    neutral_prompt += f"\n\nThis character has {mbti} personality - reflect subtle personality traits in the portrait."

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=neutral_prompt,
            config=genai.types.GenerateContentConfig(
                response_modalities=["IMAGE"]
            )
        )

        neutral_image_bytes = None
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    neutral_image_bytes = part.inline_data.data
                    images["neutral"] = base64.b64encode(neutral_image_bytes).decode('utf-8')
                    break

        if not neutral_image_bytes:
            images["neutral"] = None
            images["pout"] = None
            images["big_smile"] = None
            images["smile"] = None
            return images

    except Exception as e:
        st.error(f"Error generating neutral image: {str(e)}")
        return {"neutral": None, "pout": None, "big_smile": None, "smile": None}

    # Step 2: Edit neutral image to create other expressions
    expression_edits = {
        "pout": "Change ONLY the facial expression to pouting, annoyed, sulking with puffed cheeks. Keep everything else exactly the same - same character, same clothes, same pose, same background.",
        "big_smile": "Change ONLY the facial expression to very happy, bright beaming smile with eyes slightly closed from joy. Keep everything else exactly the same - same character, same clothes, same pose, same background."
    }

    for expr_key, edit_prompt in expression_edits.items():
        try:
            # Load neutral image for editing
            neutral_pil = Image.open(BytesIO(neutral_image_bytes))

            response = client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=[edit_prompt, neutral_pil],
                config=genai.types.GenerateContentConfig(
                    response_modalities=["IMAGE"]
                )
            )

            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        img_base64 = base64.b64encode(part.inline_data.data).decode('utf-8')
                        images[expr_key] = img_base64
                        break
                else:
                    images[expr_key] = images["neutral"]  # Fallback to neutral
            else:
                images[expr_key] = images["neutral"]

        except Exception as e:
            st.error(f"Error generating {expr_key} image: {str(e)}")
            images[expr_key] = images["neutral"]  # Fallback to neutral

    # Map 'smile' to 'neutral' (no separate smile image needed)
    images["smile"] = images.get("neutral")

    return images


def generate_ending_image(
    appearance: dict,
    mbti: str,
    success: bool
) -> str:
    """Generate ending scene image using Google Gemini.

    Args:
        appearance: Dictionary with character appearance details
        mbti: Character's MBTI type
        success: True for success ending, False for failure ending

    Returns:
        Base64 encoded image data
    """
    client = get_gemini_client()

    ending_type = "SUCCESS" if success else "FAILURE"

    prompt = ENDING_IMAGE_PROMPT.format(
        gender=appearance.get("gender", "female"),
        face_type=appearance.get("face_type", "cute"),
        hair=appearance.get("hair", "long black hair"),
        eyes=appearance.get("eyes", "brown eyes"),
        outfit=appearance.get("outfit", "casual clothes"),
        atmosphere=appearance.get("atmosphere", "warm and friendly"),
        ending_type=ending_type
    )

    prompt += f"\n\nThe character has {mbti} personality."

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                response_modalities=["IMAGE"]
            )
        )

        # Extract image from response
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    img_base64 = base64.b64encode(part.inline_data.data).decode('utf-8')
                    return img_base64

        return None

    except Exception as e:
        st.error(f"Error generating ending image: {str(e)}")
        return None
