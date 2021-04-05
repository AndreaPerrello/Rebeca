from rebeca import Rebeca


class MyRuleEngine(Rebeca):

    def __init__(self):
        super().__init__()
        self.register_entity_class('device', ['id', 'type'])

    @Rebeca.action('service')
    def on_service_call(self, service_name, target_ids, params=None):
        print(f">> Calling service: '{service_name}' on device(s) {target_ids} with params: {params}")


if __name__ == '__main__':
    # Create the engine
    rule_engine = MyRuleEngine()

    import yaml
    # Add rules from yaml config file
    with open("rules.yml") as f:
        rules = yaml.safe_load(f.read())
    for rule in rules:
        rule_engine.add_rule(rule)
        print(f"Rule => {rule['name']}): {rule['description']}")
    print("")

    # Start the engine
    rule_engine.start()

    # Trigger entities states
    event_tuples = [
        ("[Event] nobody is in the 2nd room..", 'device', {'id': 2, 'type': 'people_counter', 'count': 0}),
        ("[Event] its 6.30pm..", 'utc', {'hours': 18, 'minutes': 30}),
        ("[Event] one person enters the 2nd room.. ", 'device', {'id': 2, 'type': 'people_counter', 'count': 1}),
        ("[Event] its 7.00pm..", 'utc', {'hours': 19, 'minutes': 0}),
        ("[Event] its 7.30pm..", 'utc', {'hours': 19, 'minutes': 30}),
        ("[Event] one person enters the 5th room.. ", 'device', {'id': 5, 'type': 'people_counter', 'count': 1}),
        ("[Event] its 8.00pm..", 'utc', {'hours': 20, 'minutes': 0}),
        ("[Event] its 8.30pm..", 'utc', {'hours': 20, 'minutes': 30}),
        ("[Event] nobody in the 2nd room.. ", 'device', {'id': 2, 'type': 'people_counter', 'count': 0}),
        ("[Event] Day after, 5.30pm..", 'utc', {'hours': 17, 'minutes': 30}),
        ("[Event] its 6.00pm..", 'utc', {'hours': 18, 'minutes': 0}),
        ("[Event] one person enters the 3rd room", 'device', {'id': 3, 'type': 'people_counter', 'count': 1}),
        ("[Event] its 6.30pm..", 'utc', {'hours': 18, 'minutes': 30}),
        ("[Event] its 7.00pm..", 'utc', {'hours': 19, 'minutes': 0}),
        ("[Event] its 7.30pm..", 'utc', {'hours': 19, 'minutes': 30}),
        ("[Event] its 8.00pm..", 'utc', {'hours': 20, 'minutes': 0}),
        ("[Event] its 8.30pm..", 'utc', {'hours': 20, 'minutes': 30}),
    ]
    for event_tuple in event_tuples:
        print(event_tuple[0])
        rule_engine.trigger(event_tuple[1], event_tuple[2])

