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
    """Generate 4 character images with different expressions using Google Gemini.

    Args:
        appearance: Dictionary with character appearance details
            - gender, face_type, hair, eyes, outfit, atmosphere
        mbti: Character's MBTI type

    Returns:
        Dictionary with expression keys (neutral, pout, smile, big_smile)
        and base64 encoded image data as values
    """
    client = get_gemini_client()

    expressions = {
        "neutral": "neutral calm friendly expression",
        "pout": "pouting annoyed sulking expression with puffed cheeks",
        "smile": "gentle warm smile expression",
        "big_smile": "very happy bright beaming smile with eyes slightly closed from joy"
    }

    images = {}

    for expr_key, expr_desc in expressions.items():
        prompt = CHARACTER_IMAGE_PROMPT.format(
            gender=appearance.get("gender", "female"),
            face_type=appearance.get("face_type", "cute"),
            hair=appearance.get("hair", "long black hair"),
            eyes=appearance.get("eyes", "brown eyes"),
            outfit=appearance.get("outfit", "casual clothes"),
            atmosphere=appearance.get("atmosphere", "warm and friendly"),
            expression=expr_desc
        )

        # Add MBTI-based personality hint
        prompt += f"\n\nThis character has {mbti} personality - reflect subtle personality traits in the portrait."

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
                        images[expr_key] = img_base64
                        break
                else:
                    images[expr_key] = None
            else:
                images[expr_key] = None

        except Exception as e:
            st.error(f"Error generating {expr_key} image: {str(e)}")
            images[expr_key] = None

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
