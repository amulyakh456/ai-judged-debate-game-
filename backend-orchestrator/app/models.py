from pydantic import BaseModel
from typing import Dict, Optional

# --- WebSocket Message Models ---
class WsMessage(BaseModel):
    type: str
    user_id: str

class WsMsg_Transcript(WsMessage):
    type: str = "transcript"
    text: str
    is_final: bool

class WsMsg_DebateState(WsMessage):
    type: str = "debate_state"
    message: str

class WsMsg_Error(WsMessage):
    type: str = "error"
    error: str

# --- LLM Judge Models (for our mock service) ---
class ScoreSet(BaseModel):
    clarity: int
    logic: int
    evidence: int
    emotional_appeal: int

class JudgeScores(BaseModel):
    user_a: ScoreSet
    user_b: ScoreSet

class JudgeFeedback(BaseModel):
    user_a: str
    user_b: str

class JudgeResult(BaseModel):
    winner: str
    scores: JudgeScores
    feedback: JudgeFeedback
