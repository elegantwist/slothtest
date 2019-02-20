[![Build Status](https://travis-ci.org/elegantwist/slothtest.svg?branch=master)](https://travis-ci.org/elegantwist/slothtest)

# Description

Sloth Test is a Python library that automatically create unit tests based on previous real-life cases to prevent regression bugs.
1. You will connect the Sloth Test library to your project and run the project for execution the typical routine. 
2. The Sloth collect the internal states of the classes, methods and functions you use in your project and you pointed the Sloth to watch at. It will record all possible incomes and outcomes of each method for each run
3. After it collects enough data, the library dumps the collected data to a file
4. For each recorded run in this file, Sloth Test will automatically create a particular unit test, with the particular state of the class, the particular recorded serialized incomes and an assertion of outcomes for this method.
The result is a collection of typical pytest unit tests that can be executed as a part of testing routine.  
5. For each modification of this method you can run these created test cases to check if the method doesn’t get new bugs and implements the business logic it supposed to have.
------------------------------------------------------------------

# Installing

You can use pip to install slothtest:

```pip install slothtest```

from any directory

# Usage


Suppose that we have a critical and sophisticated method that is a part of our ETL process (pd_table is a pandas table) :

```python
def do_useful_stuff(pd_table=None, a=0, b=0):

    for i, row in pd_table.iterrows():
        pd_table['value'][i] = row['value'] * a + b

    return pd_table
```

Let’s show some run examples that we will implement via other method as the part of our ETL process:

```python
def run():

    tables = {
        'table1': pd.DataFrame([{'column': 1, 'value': 1},
                                {'column': 2, 'value': 2},
                                {'column': 3, 'value': 4}]),

        'table2': pd.DataFrame([{'column': 1, 'value': 1},
                                {'column': 2, 'value': 2},
                                {'column': 3, 'value': 4}]),

        'table3': pd.DataFrame([{'value': 1},
                                {'value': 2},
                                {'value': 4}]),

        'table4': pd.DataFrame([{'value': 1000},
                                {'value': 10}]),
    }

    for t_name, pd_table in tables.items():
        print("Table {name}: \n {table} \n".
              format(name=t_name, table=str(do_useful_stuff(pd_table=pd_table, a=2, b=3))))

if __name__ == '__main__':
    run()
```

the results are:

```
Table table1: 
    column  value
0       1      5
1       2      7
2       3     11 

Table table2: 
    column  value
0       1      5
1       2      7
2       3     11 

Table table3: 
    value
0      5
1      7
2     11 

Table table4: 
    value
0   2003
1     23
```

Ok. Next, we need to be sure that this method will implement the business logic it supposed to implement. To do that, we need to write manually a bunch of pytests for this method for various incomes and outcomes (perhaps 100+ tests for different variants of tables). Or use a Sloth Test library to do it for us automatically.

1. The first step - we need to import a @watchme() decorator from a slothtest library. This decorator should be used on the target method need the Sloth to watch at. Let’s add it to our function:

```python
from slothtest import watchme

@watchme()
def do_useful_stuff(pd_table=None, a=0, b=0):

    for i, row in pd_table.iterrows():
        pd_table['value'][i] = row['value'] * a + b

```

2. We need to point a sloth watcher where it should start its watching process and where it should stop to watch. It can be an entry and exits points of an application, or logic start and stop track inside our app. For our tiny app it’s a run method, so our code will look like:

```python
if __name__ == '__main__':
    slothwatcher.start()
    run()
    slothwatcher.stop()

```

.. and that’s all!

3. Now, let’s run our app as usual, and let the Sloth to watch our process run. After a run, in a folder with our example, a new zip-file appears with a filename in digits (it’s a timestamp) and a dump of our runs inside this zip file
The zip-dump creates after a sloth is stopped, or it recorded a certain amount of runs for all the methods it watched. An amount of runs we can set via SlothConfig class

```python
from slothtest import SlothConfig
SlothConfig.DUMP_ITER_COUNT = 200

```

4. At this point, we have a dump file. Now, for further development purpose we need to get a typical pytest unit tests. We can create that from our dump file, using a sloth translator:

```python -m slothtest.sloth_xml_converter -p o:\work\slothexample -d o:\work\slothexample 1549134821.zip```

where -p is the key to a directory where we will put a path to our project, and  -d is the key to a directory where the result pytest files will be created

5. The result of the conversion are two files: 
1) test_sloth_1549134821.py and 2) sloth_test_parval_1549134821.py
The first one is a basic pytest collection for each run of our watched function:


```python
import sloth_test_parval_1549134821 as sl 

def test_do_useful_stuff_1(): 
    from themethod import do_useful_stuff

    try:
        run_result = do_useful_stuff(pd_table=sl.val_do_useful_stuff_1_pd_table, a=sl.val_do_useful_stuff_1_a, b=sl.val_do_useful_stuff_1_b, ) 
    except Exception as e:
        run_result = e

    test_result = sl.res_do_useful_stuff_1_ret_0 
    assert(type(run_result) == type(test_result))
    assert(run_result.equals(test_result))


def test_do_useful_stuff_2(): 
    from themethod import do_useful_stuff

    try:
        run_result = do_useful_stuff(pd_table=sl.val_do_useful_stuff_2_pd_table, a=sl.val_do_useful_stuff_2_a, b=sl.val_do_useful_stuff_2_b, ) 
    except Exception as e:
        run_result = e

    test_result = sl.res_do_useful_stuff_2_ret_0 
    assert(type(run_result) == type(test_result))
    assert(run_result.equals(test_result))
…


```

And the second one is the serialized (or raw values if they are a primitive type) income and outcome values for each run of the method (4 cases):

```python
import codecs
import io
import joblib


# ===== 1: do_useful_stuff@themethod

var_stream = io.BytesIO()
var_stream_str = codecs.decode('gANdWIu…'.encode(),"base64")

var_stream.write(var_stream_str)
var_stream.seek(0)
val_do_useful_stuff_1_pd_table = joblib.load(var_stream)

val_do_useful_stuff_1_a = 2

val_do_useful_stuff_1_b = 3

res_stream = io.BytesIO()
res_stream_str = codecs.decode('gANdWIu…\n'.encode(),"base64")
res_stream.write(res_stream_str)
res_stream.seek(0)
res_do_useful_stuff_1_ret_0 = joblib.load(res_stream)
…

```

6. Now we can run our testing routine with pytest as usual:


```
python -m pytest test_sloth_1549134821.py

================================================= test session starts =================================================
platform win32 -- Python 3.7.0, pytest-4.1.1, py-1.7.0, pluggy-0.8.1
rootdir: o:\work\slothexample, inifile:
plugins: remotedata-0.3.1, openfiles-0.3.2, doctestplus-0.2.0, arraydiff-0.3
collected 4 items

test_sloth_1549134821.py ....                                                                                    [100%]

======================================== 4 passed, 2 warnings in 0.34 seconds =========================================

```

And that’s all. Easy! 

This approach to generate unit tests automatically can be extrapolated for as many cases as you need if your methods and classes are serializable and if you have enough space for data dumps
