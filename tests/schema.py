"""Defines the various schema conatained in config.json."""

import warnings
from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Dict
from typing import List
from typing import Optional


@dataclass
class SelectBoxOptions:
    """Defines the selectbox options schema for config.json."""

    label: str
    value: str
    selected: Optional[bool] = field(default=None)
    disabled: Optional[bool] = field(default=None)


@dataclass
class Question:
    """Defines the question schema for config.json."""

    label: str
    name: str
    type: str
    required: bool
    options: Optional[List[SelectBoxOptions]] = field(default=None)
    custom: Optional[Dict[str, Any]] = field(default=None)

    def __post_init__(self):
        """Post initialization method to validate options."""
        if self.type == "selectbox":
            if not self.options:
                raise ValueError("Selectbox question must have options.")
            validated_options = []
            for option in self.options:
                validated_option = SelectBoxOptions(**option)
                validated_options.append(validated_option)
            self.options = validated_options
        else:
            if self.options is not None:
                warnings.warn(
                    "Options can only be used by selectbox question type.",
                    UserWarning,
                    stacklevel=2,
                )


@dataclass
class Config:
    """Defines the schema for config.json."""

    email: str
    title: str
    subject: str
    questions: List[Question]
    form_backend_url: Optional[str] = None

    def __post_init__(self):
        """Post initialization method to validate questions."""
        validated_questions = []
        for question in self.questions:
            validated_question = Question(**question)
            validated_questions.append(validated_question)
        self.questions = validated_questions


def check_config_schema(config: dict) -> bool:
    """Check if the config dictionary conforms to the expected schema."""
    try:
        # Create Config object
        _ = Config(**config)
        return True
    except (TypeError, ValueError):
        return False
