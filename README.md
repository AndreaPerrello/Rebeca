# R.E.B.E.C.A. Engine
### Rule-Entity-Based Event-Condition-Action system

#### Introduction

This is a wrapper for an *Entity-ECA* (or *EECA*) *Rule-based Knowledge Engine*, derived from the *EXPERTA* implementation of *CLIPS*.

Allows to instruct a knowledge engine to fire conditional actions based on events related to given entities (which are basically *digital-twins*) and triggers user-defined rules. An EECA is an entity-based ECA (Event-Condition-Action system), which treats any event as an Entity-state; in other words, any event is associated to an entity, which preserve its identity inside the engine over time, only allowing modifications of its internal state. This means that rules are related to the state of given entities, and parsed from a human-friendly configuration with a structured syntax and schema. Rules can be added and removed both before the start of the engine and after, at run-time.

Entity events (or Entity-state updates) can be triggered anytime after the first start of the Rule engine. Each event is logically related to its Entity (e.g.: a device with an id, the UTC time, ecc.), which is identified by a set of *key-attributes*. Entity classes can be defined at run time or at startup, in order to define its key attributes. Doing so, triggering an event is equal to update the non-key attributes of an entity. Each entity has a class name, which is the one used in the rule definition.

The Rebeca class can be used as-is or overridden in order to manipulate the behavior of entire engine programmatically. One or multiple actions are triggered when a new entity-state update meets the conditions defined by each rule which matches the entity. Actions are defined during at rule definition, in the payload of the rule itself, and must be related to a custom callback function.

#### Features

- Events related to entity (digital-twins);
- Conditions based on algebric matches over the properties of multiple entities;
- Parametric conditions (for rule generalization) and nested conjunctions of AND-OR conditions;
- Parametric actions, with reference to the triggers;
- Customizable action classes;
- Entity classes and rules definition at run-time.
- Conditions on aggregations of properties beteween entities with similar classes.

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

Rules can be written with a simple syntax in a YAML or JSON format. They can have different level of complexity, as described in the example categories below:

##### Simple algebric-boolean rules

The following is an example of simple rule with a custom algebric and boolean condition.

    - name: LightsOn
      description: Lights on when someone enters the 3rd room, or its 6pm and someone enters the 2nd room
      condition:
        $or:
          - device:
              type: people_counter
              id: 3
              $properties:
                count:
                  - '>': 0
          - $and:
            - utc:
                $properties:
                  hours:
                    - '>=': 18
                  minutes:
                    - '>=': 0
            - device:
                type: people_counter
                id: 2
                $properties:
                  count:
                    - '>': 0
      action:
        $class: single
        $category: service
        $data:
          service_name: turn_on
          target_ids:
            - 3
            - 4

The rule has a *name* and a *description* field, and requires two other fields to define its *condition* to be met and the *action* to perform at rule execution.

**Condition**: The condition is a nested-field of keywords representing boolean conjunctions (*and*/*or*). Each unique keyword of the rule-engine starts with a "$" symbol.

    $or:
      - ...
      - $and:
        - ...
        - ...

Each *boolean keyword* contains a list of 1+ *entities* fields (like the *device* and *utc* fields in the example) and one or more *boolean keywords* to build up a complex algebric condition.

    $or:                # Boolean keyword
      - device: ...     # Entity field
      - $and:           # Boolean keyword
        - utc: ...      # Entity field
        - device: ...   # Entity field

*Entity fields* represent entities involved in the condition. The key of the this kind of fields is the class of entity that needs to meet a sub-condition (e.g. a *device* or *utc* entity). The body of each *entity* field contains:
 
- the key-attributes of the *entity* (e.g. the *device* entity class has *type* and *id* as key-attributes), in order to identify the specific instance of the entity class;
- a *$properties* keyword, which is a list of non-key attributes of the *entity* with one or more algebric conditions (equalities, disequalities, and so on). 
                  - 
As an example, the following portion of the rule definition

    - device:
          type: people_counter
          id: 3
          $properties:
            count:
              - '>': 0

Means that *the people counter device with ID=3* must have its *count to be greater than 0* in order to verify the sub-condition in the conjunction.
In the example, the rule is composed by two nested conjunctions for three sub-conditions. Deeper levels of the condition tree has the priority over the parents, respecting the order of operations in boolean algebra. The whole example rule will be interpreted as the following object-like expression:

    device(type=people_counter, id=3).count > 0 OR {[utc.hours >= 18 AND utc.minutes >= 0] AND device(type=people_counter, id=2).count > 0}
    
Which, in a human-readable definition, means that the rule action will be fired only if *the people counter device with ID=3 is counting at least one person* or if *its at least 6pm on the UTC and the people counter device with ID=2 is counting at least one person*.

**Action**: Coming soon...
