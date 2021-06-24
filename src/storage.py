from functools import wraps

from rethinkdb import RethinkDB

from utils import wrap_class_methods


def control_connection(func):
    @wraps(func)
    def wrapper(self, *args, **kw):
        conn = self.r.connect("localhost", 28015).repl()
        try:
            res = func(self, *args, **kw)
        finally:
            conn.close()
        return res

    return wrapper


@wrap_class_methods(control_connection)
class Storage:

    table_name = "schedules"

    def __init__(self) -> None:
        self.r = RethinkDB()
        with self.r.connect("localhost", 28015) as conn:
            if not self.r.table_list().contains("schedules").run(conn):
                self.r.db("test").table_create(
                    self.table_name, primary_key="chat_id"
                ).run(conn)

    def get_all(self):
        cursor = self.r.table(self.table_name).run()
        data = list(cursor)

        return data

    def get(self, chat_id: str):
        return self.r.table(self.table_name).get(chat_id).run()

    def add(self, chat_id: str, days: list, time: str):
        elem = self.r.table(self.table_name).get(chat_id).run()

        if elem:
            res = (
                self.r.table(self.table_name)
                .filter(self.r.row["chat_id"] == chat_id)
                .update({"days": days, "time": time})
                .run()
            )
            return res["replaced"] == 1

        new = {"chat_id": chat_id, "days": days, "time": time}

        res = self.r.table(self.table_name).insert(new).run()

        return res["inserted"] == 1

    def delete(self, chat_id: str):
        res = (
            self.r.table(self.table_name)
            .filter(self.r.row["chat_id"] == chat_id)
            .delete()
            .run()
        )

        return res["deleted"] == 1
