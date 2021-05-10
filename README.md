# R.E.B.E.C.A. Engine
### Rule-Entity-Based Event-Condition-Action system

#### Introduction

This is a wrapper for an *Entity-ECA* (or *EECA*) *Rule-based Knowledge Engine*, derived from the *EXPERTA* implementation of *CLIPS*.

Allows to instruct a knowledge engine to fire conditional actions based on events related to given entities, which triggers user-defined rules. An EECA is an entity-based ECA (Event-Condition-Action system), which treats any event as an Entity-state; in other words, any event is associated to an entity, which preserve its identity inside the engine over time, only allowing modifications of its internal state. This means that rules are related to the state of given entities, and parsed from a human-friendly configuration with a structured syntax and schema. Rules can be added and removed both before the start of the engine and after, at run-time.

Entity events (or Entity-state updates) can be triggered anytime after the first start of the Rule engine. Each event is logically related to its Entity (e.g.: a device with an id, the UTC time, ecc.), which is identified by a set of *key-attributes*. Entity classes can be defined at run time or at startup, in order to define its key attributes. Doing so, triggering an event is equal to update the non-key attributes of an entity. Each entity has a class name, which is the one used in the rule definition.

The Rebeca class can be used as-is or overridden in order to manipulate the behavior of entire engine programmatically. One or multiple actions are triggered when a new entity-state update meets the conditions defined by each rule which matches the entity. Actions are defined during at rule definition, in the payload of the rule itself, and must be related to a custom callback function.

#### Features

- Eventi legati alle proprietà di classi di entità
- Condizioni su confronti algebrici di una o più proprietà delle entità
- Condizioni parametriche
- Congiunzione annidate di AND e OR di condizioni
- Classi di azioni personalizzate e parametriche
- Azioni parametriche con riferimenti alle entità della condizione
- Classi di entità definibili a run-time
- Condizioni su aggregazioni di proprietà tra entità con classi omogenee

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
