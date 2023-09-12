# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2023, TVB Widgets Team
#
from typing import Callable


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class GlobalContext(metaclass=SingletonMeta):
    MATRIX_OPTIONS = [('Tracts', 'tracts'), ('Weights', 'weights')]
    _observed_state = dict()

    def __init__(self):
        self._matrix = 'weights'

    @property
    def matrix(self):
        return self._matrix

    @matrix.setter
    def matrix(self, value):
        old_value = self._matrix
        self._matrix = value
        if old_value == value:
            return
        try:
            observers = self._observed_state['matrix']
            for observer in observers:
                observer(value)
        except KeyError:
            pass

    def observe(self, observer_func, value_observed):
        # type: (Callable[[any], any], str) -> None
        """
        Method to register an observer for the specified value.
        When the specified value changes (if the value is set to the same as previous,
         observers are not triggered), all registered observers ar called
        with the new value passed as param.
        """
        try:
            observers_list = self._observed_state[value_observed]
            observers_list.append(observer_func)
        except KeyError:
            self._observed_state[value_observed] = [observer_func]

    def remove_observer(self, observer_func, value_observed):
        # type: (Callable[[any], any], str) -> None
        """
        Unregister a registered observer.
        """
        try:
            observers_list = self._observed_state[value_observed]
            observers_list.remove(observer_func)
        except KeyError:
            pass


CONTEXT = GlobalContext()
