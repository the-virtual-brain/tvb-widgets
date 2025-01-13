# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#
import enum
from typing import Callable
from tvb.datatypes.connectivity import Connectivity


class ObservableAttrs(str, enum.Enum):
    """
    Enum representing observable attributes of the GlobalContext singleton
    """
    MATRIX = 'matrix'
    CONNECTIVITY = 'connectivity'


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class GlobalContext(metaclass=SingletonMeta):
    MATRIX_OPTIONS = [('Tracts', 'tracts'), ('Weights', 'weights')]

    def __init__(self):
        self.__matrix = 'weights'
        self.__connectivity = None
        self.__observed_attributes = dict()
        self.connectivities_history = []  # list of connectivities previously used

    @property
    def matrix(self):
        return self.__matrix

    @matrix.setter
    def matrix(self, next_value):
        prev_value = self.__matrix
        self.__matrix = next_value
        if prev_value != next_value:
            self.__notify_observers(ObservableAttrs.MATRIX, next_value)

    @property
    def connectivity(self):
        # type: () -> Connectivity
        return self.__connectivity

    @connectivity.setter
    def connectivity(self, next_value):
        # type: (Connectivity) -> None
        previous = self.__connectivity
        self.__connectivity = next_value
        if not len(self.connectivities_history):
            self.connectivities_history = [self.__connectivity]
        if previous and previous.gid.hex != next_value.gid.hex:
            if not any([conn.gid == next_value.gid for conn in self.connectivities_history]):
                self.connectivities_history.append(next_value)
            self.__notify_observers(ObservableAttrs.CONNECTIVITY, next_value)

    def __notify_observers(self, observed_attribute, next_value):
        # type: (str, any) -> None
        """
        Calls all the observer functions of the provided observed attribute
        passing as argument the next value for the attribute
        """
        try:
            observers = self.__observed_attributes[observed_attribute]
            for obs in observers:
                obs(next_value)
        except KeyError:
            pass

    def observe(self, observer_func, attribute_observed):
        # type: (Callable[[any], any], str) -> None
        """
        Method to register an observer for the specified value.
        When the specified value changes (if the value is set to the same as previous,
         observers are not triggered), all registered observers ar called
        with the new value passed as param.
        """
        try:
            observers_list = self.__observed_attributes[attribute_observed]
            observers_list.append(observer_func)
        except KeyError:
            self.__observed_attributes[attribute_observed] = [observer_func]

    def remove_observer(self, observer_func, value_observed):
        # type: (Callable[[any], any], str) -> None
        """
        Unregister a registered observer.
        """
        try:
            observers_list = self.__observed_attributes[value_observed]
            observers_list.remove(observer_func)
        except KeyError:
            pass


CONTEXT = GlobalContext()
