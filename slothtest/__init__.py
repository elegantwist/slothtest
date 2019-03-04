import traceback
import os
import asyncio
import datetime
from copy import deepcopy
from .sloth_log import sloth_log
from .sloth_connector import SlothConnector
from .sloth_config import SlothConfig
from .sloth_watcher import SlothWatcher
from functools import wraps

# the name of the particular instance
os.environ['SLOTH_INSTANCE'] = 'SLOTH_WATCHER'

# an instance of sloth watcher starts with the initiation of the package
slothwatcher = SlothWatcher()


def watchme():
    """
    The main decorator for the method you need to watch at
    1. copying the income arguments
    2. intercepting the outcome result of the method
    3. regularly dumping the in-and-out of the method to dump-file

    """

    def subst_function(fn):

        @wraps(fn)
        def save_vars(*args, **kwargs):

            if slothwatcher.sloth_state != SlothConfig.SlothState.WATCHING:
                return fn(*args, **kwargs)

            if slothwatcher.dump_counter >= SlothConfig.DUMP_ITER_COUNT:
                slothwatcher.dump()

            in_args = deepcopy(args)
            in_kwargs = deepcopy(kwargs)

            start_time = datetime.datetime.now()

            try:
                res = fn(*args, **kwargs)
                additional_info = ""
            except Exception as e:
                res = e
                additional_info = traceback.format_exc()

            stop_time = datetime.datetime.now()

            asyncio.run(slothwatcher.watch(fn, in_args, in_kwargs, res, additional_info, start_time, stop_time))

            return res

        return save_vars

    return subst_function
