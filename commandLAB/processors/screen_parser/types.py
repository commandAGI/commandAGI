from pydantic import BaseModel

class ParsedElement(BaseModel):
    text: str
    bounding_box: list[int]

class ParsedScreenshot(BaseModel):
    elements: list[ParsedElement]
