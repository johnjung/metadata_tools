import datetime
import jinja2
import json
import re
import sys
import xml.etree.ElementTree as ElementTree

from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, FOAF, DC, DCTERMS, XSD
from rdflib.plugins.sparql import prepareQuery

class MarcXmlConverter:
    """
    A class to convert MARCXML to other formats. Extend this class to make
    converters for outputting specific formats. 

    Returns:
        a MarcXmlConverter
    """

    def __init__(self, marcxml):
        """Initialize an instance of the class MarcXmlConverter.

        Args:
            marcxml (str): a marcxml collection with a single record.
        """
        self.record = ElementTree.fromstring(marcxml).find(
            '{http://www.loc.gov/MARC21/slim}record')

        # Only bring in 655's where the $2 subfield is set to 'lcgft'.
        remove = []
        for element in self.record:
            if element.tag == '{http://www.loc.gov/MARC21/slim}datafield':
                if element.attrib['tag'] == '655':
                    for subfield in element:
                        if subfield.attrib['code'] == '2' and not subfield.text == 'lcgft':
                            remove.append(element)
                            break
        for element in remove:
            self.record.remove(element)

    def get_marc_field(self, field_tag, subfield_code, ind1, ind2):
        """Get a specific MARC field. 

        Args:
            field_tag (str): e.g., "245"
            subfield_code (str): subfield codes as a regex, e.g. '[a-z]'
            ind1 (str): first indicator as a regex, e.g. '4'
            ind2 (str): second indicator as a regex, e.g. '4'

        Returns:
            list: of strings, all matching MARC tags and subfields.
        """
        results = []
        for element in self.record:
            try:
                if not element.attrib['tag'] == field_tag:
                    continue
            except KeyError:
                continue
            if element.tag == '{http://www.loc.gov/MARC21/slim}controlfield':
                results.append(element.text)
            elif element.tag == '{http://www.loc.gov/MARC21/slim}datafield':
                if not re.match(ind1, element.attrib['ind1']):
                    continue
                if not re.match(ind2, element.attrib['ind2']):
                    continue
                for subfield in element:
                    if re.match(subfield_code, subfield.attrib['code']):
                        results.append(subfield.text)
        return results


class MarcToDc(MarcXmlConverter):
    """
    A class to convert MARCXML to Dublin Core. 

    The Library of Congress MARCXML to DC conversion is here:
    http://www.loc.gov/standards/marcxml/xslt/MARC21slim2SRWDC.xsl
    It produces slightly different results. 

    mappings -- a list of tuples-
        [0] -- Dublin Core metadata element.
        [1] -- a list-
            [0] a boolean, DC element is repeatable. 
            [1] a list, a MARC field specification-
                [0] a string, the MARC field itself.
                [1] a regular expression (as a string), allowable subfields. 
                [2] a regular expression (as a string), indicator 1.
                [3] a regular expression (as a string), indicator 2. 
        [2] a boolean, subfields each get their own DC element. If False,
            subfields are joined together into a single DC element.
            assert this field==False if [0]==False.
        [3] a regular expression (as a string) to strip out of the field, or
            None if there is nothing to exclude.
            if the resulting value is '' it won't be added.

    """

    mappings = [
        ('DC.rights.access',         [False, [('506', '[a-z]',  '.', '.')], False,   None]),
        ('DC.contributor',           [True,  [('700', 'a',      '.', '.'),
                                              ('710', 'a',      '.', '.')], False,   None]),
        ('DC.creator',               [True,  [('100', '[a-z]',  '.', '.'),
                                              ('110', '[a-z]',  '.', '.'),
                                              ('111', '[a-z]',  '.', '.'),
                                              ('533', 'c',      '.', '.')], False,   None]),
        ('DC.date',                  [True,  [('533', 'd',      '.', '.')], False,   None]),
        ('DC.description',           [False, [('500', '[a-z]',  '.', '.'),
                                              ('538', '[a-z]',  '.', '.')], False,   None]),
        ('DC.format',                [True,  [('255', '[ab]',   '.', '.')], False,   None]),
        ('DC.relation.hasFormat',    [True,  [('533', 'a',      '.', '.')], False,   None]),
        ('DC.identifier',            [True,  [('020', '[a-z]',  '.', '.'),
                                              ('021', '[a-z]',  '.', '.'),
                                              ('022', '[a-z]',  '.', '.'),
                                              ('023', '[a-z]',  '.', '.'),
                                              ('024', '[a-z]',  '.', '.'),
                                              ('025', '[a-z]',  '.', '.'),
                                              ('026', '[a-z]',  '.', '.'),
                                              ('027', '[a-z]',  '.', '.'),
                                              ('028', '[a-z]',  '.', '.'),
                                              ('029', '[a-z]',  '.', '.'),
                                              ('856', 'u',      '.', '.')], False,   None]),
        ('DC.relation.isPartOf',     [True,  [('533', 'f',      '.', '.'),
                                              ('700', 't',      '.', '.'),
                                              ('830', '[a-z]',  '.', '.')], False,   None]),
        ('DC.language',              [True,  [('041', '[a-z]',  '.', '.')], True,    None]),
        ('DC.medium',                [True,  [('338', '[a-z]',  '.', '.')], True,    None]),
        ('DC.coverage.location',     [True,  [('264', 'a',      '1', '.'),
                                              ('533', 'b',      '.', '.')], False,   None]),
        ('DC.coverage.periodOfTime', [True,  [('650', 'y',      '.', '.')], False,   None]),
        ('DC.publisher',             [True,  [('260', 'b',      '.', '.'),
                                              ('264', 'b',      '1', '.')], False,   None]),
        ('DC.relation',              [True,  [('730', 'a',      '.', '.')], False,   None]),
        ('DC.subject',               [True,  [('050', '[a-z]',  '.', '.')], False,   '[. ]*$']),
        ('DC.subject',               [True,  [('650', '[ax]',   '.', '.')], True,    '[. ]*$']),
        ('DC.title',                 [True,  [('130', '[a-z]',  '.', '.'),
                                              ('240', '[a-z]',  '.', '.'),
                                              ('245', '[ab]',   '.', '.')], False,   None]),
        ('DC.type',                  [True,  [('336', '[a-z]',  '.', '.'),
                                              ('650', 'v',      '.', '.'),
                                              ('651', 'v',      '.', '.')], False,   '^Maps[. ]*$|[. ]*$']),
        ('DCTERMS.alternative',      [True,  [('246', '[a-z]',  '.', '.')], False,   None]),
        ('DCTERMS.dateCopyrighted',  [True,  [('264', 'c',      '4', '.')], False,   None]),
        ('DCTERMS.extent',           [True,  [('300', '[ac]',   '.', '.')], False,   None]),
        ('DCTERMS.issued',           [True,  [('260', 'c',      '.', '.'),
                                              ('264', 'c',      '1', '.')], False,   None]),
        ('DCTERMS.location',         [True,  [('260', 'a',      '.', '.'),
                                              ('264', 'a',      '1', '.'),
                                              ('533', 'b',      '.', '.')], False,   None])
    ]

    # subjects should be deduped. 
    # issued...should this be encoded as DCTERMS.issued, or DC.date.issued???
    # dc:type 655 $2 fast.
    # dcterms.dateCopyrighted ... is that a first or second indicator 4?

    def __init__(self, marcxml):
        """Initialize an instance of the class MarcToDc.

        Args:
            marcxml (str): a marcxml collection with a single record.
        """
        for _, (repeat_dc, _, repeat_sf, _) in self.mappings:
            if repeat_dc == False:
                assert repeat_sf == False
        super().__init__(marcxml)
        self._build_xml()

    def __getattr__(self, attr):
        """Return individual Dublin Core elements as instance properties, e.g.
        self.identifier.

        Returns:
            list
        """
        vals = [e.text for e in self.dc.findall('{{http://purl.org/dc/elements/1.1/}}{}'.format(attr.replace('_','.')))]   
        return sorted(vals)

    def todict(self):
        """Return a dictionary/list/etc. of metadata elements, for display in
        templates."""
        raise NotImplementedError

    def _build_coverage(self):
        raise NotImplementedError
        # 034
        # coordinate data...may not be present for all map collections.
        # 650$z
        # 651 _7 $a $2 fast
        # 651 _7 $z $2 fast
        # FAST only. Dedupe repeated headings across dc:coverage fields.

    def _build_xml(self):
        ElementTree.register_namespace(
            'dc', 'http://purl.org/dc/elements/1.1/')

        metadata = ElementTree.Element('metadata')
        for dc_element, (repeat_dc, marc_fields, repeat_sf, strip_out) in self.mappings:
            if repeat_dc:
                field_texts = set()
                if repeat_sf:
                    for marc_field in marc_fields:
                        for field_text in self.get_marc_field(*marc_field):
                            if strip_out:
                                field_text = re.sub(strip_out, '', field_text)
                            if field_text:
                                field_texts.add(field_text)
                    for field_text in field_texts:
                        ElementTree.SubElement(
                            metadata,
                            dc_element.replace(
                                'DC.', '{http://purl.org/dc/elements/1.1/}')
                        ).text = field_text
                else:
                    for marc_field in marc_fields:
                        field_text = ' '.join(self.get_marc_field(*marc_field))
                        if strip_out:
                            field_text = re.sub(strip_out, '', field_text)
                        if field_text:
                            field_texts.add(field_text)
                    for field_text in field_texts:
                        ElementTree.SubElement(
                            metadata,
                            dc_element.replace(
                                'DC.', '{http://purl.org/dc/elements/1.1/}')
                        ).text = field_text
            else:
                field_text_arr = []
                for marc_field in marc_fields:
                    field_text_arr = field_text_arr + \
                        self.get_marc_field(*marc_field)
                field_text = ' '.join(field_text_arr)
                if strip_out:
                    field_text = re.sub(strip_out, '', field_text)
                if field_text:
                    ElementTree.SubElement(
                        metadata,
                        dc_element.replace(
                            'DC.', '{http://purl.org/dc/elements/1.1/}')
                    ).text = field_text
        self.dc = metadata

    def __str__(self):
        """Return Dublin Core XML as a string.

        Returns:
            str
        """
        def indent(elem, level=0):
            i = "\n" + level * "  "
            j = "\n" + (level - 1) * "  "
            if len(elem):
                if not elem.text or not elem.text.strip():
                    elem.text = i + "  "
                if not elem.tail or not elem.tail.strip():
                    elem.tail = i
                for subelem in elem:
                    indent(subelem, level + 1)
                if not elem.tail or not elem.tail.strip():
                    elem.tail = j
            else:
                if level and (not elem.tail or not elem.tail.strip()):
                    elem.tail = j
            return elem

        indent(self.dc)
        return ElementTree.tostring(self.dc, 'utf-8', method='xml').decode('utf-8')


class MarcXmlToSchemaDotOrg(MarcXmlConverter):
    """A class to convert MARCXML to Schema.org."""

    mappings = [
        ('about',               [False, [('050', '[a-z]', '.', '.'),
                                         ('650', 'x',     '.', '.')], False, '[. ]*$']),
        ('alternativeName',     [False, [('246', '[a-z]', '.', '.')], False, None]),
        ('contentLocation',     [False, [('043', '[a-z]', '.', '.'),
                                         ('052', '[a-z]', '.', '.'),
                                         ('651', 'a',     '.', '.')], False, None]),
        ('contributor',         [True,  [('700', 'a',     '.', '.'),
                                         ('710', 'a',     '.', '.')], False, None]),
        ('copyrightYear',       [True,  [('264', 'c',     '4', '.')], False, None]),
        ('dateCreated',         [True,  [('533', 'd',     '.', '.')], False, None]),
        ('datePublished',       [True,  [('264', 'c',     '1', '.')], False, None]),
        ('description',         [False, [('500', '[a-z]', '.', '.'),
                                         ('538', '[a-z]', '.', '.')], False, None]),
        ('encoding',            [True,  [('533', 'a',     '.', '.')], False, None]),
        ('height',              [True,  [('300', 'c',     '.', '.')], False, None]),
        ('genre',               [True,  [('650', 'v',     '.', '.'),
                                         ('651', 'v',     '.', '.')], False, '^Maps[. ]*$|[. ]*$']),
        ('identifier',          [True,  [('020', '[a-z]', '.', '.'),
                                         ('021', '[a-z]', '.', '.'),
                                         ('022', '[a-z]', '.', '.'),
                                         ('023', '[a-z]', '.', '.'),
                                         ('024', '[a-z]', '.', '.'),
                                         ('025', '[a-z]', '.', '.'),
                                         ('026', '[a-z]', '.', '.'),
                                         ('027', '[a-z]', '.', '.'),
                                         ('028', '[a-z]', '.', '.'),
                                         ('029', '[a-z]', '.', '.')], False, None]),
        ('inLanguage',          [True,  [('041', '[a-z]', '.', '.')], False, None]),
        ('isAccessibleForFree', [False, [('506', '[a-z]', '.', '.')], False, None]),
        ('isPartOf',            [True,  [('490', '[a-z]', '.', '.'),
                                         ('533', 'f',     '.', '.'),
                                         ('700', '[at]',  '.', '.'),
                                         ('830', '[a-z]', '.', '.')], False, None]),
        ('locationCreated',     [True,  [('264', 'a',     '1', '.'),
                                         ('533', 'b',     '.', '.')], False, None]),
        ('mapType',             [True,  [('655', 'a',     '.', '.')], True,  '[. ]*$']),
        ('name',                [True,  [('130', '[a-z]', '.', '.'),
                                         ('240', '[a-z]', '.', '.'),
                                         ('245', '[ab]',  '.', '.')], False, None]),
        ('publisher',           [True,  [('264', 'b',     '1', '.')], False, None]),
        ('spatialCoverage',     [False, [('255', '[a-z]', '.', '.')], False, None]),
        ('temporalCoverage',    [True,  [('650', 'y',     '.', '.')], False, None]),
        ('url',                 [True,  [('856', 'u',     '.', '.')], False, None]),
        ('width',               [True,  [('300', 'c',     '.', '.')], False, None])
    ]

    def __init__(self, marcxml):
        """Initialize an instance of the class MarcToSchemaDotOrg.

        Args:
            marcxml (str): a marcxml collection with a single record. 
        """
        for _, (repeat_dc, _, repeat_sf, _) in self.mappings:
            if repeat_dc == False:
                assert repeat_sf == False
        super().__init__(marcxml)

    def _get_creator(self):
        """Get creators from the 100, 110, or 111 fields if possible. 
        Otherwise get them from the 245c.

        Returns:
            dict
        """
        if self.get_marc_field('100', '[a-z]', '.', '.'):
            creator_type = 'Person'
        else:
            creator_type = 'Organization'

        creators = []
        for m in ('100', '110', '111'):
            creator_str = ' '.join(self.get_marc_field(m, '[a-z]', '.', '.'))
            if creator_str:
                creators.append(creator_str)
        if not creators:
            creators = [' '.join(self.get_marc_field('245', 'c', '.', '.'))]

        if len(creators) == 0:
            return None
        elif len(creators) == 1:
            return {'@type': creator_type, 'name': creators[0]}
        else:
            return [{'@type': creator_type, 'name': c} for c in creators]

    def __call__(self):
        """Return Schema.org data as a dictionary.

        Returns:
            dict
        """
        dict_ = {
            '@context':    'https://schema.org',
            '@type':       'Map',
            'creator':     self._get_creator()
        }
        for k in dict_.keys():
            if dict_[k] == None:
                dict_.pop(k)

        for schema_element, (repeat_schema, marc_fields, repeat_sf, strip_out) in self.mappings:
            if repeat_schema:
                field_texts = set() 
                if repeat_sf:
                    for marc_field in marc_fields:
                        for field_text in self.get_marc_field(*marc_field):
                            if strip_out:
                                field_text = re.sub(strip_out, '', field_text)
                            if field_text:
                                field_texts.add(field_text)
                    if len(field_texts) == 1:
                        dict_[schema_element] = list(field_texts)[0]
                    elif len(field_texts) > 1:
                        dict_[schema_element] = sorted(field_texts)
                else:
                    for marc_field in marc_fields:
                        field_text = ' '.join(self.get_marc_field(*marc_field))
                        if strip_out:
                            field_text = re.sub(strip_out, '', field_text)
                        if field_text:
                            field_texts.add(field_text)
                    if len(field_texts) == 1:
                        dict_[schema_element] = list(field_texts)[0]
                    elif len(field_texts) > 1:
                        dict_[schema_element] = sorted(field_texts)
            else:
                field_text_arr = []
                for marc_field in marc_fields:
                    field_text_arr = field_text_arr + \
                        self.get_marc_field(*marc_field)
                field_text = ' '.join(field_text_arr)
                if strip_out:
                    field_text = re.sub(strip_out, '', field_text)
                if field_text:
                    dict_[schema_element] = field_text
        return dict_

    def __str__(self):
        """Return Schema.org data as a JSON-LD string.

        Returns:
            str
        """
        return json.dumps(
            self(),
            ensure_ascii=False,
            indent=4
        )


class SocSciMapsMarcXmlToEDM(MarcToDc):
    """A class to convert MARCXML to  Europeana Data Model (EDM)."""

    # from Charles, via Slack (10/3/2019 9:52am)
    # For the TIFF image we also need a edm:WebResource. Ideally we would want
    # the original form of the metadata (whether .xml or .mrc), a ore:Proxy.

    # does everything get a dcterm:created predicate?
    # is edm:WebResource the same as ore:resourceMap?

    # Setting namespaces for subject, predicate, object values
    VRA = Namespace('http://purl.org/vra/')
    OAI = Namespace('http://www.openarchives.org/OAI/2.0/')
    ORE = Namespace('http://www.openarchives.org/ore/terms/')
    ERC = Namespace('http://purl.org/kernel/elements/1.1/')
    EDM = Namespace('http://www.europeana.eu/schemas/edm/')
    BASE = Namespace('http://ark.lib.uchicago.edu/ark:/61001/')

    def __init__(self, marcxml):
        """Initialize an instance of the class MarcXmlToEDM.

        Args:
            graph (Graph): a EDM graph collection from a single record.
        """
        super().__init__(marcxml)

        if isinstance(self.identifier, list):
            self.identifier = self.identifier[0]

        self.graph = Graph()
        for prefix, ns in (('dc', DC), ('dcterms', DCTERMS), ('edm', self.EDM),
                           ('erc', self.ERC), ('ore', self.ORE)):
            self.graph.bind(prefix, ns)
        self._build_graph()

    def _build_graph(self):
        short_id = self.identifier.replace('http://pi.lib.uchicago.edu/1001', '')
        agg = URIRef('/aggregation/digital_collections/IIIF_Files{}'.format(short_id))
        cho = URIRef('/digital_collections/IIIF_Files{}'.format(short_id))
        pro = URIRef('/digital_collections/IIIF_Files/{}.mrc_or.xml'.format(short_id))
        rem = URIRef('/rem/digital_collections/IIIF_Files{}'.format(short_id))
        wbr = URIRef('/digital_collections/IIIF_Files/{}.tif'.format(short_id))

	# Only add creation dates if notes don't exist yet.

        for sub in (rem, agg):
            if not bool(self.graph.query(
                prepareQuery('ASK { ?s ?p ?o . }'),
                initBindings={'s': sub}
            )):
                self.graph.set((
                    sub,
                    DCTERMS.created,
                    Literal(datetime.datetime.utcnow(), datatype=XSD.date)
                ))

        # Aggregation
        self.graph.set((agg, RDF.type,                self.ORE.aggregation))
        self.graph.set((agg, DCTERMS.modified,        Literal(datetime.datetime.utcnow(), datatype=XSD.date)))
        self.graph.set((agg, self.EDM.aggreatagedCHO, cho))
        self.graph.set((agg, self.EDM.dataProvider,   Literal("University of Chicago Library")))
        self.graph.set((agg, self.ORE.isDescribedBy,  cho))
        self.graph.set((agg, self.EDM.isShownAt,      Literal(self.identifier)))
        #self.graph.set((agg, self.EDM.isShownBy,      Literal('IIIF URL for highest quality image of map')))
        self.graph.set((agg, self.EDM.object,         Literal('IIIF URL for highest quality image of map')))
        self.graph.set((agg, self.EDM.provider,       Literal('University of Chicago Library')))
        self.graph.set((agg, self.EDM.rights,         URIRef('https://rightsstatements.org/page/InC/1.0/?language=en')))
 
        # Cultural Heritage Object
        self.graph.set((cho, RDF.type, self.EDM.ProvidedCHO))

        for pre, obj_str in (
            (DC.coverage,              'dc:coverage'),
            (DC.creator,               'dc:creator'),
            (DC.date,                  'dc:date'),
            (DC.description,           'dc:description'),
            (DC.extent,                'dc:extent'),
            (DC.identifier,            'dc:identifier'),
            (DC.language,              'dc:language'),
            (DC.publisher,             'dc:publisher'),
            (DC.rights,                'dc:rights'),
            (DC.subject,               'dc:subject'),
            (DC.title,                 'dc:title'),
            (DC.type,                  'dc:type'),
            (DCTERMS.spatial,          'dcterms:spatial'),
            (self.EDM.date,            'dc:date'),
            (self.ERC.what,            'dc:title'),
            (self.ERC.when,            'dc:date'),
            (self.ERC.who,             'dc:creator'),
        ):
            obj_str = obj_str.replace('dc:',      '{http://purl.org/dc/elements/1.1/}')
            obj_str = obj_str.replace('dcterms:', '{http://purl.org/dc/terms/}')

            for dc_obj_el in self.dc.findall(obj_str):
                try:
                    self.graph.set((cho, pre, Literal(dc_obj_el.text)))
                except AttributeError:
                    pass

        self.graph.set((cho, DCTERMS.isPartOf, Literal('pi-for-the-collection-in-wagtail')))
        self.graph.set((cho, self.EDM.currentLocation, Literal('Map Collection Reading Room (Room 370)')))
        self.graph.set((cho, self.EDM.type, Literal('IMAGE')))
        self.graph.set((cho, self.ERC.where, cho)) # huh?

        # Proxy
        self.graph.set((pro, RDF.type, self.ORE.proxy))
        self.graph.set((pro, URIRef('http://purl.org/dc/elements/1.1/format'), Literal('application/xml')))
        self.graph.set((pro, self.ORE.proxyFor, cho))
        self.graph.set((pro, self.ORE.proxyIn, agg))

        # Resource Map
        self.graph.set((rem, DCTERMS.modified, Literal(datetime.datetime.utcnow(), datatype=XSD.date)))
        self.graph.set((rem, DCTERMS.creator, URIRef('http://library.uchicago.edu/')))
        self.graph.set((rem, RDF.type, self.ORE.resourceMap))
        self.graph.set((rem, self.ORE.describes, agg))

        # Web Resource
        self.graph.set((wbr, RDF.type, self.EDM.WebResource))
        self.graph.set((wbr, URIRef('http://purl.org/dc/elements/1.1/format'), Literal('image/tiff')))


    def __str__(self):
        """Return EDM data as a string.

        Returns:
            str
        """
        return self.graph.serialize(format='turtle', base=self.BASE).decode("utf-8")


class MarcXmlToOpenGraph(MarcXmlConverter):
    def __init__(self, marcxml):
        self.dc = MarcToDc(marcxml)
    def __str__(self):
        html = '\n'.join(('<meta property="og:title" content="{{ og_title }}" >',
                        '<meta property="og:type" content="{{ og_type }}" >',
                        '<meta property="og:url" content="{{ og_url }}" >',
                        '<meta property="og:image" content="{{ og_image }}" >',
                        '<meta property="og:description" content="{{ og_description }}" >',
                        '<meta property="og:site_name" content="{{ og_site_name }}" >'))
        return jinja2.Template(html).render(
            og_description=self.dc.description[0],
            og_image='image',
            og_site_name='site_name',
            og_title=self.dc.title[0],
            og_type='website',
            og_url='url'
        )


class MarcXmlToTwitterCard(MarcXmlConverter):
    def __init__(self, marcxml):
        self.dc = MarcToDc(marcxml)
    def __str__(self):
        html = '\n'.join(('<meta name="twitter:card" content="{{ twitter_card }}" >',
                          '<meta name="twitter:site" content="{{ twitter_site }}" >',
                          '<meta name="twitter:title" content="{{ twitter_title }}" >',
                          '<meta name="twitter:url" content="{{ twitter_url }}" >',
                          '<meta name="twitter:description" content="{{ twitter_description }}" >',
                          '<meta name="twitter:image" content="{{ twitter_image }}" >',
                          '<meta name="twitter:image:alt" content="{{ twitter_image_alt }}" >'))
        return jinja2.Template(html).render(
            twitter_card='card',
            twitter_description=self.dc.description[0],
            twitter_image='image',
            twitter_image_alt='image_alt',
            twitter_site='site',
            twitter_title=self.dc.title[0],
            twitter_url='url'
        )
