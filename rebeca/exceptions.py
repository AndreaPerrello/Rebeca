"""
Rule Engine exceptions.
"""


class RuleEngineError(Exception):

    def __init__(self, message="An unspecified RuleEngine error has occurred"):
        super().__init__(message)


# Rules

class RuleNotFoundError(RuleEngineError):

    def __init__(self, id):
        super().__init__(f"Rule with id '{id}' not found.")


class RuleParsingError(RuleEngineError):

    def __init__(self, rule_name, reason):
        super().__init__(f"Error while parsing rule '{rule_name}': {reason}")


# Actions

class ActionClassNotSupportedError(RuleEngineError):

    def __init__(self, action_class_name):
        super().__init__(f"Action class '{action_class_name}' not supported")


class ActionCategoryNotSupportedError(RuleEngineError):

    def __init__(self, category):
        super().__init__(f"Action category '{category}' not supported.")
