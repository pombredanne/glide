from .test_utils import *
from glide import *


def test_process_pool_paraglider(rootdir):
    infile, outfile = get_filenames(rootdir, "csv")
    glider = ProcessPoolParaGlider(CSVExtract("extract") | Print("load"))
    glider.consume([infile], synchronous=True, extract=dict(nrows=10))


def test_thread_pool_paraglider(rootdir):
    infile, outfile = get_filenames(rootdir, "csv")
    glider = ThreadPoolParaGlider(CSVExtract("extract") | Print("load"))
    glider.consume([infile], synchronous=True, extract=dict(nrows=10))


def test_async_thread_pool_paraglider(rootdir):
    infile, outfile = get_filenames(rootdir, "csv")
    glider = ThreadPoolParaGlider(CSVExtract("extract") | Print("load"))
    futures = glider.consume([infile], synchronous=False, extract=dict(nrows=10))
    results = glider.get_results(futures)


def test_sql_process_pool_paraglider(rootdir):
    in_table, out_table = db_tables()
    sql = "select * from %s where Zip_Code < %%(zip)s" % in_table

    glider = ProcessPoolParaGlider(SQLExtract("extract") | PrettyPrint("load"))
    glider.consume(
        [sql],
        synchronous=True,
        cleanup=dict(extract_conn=closer),
        extract=dict(conn=RuntimeContext(get_sqlalchemy_conn), zip="01000"),
    )


def test_sql_thread_pool_paraglider(rootdir):
    in_table, out_table = db_tables()
    sql = "select * from %s where Zip_Code < %%(zip)s" % in_table
    glider = ThreadPoolParaGlider(
        SQLExtract("extract") | PrettyPrint("load"), executor_kwargs=dict(max_workers=4)
    )
    glider.consume(
        [sql],
        synchronous=True,
        extract=dict(
            conn=RuntimeContext(get_pymysql_conn),
            cursor_type=pymysql.cursors.DictCursor,
            params=dict(zip="01000"),
        ),
    )
