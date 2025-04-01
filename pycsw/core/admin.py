# -*- coding: utf-8 -*-
# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#          Angelos Tzotsos <tzotsos@gmail.com>
#
# Copyright (c) 2024 Tom Kralidis
# Copyright (c) 2015 Angelos Tzotsos
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# =================================================================

import hashlib
import json
import logging
import os
import sys
from glob import glob

import click

from pycsw import __version__
from pycsw.core import config as pconfig
from pycsw.core import metadata, repository, util
from pycsw.core.etree import etree
from pycsw.core.etree import PARSER
from pycsw.core.util import parse_ini_config, str2bool
from pycsw.ogc.api.util import get_typed_value, yaml_dump, yaml_load

LOGGER = logging.getLogger(__name__)


def load_records(context, database, table, xml_dirpath, recursive=False, hashidentifier='NEVER', source='local', force_update=False):
    """Load metadata records from directory of files to database"""

    repo = repository.Repository(database, context, table=table)

    file_list = []

    loaded_files = set()
    if os.path.isfile(xml_dirpath):
        file_list.append(xml_dirpath)
    elif recursive:
        for root, dirs, files in os.walk(xml_dirpath):
            for mfile in files:
                if mfile.endswith('.xml'):
                    file_list.append(os.path.join(root, mfile))
    else:
        files = glob(os.path.join(xml_dirpath, '*.xml')) + glob(os.path.join(xml_dirpath, '*.json'))
        for rec in files:
            file_list.append(rec)

    total = len(file_list)
    counter = 0

    for recfile in sorted(file_list):
        counter += 1
        metadata_record = None
        LOGGER.info('Processing file %s (%d of %d)', recfile, counter, total)
        # read document
        try:
            with open(recfile) as fh:
                metadata_record = json.load(fh)
        except json.decoder.JSONDecodeError:
            metadata_record = etree.parse(recfile, context.parser)
        except etree.XMLSyntaxError:
            LOGGER.error('XML document "%s" is not well-formed', recfile, exc_info=True)
            continue
        except Exception:
            LOGGER.exception('XML document "%s" is not well-formed', recfile)
            continue

        try:
            record = metadata.parse_record(context, metadata_record, repo)
        except Exception:
            LOGGER.exception('Could not parse "%s" as an XML record', recfile)
            continue

        for rec in record:
            LOGGER.info('Inserting %s %s into database %s, table %s ....',
                        rec.typename, rec.identifier, database, table)

            # hash identifier to prevent 404 when using it as parameter
            if hashidentifier.upper() == 'ALWAYS' or (hashidentifier.upper() == 'DOUBLESLASH' and rec.identifier.contains('//')): #noqa
                rec.identifier = hashlib.md5(rec.identifier.encode()).hexdigest()

            # TODO: do this as CSW Harvest
            try:

                if source != 'local':
                    rec.mdsource = source
                repo.insert(rec, source, util.get_today_and_now())
                loaded_files.add(recfile)
                LOGGER.info('Inserted %s', recfile)
            except Exception as err:
                if force_update:
                    LOGGER.info('Record exists. Updating.')
                    repo.update(rec)
                    LOGGER.info('Updated %s', recfile)
                    loaded_files.add(recfile)
                else:
                    if err.args:  # Pull a decent error message
                        LOGGER.error('ERROR: %s not inserted: %s', recfile, err.args[0], exc_info=True)
                    else:
                        LOGGER.error('ERROR: %s not inserted: %s', recfile, err, exc_info=True)

    return tuple(loaded_files)


def export_records(context, database, table, xml_dirpath):
    """Export metadata records from database to directory of files"""
    repo = repository.Repository(database, context, table=table)

    LOGGER.info('Querying database %s, table %s ....', database, table)
    records = repo.session.query(repo.dataset)

    LOGGER.info('Found %d records\n', records.count())

    LOGGER.info('Exporting records\n')

    dirpath = os.path.abspath(xml_dirpath)

    exported_files = set()

    if not os.path.exists(dirpath):
        LOGGER.info('Directory %s does not exist.  Creating...', dirpath)
        try:
            os.makedirs(dirpath)
        except OSError as err:
            LOGGER.exception('Could not create directory')
            raise RuntimeError('Could not create %s %s' % (dirpath, err)) from err

    for record in records.all():
        identifier = \
            getattr(record,
                    context.md_core_model['mappings']['pycsw:Identifier'])

        LOGGER.info('Processing %s', identifier)

        # sanitize identifier
        identifier = util.secure_filename(identifier)
        # write to XML document

        metadata_type = \
            getattr(record,
                    context.md_core_model['mappings']['pycsw:MetadataType'])

        if 'json' in metadata_type:
            extension = 'json'
        else:
            extension = 'xml'

        filename = os.path.join(dirpath, '%s.%s' % (identifier, extension))

        try:
            LOGGER.info('Writing to file %s', filename)
            if hasattr(record.xml, 'decode'):
                str_xml = record.xml.decode('utf-8')
            else:
                str_xml = record.xml
            with open(filename, 'w') as xml:
                xml.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                xml.write(str_xml)
        except Exception:
            # Something went wrong so skip over this file but log an error
            LOGGER.exception('Error writing %s to disk', filename)
            # If we wrote a partial file or created an empty file make sure it is removed
            if os.path.exists(filename):
                os.remove(filename)
            continue
        else:
            exported_files.add(filename)

    return tuple(exported_files)


def refresh_harvested_records(context, database, table, url):
    """refresh / harvest all non-local records in repository"""
    from owslib.csw import CatalogueServiceWeb

    # get configuration and init repo connection
    repos = repository.Repository(database, context, table=table)

    # get all harvested records
    count, records = repos.query(constraint={'where': "mdsource != 'local'", 'values': []})

    if int(count) > 0:
        LOGGER.info('Refreshing %s harvested records', count)
        csw = CatalogueServiceWeb(url)

        for rec in records:
            source = \
                getattr(rec,
                        context.md_core_model['mappings']['pycsw:Source'])
            schema = \
                getattr(rec,
                        context.md_core_model['mappings']['pycsw:Schema'])
            identifier = \
                getattr(rec,
                        context.md_core_model['mappings']['pycsw:Identifier'])

            LOGGER.info('Harvesting %s (identifier = %s) ...',
                        source, identifier)
            # TODO: find a smarter way of catching this
            if schema == 'http://www.isotc211.org/2005/gmd':
                schema = 'http://www.isotc211.org/schemas/2005/gmd/'
            try:
                csw.harvest(source, schema)
                LOGGER.info(csw.response)
            except Exception:
                LOGGER.exception('Could not harvest')
    else:
        LOGGER.info('No harvested records')


def gen_sitemap(context, database, table, url, output_file):
    """generate an XML sitemap from all records in repository"""

    # get configuration and init repo connection
    repos = repository.Repository(database, context, table=table)

    # write out sitemap document
    urlset = etree.Element(util.nspath_eval('sitemap:urlset',
                                            context.namespaces),
                           nsmap=context.namespaces)

    schema_loc = util.nspath_eval('xsi:schemaLocation', context.namespaces)

    urlset.attrib[schema_loc] = \
        '%s http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd' % \
        context.namespaces['sitemap']

    # get all records
    count, records = repos.query(constraint={}, maxrecords=99999999)

    LOGGER.info('Found %s records', count)

    for rec in records:
        url_ = etree.SubElement(urlset,
                                util.nspath_eval('sitemap:url',
                                                 context.namespaces))
        uri = '%s?service=CSW&version=2.0.2&request=GetRepositoryItem&id=%s' % \
            (url,
             getattr(rec,
                     context.md_core_model['mappings']['pycsw:Identifier']))
        etree.SubElement(url_,
                         util.nspath_eval('sitemap:loc',
                                          context.namespaces)).text = uri

    # write to file
    LOGGER.info('Writing to %s', output_file)
    with open(output_file, 'wb') as ofile:
        ofile.write(etree.tostring(urlset, pretty_print=1,
                    encoding='utf8', xml_declaration=1))


def post_xml(url, xml, timeout=30):
    """Execute HTTP XML POST request and print response"""

    LOGGER.info('Executing HTTP POST request %s on server %s', xml, url)

    from owslib.util import http_post
    try:
        with open(xml) as f:
            return http_post(url=url, request=f.read(), timeout=timeout)
    except Exception as err:
        LOGGER.exception('HTTP XML POST error')
        raise RuntimeError(err) from err


def get_sysprof():
    """Get versions of dependencies"""

    none = 'Module not found'

    try:
        import sqlalchemy
        vsqlalchemy = sqlalchemy.__version__
    except ImportError:
        vsqlalchemy = none

    try:
        import pyproj
        vpyproj = pyproj.__version__
    except ImportError:
        vpyproj = none

    try:
        import shapely
        try:
            vshapely = shapely.__version__
        except AttributeError:
            import shapely.geos
            vshapely = shapely.geos.geos_capi_version
    except ImportError:
        vshapely = none

    try:
        import owslib
        try:
            vowslib = owslib.__version__
        except AttributeError:
            vowslib = 'Module found, version not specified'
    except ImportError:
        vowslib = none

    return '''pycsw system profile
    --------------------
    Python version: %s
    os: %s
    SQLAlchemy: %s
    Shapely: %s
    lxml: %s
    libxml2: %s
    pyproj: %s
    OWSLib: %s''' % (sys.version_info, sys.platform, vsqlalchemy,
                     vshapely, etree.__version__, etree.LIBXML_VERSION,
                     vpyproj, vowslib)


def validate_xml(xml, xsd):
    """Validate XML document against XML Schema"""

    LOGGER.info('Validating %s against schema %s', xml, xsd)

    schema = etree.XMLSchema(file=xsd)

    try:
        tree = etree.parse(xml, PARSER)
        schema.assertValid(tree)
        return 'Valid'
    except Exception as err:
        LOGGER.exception('Invalid XML')
        raise RuntimeError('ERROR: %s' % str(err)) from err


def delete_records(context, database, table):
    """Deletes all records from repository"""

    LOGGER.info('Deleting all records')

    repo = repository.Repository(database, context, table=table)
    repo.delete(constraint={'where': '', 'values': []})


def cli_option_verbosity(f):
    def callback(ctx, param, value):
        if value is not None:
            logging.basicConfig(stream=sys.stdout,
                                level=getattr(logging, value))
        return True

    return click.option('--verbosity', '-v',
                        type=click.Choice(['ERROR', 'WARNING', 'INFO', 'DEBUG']),
                        help='Verbosity',
                        callback=callback)(f)


CLI_OPTION_CONFIG = click.option('--config', '-c', required=True,
                                 type=click.Path(exists=True, resolve_path=True),
                                 help='Path to pycsw configuration')

CLI_OPTION_YES = click.option('--yes', '-y', is_flag=True, default=False,
                              help='Bypass confirmation')

CLI_OPTION_YES_PROMPT = click.option('--yes', '-y', is_flag=True,
                                     default=False,
                                     prompt='This will delete all records! Continue?',
                                     help='Bypass confirmation')


def cli_callbacks(f):
    f = cli_option_verbosity(f)
    return f


@click.group()
@click.version_option(version=__version__)
def cli():
    pass


@click.command('setup-repository')
@cli_callbacks
@click.pass_context
@CLI_OPTION_CONFIG
def cli_setup_repository(ctx, config, verbosity):
    """Create repository tables and indexes"""

    with open(config, encoding='utf8') as fh:
        cfg = yaml_load(fh)

    try:
        repository.setup(cfg['repository']['database'], table=cfg['repository'].get('table'))
    except Exception as err:
        msg = f'ERROR: Repository already exists: {err}'
        raise click.ClickException(msg) from err


@click.command('load-records')
@cli_callbacks
@click.pass_context
@CLI_OPTION_CONFIG
@click.option('--path', '-p', 'path', required=True,
              help='File or directory path to metadata records',
              type=click.Path(exists=True, resolve_path=True, file_okay=True))
@click.option('--recursive', '-r', is_flag=True,
              default=False, help='Recurse into subfolders')
@click.option('--hashidentifier', '-h', required=False,
              default='NEVER', help='MD5 Hash of the identifier, values NEVER|ALWAYS|DOUBLESLASH') # noqa
@click.option('--source', '-s', required=False,
              default='local', help='The source of the record')
@CLI_OPTION_YES
def cli_load_records(ctx, config, path, recursive, hashidentifier, source, yes, verbosity):
    """Load metadata records from directory or file into repository"""

    with open(config, encoding='utf8') as fh:
        cfg = yaml_load(fh)

    context = pconfig.StaticContext()

    load_records(
        context,
        cfg['repository']['database'],
        cfg['repository']['table'],
        path,
        recursive,
        hashidentifier,
        source,
        yes
    )


@click.command('delete-records')
@cli_callbacks
@click.pass_context
@CLI_OPTION_CONFIG
@CLI_OPTION_YES_PROMPT
def cli_delete_records(ctx, config, yes, verbosity):
    """Delete all records from repository"""

    with open(config, encoding='utf8') as fh:
        cfg = yaml_load(fh)

    context = pconfig.StaticContext()

    delete_records(
        context,
        cfg['repository']['database'],
        cfg['repository']['table']
    )


@click.command('export-records')
@cli_callbacks
@click.pass_context
@CLI_OPTION_CONFIG
@click.option('--path', '-p', 'path', required=True,
              help='Directory path to metadata records',
              type=click.Path(exists=True, resolve_path=True,
                              writable=True, file_okay=False))
def cli_export_records(ctx, config, path, verbosity):
    """Dump metadata records from repository into directory"""

    with open(config, encoding='utf8') as fh:
        cfg = yaml_load(fh)

    context = pconfig.StaticContext()

    export_records(
        context,
        cfg['repository']['database'],
        cfg['repository']['table'],
        path
    )


@click.command('rebuild-db-indexes')
@cli_callbacks
@click.pass_context
@CLI_OPTION_CONFIG
def cli_rebuild_db_indexes(ctx, config, verbosity):
    """Rebuild repository database indexes"""

    with open(config, encoding='utf8') as fh:
        cfg = yaml_load(fh)

    context = pconfig.StaticContext()

    repo = repository.Repository(cfg['repository']['database'], context, table=cfg['repository'].get('table'))
    repo.rebuild_db_indexes()


@click.command('optimize-db')
@cli_callbacks
@click.pass_context
@CLI_OPTION_CONFIG
def cli_optimize_db(ctx, config, verbosity):
    """Optimize repository database"""

    with open(config, encoding='utf8') as fh:
        cfg = yaml_load(fh)

    context = pconfig.StaticContext()

    repo = repository.Repository(cfg['repository']['database'], context, table=cfg['repository'].get('table'))
    repo.optimize_db()


@click.command('refresh-harvested-records')
@cli_callbacks
@click.pass_context
@CLI_OPTION_CONFIG
@click.option('--url', '-u', 'url', help='URL of harvest endpoint')
def cli_refresh_harvested_records(ctx, config, verbosity, url):
    """Refresh / harvest non-local records in repository"""

    with open(config, encoding='utf8') as fh:
        cfg = yaml_load(fh)

    context = pconfig.StaticContext()

    refresh_harvested_records(
        context,
        cfg['repository']['database'],
        cfg['repository']['table'],
        url
    )


@click.command('gen-sitemap')
@cli_callbacks
@click.pass_context
@CLI_OPTION_CONFIG
@click.option('--output', '-o', 'output', required=True,
              help='Filepath to write sitemap',
              type=click.Path(resolve_path=True, writable=True,
                              dir_okay=False))
def cli_gen_sitemap(ctx, config, output, verbosity):
    """Generate XML Sitemap"""

    with open(config, encoding='utf8') as fh:
        cfg = yaml_load(fh)

    context = pconfig.StaticContext()

    gen_sitemap(
        context,
        cfg['repository']['database'],
        cfg['repository']['table'],
        cfg['server']['url'],
        output
    )


@click.command('post-xml')
@cli_callbacks
@click.pass_context
@click.option('--url', '-u', 'url', required=True, help='URL of CSW endpoint')
@click.option('--xml', '-x', 'xml', required=True,
              help='XML file to POST',
              type=click.Path(resolve_path=True, exists=True,
                              dir_okay=False))
@click.option('--timeout', '-t', 'timeout', default=30,
              help='Timeout (in seconds) for HTTP requests')
def cli_post_xml(ctx, url, xml, timeout, verbosity):
    """Execute a CSW request via HTTP POST"""

    click.echo(post_xml(url, xml, timeout))


@click.command('validate-xml')
@cli_callbacks
@click.pass_context
@click.option('--xml', '-x', 'xml', required=True,
              help='XML document',
              type=click.Path(resolve_path=True, exists=True,
                              dir_okay=False))
@click.option('--xsd', '-s', 'xsd', required=True,
              help='XML Schema document',
              type=click.Path(resolve_path=True, exists=True,
                              dir_okay=False))
def cli_validate_xml(ctx, xml, xsd, verbosity):
    """Validate an XML document against an XML Schema"""

    validate_xml(xml, xsd)


@click.command('get-sysprof')
@click.pass_context
def cli_get_sysprof(ctx):
    """Get versions of dependencies"""

    click.echo(get_sysprof())


@click.command('migrate-config')
@cli_callbacks
@click.pass_context
@CLI_OPTION_CONFIG
def cli_migrate_config(ctx, config, verbosity):
    """Migrate pycsw ini config to YAML"""

    dict_ = {
        'server': {},
        'logging': {},
        'manager': {},
        'metadata': {
            'identification': {},
            'provider': {},
            'contact': {},
            'inspire': {}
        },
        'profiles': [],
        'federatedcatalogues': [],
        'repository': {}
    }

    cfg = parse_ini_config(config)

    for name, value in cfg.items('server'):
        if name == 'loglevel':
            dict_['logging']['level'] = value
        elif name == 'logfile':
            dict_['logging']['logfile'] = value
        elif name == 'profiles':
            dict_[name] = value.split(',')
        elif name == 'federatedcatalogues':
            dict_[name] = value.split(',')
        else:
            dict_['server'][name] = get_typed_value(value)

    for name, value in cfg.items('metadata:main'):
        if name.startswith('identification'):
            new_key = name.replace('identification_', '')
            if new_key == 'keywords':
                dict_['metadata']['identification'][new_key] = value.split(',')
            elif new_key == 'abstract':
                dict_['metadata']['identification']['description'] = value
            else:
                dict_['metadata']['identification'][new_key] = get_typed_value(value)

        if name.startswith('provider'):
            new_key = name.replace('provider_', '')
            dict_['metadata']['provider'][new_key] = get_typed_value(value)

        if name.startswith('contact'):
            new_key = name.replace('contact_', '')
            dict_['metadata']['contact'][new_key] = get_typed_value(value)

    for name, value in cfg.items('manager'):
        if name == 'allowed_ips':
            dict_['manager'][name] = value.split(',')
        elif name == 'transactions':
            dict_['manager'][name] = str2bool(value)
        else:
            dict_['manager'][name] = get_typed_value(value)

    for name, value in cfg.items('repository'):
        if name == 'facets':
            dict_['repository'][name] = value.split(',')
        else:
            dict_['repository'][name] = get_typed_value(value)

    for name, value in cfg.items('metadata:inspire'):
        if name == 'languages_supported':
            dict_['metadata']['inspire'][name] = value.split(',')
        elif name == 'enabled':
            dict_['metadata']['inspire'][name] = str2bool(value)
        elif name == 'gemet_keywords':
            dict_['metadata']['inspire'][name] = value.split(',')
        elif name == 'temp_extent':
            begin, end = value.split('/')
            dict_['metadata']['inspire'][name] = {
                'begin': begin,
                'end': end
            }
        else:
            dict_['metadata']['inspire'][name] = get_typed_value(value)

    yaml_file = config.replace('.cfg', '.yml')
    click.echo(f'Writing to {yaml_file}')
    yaml_dump(dict_, yaml_file)


cli.add_command(cli_setup_repository)
cli.add_command(cli_load_records)
cli.add_command(cli_export_records)
cli.add_command(cli_delete_records)
cli.add_command(cli_rebuild_db_indexes)
cli.add_command(cli_optimize_db)
cli.add_command(cli_refresh_harvested_records)
cli.add_command(cli_gen_sitemap)
cli.add_command(cli_post_xml)
cli.add_command(cli_validate_xml)
cli.add_command(cli_get_sysprof)
cli.add_command(cli_migrate_config)
