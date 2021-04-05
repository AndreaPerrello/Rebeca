from experta import Fact

from .utils import get_id_from_dict, get_id_from_list


def not_(x):
    return not x


_aggregation_callables_map = {
    'sum': sum,
    'not': not_
}


class Entity(Fact):

    class_name = 'entity'
    meta_keys = []
    attribute_keys = []
    type_class = None

    def __str__(self):
        attr = ",".join([f"{k}={v}" for k, v in self.attributes.items()])
        descriptor = f"({attr})" if self.attributes else ""
        return f"{self.__class__.__name__}{descriptor} => {self.properties}"

    @property
    def properties(self) -> dict:
        return {k: v for k, v in self.as_dict().items() if k not in self.attribute_keys}

    @property
    def attributes(self):
        return {k: v for k, v in self.as_dict().items() if k in self.attribute_keys and k not in self.meta_keys}

    @property
    def key(self):
        return get_id_from_dict(self.attributes, str(hash(self.__class__.__name__)))

    def refresh(self, properties):
        fact_id = self.__factid__
        self.__factid__ = None
        self.update(properties)
        self.__factid__ = fact_id


class AggregationFunction:

    def __init__(self, name, property, filter_name=None, **kwargs):
        self._callable = _aggregation_callables_map.get(name)
        if self._callable is None:
            raise Exception(f"'{name}' is not a valid function name")
        self._filter = _aggregation_callables_map.get(filter_name)
        self._property: str = property

    def _apply_filter(self, value):
        return value if self._filter is None else self._filter(value)

    def apply(self, properties: list) -> object:
        values = []
        for property_data in properties:
            value = property_data.get(self._property)
            if value is not None:
                values.append(self._apply_filter(value))
        return self._callable(values)


class AggregationEntity(Entity):

    meta_keys = ['entity_keys']
    attribute_keys = ['key', 'entity_keys']

    def __init__(self, function_name=None, property_name=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._function = None
        if function_name is not None and property_name is not None:
            self._function = AggregationFunction(function_name, property_name)

    @property
    def function(self) -> AggregationFunction:
        return self._function

    @classmethod
    def aggregate(cls, entity_keys: list, result, function_name: str=None, property_name: str=None):
        return cls(
            entity_keys=entity_keys,
            key=get_id_from_list(entity_keys, cls.__name__),
            result=result,
            function_name=function_name,
            property_name=property_name
        )

    @property
    def entity_keys(self) -> list:
        return self.as_dict()['entity_keys']

    @property
    def key(self):
        return self.as_dict().get('key')

    def generate_event(self, value):
        return self.aggregate(self.entity_keys, value)
