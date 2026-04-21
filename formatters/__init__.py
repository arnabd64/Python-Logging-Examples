"""
Module: Formatters

Description:

- A formatter converts the internal `LogRecord` object which contains
all the metadata of the log into a string, dict or any other object which
then the Handler can process

- The default Formatter in python converts the `LogRecord` into a string which
the StreamHandler prints it on the console or the FileHandler dumps it on to a
log file
"""
