"""Serialization module.

This holds a class for simple serialization of Python objects.
"""
import abc


class Serializable(abc.ABC):
    """Serializable base class.

    This class allows subclasses to easily serialize into simple Python
    data types which can be serialized into JSON.
    """

    def encode(self):
        """Encode and return a simple Python data type.

        Produce a simple Python data type for serialization.
        """
        return self.__dict__

    @staticmethod
    @abc.abstractmethod
    def decode(data):
        """Decode a serialized object and return an instance.

        Decode a simple Python data type and return and instance of
        the object.
        """
