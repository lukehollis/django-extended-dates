import cftime
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import datetime
import re # Need re for parsing

# Custom Widget (Using BC Suffix)
class ExtendedDateTimeInput(forms.DateTimeInput):
    """
    A DateTimeInput widget that correctly formats cftime.datetime objects,
    representing BC years with a ' BC' suffix.
    Disables localization to prevent timezone errors with cftime objects.
    """
    needs_localization = False

    def format_value(self, value):
        """
        Formats cftime.datetime into 'YYYY-MM-DD HH:MM:SS[.ffffff] BC' string.
        """
        if isinstance(value, cftime.datetime):
            # Format cftime object back into a string with BC suffix
            cftime_year = value.year
            display_year = cftime_year
            bc_suffix = ""

            if cftime_year <= 0:
                 # cftime year 0 (1 BC) -> display_year 1, suffix ' BC'
                 # cftime year -1 (2 BC) -> display_year 2, suffix ' BC'
                 display_year = -(cftime_year - 1)
                 bc_suffix = " BC"

            # Format YYYY-MM-DD HH:MM:SS[.ffffff][ BC]
            year_str = f"{display_year:04d}"
            time_str = f"{value.hour:02d}:{value.minute:02d}:{value.second:02d}"
            if value.microsecond:
                 time_str += f".{value.microsecond:06d}"

            # Directly return the fully formatted string
            return f"{year_str}-{value.month:02d}-{value.day:02d} {time_str}{bc_suffix}"

        # If not cftime, let the parent handle formatting
        return super().format_value(value)

# Form Field (Using BC Suffix)
class ExtendedDateTimeFormField(forms.DateTimeField):
    """
    Form field for ExtendedDateTimeField. Parses/validates strings
    with ' BC' suffix for BC dates. Uses ExtendedDateTimeInput.
    """
    widget = ExtendedDateTimeInput
    default_error_messages = {
        'invalid': _('Enter a valid date/time.'),
        'invalid_format': _('Enter a valid date/time format (e.g., YYYY-MM-DD HH:MM:SS or YYYY-MM-DD HH:MM:SS BC).'),
        'invalid_year_zero': _('BC year must be positive (e.g., use 1 BC, not 0 BC).'),
    }

    def to_python(self, value):
        """
        Validates input can be converted to a cftime datetime.
        Returns a cftime.datetime object.
        Handles 'YYYY-MM-DD HH:MM:SS BC' format.
        """
        if value in self.empty_values:
            return None
        if isinstance(value, cftime.datetime):
            return value
        if isinstance(value, datetime.datetime):
             try:
                 # Standard datetime years must be AD
                if not 1 <= value.year <= 9999:
                     raise ValidationError("Standard datetime year out of range.")
                return cftime.datetime(value.year, value.month, value.day,
                                       value.hour, value.minute, value.second,
                                       value.microsecond, calendar='standard')
             except Exception as e:
                 raise ValidationError(f"Internal error converting datetime: {e}")

        if isinstance(value, str):
            value_str = value.strip()
            is_bc = False
            bc_suffix = " bc" # Check case-insensitively

            if value_str.lower().endswith(bc_suffix):
                is_bc = True
                # Remove the suffix for parsing
                value_str = value_str[:-len(bc_suffix)].strip()

            # Define expected formats (without BC suffix)
            formats = [
                '%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d %H:%M', '%Y-%m-%d',
            ]
            parsed_dt = None
            for fmt in formats:
                try:
                    parsed_dt = datetime.datetime.strptime(value_str, fmt)
                    break
                except ValueError:
                    continue

            if parsed_dt is None:
                 raise ValidationError(self.error_messages['invalid_format'], code='invalid_format')

            # Parsed year from strptime
            parsed_year = parsed_dt.year

            if parsed_year <= 0:
                 # Year before BC suffix (or without suffix) must be positive AD year
                 raise ValidationError("Year component must be positive.", code='invalid')

            cftime_year = 0
            if is_bc:
                 # Convert positive parsed year Y to cftime BC year -(Y-1)
                 # e.g., input '0001-... BC' -> parsed_year=1 -> cftime_year = -(1-1) = 0 (1 BC)
                 # e.g., input '0470-... BC' -> parsed_year=470 -> cftime_year = -(470-1) = -469 (470 BC)
                cftime_year = -(parsed_year - 1)
            else:
                # Positive year, not BC -> standard AD year
                cftime_year = parsed_year

            try:
                 # Create the cftime object (timezone naive)
                return cftime.datetime(cftime_year, parsed_dt.month, parsed_dt.day,
                                       parsed_dt.hour, parsed_dt.minute, parsed_dt.second,
                                       parsed_dt.microsecond, calendar='standard')
            except Exception as e:
                raise ValidationError(f"Error creating extended date: {e}", code='invalid')

        raise ValidationError(self.error_messages['invalid'], code='invalid')

    # Override clean or other methods as needed