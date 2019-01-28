#!/usr/bin/env python3
# coding: utf8
from datetime import datetime

from . import Utils
import logging

log = logging.getLogger(__name__)


# noinspection PyClassHasNoInit
class DbRow:
    """
    base class for classes representing a row in the database to allow easy
    generation of queries and an easy interface for callers e.g.
        q = "INSERT INTO SyncFiles ({0}) VALUES ({1})".format(
            self.SyncRow.query, self.SyncRow.params)
        self.cur.execute(query, row.dict)

    Attributes:
        cols_def: keys are names of columns and items are their type
        query: a string to insert after a SELECT or INSERT INTO {db}
        params: a string to insert after VALUES in a sql INSERT or UPDATE

        The remaining attributes are on a per subclass basis and are
        generated from row_def by the db_row decorator
    """
    cols_def = None
    no_update = []
    columns = None
    params = None
    update = None
    dict = None
    empty = False

    # empty row object = boolean False
    def __bool__(self):
        return not self.empty

    # factory method for delivering a DbRow object based on named arguments
    @classmethod
    def make(cls, **k_args):
        new_row = cls()
        for key, value in k_args.items():
            if not hasattr(new_row, key):
                raise ValueError("{0} does not have column {1}".format(
                    cls, key))
            setattr(new_row, key, value)
        new_row.empty = False
        return new_row

    @classmethod
    def db_row(cls, row_class):
        """
        class decorator function to create RowClass classes that represent a row
        in the database

        :param (DbRow) row_class: the class to decorate
        :return (DbRow): the decorated class
        """
        row_class.columns = ','.join(row_class.cols_def.keys())
        row_class.params = ':' + ',:'.join(row_class.cols_def.keys())
        row_class.update = ','.join('{0}=:{0}'.format(col) for
                                    col in row_class.cols_def.keys() if
                                    col not in row_class.no_update)

        def init(self, result_row=None):
            for col, col_type in self.cols_def.items():
                if not result_row:
                    value = None
                elif col_type == datetime:
                    value = Utils.string_to_date(result_row[col])
                else:
                    value = result_row[col]
                setattr(self, col, value)
            if not result_row:
                self.empty = True

        @property
        def to_dict(self):
            return self.__dict__

        row_class.__init__ = init
        row_class.dict = to_dict
        return row_class
