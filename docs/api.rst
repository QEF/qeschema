************
qeschema API
************

The package includes a base class for generic XML documents and some
specialized classes for Quantum Espresso applications.


Generic XML document API
------------------------

.. autoclass:: qeschema.XmlDocument

    .. autoattribute:: namespaces
    .. autoattribute:: xml_namespaces

    .. automethod:: read
    .. automethod:: from_xml
    .. automethod:: from_json
    .. automethod:: from_yaml
    .. automethod:: from_dict
    .. automethod:: write
    .. automethod:: to_dict
    .. automethod:: to_json
    .. automethod:: to_yaml
    .. automethod:: iter
    .. automethod:: find
    .. automethod:: findall


QE applications XML document API
--------------------------------

.. autoclass:: qeschema.QeDocument

    .. autoattribute:: input_path
    .. autoattribute:: output_path

    .. automethod:: get_fortran_input
    .. automethod:: write_fortran_input

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

Each QE application uses a converter to produce Fortran input (namelist) from XML input
data. A converter object is associated with the attribute *input_builder* of the instance.

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
