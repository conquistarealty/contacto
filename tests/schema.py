"""Defines the various schema conatained in config.json."""

import warnings
from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from dataclasses import field
from typing import Optional


class Schema(ABC):
    """Base class for schema validation."""

    @abstractmethod
    def __post_init__(self):
        """Abstract method for validation."""
        pass

    def validate_type(self):
        """Default implementation of type validation."""
        for field_name, field_type in self.__annotations__.items():
            if field_name in self.__dataclass_fields__:
                actual_type = type(getattr(self, field_name))
                if not issubclass(actual_type, field_type):
                    raise TypeError(
                        f"Expected {field_name:!r} to be of type "
                        f"{field_type.__name__}, got {actual_type.__name__}"
                    )


@dataclass
class SelectBoxOptions(Schema):
    """Defines the selectbox options schema for config.json."""

    label: str
    value: str
    selected: Optional[bool] = field(default=None)
    disabled: Optional[bool] = field(default=None)

    def __post_init__(self):
        """Perform validation."""
        # check type
        self.validate_type()


@dataclass
class Question(Schema):
    """Defines the question schema for config.json."""

    label: list | str
    name: str
    type: str
    required: bool
    options: Optional[list] = field(default=None)
    custom: Optional[dict] = field(default=None)

    def __post_init__(self):
        """Post initialization method to validate options."""
        # type validation
        self.validate_type()

        # custom validation for selectbox input type
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

        # validate label
        if isinstance(self.label, list):
            # loop through each string
            valid_label = []
            for line in self.label:
                if not isinstance(line, str):
                    raise ValueError("Label list only allows strings.")
                valid_label.append(line)

            # now join all strings and update instructions
            self.label = " ".join(valid_label)


@dataclass
class Config(Schema):
    """Defines the schema for config.json."""

    email: str
    title: str
    subject: str
    questions: list
    form_backend_url: Optional[str] = None
    ignore_file_upload: Optional[bool] = None
    instructions: Optional[list | str] = None

    def __post_init__(self):
        """Post initialization method to validate questions."""
        # check type
        self.validate_type()

        # validate questions
        validated_questions = []
        for question in self.questions:
            validated_question = Question(**question)
            validated_questions.append(validated_question)
        self.questions = validated_questions

        # validate instructions
        if isinstance(self.instructions, list):
            # loop through each string
            valid_instructions = []
            for line in self.instructions:
                if not isinstance(line, str):
                    raise ValueError("Instructions list only allows strings.")
                valid_instructions.append(line)

            # now join all strings and update instructions
            self.instructions = " ".join(valid_instructions)


def check_config_schema(config: dict) -> bool:
    """Check if the config dictionary conforms to the expected schema."""
    # initialize success flag to False
    success = False

    # attempt to validate config ...
    try:
        # create Config object
        _ = Config(**config)

        # validation is successful
        success = True

    # ... problem occured
    except (TypeError, ValueError) as e:
        raise AssertionError(f"Config schema validation failed: {e}") from e

    # return the success flag
    else:
        return success
