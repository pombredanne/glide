import pandas as pd
import numpy as np

try:
    from dask import compute, delayed
    from dask.dataframe import from_pandas
    from dask.distributed import Client, as_completed as dask_as_completed
except ImportError:
    compute = None
    delayed = None
    Client = None
    dask_as_completed = None
from toolbox import st, set_missing_key

from glide.core import Node, DefaultNode, FuturesPushNode, Glider, consume


class DaskClientPush(FuturesPushNode):
    """Use a dask Client to do a parallel push"""

    executor_class = Client
    as_completed_func = dask_as_completed

    def run(self, *args, **kwargs):
        assert Client, "Please install dask (Client) to use DaskClientPush"
        super().run(*args, **kwargs)


class DaskDelayedPush(DefaultNode):
    """Use dask delayed to do a parallel push"""

    def _push(self, item):
        assert delayed, "Please install dask (delayed) to use DaskDelayedPush"

        if self._logging == "output":
            self._write_log(item)

        assert not "executor_kwargs" in self.context, (
            "%s does not currently support executor_kwargs" % self.__class__
        )

        lazy = []
        if self.context.get("split", False):
            splits = np.array_split(item, len(self._downstream_nodes))
            for i, downstream in enumerate(self._downstream_nodes):
                lazy.append(delayed(downstream._process)(split[i]))
        else:
            for downstream in self._downstream_nodes:
                lazy.append(delayed(downstream._process)(item))
        result = compute(lazy)


class DaskParaGlider(Glider):
    """A parallel Glider that uses a dask Client to execute parallel calls to
    consume()"""

    def consume(self, data, **node_contexts):
        """Setup node contexts and consume data with the pipeline"""
        assert Client, "Please install dask (Client) to use DaskParaGlider"

        with Client() as client:  # Local multi-processor for now
            splits = np.array_split(data, min(len(data), len(client.ncores())))
            futures = []
            for split in splits:
                futures.append(
                    client.submit(consume, self.pipeline, split, **node_contexts)
                )
            for future in dask_as_completed(futures):
                result = future.result()


class DataFrameDaskClientTransformer(Node):
    """Apply a transform to a Pandas DataFrame using dask Client"""

    def run(self, df, func, executor_kwargs=None, **kwargs):
        """Split the DataFrame and call func() using dask Client, concat results"""
        assert Client, "The dask (Client) package is not installed"
        # https://distributed.dask.org/en/latest/api.html
        dfs = []
        executor_kwargs = executor_kwargs or {}
        with Client(**executor_kwargs) as client:
            df_split = np.array_split(df, len(client.ncores()))
            futures = client.map(func, df_split, **kwargs)
            for future, result in dask_as_completed(futures, with_results=True):
                dfs.append(result)
        df = pd.concat(dfs)
        self.push(df)


class DaskDataFrameApplyTransformer(Node):
    """Apply a transform to a Pandas DataFrame using dask dataframe"""

    # NOTE: it may be more efficient to not convert to/from Dask Dataframe in
    # this manner depending on the pipeline
    def run(self, df, func, from_pandas_kwargs=None, **kwargs):
        """Convert to dask dataframe and use apply()"""
        assert from_pandas, "The dask (dataframe) package is not installed"
        from_pandas_kwargs = from_pandas_kwargs or {}
        set_missing_key(from_pandas_kwargs, "chunksize", 500)
        set_missing_key(from_pandas_kwargs, "sort", False)
        ddf = from_pandas(df, **from_pandas_kwargs)
        for column in ddf.columns:
            ddf[column] = ddf[column].apply(
                func, meta=(column, ddf[column].dtype), **kwargs
            )
        df = ddf.compute()
        self.push(df)