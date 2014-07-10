""" Plinth project specific errors """


class PlinthError(Exception):
    pass


class ActionError(PlinthError):
    """ Use this error for exceptions when executing an action """
    pass
