import cftime
import datetime
from django.test import TestCase
from django.core.exceptions import ValidationError
from .models import TestModel

class ExtendedDateTimeFieldTests(TestCase):

    def test_save_retrieve_none(self):
        """Test saving and retrieving None."""
        m = TestModel.objects.create(name="Test None")
        self.assertIsNone(m.timestamp)
        retrieved = TestModel.objects.get(pk=m.pk)
        self.assertIsNone(retrieved.timestamp)

    def test_save_retrieve_standard_datetime(self):
        """Test saving and retrieving a standard datetime.datetime object."""
        now = datetime.datetime.now()
        # Ensure microseconds are handled if the DB supports them, round otherwise
        now = now.replace(microsecond=0) # Simplification for now
        m = TestModel.objects.create(name="Test Standard Datetime", timestamp=now)
        retrieved = TestModel.objects.get(pk=m.pk)

        # The field's from_db_value converts standard datetimes to cftime
        self.assertIsInstance(retrieved.timestamp, cftime.datetime)
        self.assertEqual(retrieved.timestamp.year, now.year)
        self.assertEqual(retrieved.timestamp.month, now.month)
        self.assertEqual(retrieved.timestamp.day, now.day)
        self.assertEqual(retrieved.timestamp.hour, now.hour)
        self.assertEqual(retrieved.timestamp.minute, now.minute)
        self.assertEqual(retrieved.timestamp.second, now.second)
        self.assertEqual(retrieved.timestamp.microsecond, now.microsecond)
        # TZ info might require more setup (settings.USE_TZ)
        # self.assertEqual(retrieved.timestamp.tzinfo, now.tzinfo)

    def test_save_retrieve_cftime_standard_range(self):
        """Test saving and retrieving a cftime object within the standard range."""
        cftime_dt = cftime.datetime(2023, 10, 26, 12, 30, 15, calendar='standard')
        m = TestModel.objects.create(name="Test Cftime Standard", timestamp=cftime_dt)
        retrieved = TestModel.objects.get(pk=m.pk)
        self.assertIsInstance(retrieved.timestamp, cftime.datetime)
        self.assertEqual(retrieved.timestamp, cftime_dt)

    # ----- Tests expected to fail until implementation -----

    # def test_save_retrieve_cftime_bc(self):
    #     """Test saving and retrieving a BC date using cftime."""
    #     # Note: This requires from_db_value and get_prep_value implementations
    #     cftime_bc = cftime.datetime(-44, 3, 15, 10, 0, 0, calendar='standard') # Approx. Ides of March, 44 BC
    #     with self.assertRaises(NotImplementedError): # Expecting failure for now
    #         m = TestModel.objects.create(name="Test Cftime BC", timestamp=cftime_bc)
    #     # Once implemented, remove assertRaises and add retrieval check:
    #     # retrieved = TestModel.objects.get(pk=m.pk)
    #     # self.assertEqual(retrieved.timestamp, cftime_bc)

    # def test_invalid_string_input_model(self):
    #      """Test that assigning an invalid string directly to the model field raises an error."""
    #      # Direct assignment bypasses form validation but should ideally fail
    #      # during save/get_prep_value or type checking.
    #      # Depending on get_prep_value, this might raise TypeError or NotImplementedError
    #      with self.assertRaises((TypeError, NotImplementedError, ValidationError)):
    #           TestModel.objects.create(name="Invalid String", timestamp="invalid date string")


    # def test_form_field_to_python_standard_datetime(self):
    #     """Test the form field's to_python with a standard datetime."""
    #     from django_extended_dates.forms import ExtendedDateTimeFormField
    #     field = ExtendedDateTimeFormField()
    #     now = datetime.datetime.now()
    #     result = field.to_python(now)
    #     self.assertIsInstance(result, cftime.datetime)
    #     self.assertEqual(result.year, now.year)
    #     # Add other component checks as in model test

    # def test_form_field_to_python_cftime(self):
    #     """Test the form field's to_python with a cftime datetime."""
    #     from django_extended_dates.forms import ExtendedDateTimeFormField
    #     field = ExtendedDateTimeFormField()
    #     cftime_dt = cftime.datetime(1582, 10, 15, 1, 2, 3, calendar='gregorian')
    #     result = field.to_python(cftime_dt)
    #     self.assertIsInstance(result, cftime.datetime)
    #     self.assertEqual(result, cftime_dt)


    # def test_form_field_to_python_valid_string(self):
    #     """Test the form field's to_python with a valid string (requires parsing impl)."""
    #     # Needs implementation in ExtendedDateTimeFormField.to_python
    #     from django_extended_dates.forms import ExtendedDateTimeFormField
    #     field = ExtendedDateTimeFormField()
    #     valid_string = "2023-10-26 14:00:00" # Example format
    #     with self.assertRaises(NotImplementedError): # Expecting failure for now
    #         result = field.to_python(valid_string)
    #     # Once implemented:
    #     # self.assertIsInstance(result, cftime.datetime)
    #     # self.assertEqual(result.year, 2023)
    #     # ... etc ...

    # def test_form_field_to_python_invalid_string(self):
    #     """Test the form field's to_python with an invalid string."""
    #     from django_extended_dates.forms import ExtendedDateTimeFormField
    #     field = ExtendedDateTimeFormField()
    #     invalid_string = "not a date"
    #     # The current implementation raises NotImplementedError first,
    #     # but should raise ValidationError once parsing is attempted.
    #     with self.assertRaises((ValidationError, NotImplementedError)):
    #         field.to_python(invalid_string)
