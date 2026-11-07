"""
End-to-end smoke test that behaves like the browser (cross-origin, cookies, CSRF header).

Prerequisites: PostgreSQL running, `python manage.py seed_demo_data` done, Django running on
http://localhost:8000, and `pip install requests` (Pillow is already in requirements.txt).
Run:  python scripts/e2e_smoke_test.py      (from the backend folder, venv active)
NOTE: it creates one extra demo ticket each time it runs.
"""
import io, requests
from PIL import Image
API="http://localhost:8000"; ORIGIN={"Origin":"http://localhost:3000"}
PW="CampusFix@123"

class Browser:
    """Mimics the Next.js api client: credentials, X-CSRFToken from /csrf/ JSON, Origin header."""
    def __init__(s): s.s=requests.Session(); s.tok=None
    def csrf(s):
        r=s.s.get(API+"/api/auth/csrf/",headers=ORIGIN); s.tok=r.json()["csrfToken"]
    def req(s,m,path,**kw):
        h=dict(ORIGIN)
        if m!="GET":
            if not s.tok: s.csrf()
            h["X-CSRFToken"]=s.tok
        return s.s.request(m,API+path,headers=h,**kw)
    def login(s,email):
        s.tok=None; r=s.req("POST","/api/auth/login/",json={"email":email,"password":PW}); s.tok=None; return r

def check(label, cond, extra=""):
    print(("PASS " if cond else "FAIL ")+label, extra if not cond else "")
    assert cond

# CORS preflight
pre=requests.options(API+"/api/tickets/",headers={**ORIGIN,"Access-Control-Request-Method":"POST","Access-Control-Request-Headers":"x-csrftoken,content-type"})
check("CORS preflight allows frontend origin + credentials + csrf header",
      pre.headers.get("Access-Control-Allow-Origin")=="http://localhost:3000" and pre.headers.get("Access-Control-Allow-Credentials")=="true" and "x-csrftoken" in pre.headers.get("Access-Control-Allow-Headers","").lower())
bad=requests.options(API+"/api/tickets/",headers={"Origin":"http://evil.example","Access-Control-Request-Method":"POST"})
check("CORS rejects unknown origin", "Access-Control-Allow-Origin" not in bad.headers)

stu,mgr,stf,stu2,other=Browser(),Browser(),Browser(),Browser(),Browser()
check("anonymous -> 401", stu.req("GET","/api/tickets/").status_code==401)
r=stu.login("student1@campusfix.test"); check("student login", r.status_code==200 and r.json()["role"]=="STUDENT")
check("sessionid cookie HttpOnly", any(c.name=="sessionid" and c.has_nonstandard_attr("HttpOnly") for c in stu.s.cookies))
check("me", stu.req("GET","/api/auth/me/").json()["email"]=="student1@campusfix.test")

cats={c["name"]:c["id"] for c in stu.req("GET","/api/categories/").json()}
buf=io.BytesIO(); Image.new("RGB",(30,30),"blue").save(buf,"PNG"); buf.seek(0)
r=stu.req("POST","/api/tickets/",data={"title":"Ceiling fan wobbling","description":"The fan in room 12 wobbles dangerously.","category":cats["Electrical fault / lighting"],"building":"Block-B","floor":"1","room_or_area":"Room 12"},files={"image":("fan.png",buf,"image/png")})
check("student creates ticket with image (multipart)", r.status_code==201, r.text)
t=r.json(); tid=t["id"]; print("   ticket:",t["ticket_number"],t["status"],t["priority"],"attachments:",len(t["attachments"]))
img=stu.req("GET",t["attachments"][0]["url"]); check("student downloads own attachment", img.status_code==200 and img.headers["Content-Type"]=="image/png")

check("student2 cannot see it (404)", stu2.login("student2@campusfix.test").status_code==200 and stu2.req("GET",f"/api/tickets/{tid}/").status_code==404)
check("student2 cannot download attachment", stu2.req("GET",t["attachments"][0]["url"]).status_code==404)

check("manager login", mgr.login("manager.electrical@campusfix.test").status_code==200)
q=mgr.req("GET","/api/tickets/?unassigned=true").json(); check("manager sees it in unassigned queue", tid in [x["id"] for x in q["results"]])
check("manager sets priority HIGH", mgr.req("POST",f"/api/tickets/{tid}/priority/",json={"priority":"HIGH"}).status_code==200)
staff=mgr.req("GET","/api/staff/eligible/").json(); print("   eligible staff:",[s["name"] for s in staff])
sid=[s["id"] for s in staff][0]
r=mgr.req("POST",f"/api/tickets/{tid}/assignments/",json={"assigned_to":sid,"note":"Check today"}); check("manager assigns", r.status_code==201 and r.json()["status"]=="ASSIGNED")

other_mgr=Browser(); other_mgr.login("manager.plumbing@campusfix.test")
check("other-department manager denied (404)", other_mgr.req("POST",f"/api/tickets/{tid}/assignments/",json={"assigned_to":sid}).status_code==404)

check("student cannot resolve via API (403)", stu.req("POST",f"/api/tickets/{tid}/status/",json={"status":"RESOLVED","note":"x"}).status_code in (403,409))
check("student cannot assign (403)", stu.req("POST",f"/api/tickets/{tid}/assignments/",json={"assigned_to":sid}).status_code==403)

email=[s for s in ["staff.electrical1@campusfix.test","staff.electrical2@campusfix.test"]][0]
assigned_email = email if mgr.req("GET",f"/api/tickets/{tid}/").json()["assigned_to"]["name"].endswith("Electrical1") else "staff.electrical2@campusfix.test"
check("staff login", stf.login(assigned_email).status_code==200)
check("staff sees assigned ticket", tid in [x["id"] for x in stf.req("GET","/api/tickets/").json()["results"]])
check("staff starts work", stf.req("POST",f"/api/tickets/{tid}/status/",json={"status":"IN_PROGRESS"}).status_code==200)
check("staff comments", stf.req("POST",f"/api/tickets/{tid}/comments/",json={"message":"Tightening the mount."}).status_code==201)
check("resolve w/o note -> 400", stf.req("POST",f"/api/tickets/{tid}/status/",json={"status":"RESOLVED","note":""}).status_code==400)
check("staff resolves with note", stf.req("POST",f"/api/tickets/{tid}/status/",json={"status":"RESOLVED","note":"Fan remounted and balanced."}).status_code==200)

d=stu.req("GET",f"/api/tickets/{tid}/").json()
check("student sees resolution + comments", d["status"]=="RESOLVED" and d["resolution_note"] and len(d["comments"])==1)
print("   student can do:",d["permissions"]["available_transitions"])
check("student closes", stu.req("POST",f"/api/tickets/{tid}/status/",json={"status":"CLOSED"}).status_code==200)
h=mgr.req("GET",f"/api/tickets/{tid}/history/").json()
print("   history:",[(x["event_type"],x["old_value"],x["new_value"]) for x in h])
check("history complete", [x["event_type"] for x in h].count("STATUS")==4)

s=stu.req("GET","/api/dashboard/summary/").json(); check("student dashboard", s["resolved_or_closed"]>=1)
m=mgr.req("GET","/api/dashboard/summary/").json(); check("manager dashboard", m["total"]>=2 and "overdue" in m)

# logout invalidates; CSRF enforced
nocsrf=requests.Session(); nocsrf.post(API+"/api/auth/csrf/")  # no token
r=stu.s.post(API+"/api/auth/logout/",headers=ORIGIN); check("logout without CSRF header rejected", r.status_code==403)
check("logout with CSRF ok", stu.req("POST","/api/auth/logout/").status_code==204)
check("session dead after logout", stu.req("GET","/api/auth/me/").status_code==401)
print("\nALL END-TO-END CHECKS PASSED")
