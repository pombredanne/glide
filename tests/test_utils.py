import configparser
import logging
import os
from shutil import copyfile

try:
    import pymysql
except ImportError:
    pymysql = None
import sqlalchemy as sa
from tlbx import rmfile

from glide import *

logging.getLogger("glide").setLevel(logging.DEBUG)

TEST_DATA_NAME = "dma_zip"

assert "GLIDE_CONFIG_FILE" in os.environ, (
    "Please specify the location of a glide config file using the environment "
    "variable GLIDE_CONFIG_FILE"
)
config = configparser.ConfigParser()
config.read(os.environ["GLIDE_CONFIG_FILE"])
test_config = config["TEST"]


def lower(s):
    return s.lower() if type(s) == str else s


def df_lower(df):
    df = df.applymap(lower)
    return df


def row_lower(row):
    for k, v in row.items():
        row[k] = lower(v)
    return row


def lower_rows(data):
    for row in data:
        row_lower(row)
    return data


def get_filenames(rootdir, extension):
    infile = "%s/%s.%s" % (rootdir, TEST_DATA_NAME, extension)
    outfile = "%s/%s.%s" % (test_config["OutputDirectory"], TEST_DATA_NAME, extension)
    rmfile(outfile, ignore_missing=True)
    return infile, outfile


def get_db_filenames(rootdir):
    table = "%s.db" % TEST_DATA_NAME
    in_db_file = rootdir + "/" + table
    out_db_file = "%s/%s" % (test_config["OutputDirectory"], table)
    return table, in_db_file, out_db_file


def get_sqlalchemy_mysql_engine():
    host = test_config["MySQLHost"]
    port = int(test_config["MySQLPort"])
    user = test_config["MySQLUser"]
    password = test_config["MySQLPassword"]
    schema = test_config["MySQLTestSchema"]
    engine = sa.create_engine(
        "mysql+pymysql://%(user)s:%(password)s@%(host)s:%(port)s/%(schema)s" % locals()
    )
    return engine


def get_sqlalchemy_conn():
    engine = get_sqlalchemy_mysql_engine()
    return engine.connect()


def get_pymysql_conn():
    assert pymysql, "PyMySQL package is not installed"
    host = test_config["MySQLHost"]
    port = int(test_config["MySQLPort"])
    user = test_config["MySQLUser"]
    password = test_config["MySQLPassword"]
    schema = test_config["MySQLTestSchema"]
    conn = pymysql.connect(
        host=host,
        port=port,
        db=schema,
        user=user,
        passwd=password,
        cursorclass=pymysql.cursors.DictCursor,
    )
    return conn


def sqlite_glider(rootdir, nodes, reset_output=False):
    table, in_db_file, out_db_file = get_db_filenames(rootdir)
    if reset_output:
        rmfile(out_db_file, ignore_missing=True)
        copyfile(in_db_file, out_db_file)
    glider = Glider(nodes)
    return glider, "`%s`" % table.strip("`")


def sqlalchemy_setup(rootdir, conn, truncate=False, sa_objects=False):
    in_table, out_table = db_tables()
    if truncate:
        try:
            conn.execute("truncate %s" % out_table)
        except Exception as e:
            print("Error during truncation: %s" % str(e))

    if sa_objects:
        meta = sa.MetaData()
        meta.bind = conn.engine
        meta.reflect()
        in_table = meta.tables[in_table.split(".")[-1]]
        out_table = meta.tables[out_table.split(".")[-1]]

    return in_table, out_table


def db_tables():
    in_table = "%s.%s" % (test_config["MySQLTestSchema"], TEST_DATA_NAME)
    out_table = "%s_tmp" % in_table
    return in_table, out_table


def dbapi_setup(rootdir, conn, truncate=False):
    in_table, out_table = db_tables()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("use %s" % test_config["MySQLTestSchema"])
    if truncate:
        cursor.execute("drop table if exists %s" % out_table)
        cursor.execute("create table %s like %s" % (out_table, in_table))
    return in_table, out_table, cursor


def file_glider(rootdir, extension, nodes):
    infile, outfile = get_filenames(rootdir, extension)
    glider = Glider(nodes)
    return glider, infile, outfile


def get_current_dir():
    return os.path.dirname(os.path.abspath(__file__))
