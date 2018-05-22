# coding: utf-8
from protovtor import *
from protovtor.validators import *
import unittest


class TestProtocol(unittest.TestCase):
    def test_Protocol(self):
        class Proto(Protocol):
            field_name = StringField()

            @staticmethod
            def post_data(data):
                return None

        p = Proto(dict(name="konglw"))
        self.assertTrue(p.validate())
        self.assertEqual(p.data, None)


class TestField(unittest.TestCase):
    def test_StringField(self):
        f = StringField()
        f.process(" test ")

        self.assertTrue(f.validate())
        self.assertTrue(" " not in f.value)

    def test_TextField(self):
        f = TextField()
        f.process("test\r\n")

        self.assertTrue(f.validate())
        self.assertTrue("\r\n" not in f.value)

    def test_LengthLimitTextField(self):
        f = LengthLimitTextField(limit=1)
        f.process("test")

        self.assertTrue(f.validate())
        self.assertTrue(len(f.value) == 1)

    def test_IntegerField(self):
        f = IntegerField()
        f.process("1")

        self.assertTrue(f.validate())
        self.assertTrue(f.value == 1)

    def test_FloatField(self):
        f = FloatField()
        f.process("1.1")

        self.assertTrue(f.validate())
        self.assertTrue(f.value == 1.1)

    def test_BooleanField(self):
        f = BooleanField()
        f.process("test")

        self.assertTrue(f.validate())
        self.assertTrue(f.value)

    def test_DateTimeField(self):
        f = DateTimeField()
        f.process("2018-05-21 13:47:13")

        self.assertTrue(f.validate())
        self.assertTrue(f.value)

    def test_PlaceField(self):
        f = PlaceField(handler=lambda x: int(x))
        f.process("1")

        self.assertTrue(f.validate())
        self.assertTrue(f.value == 1)

    def test_FieldList(self):
        f = FieldList(IntegerField())
        f.process(["1"])

        self.assertTrue(f.validate())
        self.assertTrue(f.value[0] == 1)

    def test_UniqueFieldList(self):
        f = UniqueFieldList(IntegerField())
        f.process(["1", "1"])

        self.assertTrue(f.validate())
        self.assertTrue(f.value[0] == 1)
        self.assertTrue(len(f.value) == 1)

    def test_ProtocolField(self):
        class Proto(Protocol):
            field_name = StringField()

        f = ProtocolField(Proto)
        f.process(dict(name="test"))

        self.assertTrue(f.validate())
        self.assertTrue(f.value)


class TestValidator(unittest.TestCase):
    def test_Length(self):
        with self.assertRaises(ValueError):
            v = Length(min=5, max=5)
            v.validate("test")

    def test_ByteSize(self):
        with self.assertRaises(ValueError):
            v = ByteSize(max=10)
            v.validate("test")

    def test_NumberRange(self):
        with self.assertRaises(ValueError):
            v = NumberRange(min=5, max=5)
            v.validate(6)

    def test_Regular(self):
        with self.assertRaises(ValueError):
            v = Regular(r"test")
            v.validate("1")

    def test_AnyOf(self):
        with self.assertRaises(ValueError):
            v = AnyOf(("1",))
            v.validate("test")

    def test_NoneOf(self):
        with self.assertRaises(ValueError):
            v = NoneOf(("1",))
            v.validate("1")

    def test_InstanceOf(self):
        with self.assertRaises(ValueError):
            v = InstanceOf((str,))
            v.validate(1)

    def test_KeyRequired(self):
        with self.assertRaises(ValueError):
            v = KeyRequired(("test",))
            v.validate(dict(name="test"))

    def test_ProtoRequired(self):
        class Proto(Protocol):
            field_age = IntegerField()

        with self.assertRaises(ValueError):
            v = ProtoRequired(Proto)
            v.validate(dict(age="test"))

    def test_DataRequired(self):
        with self.assertRaises(ValueError):
            v = DataRequired()
            v.validate(0)
