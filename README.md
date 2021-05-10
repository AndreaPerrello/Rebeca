# R.E.B.E.C.A. Engine
### Rule-Entity-Based Event-Condition-Action system

#### Introduction

This is a wrapper for an *Entity-ECA* (or *EECA*) *Rule-based Knowledge Engine*, derived from the *EXPERTA* implementation of *CLIPS*.

Allows to instruct a knowledge engine to fire conditional actions based on events related to given entities, which triggers user-defined rules. An EECA is an entity-based ECA (Event-Condition-Action system), which treats any event as an Entity-state. Entities preserve their identity inside the engine over time, only allowing modifications of its state.

Rules are related to the state of given entities, and are parsed from a human-friendly JSON payload with a structured schema. Rules can be added and removed both before the start of the engine and after, at run-time.

Entity events (or Entity-state updates) can be triggered anytime after the first start of the Rule engine. Each event is logically related to its Entity (e.g.: a device with an id, the UTC time, ecc.), which is identified by a set of key-attributes. The Entity class has to be overridden in order to define what are the key attribute names of the customized Entity. Triggering an events is equal to trigger an instance of the Event class with a set of attributes. Each Entity is related to a type name, which is the one used in the rule definition. The mapping between an Entity class and the related type name must be registered by adding it in the class-level dictionary named "type_entities" or using the shortcut method "register_entity(type_name, entity_class)". Any non-registered type will be ignored in expected behavior of the rule engine.

The RuleEngine class must be overridden in order to define the behavior of the fired actions. Actions are triggered when a new Entity-state update meets the conditions defined by their rule. Action are defined during at rule definition in the JSON payload and must contain an action category. For any supported category of action, this overridden class must define the related handler method, decorated with @Action, in order to define how to handle the execution of the given category of action.


#### Usage

Import the core class:

    from rebeca import Rebeca

Create an instance of the Rebeca rule engine class:

    rebeca = Rebeca()

Register an entity class to manage on the rule engine. For example, the entity class *Device* with key attributes *id* and *type*.

    rebeca.register_entity_class('device', ['id', 'type'])
    
Define a a callback function, and add it as a callback for actions of your custom category:

    def on_action_service(self, **kwargs):
        print('Fired service:', kwargs)

    rebeca.define_action('service', on_action_service)
    
Load rules as dictionaries with a defined syntax (see more in the *Rules* section). You can load them from YAML or JSON files:

    # load rule dictionary from YAML or JSON, then add it
    rebeca.add_rule(rule)
    
Start the engine and listen for triggers:

    rebeca.start()
    
Trigger new events on the system:

    rebeca.trigger('device', {'id': 2, 'type': 'people_counter', 'count': 0})

The identity of an entity is based on its class and its key attributes. Other parameters, not contained in the key attributes defined for the entity class, will considered as properties of the entity. Both key and non-key attributes are eligible to usage on the definition of rules.

#### Rules

Coming soon..
