# coding: utf-8
from datetime import datetime
import copy

__all__ = (
    "Field",
    "BaseField",
    "StringField",
    "TextField",
    "LengthLimitTextField",
    "IntegerField",
    "FloatField",
    "BooleanField",
    "DateTimeField",
    "PlaceField",
    "FieldList",
    "UniqueFieldList",
    "ProtocolField"
)


class Field(object):
    """
    Base field class.
    """

    def __init__(self, default=None, nullable=False, discard=False):
        """
        :param default:
            The default value for the field, It is valid when 'nullable' is 'False' and the value you expect
            is none or not in the data.
        :param nullable:
            If you not sure the data has the value all the time, then you can set it to 'True', unless you
            set the default value.
        :param discard:
            You can discard the none value if you don't need it. Used together with 'nullable'. If you set
            it to 'False' and 'nullable' is 'True', the field's value will be 'None', even if the value not
            in the data.
        """
        self.default = default
        self.nullable = nullable
        self.discard = discard
        self.value = None
        self.error = None

    def process(self, value):
        """
        Process the value here, set the value processed to 'self.value' here and remember to set 'self.error'
        if some errors happened.

        :param value:
            The value will be processed to.
        :return: bool
        """

        # self.value = "the value processed"
        # self.error = "some errors"
        raise NotImplementedError()

    def validate(self):
        """
        Validate the value here, remember to set 'self.error' if some errors happened.

        :return: bool
        """

        # Remember to set 'self.error' if some errors happened. It is the only way for higher level to known
        # whether the field has error.
        #
        # self.error = "some errors"
        raise NotImplementedError()

    def __deepcopy__(self, *args, **kwargs):
        """
        Return a new field instance.

        Because the field object is a class variable, If not do that, the field's data in all child protocol
        classes will be shared all the life, it is wrong.

        :return: Field
        """
        raise NotImplementedError()


class BaseField(Field):
    """
    More useful base field class.
    """

    def __init__(self, validators=(), *args, **kwargs):
        """
        :param validators: list
            Validators chain, will be called sequentially.
        """
        self._validators = validators

        super(BaseField, self).__init__(*args, **kwargs)

    def process(self, value):
        raise NotImplementedError()

    def validate(self):
        try:
            for x in self._validators:
                x.validate(self.value)

        except ValueError as e:
            # To tell higher level the field has an error.
            self.error = str(e)
            return False

        except TypeError as e:
            # We get an unexpected error.
            raise RuntimeError(e)

        return True

    def __deepcopy__(self, *args, **kwargs):
        # Copy a new field instance.
        return self.__class__(
            validators=self._validators,
            default=self.default,
            nullable=self.nullable,
            discard=self.discard
        )


class StringField(BaseField):
    """
    You should process and validate string value with this field. The method 'strip' will be called.
    """

    def process(self, value):
        try:
            self.value = str(value).strip()

        except Exception:
            self.error = "Not a valid str value"
            return False

        return True


class TextField(StringField):
    """
    You should process and validate string value with this field. The method 'strip' will be called
    and "\r\n" will be replaced to "\n" in this time.
    """

    def process(self, value):
        if super(TextField, self).process(value):
            self.value = self.value.replace("\r\n", "\n")
            return True

        return False


class LengthLimitTextField(TextField):
    """
    You should process and validate string value with this field. The string will be cut if the length
    of the string more than 'limit'. The method 'strip' will be called and "\r\n" will be replaced to
    "\n" in this time.
    """

    def __init__(self, limit, *args, **kwargs):
        """
        :param limit: int
            The max length of the string, if more than 'limit', the string will be cut.
        """
        self.__limit = limit

        super(LengthLimitTextField, self).__init__(*args, **kwargs)

    def process(self, value):
        if super(LengthLimitTextField, self).process(value):
            # Cut.
            if len(self.value) > self.__limit:
                self.value = self.value[0:self.__limit]

            return True

        return False

    def __deepcopy__(self, *args, **kwargs):
        return self.__class__(
            self.__limit,
            validators=self._validators,
            default=self.default,
            nullable=self.nullable,
            discard=self.discard
        )


class IntegerField(BaseField):
    """
    You should process and validate int value with this field.
    """

    def process(self, value):
        try:
            self.value = int(value)

        except Exception:
            self.error = "Not a valid int value"
            return False

        return True


class FloatField(BaseField):
    """
    You should process and validate float value with this field.
    """

    def __init__(self, precision=2, *args, **kwargs):
        """
        :param precision: int
            The precision of the float value.
        """
        self.__precision = precision

        super(FloatField, self).__init__(*args, **kwargs)

    def process(self, value):
        try:
            self.value = round(float(value), self.__precision)

        except Exception:
            self.error = "Not a valid float value"
            return False

        return True

    def __deepcopy__(self, *args, **kwargs):
        return self.__class__(
            precision=self.__precision,
            validators=self._validators,
            default=self.default,
            nullable=self.nullable,
            discard=self.discard
        )


class BooleanField(BaseField):
    """
    You should process and validate bool value with this field.
    """

    def process(self, value):
        try:
            self.value = bool(value)

        except Exception:
            self.error = "Not a valid bool value"
            return False

        return True


class DateTimeField(BaseField):
    """
    You should process and validate datetime value with this field.
    """

    def __init__(self, format="%Y-%m-%d %H:%M:%S", *args, **kwargs):
        """
        :param format: str
            The format of the datetime.
        """
        self.__format = format

        super(DateTimeField, self).__init__(*args, **kwargs)

    def process(self, value):
        try:
            self.value = datetime.strptime(value, self.__format)

        except Exception:
            self.error = "Not a valid datetime value"
            return False

        return True


class PlaceField(BaseField):
    """
    If the value in data need to be pre-processed, and pass the value to another field to be processed, you
    should use this field.
    """

    def __init__(self, field=None, handler=None, *args, **kwargs):
        """
        :param field: Field
            Pass the value to another field to be processed.
        :param handler: callable
            The value handler, such as 'json.loads' or others.
        """
        if handler and not callable(handler):
            raise RuntimeError("The processor is not callable")

        self.__field = field
        self.__handler = handler
        self.__value = None

        super(PlaceField, self).__init__(*args, **kwargs)

    def process(self, value):
        if self.__handler:
            try:
                self.__value = self.__handler(value)

            except Exception:
                self.error = "The value processed error"
                return False

        else:
            self.__value = value

        # Process the value by a field.
        if self.__field:
            if not self.__field.process(self.__value):
                self.error = self.__field.error
                return False

        return True

    def validate(self):
        # Validate the value by a field.
        if self.__field:
            if not self.__field.validate():
                self.error = self.__field.error
                return False

        return super(PlaceField, self).validate()

    def __deepcopy__(self, *args, **kwargs):
        return self.__class__(
            field=copy.deepcopy(self.__field),
            handler=self.__handler,
            validators=self._validators,
            default=self.default,
            nullable=self.nullable,
            discard=self.discard
        )

    @property
    def value(self):
        return self.__field.value if self.__field else self.__value

    @value.setter
    def value(self, value):
        self.__value = value


class FieldList(BaseField):
    """
    You should process and validate list-like value with this field.
    """

    def __init__(self, field, *args, **kwargs):
        """
        :param field: Field
            Each value in list will be processed and validated by 'field' implement.
        """
        self.__entries = []
        self.__field = field

        super(FieldList, self).__init__(*args, **kwargs)

        # Put here is because of the 'self.value' has been covered by super.
        self.__value = []

    def process(self, value):
        if not isinstance(value, (tuple, list, set)):
            self.error = "Not a valid list value"
            return False

        for x, y in enumerate(value):
            # If not, there will be a share data problem.
            field_new = copy.deepcopy(self.__field)

            if not field_new.process(y):
                self.error = [x, field_new.error]
                return False

            self.__entries.append(field_new)

        return True

    def validate(self):
        for x, y in enumerate(self.__entries):
            if not y.validate():
                self.error = [x, y.error]

                return False

        return super(FieldList, self).validate()

    def __deepcopy__(self, *args, **kwargs):
        return self.__class__(
            field=copy.deepcopy(self.__field),
            validators=self._validators,
            default=self.default,
            nullable=self.nullable,
            discard=self.discard
        )

    @property
    def value(self):
        return list(x.value for x in self.__entries) if self.__entries else self.__value

    @value.setter
    def value(self, value):
        self.__value = value


class UniqueFieldList(FieldList):
    """
    You should process and validate list-like value with this field. The difference is the repeat values
    will be removed, and it can not ensure the sequence.
    """

    def process(self, value):
        if isinstance(value, (tuple, list)):
            try:
                d = {x: True for x in value}

            except TypeError:
                self.error = "Not a valid one-dimensional list value"
                return False

        return super(UniqueFieldList, self).process(tuple(d.keys()))


class ProtocolField(Field):
    """
    You should process and validate dict value with this field.
    """

    def __init__(self, protoclass, *args, **kwargs):
        """
        :param protoclass: Protocol
            The value will be processed and validated by a protocol class of 'protoclass'.
        """
        self.__protoclass = protoclass
        self.__protocol = None
        self.__error = ""

        super(ProtocolField, self).__init__(*args, **kwargs)

        # Put here is because of the 'self.value' has been covered by super.
        self.__value = {}

    def process(self, value):
        try:
            self.__protocol = self.__protoclass(value)

        except RuntimeError:
            self.__error = "Not a valid dict value"
            return False

        return True

    def validate(self):
        return self.__protocol.validate()

    def __deepcopy__(self, *args, **kwargs):
        return self.__class__(
            protoclass=copy.deepcopy(self.__protoclass),
            default=self.default,
            nullable=self.nullable,
            discard=self.discard
        )

    @property
    def value(self):
        return self.__protocol.data if self.__protocol else self.__value

    @value.setter
    def value(self, value):
        self.__value = value

    @property
    def error(self):
        return self.__error if self.__error else self.__protocol.error

    @error.setter
    def error(self, error):
        self.__error = error
