import sys, traceback
import random

from json import (
    loads
)
from configman import (
    Namespace,
    RequiredConfig,
)
from sqlite3 import (
    connect,
    Error,
    OperationalError
)


class SqliteLocalSearchDB(RequiredConfig):
    required_config = Namespace()
    required_config.add_option(
        "db_connection_string",
        default="aol.db",
        doc="the name of the output sqlite file",
        is_argument=True,
    )

    def __init__(self, config):
        self.config = config
        super(SqliteLocalSearchDB, self).__init__()
        self.db_file_name = config.db_connection_string
        self.set_of_all_users = set()
        self.set_of_all_urls = set()


class SqliteLocalSearchDBCreateRaw(SqliteLocalSearchDB):

    def __init__(self, config):
        super(SqliteLocalSearchDBCreateRaw, self).__init__(config)

    def create_new(self):
        try:
            with connect(self.db_file_name) as connection:
                cursor = connection.cursor()
                cursor.execute("create table users (id text)")
                cursor.execute("create table urls (url text)")
                cursor.execute("create table raw_records (user_id text, query text, url text)")
                cursor.execute("create table O (user_id text, query text, url text)")
                cursor.execute("create table S (user_id text, query text, url text)")
                cursor.execute("create table T (user_id text, query text, url text)")
                cursor.execute("create table C (user_id text, query text, url text)")
                connection.commit()
        except OperationalError as e:
            print ('SQLite Error %s' % e)
            raise e

    def dict_to_tuple_iter(self, an_iterator):
        for a_line in an_iterator:
            a_dict = loads(a_line)
            self.set_of_all_users.add(a_dict['clientId'])
            self.set_of_all_urls.add(a_dict['url'])
            yield (a_dict['clientId'], a_dict['query'], a_dict['url'])

    def single_value_to_tuple_iter(self, an_iterator):
        for a_value in an_iterator:
            yield (a_value,)

    def load(self, fp):
        try:
            with connect(self.db_file_name) as conn:
                conn.executemany(
                    'insert into raw_records(user_id, query, url) values (?, ?, ?)',
                    self.dict_to_tuple_iter(fp)
                )
                conn.executemany(
                    'insert into users(id) values (?)',
                    self.single_value_to_tuple_iter(self.set_of_all_users)
                )
                conn.executemany(
                    'insert into urls(url) values (?)',
                    self.single_value_to_tuple_iter(self.set_of_all_urls)
                )

        except Error as e:
            print ('SQLite Error %s' % e)
            traceback.print_exc(file=sys.stdout)




class SqliteLocalSearchDBPartitioned(SqliteLocalSearchDB):
    required_config = Namespace()
    required_config.add_option(
        "opt_in_to_client_ratio",
        default=0.1,
        doc="the ratio of opt-in users to client users used to partition the raw data",
    )

    required_config.add_option(
        "m_opt_in",
        default=10,
        doc="the max number of records to collect for each opt-in user",
    )
    required_config.add_option(
        "m_client",
        default=10,
        doc="the max number of records to collect for each client user",
    )

    def __init__(self, config):
        self.opt_in_to_client_ratio = config.opt_in_to_client_ratio
        self.m_opt_in = config.m_opt_in
        self.m_client = config.m_client
        super(SqliteLocalSearchDBPartitioned, self).__init__(config)

        print ('getting all user data')

        with connect(self.db_file_name) as conn:
            cursor = conn.cursor()
            cursor.execute("select * from users")
            self.all_users = [r[0] for r in cursor.fetchall()]
        print ('shuffling all user data')

        random.shuffle(self.all_users)
        number_of_opt_in_users = int(self.config.opt_in_to_client_ratio * len(self.all_users))

        self.opt_in_users = self.all_users[:number_of_opt_in_users]
        print ('selecting opt-in data')
        self.opt_in_user_data = self.select_user_data(self.opt_in_users, config.m_opt_in)

        print ('selecting client data')
        self.client_users = self.all_users[number_of_opt_in_users:]
        self.client_user_data = self.select_user_data(self.client_users, config.m_client)


    def select_user_data(self, list_of_users, m):  # where m is max number of records per user
        with connect(self.db_file_name) as conn:
            cursor = conn.cursor()
            print ('number of users %d' % len(list_of_users))
            for a_user in list_of_users:
                print ('for user %s' % a_user)
                cursor.execute("select * from raw_records where user_id = ?", (a_user,))
                a_users_records = cursor.fetchall()
                print ('shuffling user %s' % a_user)
                random.shuffle(a_users_records)
                a_users_records = a_users_records[:m]
                print ('inserting user %s' % a_user)
                cursor.executemany("insert into O (user_id, query, url) values (?, ?, ?)", a_users_records)


