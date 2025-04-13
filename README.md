# django-extended-dates

[![PyPI version](https://badge.fury.io/py/django-extended-dates.svg)](https://badge.fury.io/py/django-extended-dates) <!-- Optional: Add badge if/when published -->

[Note: this package was fully created by LLMs, I just reviewed it to use it for BCE dates in my [map simulation platform](https://app.isildur.co/).]

Django `DateTimeField` supporting dates outside the standard Python `datetime` range (1-9999), such as BC dates, primarily for use with PostgreSQL's `timestamp` type.

This package leverages the `cftime` library to represent dates outside the standard range in Python and aims to handle the conversion between `cftime` objects and the database representation.

**Status:** Work in Progress / Alpha

- Core field structure is defined.
- Conversion for standard `datetime` and in-range `cftime` objects is partially implemented.
- **Crucially, parsing and formatting for out-of-range dates (especially BC dates and database string representations) is NOT yet implemented.** See `NotImplementedError` exceptions in `fields.py` and `forms.py`.
- Basic tests for standard cases are included.

## Requirements

*   Python 3.8+
*   Django >= 3.2
*   cftime >= 1.5.0
*   Database backend that supports extended timestamp ranges (e.g., PostgreSQL).

## Installation (Placeholder)

```bash
pip install django-extended-dates
```

*(Note: Not yet available on PyPI)*

## Basic Usage

In your Django models:

```python
from django.db import models
from django_extended_dates.fields import ExtendedDateTimeField
import cftime

class HistoricalEvent(models.Model):
    name = models.CharField(max_length=200)
    event_date = ExtendedDateTimeField()

# Example (once BC date handling is implemented):
# event = HistoricalEvent.objects.create(
#    name="Assassination of Julius Caesar",
#    event_date=cftime.datetime(-44, 3, 15, 10, 0, 0, calendar='gregorian')
# )
```

## Development & Testing (Placeholder)

1.  Clone the repository.
2.  Set up a virtual environment.
3.  Install dependencies (e.g., `poetry install`).
4.  Configure Django settings for testing (database, INSTALLED_APPS including `django_extended_dates` and `tests`).
5.  Run tests:

```bash
python manage.py test
```

## Contributing

Contributions are welcome, especially for implementing the robust parsing/formatting logic required for extended date support.

## License

MIT License (or your chosen license - update `pyproject.toml`). 