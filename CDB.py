import fer.classes
import pymysql  # for mySQL
from config import *  # import data to connect and work with DB
from tkinter import Tk  # from tkinter import Tk for Python 3.x
from tkinter.filedialog import askopenfilename  # for file_picker
# from tkinter import messagebox as mb  # for confirm window in delete_all
import platform  # for checking system name
import csv
import os


def connection():  # connect to DB
    try:
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=db_name,
            cursorclass=pymysql.cursors.DictCursor
        )
        print("Connected successfully to dataBase...")
        return conn

    except Exception as ex:
        print("Connection to dataBase refused...")
        print(ex)


v_path = ""  # global variable to save path


def file_picker():  # pick file from folders and return path of the file
    Tk().withdraw()  # we don't want a full GUI, so keep the root window form appearing
    global v_path
    v_path = askopenfilename()  # show an "Open" dialog box and return the path to the selected file
    return v_path


def file_name(fpath):  # extract file name from path
    name = ""
    for char in range(len(fpath) - 1, 0, -1):
        if fpath[char] == "/":
            break
        else:
            name = "{}{}".format(fpath[char], name)
    return name


def csv_path():   # Get (or make) direction to save csv data file and share with fer.classes.csv_path
    curr_rep = os.getcwd()
    csv_rep = ""
    if platform.system() == 'darwin' or platform.system() == 'Linux' or platform.system() == 'linux' or platform.system() == 'macOS':   # path for linux
        if os.path.exists(curr_rep + "/" + "csv_data"):   # if folder exist in exact current repository
            csv_rep = curr_rep + chr(92) + "csv_data" + chr(92) + file_name(v_path) + ".csv"
        else:
            os.makedirs(curr_rep + "/" + "csv_data")   # make folder in exact current repository
            csv_rep = curr_rep + "/" + "csv_data" + "/" + file_name(v_path) + ".csv"
    elif platform.system() == 'win32' or platform.system() == 'Windows' or platform.system() == 'windows' or platform.system() == 'cygwin':   # path for windows
        if os.path.exists(curr_rep + chr(92) + "csv_data"):   # if folder exist in exact current repository
            csv_rep = curr_rep + chr(92) + "csv_data" + chr(92) + file_name(v_path) + ".csv"
        else:
            os.makedirs(curr_rep + chr(92) + "csv_data")   # make folder in exact current repository
            csv_rep = curr_rep + chr(92) + "csv_data" + chr(92) + file_name(v_path) + ".csv"
    fer.classes.csv_path = csv_rep   # set path of csv document to global variable csv_path in fer->classes.py


# UPDATE!!!
def insert_new_video(conn):  # add information about new video in DB
    global v_path
    v_path = file_picker()
    name = file_name(v_path)
    d_status = "Not Checked"
    with conn.cursor() as cursor:
        insert_query = "INSERT INTO {} (Name, Path, Status) VALUES ('{}', '{}', '{}');".format(db_name + "." + table1, name, v_path, d_status)
        cursor.execute(insert_query)
        conn.commit()
    if platform.system() == 'darwin' or platform.system() == 'Linux' or platform.system() == 'linux' or platform.system() == 'macOS':  # return path for Linux/macOS
        return v_path
    elif platform.system() == 'win32' or platform.system() == 'Windows' or platform.system() == 'windows' or platform.system() == 'cygwin':  # return path for Windows
        return v_path.replace("/", chr(92))
    else:  # return name in case: cannot identify the system
        return name


def stat_in_proc(conn):  # change status in DB to "In Process" (by path)
    with conn.cursor() as cursor:
        update_query = "UPDATE {} SET Status='{}' WHERE Path='{}';".format(db_name + "." + table1, "In Process", v_path)
        cursor.execute(update_query)
        conn.commit()
    csv_path()


def stat_finished(conn):  # change status in DB to "Finished" (by path)
    with conn.cursor() as cursor:
        update_query = "UPDATE {} SET Status='{}' WHERE Path='{}';".format(db_name + "." + table1, "Finished", v_path)
        cursor.execute(update_query)
        conn.commit()


def insert_vreport(conn):   # Add data, collected from the video, into DB
    file = fer.classes.csv_path   # get path of csv file from fer->classes
    rows = []
    with open(file, newline='') as csvfile:
        csvreader = csv.reader(csvfile)
        header_csv = next(csvreader)   # save 1st row of file (emotion names)
        for row in csvreader:
            rows.append(row)   # save values of all rows in csv file
    num_of_h = (len(header_csv)/8)   # get number of humans in csv file
    with conn.cursor() as cursor:
        select_query = "SELECT Id AS v_id FROM {} WHERE Status='{}' AND Path='{}';".format(db_name + "." + table1, 'In Process', v_path)
        cursor.execute(select_query)
        vid_id = cursor.fetchone()   # get video id
        conn.commit()
        h_id = 1   # human counter
        for emotion in header_csv:
            # remove person id number from emotion name
            if h_id >= 10:
                for i in range(2):
                    emotion_db = emotion.replace(emotion[len(emotion) - 1], '')
            elif h_id >= 100:
                for i in range(3):
                    emotion_db = emotion.replace(emotion[len(emotion) - 1], '')
            elif h_id >= 1000:
                for i in range(4):
                    emotion_db = emotion.replace(emotion[len(emotion) - 1], '')
            else:
                emotion_db = emotion.replace(emotion[len(emotion)-1], '')
            if h_id > num_of_h:   # refresh human counter for next emotion
                h_id = 1
            index = header_csv.index(emotion)   # get index of current emotion
            if index >= num_of_h:   # in case we have added all values for 1st emotion 'angry'
                if index % num_of_h == 0:   # in case we add values for every next emotion besides angry
                    select_query = "SELECT MIN({}.Row) AS min_r FROM {} WHERE Video_id={};".format(table2, db_name + "." + table2, vid_id['v_id'])
                    cursor.execute(select_query)
                    min_row = cursor.fetchone()   # get 1st row in DB
                    conn.commit()
                    min_r = min_row['min_r']
                    count_r = min_r   # row counter
                for row in rows:
                    if row[index] == '':   # in case value saved as empty string
                        row[index] = 0
                    if emotion_db == 'box':   # another data type for 'box'
                        update_query = "UPDATE {} SET {}='{}' WHERE {}.Row={};".format(db_name + "." + table2, emotion_db, row[index], table2, count_r)
                        cursor.execute(update_query)
                        conn.commit()
                    else:
                        update_query = "UPDATE {} SET {}={} WHERE {}.Row={};".format(db_name + "." + table2, emotion_db, row[index], table2, count_r)
                        cursor.execute(update_query)
                        conn.commit()
                    count_r += 1
            else:   # in case we add 1st emotion 'angry'
                for row in rows:
                    if row[index] == '':
                        row[index] = 0
                    insert_query = "INSERT INTO {} (Video_id, Human_id, {}) VALUES ({}, {}, '{}');".format(db_name + "." + table2, emotion_db, vid_id['v_id'], h_id, row[index])
                    cursor.execute(insert_query)
                    conn.commit()
            h_id += 1


def insert_duration(conn):   # Insert Duration of the video (by path and status)
    with conn.cursor() as cursor:
        update_query = "UPDATE {} SET Duration={} WHERE Status='{}' AND Path='{}';".format(db_name + "." + table1, fer.classes.get_duration, 'In Process', v_path)
        cursor.execute(update_query)
        conn.commit()


def get_emotion_n(conn, vid_id):   # function to know the emotions value for Nsecs (by video id)
    emotions = ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral']
    emotions_val = {'angry': 0.0, 'disgust': 0.0, 'fear': 0.0, 'happy': 0.0, 'sad': 0.0, 'surprise': 0.0, 'neutral': 0.0}
    with conn.cursor() as cursor:
        select_query = "SELECT Duration AS duration FROM {} WHERE Id={};".format(db_name + "." + table1, vid_id)
        cursor.execute(select_query)
        duration = cursor.fetchone()   # get Duration of the video from DB
        conn.commit()
        select_query = "SELECT MAX(Human_id) AS persons FROM {} WHERE Video_id={};".format(db_name + "." + table2, vid_id)
        cursor.execute(select_query)
        m_person = cursor.fetchone()   # get Number of Persons in the video from DB
        conn.commit()
        select_query = "SELECT MIN({}.Row) AS min_r, MAX({}.Row) AS max_r FROM {} WHERE Video_id={} AND Human_id=1;".format(table2, table2, db_name + "." + table2, vid_id)
        cursor.execute(select_query)
        min_max = cursor.fetchone()   # get min and max Row from DB to count frames and fps
        conn.commit()
        frames = min_max["max_r"] - (min_max["min_r"] - 1)   # get actual number of rows(frames) from DB
        fps = round(frames / duration["duration"])   # get frames per second (fps)
        exp_frames = fps * round(duration["duration"])   # get expected number of rows due to fps
        diff = 0
        if exp_frames != frames:
            diff = exp_frames - frames   # get difference between expected and actual number of rows if there is
        first_sec = int(input("Emotions from second: "))
        last_sec = int(input("to second: "))
        r_slice = (last_sec * fps) - (first_sec * fps)
        for emotion in emotions:
            for person in range(1, m_person['persons']+1):#print("Current Person: ", person)
                select_query = "SELECT MIN({}.Row) AS min_r_p FROM {} WHERE Video_id={} AND Human_id={};".format(table2, db_name + "." + table2, vid_id, person)
                cursor.execute(select_query)
                min_row_per_person = cursor.fetchone()  # get min Row for person from DB
                conn.commit()
                if first_sec == last_sec:   # get emotions value in exact Nsecond
                    if first_sec == round(duration["duration"]):   # for the last second of the video
                        select_query = "SELECT {} AS em_val FROM {} WHERE {}.Row=(SELECT MAX({}.Row) FROM {} WHERE Video_id={} AND Human_id={});".format(emotion, db_name + "." + table2, table2, table2, db_name + "." + table2, vid_id, person)
                        cursor.execute(select_query)
                        em_val = cursor.fetchone()  # get emotion value in exact Nsecond Not considering persons
                        conn.commit()
                        emotions_val[emotion] += em_val['em_val']
                    else:
                        moment_row = min_row_per_person['min_r_p'] + (fps * first_sec)
                        select_query = "SELECT {} AS em_val FROM {} WHERE {}.Row={};".format(emotion, db_name + "." + table2, table2, moment_row)
                        cursor.execute(select_query)
                        em_val = cursor.fetchone()  # get emotion value in exact Nsecond Not considering persons
                        conn.commit()
                        emotions_val[emotion] += em_val['em_val']  # set avg_emotion_val to the key dictionary
                else:   # get emotions value for duration between first Nsecond and last Nsecond
                    start_row = min_row_per_person['min_r_p'] + (fps * first_sec)
                    if last_sec != round(duration['duration']) or diff == 0:
                        finish_row = start_row + r_slice   # set last Row for person from DB for chosen duration, if there is No difference
                    else:
                        finish_row = (start_row + r_slice) - diff   # set last Row for person from DB for chosen duration if there is difference
                    select_query = "SELECT AVG({}) AS avg_val FROM {} WHERE {}.Row>={} AND {}.Row<{};".format(emotion, db_name + "." + table2, table2, start_row, table2, finish_row)
                    cursor.execute(select_query)
                    em_val = cursor.fetchone()   # get average emotion value for the period Not considering persons
                    conn.commit()
                    emotions_val[emotion] += em_val['avg_val']   # set avg_emotion_val to the key dictionary
            emotions_val[emotion] /= m_person['persons']   # set average emotion value for the period considering persons
    return emotions_val

'''def print_p():  # print path saved in global variable v_path
    global v_path
    print("v_path = " + v_path)'''


'''def delete_all(conn):  # delete all information from DB table
    opt = mb.askyesno(title='Delete all data from DataBase?',
                      message='Are you sure you want to Delete All data from DataBase?')  # confirmation window
    if opt:
        with conn.cursor() as cursor:
            delete_query = "DELETE FROM {}".format(db_name + table1)
            cursor.execute(delete_query)
            conn.commit()
    else:
        return'''


'''def print_all(conn):  # print all columns in DB
    with conn.cursor() as cursor:
        select_all_rows = 'SELECT * FROM {};'.format(db_name + table1)
        cursor.execute(select_all_rows)
        rows = cursor.fetchall()
        conn.commit()
        print(" " + ("_" * 138))
        print("| {:<5}| {:<30}| {:80}| {:<15}|".format("Id", "Name", "Path", "Status"))
        print(" " + ("_" * 138))
        for row in rows:
            print("| {:<5}| {:<30}| {:80}| {:<15}|".format(row['Id'], row['Name'], row['Path'], row['Status']))
            print("|" + (138 * "_") + "\n")'''
