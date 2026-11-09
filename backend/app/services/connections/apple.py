"""Bounded local JXA adapters. No native application access until explicit setup/discovery."""

from __future__ import annotations

import json
import platform
import subprocess

from .reconcile import COLOURS


class AppleAdapter:
    writable = {
        "tasks": {"title", "body", "status", "due"},
        "contacts": {"title", "body", "emails", "phones"},
        "notes": {"title", "body"},
        "calendar": {"title", "body", "start", "end"},
        "mail": {"read", "flags"},
    }

    def __init__(self, runner=None):
        self.runner = runner or self.run

    @staticmethod
    def run(script):
        if platform.system() != "Darwin":
            raise RuntimeError("Apple connections require macOS")
        result = subprocess.run(
            ["osascript", "-l", "JavaScript", "-e", script],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode:
            raise RuntimeError(
                "Apple Automation permission is required, or the selected app is unavailable"
            )
        return json.loads(result.stdout or "[]")

    def representation(self, kind, data, scope=None):
        result = {key: data[key] for key in self.writable.get(kind, set()) if key in data}
        if kind == "contacts" and scope and scope.get("vip_group") and "vip" in data:
            result["vip"] = data["vip"]
        if kind == "tasks":
            result["status"] = "completed" if data.get("status") == "completed" else "todo"
        return result

    def discover(self, connection):
        result = {}
        expressions = {
            "tasks": ("Reminders", "lists"),
            "notes": ("Notes", "folders"),
            "calendar": ("Calendar", "calendars"),
            "contacts": ("Contacts", "groups"),
        }
        for kind in connection["config"]["collections"]:
            if kind in expressions:
                app, container = expressions[kind]
                identity = "calendarIdentifier" if kind == "calendar" else "id"
                result[kind] = self.runner(
                    f"const a=Application({json.dumps(app)}); JSON.stringify(a.{container}().map(x=>({{id:String(x.{identity}()),title:String(x.name())}})));"
                )
                if kind == "contacts":
                    result[kind].insert(0, {"id": "all", "title": "All contacts"})
            elif kind == "mail":
                result[kind] = [{"id": "inbox", "title": "Inbox"}]
        return result

    def pull(self, connection, kind, scope):
        config = json.dumps({"lists": scope["lists"], "vip_group": scope.get("vip_group", "")})
        common = f'const c={config}; const rows=[]; const str=x=>String(x||"");\n'
        scripts = {
            "tasks": """const a=Application("Reminders");
for(const l of a.lists()){if(!c.lists.includes(str(l.id())))continue;
for(const r of l.reminders()){let due="";try{const d=r.dueDate();if(d)due=d.toISOString()}catch(e){}
rows.push({id:str(r.id()),version:str(r.modificationDate()),data:{title:str(r.name())||"Reminder",body:str(r.body()),status:r.completed()?"completed":"todo",due:due,list:str(l.name())}}); if(rows.length>1000)throw Error("Choose smaller lists");}}""",
            "contacts": """const a=Application("Contacts"); const vip=new Set();
if(c.vip_group){for(const g of a.groups()){if(str(g.id())===c.vip_group){for(const p of g.people())vip.add(str(p.id()));}}}
let people=[]; if(c.lists.includes("all"))people=a.people();else for(const g of a.groups()){if(c.lists.includes(str(g.id())))people=people.concat(g.people());}
const seen=new Set(); for(const p of people){const id=str(p.id());if(seen.has(id))continue;seen.add(id);
rows.push({id:id,version:str(p.modificationDate()),data:{title:str(p.name())||"Contact",body:str(p.note()),emails:p.emails().map(x=>str(x.value())),phones:p.phones().map(x=>str(x.value())),vip:vip.has(id)}});if(rows.length>1000)throw Error("Choose smaller groups");}""",
            "notes": """const a=Application("Notes");for(const f of a.folders()){if(!c.lists.includes(str(f.id())))continue;for(const n of f.notes()){rows.push({id:str(n.id()),version:str(n.modificationDate()),data:{title:str(n.name())||"Note",body:str(n.plaintext())}});if(rows.length>1000)throw Error("Choose smaller folders");}}""",
            "calendar": """const a=Application("Calendar");for(const cal of a.calendars()){if(!c.lists.includes(str(cal.calendarIdentifier())))continue;for(const e of cal.events()){rows.push({id:str(cal.calendarIdentifier())+"/"+str(e.uid()),version:str(e.stampDate()),data:{title:str(e.summary())||"Event",body:str(e.description()),start:{dateTime:e.startDate().toISOString()},end:{dateTime:e.endDate().toISOString()}}});if(rows.length>1000)throw Error("Choose smaller calendars");}}""",
            "mail": """const a=Application("Mail");for(const m of a.inbox.messages()){let flag=-1;try{if(m.flaggedStatus())flag=m.flagIndex()}catch(e){};const colours=["red","orange","yellow","green","blue","purple","grey"];
rows.push({id:str(m.messageId()),version:"",data:{title:str(m.subject())||"Message",body:str(m.content()),sender:str(m.sender()),read:Boolean(m.readStatus()),flags:flag>=0?[colours[flag]]:[]}});if(rows.length>=200)break;}""",
        }
        rows = self.runner(common + scripts[kind] + "\nJSON.stringify(rows);")
        for row in rows:
            import re

            body = re.sub(
                r"\n*uCore record: [a-f0-9]+\s*$", "", row["data"].get("body", "")
            ).strip()
            if kind == "notes" and body.startswith(row["data"]["title"] + "\n"):
                body = body[len(row["data"]["title"]) :].lstrip()
            row["data"]["body"] = body
        return rows

    def push(self, connection, kind, scope, record, mapping):
        remote = mapping["remote"].split(":", 1)[1] if mapping else ""
        data = record["data"]
        if kind == "mail" and not remote:
            raise ValueError("Mail sync updates existing messages; it does not send or copy mail")
        if kind == "contacts" and not remote:
            # New records have an explicit destination group; all is not a group.
            if scope["target"] == "all":
                raise ValueError("Choose a Contacts group for new contacts")
        payload = json.dumps(
            {
                "data": data,
                "remote": remote,
                "target": scope["target"],
                "record": record["id"],
                "version": mapping["version"] if mapping else "",
                "vip_group": scope.get("vip_group", ""),
            }
        )
        common = (
            "const c=" + payload + ';const d=c.data;const str=x=>String(x||"");let item=null;\n'
        )
        # Existing remote objects are never deleted or recreated. Native optimistic checks
        # protect edits made after the pull phase; missing mapped records need user review.
        scripts = {
            "tasks": """const a=Application("Reminders");const marker="uCore record: "+c.record;
for(const l of a.lists())for(const r of l.reminders()){if((c.remote&&str(r.id())===c.remote)||(!c.remote&&str(r.body()).includes(marker)))item=r;}
if(c.remote&&!item)throw Error("Remote reminder missing");
if(item&&c.version&&str(item.modificationDate())!==c.version)throw Error("Reminder changed remotely");
if(!item){const list=a.lists().find(l=>str(l.id())===c.target);if(!list)throw Error("List unavailable");item=a.Reminder({name:d.title,body:(d.body||"")+"\\n\\n"+marker});list.reminders.push(item);}
item.name=d.title;item.body=(d.body||"").replace(/\\n\\nuCore record: [a-f0-9]+$/,"")+"\\n\\n"+marker;item.completed=d.status==="completed";item.dueDate=d.due?new Date(d.due):null;
JSON.stringify({id:str(item.id()),version:str(item.modificationDate())});""",
            "notes": """const a=Application("Notes");const marker="uCore record: "+c.record;for(const f of a.folders())for(const n of f.notes()){if((c.remote&&str(n.id())===c.remote)||(!c.remote&&str(n.plaintext()).includes(marker)))item=n;}
if(c.remote&&!item)throw Error("Note missing");if(item&&c.version&&str(item.modificationDate())!==c.version)throw Error("Note changed remotely");
if(item){const html=str(item.body());if(item.attachments().length||/<(?!\\/?(?:div|br|h1|p)\\b)[a-z][^>]*>|<(?:div|p|h1)\\b[^>]*\\s(?:style|class)=/i.test(html))throw Error("Rich Apple Notes are read-only here; edit the original to preserve formatting and attachments");}
const esc=s=>str(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");const body="<h1>"+esc(d.title)+"</h1><div>"+esc(d.body||"").replace(/\\n/g,"<br>")+"</div><div>"+marker+"</div>";
if(!item){const f=a.folders().find(f=>str(f.id())===c.target);if(!f)throw Error("Folder unavailable");item=a.Note({name:d.title,body:body});f.notes.push(item);}else {item.name=d.title;item.body=body;}
JSON.stringify({id:str(item.id()),version:str(item.modificationDate())});""",
            "contacts": """const a=Application("Contacts");for(const p of a.people()){if(c.remote&&str(p.id())===c.remote)item=p;}
if(c.remote&&!item)throw Error("Contact missing");if(item&&c.version&&str(item.modificationDate())!==c.version)throw Error("Contact changed remotely");
if(!item){item=a.Person({firstName:d.title,note:d.body||""});a.people.push(item);const group=a.groups().find(g=>str(g.id())===c.target);if(group)a.add(item,{to:group});}
if(str(item.name())!==d.title){item.firstName=d.title;item.lastName="";}item.note=d.body||"";
// Preserve existing addresses; append only values not already present.
for(const value of (d.emails||[])){if(!item.emails().some(x=>str(x.value())===value))item.emails.push(a.Email({value:value}));}
for(const value of (d.phones||[])){if(!item.phones().some(x=>str(x.value())===value))item.phones.push(a.Phone({value:value}));}
if(c.vip_group){const group=a.groups().find(g=>str(g.id())===c.vip_group);if(group){const contains=group.people().some(p=>str(p.id())===str(item.id()));if(d.vip&&!contains)a.add(item,{to:group});if(d.vip===false&&contains)a.remove(item,{from:group});}}a.save();
JSON.stringify({id:str(item.id()),version:str(item.modificationDate())});""",
            "calendar": """const a=Application("Calendar");let cal=null;for(const x of a.calendars()){for(const e of x.events()){if(c.remote===str(x.calendarIdentifier())+"/"+str(e.uid())){item=e;cal=x;}}}
if(c.remote&&!item)throw Error("Event missing");if(item&&c.version&&str(item.stampDate())!==c.version)throw Error("Event changed remotely");
if(!d.start||!d.end)throw Error("Event dates required");const start=new Date(d.start.dateTime||d.start.date),end=new Date(d.end.dateTime||d.end.date);
if(!item){cal=a.calendars().find(x=>str(x.calendarIdentifier())===c.target);if(!cal)throw Error("Calendar unavailable");item=a.Event({summary:d.title,startDate:start,endDate:end,description:d.body||""});cal.events.push(item);}else{item.summary=d.title;item.startDate=start;item.endDate=end;item.description=d.body||"";}
JSON.stringify({id:str(cal.calendarIdentifier())+"/"+str(item.uid()),version:str(item.stampDate())});""",
            "mail": """const a=Application("Mail");for(const m of a.inbox.messages()){if(str(m.messageId())===c.remote)item=m;}if(!item)throw Error("Message missing");
item.readStatus=Boolean(d.read);const colours=["red","orange","yellow","green","blue","purple","grey"];const flags=d.flags||[];item.flaggedStatus=flags.length>0;if(flags.length)item.flagIndex=colours.indexOf(flags[0]);
JSON.stringify({id:c.remote,version:""});""",
        }
        if kind == "mail" and (
            len(data.get("flags", [])) > 1 or any(c not in COLOURS for c in data.get("flags", []))
        ):
            raise ValueError("Apple Mail supports one colour flag; choose one before syncing")
        return self.runner(common + scripts[kind])
