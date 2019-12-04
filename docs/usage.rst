********************************
Extracting data from  XML files
********************************

PwDocument instances can be used to extract data from XML data files converting them to dictionaries. 
One has just to create a PwDocument object use it to read the XML file and then use the decoders provided 
by qeschema. 


::
   
   >>>import qeschema
   >>>doc = qeschema.PwDocument(schema='../qeschema/schemas/releases/qes_190304.xsd')
   >>>doc.read('pwscf.save/data-file-schema.xml') 
   >>>pwdict = doc.to_dict() 
   >>>bsdict = pwdict['qes:espresso']['output']['band_structure'] 


One can also use the elementpath  and xmlschema functionalities of the PwDocument object and obtain directly 
the desired dictionary: 

::

    >>>import qeschema
    >>>doc = qeschema.PwDocument(schema='../qeschema/schemas/releases/qes_190304.xsd')
    >>>doc.read('pwscf.save/data-file-schema.xml') 
    >>>path = './/output/band_structure' 
    >>>bsdict = doc.schema.find(path).decode(doc.find(path) 




