from pydantic import BaseModel, field_validator


class ParsedElement(BaseModel):
    text: str
    bounding_box: list[int]
    
    @field_validator('bounding_box')
    @classmethod
    def validate_bounding_box(cls, v):
        if len(v) != 4:
            raise ValueError("Bounding box must have exactly 4 elements: [left, top, right, bottom]")
        return v


class ParsedScreenshot(BaseModel):
    elements: list[ParsedElement]
