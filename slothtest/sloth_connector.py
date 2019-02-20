import os
import xml.etree.ElementTree as xml
import zipfile
from . import sloth_log


class SlothConnector:

    sloth_service = None
    instance_id = ""
    snapshot_id = ""
    session_id = ""
    scope_path = ""
    engage_counter = 0
    xml_filename = ""
    xml_data = None
    to_dir = None


    def __init__(self, session_id="", snapshot_id="", to_dir=None):

        self.to_dir = to_dir

        self.session_id = session_id
        if snapshot_id != "":
            self.snapshot_id = snapshot_id

        self.init_xml()

    def init_xml(self):

        if self.to_dir is None:
            self.to_dir = os.getcwd()

        self.xml_filename = os.path.join(self.to_dir, self.snapshot_id + ".xml")
        #self.xml_filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.snapshot_id+".xml")

        self.xml_data = xml.Element("SlothWatch")

        instance_name = xml.SubElement(self.xml_data, "instance_name")
        instance_name.text = self.instance_id

        snapshot_name = xml.SubElement(self.xml_data, "snapshot_name")
        snapshot_name.text = self.snapshot_id

        session_name = xml.SubElement(self.xml_data, "session_id")
        session_name.text = self.session_id

    def dump_data(self, data_watch_dump=None):

        if data_watch_dump is None:
            sloth_log.error("couldn't dump the data. watch data was not provided!")
            return None

        functions = xml.Element("functions_list")

        n = 0
        for func_watch in data_watch_dump:
            n += 1
            self.dump_function(functions, func_watch['function'], func_watch['arguments'], func_watch['results'], n)

        self.xml_data.append(functions)

        tree = xml.ElementTree(self.xml_data)

        with open(self.xml_filename, "wb") as fh:
            tree.write(fh)

        zip_fn = self.xml_filename[:-4]+'.zip'
        with zipfile.ZipFile(zip_fn, 'w', compression=zipfile.ZIP_DEFLATED) as myzip:
            myzip.write(self.xml_filename, arcname=os.path.basename(self.xml_filename))

        sloth_log.info('zip pack created: '+zip_fn)

        os.remove(self.xml_filename)

        return zip_fn

    def dump_function(self, functions_element=None, function_dict=None, args_dicts=None, res_dicts=None, n=0):

        function_element = xml.SubElement(functions_element, "function")

        run_id = xml.SubElement(function_element, "run_id")
        run_id.text = str(n)

        scope_name = xml.SubElement(function_element, "scope_name")
        scope_name.text = function_dict['scope_name']

        classname = xml.SubElement(function_element, "class_name")
        classname.text = function_dict['class_name']

        classdump = xml.SubElement(function_element, "class_dump")
        classdump.text = function_dict['class_dump']

        function_name = xml.SubElement(function_element, "function_name")
        function_name.text = function_dict['function_name']

        call_stack = xml.SubElement(function_element, "call_stack")
        call_stack.text = function_dict['call_stack']

        args_xml = xml.SubElement(function_element, "arguments_list")
        for arg_dict in args_dicts:

            arg_xml = xml.SubElement(args_xml, "argument")

            par_type = xml.SubElement(arg_xml, "par_type")
            par_type.text = arg_dict['par_type']

            par_name = xml.SubElement(arg_xml, "par_name")
            par_name.text = arg_dict['par_name']

            par_value = xml.SubElement(arg_xml, "par_value")
            par_value.text = arg_dict['par_value']

            par_state = xml.SubElement(arg_xml, "par_state")
            par_state.text = arg_dict['par_state']

            par_simple = xml.SubElement(arg_xml, "par_simple")
            par_simple.text = arg_dict['par_simple']

            additional_info = xml.SubElement(arg_xml, "additional_info")
            additional_info.text = arg_dict['additional_info']

        reslts_xml = xml.SubElement(function_element, "results_list")
        for res_dict in res_dicts:

            reslt_xml = xml.SubElement(reslts_xml, "result")

            par_type = xml.SubElement(reslt_xml, "par_type")
            par_type.text = res_dict['par_type']

            par_name = xml.SubElement(reslt_xml, "par_name")
            par_name.text = res_dict['par_name']

            par_value = xml.SubElement(reslt_xml, "par_value")
            par_value.text = res_dict['par_value']

            par_state = xml.SubElement(reslt_xml, "par_state")
            par_state.text = res_dict['par_state']

            par_simple = xml.SubElement(reslt_xml, "par_simple")
            par_simple.text = res_dict['par_simple']

            additional_info = xml.SubElement(reslt_xml, "additional_info")
            additional_info.text = res_dict['additional_info']

