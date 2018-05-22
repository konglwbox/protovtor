# coding: utf-8
from protovtor.protocol import Protocol
import sys
import re

__all__ = (
    "Validator",
    "Length",
    "ByteSize",
    "NumberRange",
    "Regular",
    "AnyOf",
    "NoneOf",
    "InstanceOf",
    "KeyRequired",
    "ProtoRequired",
    "DataRequired"
)


class Validator(object):
    """
    Base validator class.
    """

    def validate(self, value):
        """
        Validate the value here.

        :param value:
            The value will be validated to.
        :raise ValueError:
            You should raise 'ValueError' if the value validated failed.
        """
        raise NotImplementedError()


class Length(Validator):
    """
    You should validate string value with this validator.
    """

    def __init__(self, min=-1, max=-1):
        """
        :param min: int
            The min length.
        :param max: int
            The max length.
        """
        if not (isinstance(min, int) and isinstance(max, int)):
            raise RuntimeError("The min and max must be int type")

        if min == max == -1:
            raise RuntimeError("The min and max must be set one at least")

        if min < -1 or max < -1:
            raise RuntimeError("The min and max must be a positive int value")

        if min != max != -1 and min > max:
            raise RuntimeError("The min can not greater then max")

        self._min = min
        self._max = max

    def validate(self, value):
        value_length = len(value)

        if self._min == -1:
            if value_length > self._max:
                raise ValueError("Can not longer then {0}".format(self._max))

        elif self._max == -1:
            if value_length < self._min:
                raise ValueError("Can not shorter then {0}".format(self._min))

        else:
            if not (self._min <= value_length <= self._max):
                raise ValueError("Must between {min} and {max} chars length".format(min=self._min, max=self._max))


class ByteSize(Validator):
    """
    You should validate value bytes size with this validator.
    """

    def __init__(self, max):
        """
        :param max: int
            The max bytes size.
        """
        if not isinstance(max, int):
            raise RuntimeError("The max must be int type")

        if max <= 0:
            raise RuntimeError("The max must be a valid positive int value")

        self._max = max

    def validate(self, value):
        value_size = sys.getsizeof(value)

        if value_size > self._max:
            raise ValueError("Can not greater then {0} bytes size".format(self._max))


class NumberRange(Length):
    """
    You should validate number value interval with this validator.
    """

    def validate(self, value):
        if self._min == -1:
            if value > self._max:
                raise ValueError("Can not greater then {0}".format(self._max))

        elif self._max == -1:
            if value < self._min:
                raise ValueError("Can not less than {0}".format(self._min))

        else:
            if not (self._min <= value <= self._max):
                raise ValueError("Must between {min} and {max}".format(min=self._min, max=self._max))


class Regular(Validator):
    """
    You should validate string value with this validator.
    """

    def __init__(self, pattern):
        """
        :param pattern: str
            The pattern of the regular.
        """
        self._pattern = pattern
        self._compile_pattern = re.compile(pattern)

    def validate(self, value):
        if not self._compile_pattern.match(value):
            raise ValueError("Not match the pattern: {0}".format(self._pattern))


class AnyOf(Validator):
    """
    You should validate a value that must be one of the values you define.
    """

    def __init__(self, values):
        """
        :param values: list
            The set that the value must be one of it.
        """
        if not isinstance(values, (tuple, list)):
            raise RuntimeError("The values must be tuple or list type")

        self._values = values

    def validate(self, value):
        if value not in self._values:
            raise ValueError("Must be one of {0}".format(self._values))


class NoneOf(AnyOf):
    """
    You should validate a value that must not be one of the values you define.
    """

    def validate(self, value):
        if value in self._values:
            raise ValueError("Can not be one of {0}".format(self._values))


class InstanceOf(AnyOf):
    """
    You should validate a value's type that must be one of the values you define.
    """

    def __init__(self, *args, **kwargs):
        super(InstanceOf, self).__init__(*args, **kwargs)

        for x in self._values:
            if not isinstance(x, type):
                raise RuntimeError("Each value must be a type type")

    def validate(self, value):
        if not isinstance(value, tuple(self._values)):
            raise ValueError("Must be instance of {0}".format(self._values))


class KeyRequired(Validator):
    """
    You should validate dict value with this validator. The keys in value must be all existed.
    """

    def __init__(self, values):
        """
        :param values: list
            The keys will be validated. The keys in value must be all existed in the values.
        """
        if not isinstance(values, (tuple, list)):
            raise RuntimeError("The values must be tuple or list type")

        self._values = values

    def validate(self, value):
        for key in self._values:
            if key not in value:
                raise ValueError("Must has key: {0}".format(key))


class ProtoRequired(Validator):
    """
    You should validate dict value with this validator. The value must be validated successfully with the
    protocol class you set.
    """

    def __init__(self, protoclass):
        """
        :param protoclass:
            The protocol class that the value will be validated to.
        """
        if not issubclass(protoclass, Protocol):
            raise RuntimeError("The value must be a protocol type")

        self._protoclass = protoclass

    def validate(self, value):
        proto = self._protoclass(value)

        if not proto.validate():
            raise ValueError("Must be a valid value of {0}: {1}".format(self._protoclass, proto.error))


class DataRequired(Validator):
    """
    You should validate a value that must not be a zero value.
    """

    def validate(self, value):
        if not value:
            raise ValueError("The value is required")
