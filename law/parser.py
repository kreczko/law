# coding: utf-8

"""
Helpers to extract useful information from the luigi command line parser.
"""


__all__ = []


import logging
from argparse import ArgumentParser

import luigi


logger = logging.getLogger(__name__)


# cached objects
_full_parser = None
_root_task_parser = None
_global_cmdline_args = None
_global_cmdline_values = None


def full_parser():
    """
    Returns the full *ArgumentParser* used by the luigi ``CmdlineParser``. The returned instance is
    cached.
    """
    global _full_parser

    if _full_parser:
        return _full_parser

    luigi_parser = luigi.cmdline_parser.CmdlineParser.get_instance()
    if not luigi_parser:
        return None

    # build the full argument parser with luigi helpers
    root_task = luigi_parser.known_args.root_task
    _full_parser = luigi_parser._build_parser(root_task)

    logger.debug("build full luigi argument parser")

    return _full_parser


def root_task_parser():
    """
    Returns a new *ArgumentParser* instance that only contains paremeter actions of the root task.
    The returned instance is cached.
    """
    global _root_task_parser

    if _root_task_parser:
        return _root_task_parser

    luigi_parser = luigi.cmdline_parser.CmdlineParser.get_instance()
    if not luigi_parser:
        return None

    root_task = luigi_parser.known_args.root_task

    # get all root task parameter destinations
    root_dests = []
    for task_name, _, param_name, _ in luigi.task_register.Register.get_all_params():
        if task_name == root_task:
            root_dests.append(param_name)

    # create a new parser and add all root actions
    _root_task_parser = ArgumentParser(add_help=False)
    for action in list(full_parser()._actions):
        if not action.option_strings or action.dest in root_dests:
            _root_task_parser._add_action(action)

    logger.debug("build luigi argument parser for root task {}".format(root_task))

    return _root_task_parser


def global_cmdline_args():
    """
    Returns the list of command line arguments that do not belong to the root task. The returned
    list is cached. Example:

    .. code-block:: python

        global_cmdline_args()
        # -> ["--local-scheduler"]
    """
    global _global_cmdline_args

    if _global_cmdline_args:
        return _global_cmdline_args

    luigi_parser = luigi.cmdline_parser.CmdlineParser.get_instance()
    if not luigi_parser:
        return None

    _global_cmdline_args = root_task_parser().parse_known_args(luigi_parser.cmdline_args)[1]

    return _global_cmdline_args


def global_cmdline_values():
    """
    Returns a dictionary of global command line arguments (computed with
    :py:func:`global_cmdline_args`) to their current values. The returnd dictionary is cached.
    Example:

    .. code-block:: python

        global_cmdline_values()
        # -> {"core_local_scheduler": True}
    """
    global _global_cmdline_values

    if _global_cmdline_values:
        return _global_cmdline_values

    luigi_parser = luigi.cmdline_parser.CmdlineParser.get_instance()
    if not luigi_parser:
        return None

    # go through all actions of the full luigi parser and compare option strings
    # with the global cmdline args
    parser = full_parser()
    global_args = global_cmdline_args()
    _global_cmdline_values = {}
    for action in parser._actions:
        if any(arg in action.option_strings for arg in global_args):
            _global_cmdline_values[action.dest] = getattr(luigi_parser.known_args, action.dest)

    return _global_cmdline_values


def add_cmdline_arg(args, arg, *values):
    """
    Adds a command line argument *arg* to a list of argument *args*, e.g. as returned from
    :py:func:`global_cmdline_args`. When *arg* exists, *args* is returned unchanged. Otherwise,
    *arg* is appended to the end with optional argument *values*. Example:

    .. code-block:: python

        args = global_cmdline_values()
        # -> ["--local-scheduler"]

        add_cmdline_arg(args, "--local-scheduler")
        # -> ["--local-scheduler"]

        add_cmdline_arg(args, "--workers", 4)
        # -> ["--local-scheduler", "--workers", "4"]
    """
    if arg not in args:
        args = list(args) + [arg] + list(values)
    return args


def remove_cmdline_arg(args, arg, n=1):
    """
    Removes the command line argument *args* from a list of arguments *args*, e.g. as returned from
    :py:func:`global_cmdline_args`. When *n* is 1 or less, only the argument is removed. Otherwise,
    the following *n-1* values are removed. Example:

    .. code-block:: python

        args = global_cmdline_values()
        # -> ["--local-scheduler", "--workers", "4"]

        remove_cmdline_arg(args, "--local-scheduler")
        # -> ["--workers", "4"]

        remove_cmdline_arg(args, "--workers", 2)
        # -> ["--local-scheduler"]
    """
    if arg in args:
        idx = args.index(arg)
        args = list(args)
        del args[idx:idx + max(n, 1)]
    return args
