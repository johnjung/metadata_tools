# -*- coding: utf-8 -*-
import json, pymarc, sys, unittest
from metadata_converters import MarcXmlConverter, SocSciMapsMarcXmlToDc, SocSciMapsMarcXmlToEDM, MarcXmlToSchemaDotOrg
from pathlib import Path
from pymarc import MARCReader
from rdflib import Literal, URIRef
from rdflib.namespace import DC, DCTERMS
import xml.etree.ElementTree as ElementTree

'''
class TestMarcXmlConverter(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        """Create test objects. Test data should be placed in the test_data
        directory of this project. It should include sample data from different
        digital collections projects, and the data should be varied enough to 
        be able to catch different kinds of edge cases in testing."""
        super().__init__(*args, **kwargs)
        self.test_init()

    def test_init(self):
        """MarcXmlConverter should have a .record property which is a
        xml.etree.ElementTree.Element."""
        file = Path('test_data/sample_record_01.xml')
        with open(file, 'r', encoding='utf-8') as f:
            data = f.read().replace('\n', '')
            self.assertTrue(len(data) > 0)
        self.collection = MarcXmlConverter(data)
        self.assertIsInstance(self.collection.record, ElementTree.Element)
        self.assertEqual(self.collection.get_marc_field('655', '', '', ''), ['Thematic maps.', 'lcgft'])

    def test_get_marc_field_field_tag(self):
        """Retrieve a marc data field and a control field using the
        get_marc_field() method."""
        self.assertEqual(self.collection.get_marc_field('003', '', '', ''), ['OLE'])
        self.assertEqual(self.collection.get_marc_field('003', '5', '', ''), ['OLE'])
        self.assertEqual(self.collection.get_marc_field('003', '', '5', ''), ['OLE'])
        self.assertEqual(self.collection.get_marc_field('003', '', '', '5'), ['OLE'])
        self.assertEqual(self.collection.get_marc_field('651', '', '', ''),  ['Illinois', 'Chicago.', 'fast', '(OCoLC)fst01204048'])

    def test_get_marc_field_subfield(self):
        """Retrieve a marc data field and subfield using the get_marc_field()
        method."""
        self.assertEqual(self.collection.get_marc_field('650', '[a]', '', '4'), [])
        self.assertEqual(self.collection.get_marc_field('650', '[a]', '4', ''), [])
        self.assertEqual(self.collection.get_marc_field('650', '[a]', '', '')[0], 'Ethnology')

    def test_get_marc_field_indicator_1(self):
        """Retrieve a record with the first indicator marked using the
        get_marc_field() method."""
        self.assertEqual(self.collection.get_marc_field('', '', '2', '4'), [])
        self.assertEqual(self.collection.get_marc_field('', '', '2', ''), [])
        self.assertEqual(self.collection.get_marc_field('650', '[a]', '4', ''), [])
        self.assertEqual(self.collection.get_marc_field('245', '', '1', ''), ['Census tracts of Chicago, 1940', 'Races and nationalities.'])

    def test_get_marc_field_indicator_2(self):
        """Retrieve a record with the second indicator marked using the
        get_marc_field() method."""
        self.assertEqual(self.collection.get_marc_field('', '', '', 's'), [])
        self.assertEqual(self.collection.get_marc_field('655', '[a]', '4', '7'), [])
        self.assertEqual(self.collection.get_marc_field('830', '', '', '0'), ['Social scientists map Chicago.', 'ICU', 'University of Chicago Digital Preservation Collection.', 'ICU'])
'''

'''
class TestMarcXmlToSchemaDotOrg(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        """Create test objects. Test data should be placed in the test_data
        directory of this project. It should include sample data from different
        digital collections projects, and the data should be varied enough to 
        be able to catch different kinds of edge cases in testing."""
        super().__init__(*args, **kwargs)
        self.test_init()

    def test_init(self):
        """MarcXmlToSchemaDotOrg extends the MarcXmlConverter class and should 
        have a call function that returns data as a dictionary."""
        file = Path('test_data/sample_record_03.xml')
        with open(file, 'r', encoding='utf-8') as f:
            data = f.read().replace('\n', '')
            self.assertTrue(len(data) > 0)
        self.collection = MarcXmlToSchemaDotOrg(data)
        self.collection.schema = self.collection.__call__()
        self.assertIsInstance(self.collection.schema, dict)
        self.assertEqual(self.collection.schema['@context'], 'https://schema.org')
        self.assertEqual(self.collection.schema['@type'], 'Map')
        with self.assertRaises(KeyError):
            self.collection.schema['badKey']

    def test_get_creator(self):
        """Be sure the object can return the Schema dictionary."""
        self.assertEqual(self.collection._get_creator(), {'@type': 'Person', 'name': 'Mayer, Harold M. (Harold Melvin), 1916-1994.'})

    def test_get_about(self):
        """Be sure the object can return the Schema dictionary."""
        self.assertEqual(self.collection.schema['about'], 'G4104.C6P3 1943 .M21')

    def test_get_alternative_name(self):
        """Be sure the object can return the Schema dictionary. Testing with Lorem Ipsum random value in record"""
        self.assertEqual(self.collection.schema['alternativeName'], 'Duis morbi convallis nullam')

    def test_get_content_location(self):
        """Be sure the object can return the Schema dictionary."""
        self.assertEqual(self.collection.schema['contentLocation'], 'n-us-il 4104 C6 Illinois')

    def test_get_contributor(self):
        """Be sure the object can return the Schema dictionary."""
        self.assertEqual(self.collection.schema['contributor'], 'Thematic')

    def test_get_copyright_year(self):
        """Be sure the object can return the Schema dictionary."""
        self.assertEqual(self.collection.schema['copyrightYear'], '1943.')

    def test_get_date_created(self):
        """Be sure the object can return the Schema dictionary."""
        self.assertEqual(self.collection.schema['dateCreated'], '[2006].')

    def test_get_date_published(self):
        """Be sure the object can return the Schema dictionary."""
        self.assertEqual(self.collection.schema['datePublished'], '1843.')

    def test_get_description(self):
        """Be sure the object can return the Schema dictionary."""
        self.assertEqual(self.collection.schema['description'], '"Figure 2." Also appeared in author\'s Ph. D. dissertation (University of Chicago, 1943): The railway pattern of metropolitan Chicago. Master and use copy. Digital master created according to Benchmark for Faithful Reproductions of Monographs and Serials, Version 1. Digital Library Federation, December 2002. http://www.diglib.org/standards/bmarkfin.htm')

    def test_get_encoding(self):
        """Be sure the object can return the Schema dictionary."""
        self.assertEqual(self.collection.schema['encoding'], 'Electronic reproduction.')

    def test_get_height(self):
        """Be sure the object can return the Schema dictionary. Testing with Lorem Ipsum random value in record"""
        self.assertEqual(self.collection.schema['height'], 'Dictumst nec duis')

    def test_get_genre(self):
        """Be sure the object can return the Schema dictionary. Testing with Lorem Ipsum random value in record"""
        self.assertEqual(self.collection.schema['genre'], 'Maps. Netus accumsan ornare et')

    def test_get_identifier(self):
        """Be sure the object can return the Schema dictionary."""
        self.assertEqual(self.collection.schema['identifier'], 'CGU')

    def test_get_in_language(self):
        """Be sure the object can return the Schema dictionary."""
        self.assertEqual(self.collection.schema['inLanguage'], 'Eng')

    def test_get_is_accessible_for_free(self):
        """Be sure the object can return the Schema dictionary."""
        self.assertEqual(self.collection.schema['isAccessibleForFree'], 'Digital version available with restrictions Unrestricted online access')

    def test_get_is_part_of(self):
        """Be sure the object can return the Schema dictionary."""
        self.assertEqual(self.collection.schema['isPartOf'], ['(Social scientists map Chicago); (University of Chicago Digital Preservation Collection)', 'Social scientists map Chicago. University of Chicago Digital Preservation Collection.', 'Thematic'])

    def test_get_location_created(self):
        """Be sure the object can return the Schema dictionary."""
        self.assertEqual(self.collection.schema['locationCreated'], '[Chicago] :')

    def test_get_map_type(self):
        """Be sure the object can return the Schema dictionary."""
        self.assertEqual(self.collection.schema['mapType'], 'Thematic maps')

    def test_get_name(self):
        """Be sure the object can return the Schema dictionary."""
        self.assertEqual(self.collection.schema['name'], 'Functional pattern of the railways in Metropolitan Chicago /')

    def test_get_publisher(self):
        """Be sure the object can return the Schema dictionary."""
        self.assertEqual(self.collection.schema['publisher'], '[publisher not identified],')

    def test_get_spatial_coverage(self):
        """Be sure the object can return the Schema dictionary."""
        self.assertEqual(self.collection.schema['spatialCoverage'], 'Scale [ca. 1:580,000] (W 88°30ʹ00ʺ--W 86°44ʹ00ʺ/N 42°46ʹ00ʺ--N 41°17ʹ00ʺ).')

    def test_get_temporal_coverage(self):
        """Be sure the object can return the Schema dictionary. Testing with Lorem Ipsum random value in record"""
        self.assertEqual(self.collection.schema['temporalCoverage'], 'Metus feugiat sollicitudin')

    def test_get_url(self):
        """Be sure the object can return the Schema dictionary."""
        self.assertEqual(self.collection.schema['url'], 'http://pi.lib.uchicago.edu/1001/maps/chisoc/G4104-C6P3-1943-M21')

    def test_get_width(self):
        """Be sure the object can return the Schema dictionary. Testing with Lorem Ipsum random value in record"""
        self.assertEqual(self.collection.schema['width'], 'Dictumst nec duis')
'''

if __name__ == '__main__':
    unittest.main()
