import json
import re
from abc import ABC

from .condition import Condition
from .exceptions import ActionClassNotSupportedError


_category_key = '$category'
_class_key = '$class'
_data_key = '$data'
_enter_key = '$enter'
_exit_key = '$exit'


class Action(ABC):

    class_name = 'default'

    def __init__(self, condition: Condition, category: str, data: dict):
        self._condition: Condition = condition
        self._category: str = category
        self._data: dict = data
        self._engine = None
        self._facts: tuple = tuple()

    def __repr__(self):
        return f"{self.__class__.__name__}(category={self._category}, {self._data})"

    def execution(self, engine, *args, **kwargs):
        self._engine = engine

    def _on_event(self, facts):
        self._facts = facts

    def on_added(self, facts):
        self._on_event(facts)

    def on_removed(self, facts):
        self._on_event(facts)

    def on_trigger(self):
        pass

    def _on_execute(self, data=None):
        if self._engine is not None:
            if data is None:
                data = self._data
            plain_data = json.dumps(data)
            matches = re.findall(r'"\$([^"]*)"', plain_data)
            for match in matches:
                alias, property_name = match.split('.')
                member = self._condition.family.get_member(alias)
                if member is None:
                    raise Exception(f"Rule member '{alias}' undefined")
                for fact in self._facts:
                    if fact.class_name == member.entity_class.class_name:
                        property_value = str(fact.attributes.get(property_name))
                        if property_value.isdigit():
                            property_value = f'§{property_value}§'
                        plain_data = plain_data.replace(f"${match}", property_value)
            plain_data = plain_data.replace('"§', '').replace('§"', '')
            parsed_data = json.loads(plain_data)
            self._engine.on_execute(action_category=self._category, **parsed_data)

    @property
    def category(self):
        return self._category

    @property
    def info(self) -> dict:
        return {'category': self._category, 'class': self.class_name, 'data': self._data}

    @classmethod
    def parse(cls, condition: Condition, payload: dict):
        action_class_name = payload.pop(_class_key, None)
        action_class = None
        for subclass in cls.__subclasses__():
            if subclass.class_name == action_class_name:
                action_class = subclass
        if action_class is None:
            raise ActionClassNotSupportedError(action_class_name)
        action_category = payload.pop(_category_key)
        action_data = payload.pop(_data_key)
        return action_class(condition, action_category, action_data)


class SingleTimeAction(Action):

    class_name = 'single'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._executed = False
        self._can_execute = False

    def execution(self, engine, *args, **kwargs):
        super().execution(engine)
        if self._can_execute and not self._executed:
            self._on_execute(self._data.get(_enter_key))
            self._executed = True

    def on_added(self, facts):
        super().on_added(facts)
        self._can_execute = True
        self._executed = False

    def on_removed(self, facts):
        super().on_removed(facts)
        self._can_execute = False
        if self._executed and 'exit' in self._data:
            self._on_execute(self._data.get(_exit_key))
