import xml.etree.ElementTree as ET
import pickle
import codecs
import argparse
import os
import zipfile
# it can be either called via the CLI as a standalone, or as a class
try:
    from .sloth_config import SlothConfig
    from .sloth_log import sloth_log
except:
    from sloth_config import SlothConfig
    from sloth_log import sloth_log


class SlothTestConverter:

    xml_list_tag = '__list__'
    xml_content_tag = '__content__'

    objects_eq_function = SlothConfig.objects_eq

    def _parseXMLtodict(self, parent):
        """
        Converting incoming xml file to dict for better usability

        :param parent: root element, on initial run
        :return: dict
        """

        ret = {}
        if parent.items():
            ret.update(dict(parent.items()))

        if parent.text:
            ret[self.xml_content_tag] = parent.text

        if 's_list' in parent.tag:
            ret[self.xml_list_tag] = []
            for element in parent:
                ret[self.xml_list_tag].append(self._parseXMLtodict(element))
        else:
            for element in parent:
                ret[element.tag] = self._parseXMLtodict(element)

        return ret

    def create_text_of_test_module(self, func_data_dict=None):
        """
        Creating python code for test module, based on incoming dictionary with the description of the function and params

        Results are separated by two modules: test and variables.
        Test module consists of the python unit test for a particular function
        Variables module consists of the income and outcome variables, used in created unit test module

        :param func_data_dict: description of the function and income/outcome params
        :return: text of the test module, text of the variables module

        == Test module text ex:

        ...
        def test_cleanup_1():
            from main import cleanup

            try:
                run_result = cleanup(dt=sl.val_cleanup_1_dt, column_name=sl.val_cleanup_1_column_name, )
            except Exception as e:
                run_result = e

            test_result = sl.res_cleanup_1_ret_0
            assert(run_result.equals(test_result))
        ...

        == Variables module text ex:

        ...
        val_cleanup_1_dt = pickle.loads(codecs.decode('gANjcGFu.......'.encode(),"base64"))
        val_cleanup_1_column_name = 'Advertisers list'
        res_cleanup_1_ret_0 = pickle.loads(codecs.decode('gANjcGFuZGF.........'.encode(),"base64"))
        ...

        """

        func_text = ""
        var_text = ""

        if not func_data_dict:
            sloth_log.error("Couldn't convert the pack. Data dict was not provided!")
            return func_text

        run_id = func_data_dict.get('run_id', "")
        scope = func_data_dict.get('scope', "")
        classname = func_data_dict.get('class_name', "")
        class_dump = func_data_dict.get('class_dump', "")
        fnname = func_data_dict.get('func_name', "")
        target_values_raw = func_data_dict.get('in', [])
        target_result_raw = func_data_dict.get('out', [])

        target_values = self.get_dumped_parameters(target_values_raw)
        target_result = self.get_dumped_parameters(target_result_raw)

        t_func_name = fnname + "_" + str(run_id)

        func_text += 'def test_'+t_func_name+"(): \n"

        if classname == "":
            func_text += '    from ' + scope + ' import ' + fnname + '\n'

        par_str = ""
        for v_val in target_values:

            parname = str(v_val['par_name'])

            if parname == 'self':
                continue

            v_parname = 'val_' + t_func_name + '_' + parname

            if v_val['par_simple']:

                parval = v_val['par_value']
                var_text += v_parname + ' = ' + str(eval(parval)) + '\n\n'

            else:

                parval = "%r" % v_val['par_value']
                var_text += 'var_stream = io.BytesIO()\n'
                var_text += 'var_stream_str = codecs.decode(' + parval + '.encode(),"base64")\n\n'
                var_text += 'var_stream.write(var_stream_str)\n'
                var_text += 'var_stream.seek(0)\n'
                var_text += v_parname + ' = joblib.load(var_stream)\n\n'

            par_str += parname + '=sl.' + v_parname + ', '

        func_text += "\n    try:\n"

        if classname == "":
            func_text += '        run_result = ' + fnname + "(" + par_str + ") \n"
        else:
            parval = "%r" % class_dump
            var_text += 'class_stream = io.BytesIO()\n'
            var_text += 'class_stream_str = codecs.decode(' + parval + '.encode(),"base64")\n'
            var_text += 'class_stream.write(class_stream_str)\n'
            var_text += 'class_stream.seek(0)\n'
            v_classname = 'cls_' + t_func_name + '_' + classname
            var_text += v_classname + ' = joblib.load(class_stream)\n\n'

            func_text += '        run_result = sl.' + v_classname + "." + fnname + "(" + par_str + ") \n"

        func_text += '    except Exception as e:\n'
        func_text += '        run_result = e\n\n'

        # result

        res = []
        for v_res in target_result:

            parname = str(v_res['par_name'])
            v_parname = 'res_' + t_func_name + '_' + parname

            if v_res['par_simple']:

                parval = v_res['par_value']
                var_text += v_parname + ' = ' + str(eval(parval)) + '\n\n'

            else:

                parval = "%r" % v_res['par_value']
                var_text += 'res_stream = io.BytesIO()\n'
                var_text += 'res_stream_str = codecs.decode(' + parval + '.encode(),"base64")\n'
                var_text += 'res_stream.write(res_stream_str)\n'
                var_text += 'res_stream.seek(0)\n'
                var_text += v_parname + ' = joblib.load(res_stream)\n\n'

            res.append('sl.' + v_parname)

        t_res = ', '.join(res)

        if len(target_result) == 0:

            func_text += "    assert(run_result is None)\n"

        elif len(target_result) == 1:

            func_text += "    test_result = " + t_res + " \n"

            var_type = target_result[0]['par_type']

            eq_expr = self.objects_eq_function.get(str(var_type), None)
            if eq_expr is None:
                eq_expr = "__eq__"

            func_text += "    assert(run_result." + eq_expr + "(test_result))\n"

        else:

            func_text += "    test_result = (" + t_res + ") \n"

            for i in range(len(target_result)):

                var_type = target_result[i]['par_type']

                eq_expr = self.objects_eq_function.get(str(var_type), None)
                if eq_expr is None:
                    eq_expr = "__eq__"

                func_text += "    assert(run_result["+str(i)+"]." + eq_expr + "(test_result["+str(i)+"]))\n"

        return func_text, var_text

    def get_dumped_parameters(self, par_val_arr=None):
        """

        Collecting and parsing an array of income/outcome parameters to dict
        An additional logic: decision if the value is simple or not (can you push a value itself to a var,
        or you can serialize only)

        :param par_val_arr: an array of parameters
        :return: an array of dictionaries
        """

        params = []

        if par_val_arr is not None:

            for rec in par_val_arr:

                p_type_tmp = pickle.loads(codecs.decode(rec['par_type'].encode(), "base64"))

                t_d = {
                    'par_name': rec['par_name'],
                    'par_value': rec['par_value'],
                    'par_type': p_type_tmp,
                    'par_simple': rec['par_simple']
                }
                params.append(t_d)

        return params

    def parse_file_create_tests(self, filename=None, to_dir=None):
        """
        The Main function. Get an XML file (zip) of dumped functions and converts it to python unit-test code

        The result is two files:
        test_sloth.py - python code for unit testing all dumped function
        sloth_test_parval.py - python code for dumped variables that used in unit tests

        :param filename: the XML file with dumps you need to convert
        :param to_dir: the directory where to put the result files (current dir by default)
        :return: None
        """

        if filename is None:
            sloth_log.error('Filename was not defined')
            raise Exception('Filename was not defined')

        packname = os.path.basename(filename)[:-4]
        with zipfile.ZipFile(filename) as myzip:
            xml_filename = packname+'.xml'
            with myzip.open(xml_filename) as myfile:
                with open(os.path.join(os.path.dirname(filename),xml_filename), "wb") as fh:
                    fh.write(myfile.read())

        sloth_log.info("Converting: " + packname)

        if to_dir is None:
            to_dir = os.path.dirname(os.path.abspath(__file__))

        try:
            tree = ET.parse(xml_filename)
            root = tree.getroot()
        except Exception as e:
            sloth_log.error('Error while parsing the XML file: ' + str(e))
            raise Exception('Error while parsing the XML file: ' + str(e))

        func_dict = self._parseXMLtodict(root)

        target_test_file = 'import sloth_test_parval_'+packname+' as sl \n\n'

        target_variable_file = "import codecs\n"
        target_variable_file += "import io\n"
        target_variable_file += "import joblib\n\n"

        for func_element in func_dict['functions_list'][self.xml_list_tag]:

            f_run_id = func_element['run_id'].get(self.xml_content_tag, "")
            f_scope = func_element['scope_name'].get(self.xml_content_tag, "")
            f_class_name = func_element['class_name'].get(self.xml_content_tag, "")
            f_class_dump = func_element['class_dump'].get(self.xml_content_tag, "")
            f_name = func_element['function_name'].get(self.xml_content_tag, "")

            f_in = []
            for arg_element in func_element['arguments_list'][self.xml_list_tag]:
                in_d = {
                    'par_type': arg_element['par_type'].get(self.xml_content_tag, ""),
                    'par_name': arg_element['par_name'].get(self.xml_content_tag, ""),
                    'par_value': arg_element['par_value'].get(self.xml_content_tag, ""),
                    'par_simple': eval(arg_element['par_simple'].get(self.xml_content_tag, 'True')),
                }

                f_in.append(in_d)

            f_out = []
            for arg_element in func_element['results_list'][self.xml_list_tag]:
                out_d = {
                    'par_type': arg_element['par_type'].get(self.xml_content_tag, ""),
                    'par_name': arg_element['par_name'].get(self.xml_content_tag, ""),
                    'par_value': arg_element['par_value'].get(self.xml_content_tag, ""),
                    'par_simple': eval(arg_element['par_simple'].get(self.xml_content_tag, 'True')),
                }

                f_out.append(out_d)

            func_dict = {
                'scope': f_scope,
                'class_name': f_class_name,
                'class_dump': f_class_dump,
                'func_name': f_name,
                'run_id': f_run_id,
                'in': f_in,
                'out': f_out
            }

            t_f_t, v_f_t = self.create_text_of_test_module(func_dict)

            target_variable_file += "\n# ===== "+f_run_id+": "+f_name+"@"+f_scope+"\n\n"

            target_test_file += t_f_t
            target_variable_file += v_f_t

            target_variable_file += "\n\n"
            target_test_file += "\n\n"

        ttf = os.path.join(to_dir, "test_sloth_" + packname + ".py")
        with open(ttf, 'w') as f:
            f.write(target_test_file)

        ttv = os.path.join(to_dir, "sloth_test_parval_"+packname+".py")
        with open(ttv, 'w') as f:
            f.write(target_variable_file)

        os.remove(xml_filename)

        sloth_log.info("Convertion finished. Files " + ttf + " and "+ttv+" created!")


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Sloth Watcher Dump to pytest converter')
    parser.add_argument("filename", help="a Sloth's xml dump file (zip archive)")
    parser.add_argument('-d', "--to_dir", help="The directory for result files",
                        default=os.path.dirname(os.path.abspath(__file__)))
    args = parser.parse_args()

    sltc = SlothTestConverter()
    sltc.parse_file_create_tests(args.filename, args.to_dir)
