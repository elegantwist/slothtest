import os
import datetime
import inspect
import pickle
import codecs
import joblib
import io
from . import SlothConnector, sloth_log
from . import SlothConfig


class SlothWatcher:

    sloth_state = None

    instance_id = ""
    snapshot_id = ""

    service_online = False
    sloth_connector = None

    data_watch_dump = []

    dump_counter = 0

    to_dir = None

    def __init__(self):

        self.instance_id = str(os.environ.get('SLOTH_INSTANCE_ID', ""))

    def start(self, to_dir=None):

        self.to_dir = to_dir

        self.session_id = str(datetime.datetime.now().replace(microsecond=0).timestamp())[:-2]

        snap_id = str(os.environ.get('SLOTH_SNAPSHOT_ID', ""))
        if snap_id == "":
            self.snapshot_id = self.session_id

        self.sloth_connector = SlothConnector(self.session_id, self.snapshot_id, self.to_dir)

        self.sloth_state = SlothConfig.SlothState.WATCHING
        os.environ['SLOTH_STATE'] = SlothConfig.SlothState.WATCHING
        os.environ['SLOTH_SNAPSHOT_ID'] = str(self.snapshot_id)

        sloth_log.info("Started id: " + self.session_id)

    def stop(self):

        sloth_log.info("Stopped id: " + self.session_id)

        zip_fn = self.sloth_connector.dump_data(self.data_watch_dump)

        sloth_log.info("Snapshot dumped to: " + zip_fn)

        self.sloth_state = SlothConfig.SlothState.IDLE
        os.environ['SLOTH_STATE'] = str(SlothConfig.SlothState.IDLE)
        self.snapshot_id = ""
        os.environ['SLOTH_SNAPSHOT_ID'] = ""

    def dump(self):

        self.stop()
        self.start()

        self.dump_counter = 0

    def watch(self, fn, in_args, in_kwargs, res, additional_info=""):

        sloth_log.debug("Start watching: " + str(fn))

        try:

            func_dict = self.watch_function(fn, in_args)

            args_dict = self.watch_function_args(fn, in_args, in_kwargs)

            res_dict = self.watch_function_result(res, additional_info)

            sloth_log.debug("End watching: " + str(fn))

            self.data_watch_dump.append({
                'function': func_dict,
                'arguments': args_dict,
                'results': res_dict
            })

            sloth_log.debug("Data dumped for: " + str(fn))

            self.dump_counter += 1

        except Exception as e:

            sloth_log.error("Data was not dumped. Error: " + str(e))

    def watch_function(self, fn, in_args):

        def get_full_scope(fn):
            # build a full path to the method

            def unique_path(shorter_dir=None, longer_dir=None):

                sep = 0
                for i in range(len(longer_dir)):
                    if i >= len(shorter_dir):
                        sep = i
                        break
                    if shorter_dir[i] != longer_dir[i]:
                        sep = i
                        break

                return longer_dir[-(len(longer_dir)-sep):]

            this_dir = os.getcwd()
            remote_dir = os.path.normpath(inspect.getfile(fn)[:-3])

            remote_dir_list = remote_dir.split(os.path.sep)
            this_dir_list = this_dir.split(os.path.sep)

            diff_dir = unique_path(this_dir_list, remote_dir_list)

            return '.'.join(diff_dir)

        def get_callers_stack(fn):
            # get a human-readable stack of callers for the method

            stack = inspect.stack()

            stack_size = len(stack)

            modules = [(index, inspect.getmodule(stack[index][0]))
                       for index in reversed(range(1, stack_size))]

            s = '{name}@{module} '
            callers = []

            for index, module in modules:
                if module.__name__.find("sloth") == -1:
                    callers.append(s.format(module=module.__name__, name=stack[index][3]))

            callers.append(s.format(module=fn.__module__, name=fn.__name__))

            callers.append('')
            callers.reverse()

            return ' <- '.join(callers)

        # check if the function is a class member
        # if it's a class member, we need to dump a class instance

        fn_name = fn.__name__
        if fn.__qualname__.find(".") == -1:
            classname = ""
            class_dump = ""
        else:
            classname = fn.__qualname__.split(".")[0]
            class_dump = self.dump_class_with_joblib(in_args[0])

        dict_comm = {
            'instance_name': self.instance_id,
            'snapshot_name': self.snapshot_id,
            'scope_name': get_full_scope(fn),
            'class_name': classname,
            'class_dump': class_dump,
            'function_name': fn_name,
            'call_stack': get_callers_stack(fn)
        }

        return dict_comm

    def watch_function_args(self, fn=None, in_args=None, in_kwargs=None):
        # bound income real arguments with the all possible arguments of the method
        # and serialize this kwargs list

        bound_args = inspect.signature(fn).bind(*in_args, **in_kwargs)
        bound_args.apply_defaults()
        target_args = dict(bound_args.arguments)

        var_pack = []

        for key, value in target_args.items():

            p_type_tmp = type(value)

            if p_type_tmp is int or p_type_tmp is float or p_type_tmp is bool:
                d_simple = True
                d_val = value
            else:
                d_simple = False
                d_val = self.dump_class_with_joblib(value)

            d_type = codecs.encode(pickle.dumps(p_type_tmp), "base64").decode()

            var_pack.append(self.var_d_pack(par_type=d_type, par_name=key, par_value=d_val,
                                            par_state=str(SlothConfig.SlothValueState.INCOME),
                                            par_simple=d_simple, ))

        return var_pack

    def watch_function_result(self, res=None, additional_info=""):
        # watch and save the result of the method

        var_pack = []
        if type(res) == tuple:

            i = 0
            for ret_val in res:

                p_type_tmp = type(ret_val)

                if p_type_tmp is int or p_type_tmp is float or p_type_tmp is bool:
                    d_simple = True
                    d_res = ret_val
                else:
                    d_simple = False
                    d_res = self.dump_class_with_joblib(ret_val)

                d_type = codecs.encode(pickle.dumps(p_type_tmp), "base64").decode()

                var_pack.append(self.var_d_pack(par_type=d_type, par_name='ret_' + str(i), par_value=d_res,
                                                par_state=str(SlothConfig.SlothValueState.RESULT),
                                                par_simple=d_simple, ))
                i = i + 1
        else:

            p_type_tmp = type(res)

            if p_type_tmp is int or p_type_tmp is float or p_type_tmp is bool:
                d_simple = True
                d_res = res
            else:
                d_simple = False
                d_res = self.dump_class_with_joblib(res)

            d_type = codecs.encode(pickle.dumps(p_type_tmp), "base64").decode()

            var_pack.append(self.var_d_pack(par_type=d_type, par_name='ret_0', par_value=d_res,
                                            par_state=str(SlothConfig.SlothValueState.RESULT),
                                            par_simple=d_simple,
                                            additional_info=additional_info))

        return var_pack

    def dump_class_with_joblib(self, value):

        outputStream = io.BytesIO()
        joblib.dump(value, outputStream)
        outputStream.seek(0)
        d_val = codecs.encode(outputStream.read(), "base64").decode()

        return d_val

    def var_d_pack(self, **kwargs):

        return {
            'par_type': kwargs.get('par_type', ""),
            'par_name': kwargs.get('par_name', ""),
            'par_value': str(kwargs.get('par_value', "")),
            'par_state': kwargs.get('par_state', ""),
            'par_simple': str(kwargs.get('par_simple', "")),
            'additional_info': kwargs.get('additional_info', ""),
        }


