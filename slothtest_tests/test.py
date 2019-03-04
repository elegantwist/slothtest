import pytest
import os
import pandas as pd
from slothtest import watchme
from slothtest import slothwatcher


class ClassForTesting:
    debugging = 99

    def __init__(self, dd=0):
        self.debugging = dd

    @watchme()
    def im_a_function_for_testing(self, d_table=None, vv=1):
        for i, row in d_table.iterrows():
            d_table['value'][i] = row['value'] * 10

        return d_table, vv


@watchme()
def im_another_function_for_testing(d_table=None, vv=1):
    for i, row in d_table.iterrows():
        d_table['value'][i] = row['value'] * 10

    return d_table, vv


def test_classmethod():
    dirname = os.path.dirname(__file__)

    d_data = [{'column': 1, 'value': 1},
              {'column': 2, 'value': 2},
              {'column': 3, 'value': 4}]

    d_table = pd.DataFrame(d_data)

    slothwatcher.start()

    fn = ClassForTesting(12).im_a_function_for_testing(d_table, 2)

    assert slothwatcher.dump_counter == 1

    assert len(slothwatcher.data_watch_dump) == 1
    assert len(slothwatcher.data_watch_dump[0]['function']) > 0
    assert len(slothwatcher.data_watch_dump[0]['arguments']) == 3
    assert len(slothwatcher.data_watch_dump[0]['results']) == 2

    assert slothwatcher.data_watch_dump[0]['function']['class_name'] == 'ClassForTesting'
    assert slothwatcher.data_watch_dump[0]['function']['function_name'] == 'im_a_function_for_testing'
    assert slothwatcher.data_watch_dump[0]['function']['scope_name'] == 'test'

    slothwatcher.stop()

    assert os.path.isfile(os.path.join(dirname, slothwatcher.session_id + '.zip'))


def test_function():
    dirname = os.path.dirname(__file__)

    d_data = [{'column': 1, 'value': 1},
              {'column': 2, 'value': 2},
              {'column': 3, 'value': 4}]

    d_table = pd.DataFrame(d_data)

    slothwatcher.start()

    fn = im_another_function_for_testing(d_table, 2)

    assert slothwatcher.dump_counter == 1

    assert len(slothwatcher.data_watch_dump) == 1
    assert len(slothwatcher.data_watch_dump[0]['function']) > 0
    assert len(slothwatcher.data_watch_dump[0]['arguments']) == 2
    assert len(slothwatcher.data_watch_dump[0]['results']) == 2

    assert slothwatcher.data_watch_dump[0]['function']['class_name'] == ''
    assert slothwatcher.data_watch_dump[0]['function']['function_name'] == 'im_another_function_for_testing'
    assert slothwatcher.data_watch_dump[0]['function']['scope_name'] == 'test'

    slothwatcher.stop()

    assert os.path.isfile(os.path.join(dirname, slothwatcher.session_id + '.zip'))
