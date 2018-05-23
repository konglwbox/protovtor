# coding: utf-8
from protovtor.fields import Field
import copy

__all__ = ("Protocol",)


class Protocol(object):
    """
    Base protocol class.

    It is usually used for validating dict data, support complex and nested data. Every protocol class you define
    must to inherit it, and you can define some field objects you expect as class variables in the class, a key
    in dict corresponds to a class variable with a prefix, the value of that key corresponds to a field object
    you expect, the protocol class will convert and validate the data as what you want, if everything works fine,
    the valid data will be returned, if there are some errors, you will receive a detailed error message.
    """

    def __init__(self, data, prefix="field_"):
        """
        :param data: dict
            The data will be converted and validated to, it must be a dict data.
        :param prefix: str
            A prefix for a field. In order to avoid variable name conflict with class's variables, protocol class
            handles the field objects with a prefix only, default 'field_'.
        """
        if not isinstance(data, dict):
            raise RuntimeError("Data must be a dict type")

        # All field instances.
        self.__fields = {}

        # The field instances validated successfully.
        self._valid_fields = {}

        # The field names discarded.
        self._discard_fields = []

        # The field instances validated wrong.
        self._error_fields = {}

        # Find field objects all.
        for name in dir(self):
            attr = getattr(self, name)

            if name.startswith(prefix) and isinstance(attr, Field):
                # Remove the field prefix.
                name = name[len(prefix):]

                # Copy a new field instance, because the field object is a class variable, if not do that, all child
                # classes data will be shared, it is wrong.
                self.__fields[name] = copy.deepcopy(attr)

        # Process the data.
        self.process(data)

    def process(self, data):
        """
        The values in data will be processed in this method, such as type conversion or something other defined in
        field class. It is an important step before validation.

        :param data: dict
            The data will be processed to.
        """
        for name, field in self.__fields.items():
            # It mean the value you expect not in the data or is none, btw, if a value is nullable, it can be set
            # none or not be set in the data.
            if data.get(name) is None:
                # If you don't like to get none values, you can discard them, the none values will be removed in
                # the result set.
                if field.nullable and field.discard:
                    self._discard_fields.append(name)
                    continue

                # If you don't mind to get none values, you can keep them, the none values will be kept in the
                # result set.
                if field.nullable and not field.discard:
                    field.value = None
                    self._valid_fields[name] = field
                    continue

                # You can set a default value for the field.
                if not field.nullable and field.default is not None:
                    data[name] = field.default

                else:
                    field.error = "The field is required"
                    self._error_fields[name] = field
                    break

            # Process the field's value.
            if not field.process(data[name]):
                self._error_fields[name] = field
                break

    def post_data(self, data):
        """
        You can overwrite this method in order to do something you like with the result data. The method will be
        called before the 'data' method return. You can do everything safely with 'data' here, because the 'data'
        has been converted and validated successfully.

        :param data: dict
            The result data will be processed to.
        :return: dict
        """
        return data

    def validate(self):
        """
        Validate the data.

        :return: bool
        """
        # There were some errors happened when processed the data, maybe.
        if self._error_fields:
            return False

        # Find all the unverified fields.
        uncheck_fields = {k: v for k, v in self.__fields.items() if
                          k not in self._valid_fields and k not in self._discard_fields}

        # Validate the field's value.
        for name, field in uncheck_fields.items():
            if not field.validate():
                self._error_fields[name] = field
                return False

        self._valid_fields.update(uncheck_fields)

        # Call the 'post_validate' method and get the error fields.
        if not self.post_validate(self._valid_fields):
            for name, field in self._valid_fields.items():
                if hasattr(field, "error") and field.error:
                    self._error_fields[name] = field

            return False

        return True

    def post_validate(self, fields):
        """
        You can overwrite this method in order to have a custom validation with the fields. The method will be
        called before the 'validate' method return.

        :param fields: dict
            The fields will be validated to.
        :return: bool
        """
        return True

    @property
    def data(self):
        """
        Get the valid data.

        :return: dict
        """
        if self._error_fields or not self._valid_fields:
            return {}

        pre_data = {name: field.value for name, field in self._valid_fields.items()}
        return self.post_data(pre_data)

    @property
    def error(self):
        """
        Get the errors.

        :return: dict
        """
        return {name: field.error for name, field in self._error_fields.items()}
