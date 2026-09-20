from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
import threading
import time
import uuid
from typing import Any

from .executor import CrewExecutor
from .registry import CrewRegistry


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class JsonState:
    def __init__(self, path: str | Path, default: Any):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.default = default
        self.lock = threading.RLock()

    def load(self):
        with self.lock:
            if not self.path.exists(): return json.loads(json.dumps(self.default))
            return json.loads(self.path.read_text(encoding='utf-8'))

    def save(self, value):
        with self.lock:
            tmp = self.path.with_suffix(self.path.suffix + '.tmp')
            tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
            tmp.replace(self.path)


class CrewAdminService:
    """Administrator-owned operational state. State lives outside deployed packages.

    Schedules/default inputs/metadata overrides are keyed by crew_id, therefore a new
    deployment/version never overwrites administrator settings.
    """
    def __init__(self, registry: CrewRegistry, executor: CrewExecutor, state_root: str | Path = 'admin_state', max_workers: int = 4):
        self.registry, self.executor = registry, executor
        root = Path(state_root)
        self.settings = JsonState(root/'crew_settings.json', {})
        self.history = JsonState(root/'run_history.json', [])
        self.pool = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix='crew-worker')
        self.max_workers = max_workers
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._last_minute: dict[str, str] = {}

    def start_scheduler(self):
        if self._thread and self._thread.is_alive(): return
        self._thread = threading.Thread(target=self._scheduler_loop, daemon=True, name='crew-cron')
        self._thread.start()

    def stop_scheduler(self): self._stop.set()

    def get_settings(self, crew_id: str) -> dict:
        allv = self.settings.load()
        return allv.get(crew_id, {'schedule': {'enabled': False, 'cron': ''}, 'default_inputs': {}, 'metadata': {}})

    def patch_settings(self, crew_id: str, patch: dict) -> dict:
        allv = self.settings.load(); cur = self.get_settings(crew_id)
        for key in ('schedule','default_inputs','metadata'):
            if key in patch:
                if isinstance(cur.get(key), dict) and isinstance(patch[key], dict): cur[key].update(patch[key])
                else: cur[key] = patch[key]
        if cur.get('schedule',{}).get('cron'): validate_cron(cur['schedule']['cron'])
        allv[crew_id] = cur; self.settings.save(allv); return cur

    def kickoff(self, crew_id: str, version: str, inputs: dict | None = None, trigger='manual') -> dict:
        run_id = str(uuid.uuid4())
        defaults = self.get_settings(crew_id).get('default_inputs', {})
        merged = {**defaults, **(inputs or {})}
        rec = {'run_id':run_id,'crew_id':crew_id,'version':version,'trigger':trigger,'status':'queued','inputs':merged,'created_at':_now(),'started_at':None,'ended_at':None,'outputs':None,'error':None,'verbose':[]}
        self._append_history(rec)
        self.pool.submit(self._run, run_id, crew_id, version, merged)
        return rec

    def _run(self, run_id, crew_id, version, inputs):
        self._update_run(run_id, status='running', started_at=_now(), verbose_append='worker started')
        try:
            result = self.executor.run(crew_id, version, inputs, correlation_id=run_id)
            verbose = result.metadata.get('verbose') if isinstance(result.metadata, dict) else None
            self._update_run(run_id, status='succeeded', ended_at=_now(), outputs=result.outputs, verbose_append=verbose or 'crew completed')
        except Exception as exc:
            self._update_run(run_id, status='failed', ended_at=_now(), error=str(exc), verbose_append=f'ERROR: {exc}')

    def list_history(self, crew_id: str | None = None) -> list[dict]:
        rows = self.history.load()
        if crew_id: rows = [x for x in rows if x['crew_id']==crew_id]
        return list(reversed(rows))

    def get_run(self, run_id: str) -> dict:
        for x in self.history.load():
            if x['run_id']==run_id: return x
        raise KeyError(run_id)

    def delete_run(self, run_id: str):
        rows=self.history.load(); new=[x for x in rows if x['run_id']!=run_id]
        if len(new)==len(rows): raise KeyError(run_id)
        self.history.save(new)

    def _append_history(self, rec): rows=self.history.load(); rows.append(rec); self.history.save(rows)
    def _update_run(self, run_id, verbose_append=None, **changes):
        rows=self.history.load()
        for r in rows:
            if r['run_id']==run_id:
                r.update(changes)
                if verbose_append is not None:
                    if isinstance(verbose_append, list): r['verbose'].extend(map(str, verbose_append))
                    else: r['verbose'].append(str(verbose_append))
                break
        self.history.save(rows)

    def _scheduler_loop(self):
        while not self._stop.wait(15):
            now=datetime.now(); minute=now.strftime('%Y%m%d%H%M')
            for item in self.registry.list_deployments():
                cid=item['crew_id']; cfg=self.get_settings(cid).get('schedule',{})
                if not cfg.get('enabled') or not cfg.get('cron'): continue
                key=f'{cid}:{cfg["cron"]}'
                if self._last_minute.get(key)==minute: continue
                if cron_matches(cfg['cron'], now):
                    self._last_minute[key]=minute
                    # latest listed version for this crew
                    versions=self.registry.list_versions(cid)
                    if versions: self.kickoff(cid, versions[-1], trigger='schedule')


def validate_cron(expr: str):
    parts=expr.split()
    if len(parts)!=5: raise ValueError('cron must have 5 fields: minute hour day month weekday')
    for token,lo,hi in zip(parts,(0,0,1,1,0),(59,23,31,12,6)): _parse_field(token,lo,hi)


def _parse_field(token: str, lo: int, hi: int) -> set[int]:
    values=set()
    for part in token.split(','):
        step=1
        if '/' in part: part, st=part.split('/',1); step=int(st)
        if part=='*': start,end=lo,hi
        elif '-' in part: start,end=map(int,part.split('-',1))
        else: start=end=int(part)
        if start<lo or end>hi or start>end or step<1: raise ValueError(f'invalid cron field: {token}')
        values.update(range(start,end+1,step))
    return values


def cron_matches(expr: str, dt: datetime) -> bool:
    validate_cron(expr); p=expr.split(); vals=(dt.minute,dt.hour,dt.day,dt.month,(dt.weekday()+1)%7)
    ranges=((0,59),(0,23),(1,31),(1,12),(0,6))
    return all(v in _parse_field(t,*r) for v,t,r in zip(vals,p,ranges))
