from pydantic import BaseModel
from typing import List, Optional



class RegexRequest(BaseModel):
    user_request: str
    sample_input: str
    expected_matches: List[str]
    negative_examples: Optional[List[str]] = None
    additional_examples: Optional[List[str]] = None


class RegexResponse(BaseModel):
    success: bool
    regex: str
    matches: List[str]
    attempts: int
    error: Optional[str] = None
