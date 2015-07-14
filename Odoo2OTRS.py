#!/usr/bin/python2.6
# -*- coding: utf-8 -*-

#Abstract:
#Take customers from odoo, handle that data creating users for otrs, and insert users into otrs
#database allowing them to use our otrs ticketing system
#ADiEmme - delmonaco.andrea@gmail.com

import psycopg2, sys, datetime, random, subprocess, smtplib, MySQLdb as mdb

def pg_connect():
    con = None
    try:
        con = psycopg2.connect(database="odoodbname", user="pgsql2mysql", password="password", host="127.0.0.1", port="65432")
        cur = con.cursor()
   
    except psycopg2.DatabaseError, e:
        print "["+cur_date()+"] Error %s" % e
        sys.exit(1)
   
    finally:
        if con:
            return cur


def mysql_connect():
    try:
        con = mdb.connect('localhost', 'otrs', 'otrs_password', 'otrs');
	con.autocommit(True) 
        cur = con.cursor()
    
    except mdb.Error, e:
        print "["+cur_date()+"] Error %d: %s" % (e.args[0],e.args[1]) 
        sys.exit(1)
    
    finally:    
        if con:    
            return cur


def mysql_exist(mysql_conn, email):
    if ',' in email:
        email = email.split(',')
        email = email[0]

    mysql_conn.execute("SELECT id FROM customer_user WHERE email like '"+email+"';")
    res = mysql_conn.fetchone()
    if res:
        return res[0], email;
    else: 
        return 0, email;
        

def mysql_insert_customer(mysql_conn, data_array):
    mysql_conn.execute("SELECT MAX(CAST(customer_id AS UNSIGNED)) FROM customer_company;")
    row = mysql_conn.fetchone()
    customer_id = int(row[0]) + 1
    query = 'INSERT INTO customer_company(customer_id, name, street, zip, city, country, url, valid_id, create_time, create_by, change_time, change_by) VALUES("'+str(customer_id)+'", "'+str(data_array[0])+'", "'+str(data_array[1])+'", "'+str(data_array[2])+'", "'+str(data_array[3])+'", "'+str(data_array[4])+'", "'+str(data_array[5])+'", "'+str(data_array[6])+'", "'+str(data_array[7])+'", "'+str(data_array[8])+'", "'+str(data_array[9])+'", "'+str(data_array[10])+'");'
    mysql_conn.execute(query)
    return customer_id


def gen_password(email):
    rand_num = random.randrange(0, 9999)
    email = email.replace("@", "")
    split_email = email.split(".");
    password = split_email[0]+""+str(rand_num)
    return password  


def mysql_insert_user(mysql_conn, email, customer_id):
    nickname = email
    password = gen_password(email)
    try:
        proc = subprocess.Popen(['/opt/otrs/bin/otrs.AddCustomerUser.pl -f "'+str(nickname)+'" -l "'+str(nickname)+'" -e "'+email+'" -p "'+password+'" -c "'+str(customer_id)+'" "'+str(nickname)+'"'], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()
        print "["+cur_date()+"] "+out
    except:
        print "["+cur_date()+"] Error douring adding user to Otrs db via AddCustomerUser.pl script"
    query = 'SELECT id FROM customer_user WHERE email like "'+str(email)+'" AND login like "'+str(email)+'";'
    mysql_conn.execute(query)
    user_id = mysql_conn.fetchone()
    return user_id[0], password


def send_email(email, password):
    FROM = 'support@yourdomain.net'
    TO = [email]
    SUBJECT = "subject!"
    TEXT = """Put here the text to send to the customer when the user of otrs has been made"""
    message = """\From: %s\nTo: %s\nSubject: %s\n\n%s
    """ % (FROM, ", ".join(TO), SUBJECT, TEXT)
    try:
        server = smtplib.SMTP("mail.example.net", 25)
        server.ehlo()
        server.starttls()
        server.login("user@example.com", "password")
        server.sendmail(FROM, TO, message)
        server.close()
        print "["+cur_date()+"] Email to: "+str(email)+" - "+str(password)+" has been sent"
    except:
        print "["+cur_date()+"] Unable to send email to: "+str(email)


def cur_date():
    date = datetime.datetime.now().strftime( "%Y-%m-%d %H:%M:%S" );
    return date


def syncit(mysql_cur, pg_cur):
    mysql_cur.execute('SELECT name, customer_id FROM customer_company WHERE customer_id != 1')
    mysql_rows = mysql_cur.fetchall()
    for mysql_row in mysql_rows:
        query = "SELECT id, name, comment FROM res_partner WHERE name = '"+str(mysql_row[0])+"';"
        pg_cur.execute(query)
        pg_row = pg_cur.fetchone() 
        if not pg_row or pg_row[1] != mysql_row[0] or not pg_row[2] or 'otrs' not in pg_row[2]:
            mysql_cur.execute("DELETE FROM customer_user WHERE customer_id = '"+str(mysql_row[1])+"';")
            mysql_cur.execute("DELETE FROM customer_company WHERE customer_id = '"+str(mysql_row[1])+"';")
            print "["+cur_date()+"] Company deleted: "+str(pg_row[1])
 

def main():
    pg_cur = pg_connect()
    pg_cur.execute("SELECT name, street, zip, city, (SELECT name FROM res_country WHERE res_country.id = country_id), website, email, comment FROM res_partner WHERE is_company = true AND email IS NOT NULL and id != 1")
    rows = pg_cur.fetchall()
    mysql_cur = mysql_connect()
    for row in rows:
        if row[7] and "otrs" in row[7]: 
            res_ext, email = mysql_exist(mysql_cur, row[6])
            if res_ext == 0:
                data_array = [row[0], row[1], row[2], row[3], str(row[4]), row[5], '1', cur_date(), '2', cur_date(), '2']
                customer_id = mysql_insert_customer(mysql_cur, data_array)
                if customer_id == 0:
                    print "["+cur_date()+"] Problem happened douring adding customer"
                    pg_cur.close()
                    mysql_cur.close()
                    sys.exit(1)
                print "["+cur_date()+"] Customer "+str(row[0])+" with ID:"+str(customer_id)+" added."
	        user_id, password = mysql_insert_user(mysql_cur, email, customer_id)
                if user_id == 0:
                    print "["+cur_date()+"] Problem happened during adding user"
                    pg_cur.close()
                    mysql_cur.close()
                    sys.exit(1)

                print "["+cur_date()+"] User "+str(email)+" with ID:"+str(user_id)+" added."
                send_email(email, password)
            
    syncit(mysql_cur, pg_cur)
    pg_cur.close()
    mysql_cur.close()


if __name__ == "__main__":
    main()
