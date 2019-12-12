************
qeschema API
************

The package includes a base class for generic XML documents and some
specialized classes for Quantum Espresso applications.


Generic XML document API
------------------------

.. autoclass:: qeschema.XmlDocument

    .. autoattribute:: namespaces
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

Specialized classes for QE applications can extend the base class :class:`qeschema.XmlDocument`
with helper functions for extracting data from XML data files produced by each application.
These classes have a common base class :class:`qeschema.QeDocument` that defines common methods
an properties for accessing input and ouput data and for converting XML input to legacy
Fortran namelist input.

.. autoclass:: qeschema.QeDocument

    .. autoattribute:: input_path
    .. autoattribute:: output_path

    .. automethod:: get_fortran_input
    .. automethod:: write_fortran_input

.. autoclass:: qeschema.PwDocument

    .. automethod:: get_atomic_positions
    .. automethod:: get_cell_parameters
    .. automethod:: get_stress
    .. automethod:: get_forces
    .. automethod:: get_k_points
    .. automethod:: get_ks_eigenvalues
    .. automethod:: get_total_energy

.. autoclass:: qeschema.PhononDocument

    .. automethod:: get_fortran_input

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
