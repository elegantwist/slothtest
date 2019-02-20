class SlothConfig:

    # an iteration amount after which the dump will happen in watchme decorator
    DUMP_ITER_COUNT = 100

    # a dictionary that defines the equality operator between two values of the particular type
    # used in pytest creation
    objects_eq = {
        "<class 'pandas.core.series.Series'>": "equals",
        "<class 'pandas.core.frame.DataFrame'>": "equals"
    }

    class SlothState:
        IDLE = "0"
        WATCHING = "1"
        TESTING = "2"

    class SlothValueState:
        RESULT = "0"
        INCOME = "1"
        TEST = "2"

    class SlothResultState:
        NoErrors = "0"
        Warning = "1"
        Errors = "2"
