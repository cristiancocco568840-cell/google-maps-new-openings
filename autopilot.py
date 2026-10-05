import os, smtplib, requests
from email.mime.text import MIMEText
from zoneinfo import ZoneInfo
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
_started=False

def truthy(v): return str(v or '').lower() in {'1','true','yes','on'}

def telegram(text):
    token=os.getenv('TELEGRAM_BOT_TOKEN','').strip(); chat=os.getenv('TELEGRAM_CHAT_ID','').strip()
    if not token or not chat:return False
    r=requests.post(f'https://api.telegram.org/bot{token}/sendMessage',json={'chat_id':chat,'text':text,'disable_web_page_preview':True},timeout=20); r.raise_for_status(); return True

def email_alert(subject,text):
    host=os.getenv('SMTP_HOST','').strip(); user=os.getenv('SMTP_USER','').strip(); pwd=os.getenv('SMTP_PASSWORD',''); sender=os.getenv('SMTP_FROM',user).strip(); to=os.getenv('ALERT_EMAIL_TO','').strip(); port=int(os.getenv('SMTP_PORT','587'))
    if not host or not sender or not to:return False
    m=MIMEText(text,'plain','utf-8'); m['Subject']=subject; m['From']=sender; m['To']=to
    with smtplib.SMTP(host,port,timeout=20) as s:
        s.starttls();
        if user:s.login(user,pwd)
        s.sendmail(sender,[to],m.as_string())
    return True

def notify(scan,new_rows,future_rows):
    if not new_rows and not future_rows:return
    base=os.getenv('PUBLIC_BASE_URL','').rstrip('/'); lines=[f'New Openings Radar — scan #{scan["id"]}',f'Nuove attività: {len(new_rows)}',f'Aperture future note: {len(future_rows)}']
    if new_rows:
        lines += ['', 'Prime nuove attività:']
        for r in new_rows[:10]: lines.append(f'• {r["name"]} — {r["phone"] or "senza telefono"}')
    if base: lines += ['',f'Risultati: {base}/results/{scan["id"]}']
    text='\n'.join(lines); sent=False
    for fn,args in ((telegram,(text,)),(email_alert,(f'Radar: {len(new_rows)} nuove attività',text))):
        try: sent=fn(*args) or sent
        except Exception as e: print('Alert failed:',e,flush=True)
    if not sent: print(text,flush=True)

def start_scheduler(app):
    global _started
    if _started or not truthy(os.getenv('AUTO_SCAN_ENABLED')): return None
    _started=True; tz=ZoneInfo(os.getenv('AUTO_SCAN_TIMEZONE','Europe/Rome')); hour=int(os.getenv('AUTO_SCAN_HOUR','7')); minute=int(os.getenv('AUTO_SCAN_MINUTE','30'))
    def job():
        try:
            preset=os.getenv('AUTO_SCAN_PRESET','Milano'); p=app.PRESETS.get(preset,app.PRESETS['Milano']); km=float(os.getenv('AUTO_SCAN_COVERAGE_KM',p['coverage_km'])); rad=float(os.getenv('AUTO_SCAN_CELL_RADIUS_M','500')); contacts=truthy(os.getenv('AUTO_SCAN_INCLUDE_CONTACT','true')); raw=os.getenv('AUTO_SCAN_TYPES','').strip(); types=[x.strip() for x in raw.split(',') if x.strip()] if raw else []
            if not types: types=['beauty_salon','hair_salon','barber_shop','nail_salon','spa','gym','fitness_center','supermarket']
            print(f'AUTO SCAN START preset={preset} km={km} radius={rad} types={len(types)} contacts={contacts}',flush=True)
            sid,_=app.run_scan(p['lat'],p['lon'],km,rad,types,contacts); s,n,f=app.get_scan(sid); notify(s,n,f); print(f'Auto scan #{sid}: {len(n)} new',flush=True)
        except Exception as e: print('AUTO SCAN FAILED:',repr(e),flush=True)
    sch=BackgroundScheduler(timezone=tz); sch.add_job(job,CronTrigger(hour=hour,minute=minute,timezone=tz),id='daily_places_scan',replace_existing=True,max_instances=1,coalesce=True); sch.start(); print(f'Autopilot daily {hour:02d}:{minute:02d}',flush=True); return sch
