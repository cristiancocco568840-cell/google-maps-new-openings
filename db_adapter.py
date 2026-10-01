import os, sqlite3
from sqlalchemy import create_engine, text

DB_PATH=os.getenv("DB_PATH","places.db")
DATABASE_URL=os.getenv("DATABASE_URL","").strip()
DB_URL=DATABASE_URL or f"sqlite:///{DB_PATH}"
engine=create_engine(DB_URL,pool_pre_ping=True)

class RowResult:
    def __init__(self,result,lastrowid=None):
        self.result=result; self.lastrowid=lastrowid
    def fetchone(self):
        r=self.result.mappings().first()
        return dict(r) if r else None
    def fetchall(self):
        return [dict(x) for x in self.result.mappings().all()]

class DB:
    def __init__(self): self.conn=engine.connect()
    def _convert(self,sql,params):
        if not isinstance(params,(list,tuple)): return sql,(params or {})
        data={}
        for i,v in enumerate(params):
            k=f"p{i}"; sql=sql.replace("?",f":{k}",1); data[k]=v
        return sql,data
    def execute(self,sql,params=()):
        sql,data=self._convert(sql,params)
        lastrowid=None
        if engine.dialect.name=="postgresql" and sql.lstrip().upper().startswith("INSERT INTO SCANS") and "RETURNING" not in sql.upper():
            sql=sql.rstrip().rstrip(";")+" RETURNING id"
            r=self.conn.execute(text(sql),data)
            row=r.mappings().first(); lastrowid=row["id"] if row else None
            class Empty:
                def mappings(self):
                    class M:
                        def first(self): return None
                        def all(self): return []
                    return M()
            return RowResult(Empty(),lastrowid)
        r=self.conn.execute(text(sql),data)
        try: lastrowid=r.lastrowid
        except Exception: pass
        return RowResult(r,lastrowid)
    def commit(self): self.conn.commit()
    def rollback(self): self.conn.rollback()
    def close(self): self.conn.close()

def conn(): return DB()

def init_db():
    c=conn()
    try:
        sid="BIGSERIAL PRIMARY KEY" if engine.dialect.name=="postgresql" else "INTEGER PRIMARY KEY AUTOINCREMENT"
        c.execute("""CREATE TABLE IF NOT EXISTS places(
          place_id TEXT PRIMARY KEY,name TEXT,address TEXT,primary_type TEXT,types TEXT,
          business_status TEXT,opening_date TEXT,phone TEXT,website TEXT,maps_uri TEXT,
          lat REAL,lon REAL,first_seen TEXT NOT NULL,last_seen TEXT NOT NULL,first_scan_id INTEGER,
          baseline INTEGER DEFAULT 0)""")
        c.execute(f"""CREATE TABLE IF NOT EXISTS scans(
          id {sid},created_at TEXT NOT NULL,center_lat REAL,center_lon REAL,
          coverage_km REAL,cell_radius_m REAL,types_count INTEGER,requests_count INTEGER DEFAULT 0,
          places_seen INTEGER DEFAULT 0,new_places INTEGER DEFAULT 0,future_openings INTEGER DEFAULT 0,
          is_baseline INTEGER DEFAULT 0)""")
        c.commit()
    finally: c.close()
