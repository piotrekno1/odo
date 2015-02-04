from into.backends.sql_csv import *
from into import resource, into
import datashape
from into.utils import tmpfile
import os


def normalize(s):
    s2 = ' '.join(s.strip().split()).lower().replace('_', '')
    return s2


fn = os.path.abspath('myfile.csv')

csv = CSV(fn, delimiter=',', has_header=True)
ds = datashape.dshape('var * {name: string, amount: int}')
tbl = resource('sqlite:///:memory:::my_table', dshape=ds)


def test_postgres_load():
    assert normalize(copy_command('postgresql', tbl, csv)) == normalize("""
    COPY my_table from '%s'
        (FORMAT csv,
         DELIMITER E',',
         NULL '',
         QUOTE '"',
         ESCAPE '\\',
         HEADER True,
         ENCODING 'utf-8');
    """ % fn)


def test_sqlite_load():
    assert normalize(copy_command('sqlite', tbl, csv)) == normalize("""
     (echo '.mode csv'; echo '.import %s my_table';) | sqlite3 :memory:
     """ % fn)


def test_mysql_load():
    assert normalize(copy_command('mysql', tbl, csv)) == normalize("""
            LOAD DATA  INFILE '%s'
            INTO TABLE my_table
            CHARACTER SET utf-8
            FIELDS
                TERMINATED BY ','
                ENCLOSED BY '"'
                ESCAPED BY '\\'
            LINES TERMINATED BY '\\n\\r'
            IGNORE 1 LINES;""" % fn)


def test_into_sqlite():
    data = [('Alice', 100), ('Bob', 200)]
    ds = datashape.dshape('var * {name: string, amount: int}')

    with tmpfile('.db') as dbpath:
        with tmpfile('.csv') as csvpath:
            csv = into(csvpath, data, dshape=ds, has_header=False)
            sql = resource('sqlite:///%s::mytable' % dbpath, dshape=ds)
            append_csv_to_sql_table(sql, csv)

            assert into(list, sql) == data
