import typing

from experta.conditionalelement import ConditionalElement

from .entity import Entity


class ConditionFamilyMember:

    def __init__(self, key: str, entity_class: Entity, alias: str):
        self._key: str = key
        self._entity_class = entity_class
        self._alias: str = alias

    @property
    def entity_class(self) -> Entity:
        return self._entity_class


class ConditionFamily:

    _function_key = '->'
    _alias_key = '||'
    _any_key = '$any'
    _keys = [_any_key]

    def __init__(self):
        self._members: typing.Dict[str, ConditionFamilyMember] = dict()

    def parse_add_member(self, k, type_entities: dict) -> ConditionFamilyMember:
        for key in self._keys:
            if k.startswith(key):
                definition = k.split(self._function_key)[1]
                entity_class_name, alias = definition.split(self._alias_key)
                entity_class = type_entities.get(entity_class_name)
                member = ConditionFamilyMember(key, entity_class, alias)
                self._members[alias] = member
                return member

    def get_member(self, k):
        return self._members.get(k)

    @property
    def members(self) -> typing.Dict[str, ConditionFamilyMember]:
        return self._members

    def match(self, fact: Entity):
        for member in self._members.values():
            if member.entity_class.class_name == fact.class_name:
                return member


class Condition:

    def __init__(self, data: ConditionalElement, payload: dict, is_aggregation: bool=False,
                 family: ConditionFamily=None):
        self._expression: ConditionalElement = data
        self._is_aggregation: bool = is_aggregation
        self._family: ConditionFamily = family
        self._payload: dict = payload

    @property
    def expression(self) -> ConditionalElement:
        return self._expression

    @property
    def payload(self) -> dict:
        return self._payload

    @property
    def is_aggregation(self):
        return self._is_aggregation

    @property
    def family(self) -> ConditionFamily:
        return self._family
