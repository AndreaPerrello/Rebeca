import typing

from experta import (
    KnowledgeEngine, GT, GE, LT, LE, EQ, NE,
    BETWEEN, CONTAINS, REGEX, AND, OR
)

from .rule import Rule, _RuleEngineAction
from .entity import Entity, AggregationEntity, UTC
from .strategy import _RuleEngineStrategy
from .condition import Condition, ConditionFamily, ConditionFamilyMember
from .actions import Action
from .exceptions import *

import logging

logging.getLogger('experta').disabled = True


class Rebeca:
    """
    R.E.B.E.C.A. Engine (Rule-Entity-Based Event-Condition-Action system).
    Wrapper for an Entity-ECA (aka EECA) Rule-based Knowledge Engine, derived from EXPERTA implementation of CLIPS.
    Allows to instruct a knowledge engine to fire conditional actions based on events related to given
    entities, which triggers user-defined rules. An EECA is an entity-based ECA (Event-Condition-Action system),
    which treats any event as an Entity-state. Entities preserve their identity inside the engine over time,
    only allowing modifications of its state.

    Rules are related to the state of given entities, and are parsed from a human-friendly JSON payload with a
    structured schema. Rules can be added and removed both before the start of the engine and after, at run-time.

    Entity events (or Entity-state updates) can be triggered anytime after the first start of the Rule engine.
    Each event is logically related to its Entity (e.g.: a device with an id, the UTC time, ecc.), which is identified
    by a set of key-attributes. The Entity class has to be overridden in order to define what are the key attribute
    names of the customized Entity. Triggering an events is equal to trigger an instance of the Event class with
    a set of attributes. Each Entity is related to a type name, which is the one used in the rule definition.
    The mapping between an Entity class and the related type name must be registered by adding it in the class-level
    dictionary named "type_entities" or using the shortcut method "register_entity(type_name, entity_class)".
    Any non-registered type will be ignored in expected behavior of the rule engine.

    The RuleEngine class must be overridden in order to define the behavior of the fired actions. Actions are
    triggered when a new Entity-state update meets the conditions defined by their rule. Action are defined during
    at rule definition in the JSON payload and must contain an action category. For any supported category of action,
    this overridden class must define the related handler method, decorated with @Action, in order to define how
    to handle the execution of the given category of action:
        @Action('category_name')
        def function_name(self, **kwargs):
            pass
    """

    _registered_type_entities = {}
    _basic_type_entities = {'utc': UTC}
    _category_functions = {}

    _aggregation_key = '$aggregation'
    _aggregation_function_key = '$function'
    _properties_key = '$properties'
    _property_key = '$property'
    _entities_key = '$entities'

    _comparison_operators_map = {
        ">": GT, ">=": GE,
        "<": LT, "<=": LE,
        "=": EQ, "!=": NE,
        "between": BETWEEN,
        "contains": CONTAINS,
        "regex": REGEX
    }

    _conjunctions_map = {
        "$and": AND,
        "$or": OR
    }

    def __init__(self):
        self._engine: KnowledgeEngine = None
        self._rules = dict()
        self._entities = dict()
        self._aggregation_entities = dict()

    @property
    def _strategy(self) -> _RuleEngineStrategy:
        return self._engine.strategy

    @classmethod
    def action(cls, category, *args, **kwargs):
        def wrapper(function):
            cls._category_functions[category] = function
            return _RuleEngineAction(function, category, *args, **kwargs)
        return wrapper

    @property
    def type_entities(self) -> dict:
        return {**self._registered_type_entities,
                **self._basic_type_entities}

    def _parse_rule(self, payload: dict) -> Rule:
        condition_payload = payload.pop('condition')
        action_payload = payload.pop('action')
        try:
            # Parse the condition payload
            condition = self._parse_condition(condition_payload)
            # Parse the action payload
            action = Action.parse(condition, action_payload)
        except ActionClassNotSupportedError as e:
            raise RuleParsingError(payload['name'], e)
        # Create a new rule with the parsed condition, action and the remaining payload
        return Rule(condition, action, **payload)

    def _add_rule(self, payload) -> int:
        """
        Parse the rule and save it in the storage.
        :param payload: Content of the rule to add.
        :return: The id of the stored rule.
        """
        rule: Rule = self._parse_rule(payload)

        ids = sorted(self._rules.keys())
        missing_ids = [x for x in range(ids[0], ids[-1] + 1) if x not in ids] if ids else []
        rule_id = min(missing_ids) if missing_ids else max(ids) + 1 if ids else 1

        self._rules[rule_id] = rule
        if rule.condition.is_aggregation:
            for entity_key in rule.condition.expression[0].entity_keys:
                self._aggregation_entities[entity_key] = rule
        return rule_id

    def register_entity_class(self, class_name: str, attributes: typing.List[str]):
        entity_class: Entity = type(class_name.title(), (Entity,), {"attribute_keys": attributes})
        entity_class.class_name = class_name
        self._registered_type_entities[class_name] = entity_class

    def add_rule(self, *payloads):
        """
        Parse and add one or more rule(s) to the engine, storing it.
        :param payloads: Content of the rule(s) to add.
        :return: The id of the stored rule.
        """
        # Parse and add the rule
        for payload in payloads:
            self._add_rule(payload)
        # If engine already started, restart it
        if self.is_running:
            self.restart()

    def remove_rule(self, rule_id):
        """
        Remove a rule by its id.
        :param rule_id: The id of the rule to remove.
        :return: The removed rule.
        """
        rule = self._rules.pop(rule_id, None)
        if rule is None:
            raise RuleNotFoundError(rule_id)
        if self.is_running:
            self.restart()
        return rule

    def _update_rule(self, rule_id, payload) -> bool:
        """
        Parse the rule and update it the storage.
        :param rule_id: The id of the rule.
        :param payload: Payload of the rule.
        :return: True if the rule is updated, False elsewhere.
        """
        rule = self._rules.get(rule_id)
        if rule is not None:
            rule = self._parse_rule(payload)
            self._rules[rule_id] = rule
        return rule is not None

    def update_rule(self, rule_id, payload):
        """
        Update a rule by its id.
        :param rule_id: Id of the rule to update.
        :param payload: Payload of the rule.
        """
        # Update the rule
        self._update_rule(rule_id, payload)
        # If engine already started, restart it
        if self.is_running:
            self.restart()

    def read_rules(self) -> dict:
        """
        Read the data of all the stored rules.
        :return: JSON data of the stored rules.
        """
        return {rule_id: rule.info for rule_id, rule in self._rules.items()}

    def _build_knowledge_engine(self) -> KnowledgeEngine:
        """
        Dynamically build the knowledge engine.
        :return: The KnowledgeEngine instance.
        """
        built_rules = {rule.name: rule.build() for rule in self._rules.values()}
        methods = {**{self.on_execute.__name__: self.on_execute}, **built_rules}
        return type(self.__class__.__name__, (KnowledgeEngine,), methods)()

    def _trigger(self, entity: Entity):
        """
        Declare or modify a tuple of Entity in the engine.
        :param entity: The Entity Events to declare or modify.
        """
        if self._engine is None:
            raise Exception("Must start the rule engine before adding entities")
        _entity: Entity = self._entities.get(entity.key)
        if _entity is not None:
            if entity.properties != _entity.properties:
                self._entities[entity.key] = self._engine.modify(_entity, **entity.properties)
                self._entities[entity.key].refresh(entity.properties)
        else:
            self._entities[entity.key] = self._engine.declare(*([entity]))

    def _trigger_aggregation(self, entity):
        aggregation_rule: Rule = self._aggregation_entities.get(entity.key)
        if aggregation_rule is not None:
            aggregation_entity: AggregationEntity = aggregation_rule.condition.expression[0]
            properties_list = [entity.properties for entity_key, entity in self._entities.items()
                               if entity_key in aggregation_entity.entity_keys]
            if aggregation_entity.function is not None:
                value = aggregation_entity.function.apply(properties_list)
                self._trigger(aggregation_entity.generate_event(value))

    def start(self) -> KnowledgeEngine:
        """
        Start the rule engine, dynamically building defined rules.
        """
        self._engine: KnowledgeEngine = self._build_knowledge_engine()
        self._engine.strategy = _RuleEngineStrategy()
        self._engine.reset()

    def restart(self):
        """
        Restart the rule engine. This causes all the current entities state to be re-triggered.
        """
        events = self._entities
        self._entities = dict()
        self.start()
        self._trigger(*tuple(events.values()))

    def _evaluate(self):
        """
        Evaluate current entity states on the defined rules and eventually fire related actions.
        """
        if self._engine is None:
            raise Exception("Must generate the rule engine before evaluating")
        self._engine.run()

    def trigger(self, entity_name: str, entity_data: dict):
        """
        Trigger an Entity state update and evaluate the rules.
        """
        entity_class = self.type_entities.get(entity_name)
        if entity_class is not None:
            entity = entity_class(**entity_data)
            self._trigger(entity)
            self._trigger_aggregation(entity)
            self._evaluate()
            self._strategy.reset()

    def _default_execution_function(self, category, *args, **kwargs):
        """ Default execution function for an undefined action category. """
        raise ActionCategoryNotSupportedError(category)

    def on_execute(self, action_category, *args, **kwargs):
        """
        Engine interface to get the function related to the action fired by an Entity-state update on a matched rule.
        :param action_category: Category of the action to execute.
        :return: The rule engine method to execute.
        """
        if action_category not in self._category_functions:
            default_function = self._category_functions.get('default', self._default_execution_function)
            return default_function(category=action_category, *args, **kwargs)
        return self._category_functions[action_category](self, *args, **kwargs)

    @property
    def is_running(self) -> bool:
        """ Check if the rule engine is running. """
        return self._engine is not None

    @property
    def rules(self) -> dict:
        """ Dictionary of rules defined in the engine. """
        return self._rules

    @property
    def entities(self) -> dict:
        """ Dictionary of entities states on the engine. """
        return self._entities

    def _parse_condition(self, payload):
        return self._parse_expression(payload)

    # Expression parsing

    def _parse_expression(self, payload: dict) -> Condition:
        expression_data: object = None
        is_aggregation: bool = self._aggregation_key in payload
        family: ConditionFamily = ConditionFamily()
        if is_aggregation:
            aggregation_payload: dict = payload[self._aggregation_key]
            aggregation_function_name: str = aggregation_payload[self._aggregation_function_key]
            entities = list()
            for entity_data in aggregation_payload[self._entities_key]:
                entity_name: str = list(entity_data.keys())[0]
                entity_payload: dict = entity_data[entity_name]
                aggregation_entity_class = self.type_entities.get(entity_name)
                entities.append(aggregation_entity_class(**entity_payload))
            entity_keys: list = [entity.key for entity in entities]
            aggregation_property: dict = aggregation_payload[self._property_key]
            aggregation_property_name: str = list(aggregation_property.keys())[0]
            aggregation_property_payload: typing.List[dict] = aggregation_property[aggregation_property_name]
            result_comparisons = self._parse_comparisons(aggregation_property_payload)
            if all([k is not None for k in entity_keys]):
                aggregation_entity = AggregationEntity.aggregate(
                    function_name=aggregation_function_name,
                    property_name=aggregation_property_name,
                    entity_keys=entity_keys, result=result_comparisons)
                expression_data = AND(aggregation_entity)
        else:
            expression_data = self._parse_expression_recursive(payload, family)
        if expression_data is None:
            raise Exception(f"Expression '{payload}' is not valid")
        return Condition(expression_data, payload, is_aggregation, family)

    def _parse_expression_recursive(self, payload, family: ConditionFamily) -> object:
        for k, v in payload.items():
            if k.startswith('$'):
                family_member: ConditionFamilyMember = family.parse_add_member(k, self.type_entities)
                if family_member is not None:
                    return self._parse_entity(family_member.entity_class.class_name, v)
                conjunction_class = self._conjunctions_map.get(k)
                if conjunction_class is None:
                    raise Exception(f"Conjunction '{k}' not valid.")
                if not isinstance(v, list):
                    raise Exception(f"Conjunction '{k}' does not contain a list of expressions.")
                conjunction_args = [self._parse_expression_recursive(vi, family) for vi in v]
                return conjunction_class(*conjunction_args)
            elif self._properties_key in v:
                return self._parse_entity(k, v)

    def _parse_comparisons(self, comparisons: typing.List[dict]) -> object:
        comparison_args = list()
        for comparison in comparisons:
            for operator_key, values in comparison.items():
                operator = self._comparison_operators_map.get(operator_key)
                if operator is None:
                    raise Exception(f"'{operator_key}' is not a valid operator.")
                if not isinstance(values, list):
                    values = [values]
                comparison_args.append(operator(*tuple(values)))
        return AND(*tuple(comparison_args))

    def _parse_entity(self, entity_class_name: str, entity_data: dict):
        entity_properties = entity_data.pop(self._properties_key)
        entity_properties = {
            name: self._parse_comparisons(comparisons)
            for name, comparisons in entity_properties.items()
        }
        entity_class = self.type_entities.get(entity_class_name)
        entity_payload = {**entity_data, **entity_properties}
        return entity_class(**entity_payload)
