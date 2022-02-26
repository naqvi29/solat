from flask import Flask, jsonify
from flask_apscheduler import APScheduler
import requests
import json
from datetime import date, datetime, timedelta
import pymongo
from bson.objectid import ObjectId


# set Flask scheduler configuration values
class Config:
    SCHEDULER_API_ENABLED = True

app = Flask(__name__)


# flask scheduler
app.config.from_object(Config())
# initialize scheduler
scheduler = APScheduler()
# if you don't wanna use a config, you can set options here:
# scheduler.api_enabled = True
scheduler.init_app(app)


# MONGOGB DATABASE CONNECTION
connection_url = "mongodb://localhost:27017"
client = pymongo.MongoClient(connection_url)
client.list_database_names()
database_name = "solat"
db = client[database_name]

# interval example
@scheduler.task('interval', id='do_job_1', seconds=30, misfire_grace_time=9)
def job1():
    print('Job 1 executed')
    return save_timings()
@scheduler.task('interval', id='do_job_2', seconds=5, misfire_grace_time=9)
def job2():
    print('Job 2 executed')
    return sendpush()

@app.route("/save-timings")
def save_timings():
    # check if data is already stored
    exist = db.timings.find_one({"date":str(datetime.now().date())})
    if  not exist:
        # inserting
        response =  requests.get("http://api.aladhan.com/v1/timingsByCity?city=Karachi&country=Pakistan&method=1&state=Sindh&school=1")
        data = response.json()
        zone = data['data']['meta']['timezone']
        timings = data['data']['timings']
        print(timings)
        timings['date']= str(datetime.now().date())
        timings['zone'] = zone
        db.timings.insert_one(timings)

        db.tasks.insert_one({"date":str(datetime.now().date()),"zone":zone,"Azan":timings['Fajr'], "status":"pending"})
        db.tasks.insert_one({"date":str(datetime.now().date()),"zone":zone,"Azan":timings['Dhuhr'], "status":"pending"})
        db.tasks.insert_one({"date":str(datetime.now().date()),"zone":zone,"Azan":timings['Asr'], "status":"pending"})
        db.tasks.insert_one({"date":str(datetime.now().date()),"zone":zone,"Azan":timings['Maghrib'], "status":"pending"})
        db.tasks.insert_one({"date":str(datetime.now().date()),"zone":zone,"Azan":timings['Isha'], "status":"pending"})

        # after inserting time for a new day delete the previous one
        prev_day = datetime.now()
        prev_day = prev_day - timedelta(days=1)
        prev_day = str(prev_day.date())
        db.timings.delete_one(({"date":prev_day}))
    return True

@app.route("/fetch-timings")
def fetch_timings():
    times = db.timings.find_one({"date":str(datetime.now().date())})
    return str(times['Fajr'])
    return jsonify({"data":lists})
    

def sendpush():
    try:
        with app.app_context():
            print("job 2 starting")
            # fetch timings 
            times = db.tasks.find({"date":str(datetime.now().date()),"status":"pending"})
            lists = []
            for i in times:
                i.update({"_id": str(i["_id"])})
                lists.append(i)
            time_now = str(datetime.now().strftime("%H:%M"))
            for i in lists:
                print("time_now: ",time_now)
                print("Azan : ",i['Azan'])
                if time_now == i['Azan']:
                    header = {"Content-Type": "application/json; charset=utf-8",
                "Authorization": "Basic OGRjMjc5ZjAtY2ZlMC00MTZhLTgxN2ItNjI3ZWFlYmQ2YjQx"}

                    payload = {"app_id": "19114e23-f9d3-4ea3-a1c2-4984a69a07c3",
                            "included_segments": ["Subscribed Users"],
                            "contents": {"azan2": "play","Azan.aiff":"play"}}
                    
                    req = requests.post("https://onesignal.com/api/v1/notifications", headers=header, data=json.dumps(payload))
                    
                    print(req.status_code, req.reason)
                    print("SOLAT")
                    query = {"_id":ObjectId(i['_id'])}
                    # newvalues = {
                    #     "$set": {
                    #         'status': "completed"
                    #     }
                    #     }      
                    # db.tasks.update_one(query,newvalues)
                    db.tasks.delete_one((query))
    except Exception as e:
        return str(e)

@app.route("/")
def hello_world():
    header = {"Content-Type": "application/json; charset=utf-8",
        "Authorization": "Basic OGRjMjc5ZjAtY2ZlMC00MTZhLTgxN2ItNjI3ZWFlYmQ2YjQx"}

    payload = {"app_id": "19114e23-f9d3-4ea3-a1c2-4984a69a07c3",
            "included_segments": ["Subscribed Users"],
            "contents": {"azan2": "play","Azan.aiff":"play"}}
    
    req = requests.post("https://onesignal.com/api/v1/notifications", headers=header, data=json.dumps(payload))
    
    print(req.status_code, req.reason)
    return jsonify({"success":True,"azan2":True,"Azan.aiff":True,"status":"Notification Send Successfully"})

@app.route("/time")
def time():
    time = datetime.now()
    return str(time)
scheduler.start()
if __name__ == '__main__':
    app.run(debug=True)