Changelog
=========

We are operating with `semantic versioning <http://semver.org>`_.



v2.0.0
------

Major:

- SQLite no longer checks if it is in the same thread.
- SQLite detects types by default.

Minor:

- Exposed a few protected functions as public.
- :class:`.Row` is directly equatable to common data types.

Patch:

- Fix issue when param indexes given out of order.
- Try a little harder to shutdown SSH tunnels.


v1.0.0
------

Initial release!
