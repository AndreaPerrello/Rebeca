from experta import Rule as ExpRule

from .condition import Condition
from .actions import Action


class _Rule(ExpRule):

    @property
    def action(self):
        return self._wrapped.__self__


class _RuleEngineAction:
    def __init__(self, function, category):
        self._function = function
        self._category = category

    def __call__(self, *args):
        return self


class Rule:

    def __init__(self, condition: Condition, action: Action, **kwargs):
        self._condition: Condition = condition
        self._action: Action = action
        self._data: dict = kwargs

    def __repr__(self):
        return f"Rule({self.name}, {self._condition} ==> {self._action})"

    @property
    def name(self) -> str:
        return self._data['name']

    @property
    def description(self) -> str:
        return self._data['description']

    @property
    def meta(self) -> dict:
        return self._data['meta']

    @property
    def condition(self) -> Condition:
        return self._condition

    @property
    def action(self) -> Action:
        return self._action

    def build(self) -> _Rule:
        return _Rule(self._condition.expression)(self._action.execution)

    @property
    def info(self) -> dict:
        return dict(
            name=self.name,
            description=self.description,
            meta=self.meta,
            condition=self._condition.payload,
            action=self._action.info
        )
