************
qeschema API
************

The package includes two base classes for generic XML documents or Quantum Espresso
documents and some specialized classes for specific Quantum Espresso applications.


Generic XML document API
------------------------

.. autoclass:: qeschema.XmlDocument

.. autoclass:: qeschema.QeDocument


QE application document API
---------------------------

.. autoclass:: qeschema.PwDocument
.. autoclass:: qeschema.PhononDocument
.. autoclass:: qeschema.NebDocument
.. autoclass:: qeschema.TdDocument
.. autoclass:: qeschema.TdSpectrumDocument


Other API
---------

These API calls can be useful for programmers that wants to make more complex scripts
or to debug data.

XML input to namelist format converters
.......................................

Each application use a converter to produce Fortran input (namelist) from XML input data.
A converter object is associated with the attribute *input_builder* of the instance.

.. autoclass:: qeschema.RawInputConverter
.. autoclass:: qeschema.PwInputConverter
.. autoclass:: qeschema.PhononInputConverter
.. autoclass:: qeschema.NebInputConverter
.. autoclass:: qeschema.TdInputConverter
.. autoclass:: qeschema.TdSpectrumInputConverter

Exception classes and utilities
...............................

.. autoclass:: qeschema.QESchemaError
.. autoclass:: qeschema.XmlDocumentError

.. autofunction:: qeschema.set_logger
