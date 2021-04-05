import typing
from experta.activation import Activation
from experta.strategies import DepthStrategy


class _RuleEngineStrategy(DepthStrategy):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._removed_rules = list()

    def _update_agenda(self, agenda, added: typing.List[Activation], removed: typing.List[Activation]):
        super()._update_agenda(agenda, added, removed)
        for activation in removed:
            if activation.rule not in self._removed_rules:
                activation.rule.action.on_removed(activation.facts)
            self._removed_rules.append(activation.rule)
        for activation in added:
            if activation.rule not in self._removed_rules:
                activation.rule.action.on_added(activation.facts)

    def reset(self):
        self._removed_rules = list()
