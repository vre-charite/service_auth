from authconfig import ConfigClass
import psycopg2

class Policy(object):
    def __init__(self):
        try:
            self.conn = psycopg2.connect(
                user = ConfigClass.dbuser,
                password = ConfigClass.dbpass,
                host = ConfigClass.dbhost,
                port = ConfigClass.dbport,
                database = ConfigClass.db)
             
            self.table = ConfigClass.policy_table

        except (Exception, psycopg2.Error) as error :
            print ("Error while connecting to PostgreSQL", error)

    def add_policy(self, name, roles):
        if self.get_policy(name):
            return False
        cur = self.conn.cursor()
        roles = map(lambda i:"'"+i+"'", roles)
        roles = ','.join(roles)
        sqlstring = "INSERT INTO policy (name, role) VALUES('{}',ARRAY [{}]);".format(name, roles)
        cur.execute(sqlstring)
        self.conn.commit()
        cur.close()
        return True

    def delete_policy(self, name):
        pass
    def update_policy(self, name, roles):
        pass

    def get_policy(self, name):
        cur = self.conn.cursor()
        cur.execute("""SELECT * FROM  {} WHERE name='{}';""".format(self.table, name))
        rows = cur.fetchall()
        result = rows[0] if len(rows)>0 else None 
        cur.close()
        return result

    def close_con(self):
        self.conn.close()

p = Policy()
p.add_policy("n2",['r1','r2'])