import cftime
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import datetime # Need this import
import re # Import re for parsing

# Potentially helper functions for parsing/formatting PG strings
# from .utils import parse_pg_timestamp_string, format_cftime_for_pg

# Import the form field and widget (needed for formfield method)
# Ensure these imports are correct relative to your structure
from .forms import ExtendedDateTimeFormField, ExtendedDateTimeInput

class ExtendedDateTimeField(models.DateTimeField):
    """
    A Django DateTimeField that supports dates outside the standard
    Python datetime range (e.g., BC dates), leveraging the database's
    native timestamp type and cftime for Python representation.
    """
    description = _("Extended date and time")

    def from_db_value(self, value, expression, connection):
        """
        Converts value from the database (expecting standard datetime or
        'YYYY-MM-DD HH:MM:SS BC' string) to a cftime object.
        """
        if value is None:
            return value
        if isinstance(value, cftime.datetime):
            return value
        if isinstance(value, datetime.datetime):
            # Convert standard datetime to cftime, dropping tzinfo
            try:
                 if not 1 <= value.year <= 9999:
                      raise ValidationError(f"Unexpected standard datetime year {value.year} from DB.")
                 return cftime.datetime(value.year, value.month, value.day,
                                       value.hour, value.minute, value.second,
                                       value.microsecond, calendar='standard')
            except Exception as e:
                raise ValidationError(f"Could not convert standard datetime {value} to cftime: {e}")

        if isinstance(value, str):
            # Primarily expect 'YYYY-MM-DD HH:MM:SS BC' format from Postgres
            value_str = value.strip()
            # Regex allows for optional microseconds and case-insensitive 'BC'
            bc_match = re.match(r"(\d{4,})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?\s+BC", value_str, re.IGNORECASE)

            if bc_match:
                 # Year YYYY BC -> cftime year -(YYYY-1)
                year_str, month, day, hour, minute, second, microsecond_str = bc_match.groups()
                year_int = int(year_str)
                if year_int <= 0:
                     raise ValueError("Year must be positive with BC suffix in DB string")
                cftime_year = -(year_int - 1) # 1 BC -> 0, 2 BC -> -1, etc.

                try:
                    microsecond = int(microsecond_str.ljust(6, '0')) if microsecond_str else 0
                    return cftime.datetime(cftime_year, int(month), int(day),
                                           int(hour), int(minute), int(second),
                                           microsecond, calendar='standard')
                except Exception as e:
                    raise ValidationError(f"Error creating cftime from DB string '{value_str}': {e}")
            else:
                 # If it's not BC format, maybe it's a standard ISO string AD date?
                 # psycopg2 usually handles standard datetimes correctly.
                 # We might need more robust parsing if other string formats are expected from DB.
                 # For now, assume only standard datetime or BC format string.
                 try:
                     # Attempt parsing as standard datetime string (might be redundant if psycopg2 handles it)
                     parsed_dt = datetime.datetime.fromisoformat(value_str)
                     if 1 <= parsed_dt.year <= 9999:
                          return cftime.datetime(parsed_dt.year, parsed_dt.month, parsed_dt.day,
                                                parsed_dt.hour, parsed_dt.minute, parsed_dt.second,
                                                parsed_dt.microsecond, calendar='standard')
                     else:
                          raise ValidationError("Parsed standard datetime year out of range.")
                 except ValueError:
                     # Raise error for unexpected string formats if standard parsing fails
                    raise ValidationError(f"Unrecognized string format from DB for ExtendedDateTimeField: {value}")


        raise TypeError(f"Unexpected type from database for ExtendedDateTimeField: {type(value)}")

    def get_prep_value(self, value):
        """
        Converts Python cftime/datetime object to a value suitable for the database.
        Formats BC dates as 'YYYY-MM-DD HH:MM:SS BC'.
        Passes standard datetimes to parent method.
        """
        if value is None:
            return value

        # If it's already a standard datetime within range, let Django handle it
        if isinstance(value, datetime.datetime):
            if 1 <= value.year <= 9999:
                # Use standard Django prep for standard dates
                return super().get_prep_value(value)
            else:
                # Convert out-of-range standard datetime to cftime first
                try:
                    value = cftime.datetime(value.year, value.month, value.day,
                                          value.hour, value.minute, value.second,
                                          value.microsecond, calendar='standard')
                    # Fall through to cftime handling
                except Exception as e:
                    raise ValidationError(f"Could not convert standard datetime {value} to cftime for DB prep: {e}")

        if isinstance(value, cftime.datetime):
            cftime_year = value.year
            bc_suffix = ""
            display_year = cftime_year # Year used for formatting

            if cftime_year <= 0:
                 # Convert cftime year (0, -1, -2...) to positive year for BC string
                 # Year 0 (1 BC) -> display_year 1, suffix ' BC'
                 # Year -1 (2 BC) -> display_year 2, suffix ' BC'
                 display_year = -(cftime_year - 1)
                 if display_year <=0: # Sanity check
                    raise ValueError("Calculated display year for BC cannot be zero or negative.")
                 bc_suffix = " BC"
            # Else (AD year), display_year remains cftime_year

            # Format as YYYY-MM-DD HH:MM:SS[.ffffff][ BC]
            # Ensure year is padded to at least 4 digits
            year_str = f"{display_year:04d}"

            iso_string = f"{year_str}-{value.month:02d}-{value.day:02d} {value.hour:02d}:{value.minute:02d}:{value.second:02d}"
            if value.microsecond:
                iso_string += f".{value.microsecond:06d}"

            iso_string += bc_suffix # Add ' BC' if needed
            return iso_string # Return the formatted string with BC suffix

        raise TypeError(f"Unsupported type for ExtendedDateTimeField prep: {type(value)}")


    def to_python(self, value):
        """
        Converts input value (e.g., from serialization) to cftime.
        Relies on from_db_value logic for string parsing.
        """
        if value is None:
            return value
        if isinstance(value, cftime.datetime):
            return value
        if isinstance(value, datetime.datetime):
             try:
                return cftime.datetime(value.year, value.month, value.day,
                                       value.hour, value.minute, value.second,
                                       value.microsecond, calendar='standard')
             except Exception as e:
                raise ValidationError(f"Could not convert standard datetime {value} to cftime: {e}")
        if isinstance(value, datetime.date):
             try:
                return cftime.datetime(value.year, value.month, value.day, calendar='standard')
             except Exception as e:
                raise ValidationError(f"Could not convert standard date {value} to cftime: {e}")

        if isinstance(value, str):
             # Attempt parsing using from_db_value logic
            try:
                # Pass None for expression and connection as they aren't strictly needed for string parsing logic here
                return self.from_db_value(value, None, None)
            except ValidationError as e:
                 raise ValidationError(f"Invalid string format for to_python ('{value}'): {e}")

        raise ValidationError(f"Cannot convert value '{value}' (type: {type(value)}) to ExtendedDateTimeField")


    def formfield(self, **kwargs):
        """
        Ensure the correct form field AND widget are used, overriding admin defaults.
        """
        from .forms import ExtendedDateTimeFormField, ExtendedDateTimeInput # Local import
        defaults = {
            'form_class': ExtendedDateTimeFormField,
            'widget': ExtendedDateTimeInput
        }
        defaults.update(kwargs)
        return super().formfield(**defaults)
