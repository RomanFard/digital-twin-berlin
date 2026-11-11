import os
from groq import Groq
from fastapi import APIRouter
from pydantic import BaseModel
from database import get_connection, return_connection

router = APIRouter()
client = Groq(api_key=os.environ["GROQ_API_KEY"])

GROQ_MODEL = "openai/gpt-oss-120b"


class ExplainRequest(BaseModel):
    feature_id: str
    violation_type: str
    species: str
    overlap_amount: float
    language: str = "de"


PROMPT_TEMPLATE = """You are an urban planning advisor explaining a design rule
violation to a non-technical municipal employee.

Rule context: German tree root protection (Wurzelschutzradius, DIN 18920).
Construction work must stay outside a protective radius around a tree's
trunk, calculated from trunk circumference, to avoid root damage.

This specific case:
- Tree species: {species}
- The protection radius overlaps a nearby building's foundation by {overlap_amount:.1f} meters

Write your answer in {language_name}. In 2-3 short sentences:
1. Explain plainly why this counts as a violation.
2. Suggest one concrete, practical way to resolve it.

Keep it under 60 words total."""

LANGUAGE_NAMES = {"de": "German", "en": "English"}


@router.post("/api/rules/explain")
def explain_violation(req: ExplainRequest):
    conn = get_connection()
    try:
        cur = conn.cursor()

        cur.execute(
            "SELECT explanation FROM rule_explanations WHERE feature_id = %s AND violation_type = %s",
            (req.feature_id, req.violation_type),
        )
        row = cur.fetchone()
        if row:
            cur.close()
            return {"explanation": row[0], "cached": True}

        prompt = PROMPT_TEMPLATE.format(
            species=req.species,
            overlap_amount=req.overlap_amount,
            language_name=LANGUAGE_NAMES.get(req.language, "German"),
        )

        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )
        explanation = completion.choices[0].message.content.strip()

        cur.execute(
            "INSERT INTO rule_explanations (feature_id, violation_type, explanation) VALUES (%s, %s, %s)",
            (req.feature_id, req.violation_type, explanation),
        )
        conn.commit()
        cur.close()

        return {"explanation": explanation, "cached": False}
    finally:
        return_connection(conn)