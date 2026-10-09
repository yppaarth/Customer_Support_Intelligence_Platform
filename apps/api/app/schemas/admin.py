from pydantic import BaseModel, Field


class SettingsOut(BaseModel):
    autonomous_send_enabled: bool
    retention_days: int
    model_settings: dict


class SettingsUpdate(BaseModel):
    autonomous_send_enabled: bool | None = None
    retention_days: int | None = Field(default=None, ge=1, le=3650)
    model_settings: dict | None = None


class DocumentCreate(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    content: str = Field(min_length=20, max_length=100_000)
    source_type: str = "markdown"
