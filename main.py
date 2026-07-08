# -*- coding: utf-8 -*-
"""TurbineLabelStudio FastAPI 服务入口。"""
import os
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from dao import annotation, label, operation_log, uc_md5_map, user_account, wav_buc  # noqa: F401
from dao.database import Session, beijing_now, create_all_tables, json_text
from dao.label import Label
from dao.operation_log import OperationLog
from dao.user_account import UserAccount


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(BASE_DIR, "app")
STATIC_DIR = os.path.join(APP_DIR, "static")

app = FastAPI(title="TurbineLabelStudio")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class LoginPayload(BaseModel):
    name: str
    password: str


class LabelPayload(BaseModel):
    label: str
    des: Optional[str] = None
    update_by: Optional[str] = None
    extra_info: Optional[Dict[str, Any]] = None


class AccountPayload(BaseModel):
    name: str
    password: Optional[str] = None
    alias: Optional[str] = None
    end_time: Optional[str] = None
    role: str


ROLE_PERMISSIONS = {
    "观察者": {
        "label_write": False,
        "label_export": False,
        "account_manage": False,
    },
    "编辑者": {
        "label_write": True,
        "label_export": True,
        "account_manage": False,
    },
    "管理员": {
        "label_write": True,
        "label_export": True,
        "account_manage": True,
    },
}


def _page(name):
    return FileResponse(os.path.join(APP_DIR, name))


def _format_dt(value):
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return value.strftime("%Y-%m-%d %H:%M:%S")


def _parse_dt(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="时间格式应为 YYYY-MM-DD HH:MM:SS") from exc


def _safe_user(record):
    return {
        "id": record.id,
        "name": record.name,
        "alias": record.alias,
        "end_time": _format_dt(record.end_time),
        "role": record.role,
    }


def _label_dict(record):
    return record.to_dict()


def _log(session, user_id, act, table_name, change_info):
    session.add(
        OperationLog(
            role_id=user_id,
            act=act,
            table_name=table_name,
            change_info=json_text(change_info),
        )
    )


def _get_actor(session, x_user_id):
    if not x_user_id:
        raise HTTPException(status_code=401, detail="未登录")
    actor = session.query(UserAccount).filter_by(id=int(x_user_id)).first()
    if not actor:
        raise HTTPException(status_code=401, detail="用户不存在")
    if actor.end_time and actor.end_time <= beijing_now():
        raise HTTPException(status_code=403, detail="账号已停用")
    return actor


def _require(actor, permission):
    rules = ROLE_PERMISSIONS.get(actor.role, ROLE_PERMISSIONS["观察者"])
    if not rules.get(permission):
        raise HTTPException(status_code=403, detail="当前角色没有权限")


@app.on_event("startup")
def startup():
    create_all_tables()


@app.get("/")
def root():
    return RedirectResponse("/index.html")


@app.get("/index.html")
def index_page():
    return _page("index.html")


@app.get("/login.html")
def login_page():
    return _page("login.html")


@app.get("/labels.html")
def labels_page():
    return _page("labels.html")


@app.get("/label_view.html")
def label_view_page():
    return _page("label_view.html")


@app.get("/accounts.html")
def accounts_page():
    return _page("accounts.html")


@app.post("/api/login")
def login(payload: LoginPayload):
    session = Session()
    try:
        record = (
            session.query(UserAccount)
            .filter_by(name=payload.name, password=payload.password)
            .first()
        )
        if not record:
            raise HTTPException(status_code=401, detail="账号或密码不正确")
        if record.end_time and record.end_time <= beijing_now():
            raise HTTPException(status_code=403, detail="账号已停用")
        _log(session, record.id, "login", "user_account", {"name": record.name})
        session.commit()
        return {
            "user": _safe_user(record),
            "permissions": ROLE_PERMISSIONS.get(record.role, ROLE_PERMISSIONS["观察者"]),
            "server_time": _format_dt(beijing_now()),
        }
    finally:
        session.close()


@app.get("/api/permissions")
def permissions(x_user_id: Optional[str] = Header(None, alias="X-User-Id")):
    session = Session()
    try:
        actor = _get_actor(session, x_user_id)
        return {
            "user": _safe_user(actor),
            "permissions": ROLE_PERMISSIONS.get(actor.role, ROLE_PERMISSIONS["观察者"]),
            "server_time": _format_dt(beijing_now()),
        }
    finally:
        session.close()


@app.get("/api/labels")
def list_labels(x_user_id: Optional[str] = Header(None, alias="X-User-Id")):
    session = Session()
    try:
        _get_actor(session, x_user_id)
        rows = session.query(Label).order_by(Label.id).all()
        return {"items": [_label_dict(row) for row in rows]}
    finally:
        session.close()


@app.post("/api/labels")
def create_label(payload: LabelPayload, x_user_id: Optional[str] = Header(None, alias="X-User-Id")):
    session = Session()
    try:
        actor = _get_actor(session, x_user_id)
        _require(actor, "label_write")
        record = Label(
            label=payload.label,
            des=payload.des,
            update_by=actor.name,
            extra_info=json_text(payload.extra_info),
        )
        session.add(record)
        session.flush()
        _log(session, actor.id, "create", "label", record.to_dict())
        session.commit()
        session.refresh(record)
        return {"item": _label_dict(record)}
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail="标签已存在") from exc
    except SQLAlchemyError as exc:
        session.rollback()
        raise HTTPException(status_code=500, detail="创建标签失败") from exc
    finally:
        session.close()


@app.put("/api/labels/{label_id}")
def update_label(label_id: int, payload: LabelPayload, x_user_id: Optional[str] = Header(None, alias="X-User-Id")):
    session = Session()
    try:
        actor = _get_actor(session, x_user_id)
        _require(actor, "label_write")
        record = session.query(Label).filter_by(id=label_id).first()
        if not record:
            raise HTTPException(status_code=404, detail="标签不存在")
        before = record.to_dict()
        record.label = payload.label
        record.des = payload.des
        record.update_by = actor.name
        record.extra_info = json_text(payload.extra_info)
        record.update_time = beijing_now()
        session.flush()
        _log(session, actor.id, "update", "label", {"before": before, "after": record.to_dict()})
        session.commit()
        session.refresh(record)
        return {"item": _label_dict(record)}
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail="标签已存在") from exc
    except SQLAlchemyError as exc:
        session.rollback()
        raise HTTPException(status_code=500, detail="更新标签失败") from exc
    finally:
        session.close()


@app.delete("/api/labels/{label_id}")
def delete_label(label_id: int, x_user_id: Optional[str] = Header(None, alias="X-User-Id")):
    session = Session()
    try:
        actor = _get_actor(session, x_user_id)
        _require(actor, "label_write")
        record = session.query(Label).filter_by(id=label_id).first()
        if not record:
            raise HTTPException(status_code=404, detail="标签不存在")
        before = record.to_dict()
        session.delete(record)
        _log(session, actor.id, "delete", "label", before)
        session.commit()
        return {"ok": True}
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail="标签已被标注引用，不能删除") from exc
    finally:
        session.close()


@app.get("/api/accounts")
def list_accounts(x_user_id: Optional[str] = Header(None, alias="X-User-Id")):
    session = Session()
    try:
        _get_actor(session, x_user_id)
        rows = session.query(UserAccount).order_by(UserAccount.id).all()
        return {"items": [_safe_user(row) for row in rows]}
    finally:
        session.close()


@app.post("/api/accounts")
def create_account(payload: AccountPayload, x_user_id: Optional[str] = Header(None, alias="X-User-Id")):
    session = Session()
    try:
        actor = _get_actor(session, x_user_id)
        _require(actor, "account_manage")
        if payload.role not in ROLE_PERMISSIONS:
            raise HTTPException(status_code=400, detail="角色不合法")
        if not payload.password:
            raise HTTPException(status_code=400, detail="新账号密码不能为空")
        record = UserAccount(
            name=payload.name,
            password=payload.password,
            alias=payload.alias,
            end_time=_parse_dt(payload.end_time),
            role=payload.role,
        )
        session.add(record)
        session.flush()
        _log(session, actor.id, "create", "user_account", _safe_user(record))
        session.commit()
        session.refresh(record)
        return {"item": _safe_user(record)}
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail="账号已存在") from exc
    finally:
        session.close()


@app.put("/api/accounts/{account_id}")
def update_account(account_id: int, payload: AccountPayload, x_user_id: Optional[str] = Header(None, alias="X-User-Id")):
    session = Session()
    try:
        actor = _get_actor(session, x_user_id)
        _require(actor, "account_manage")
        if payload.role not in ROLE_PERMISSIONS:
            raise HTTPException(status_code=400, detail="角色不合法")
        record = session.query(UserAccount).filter_by(id=account_id).first()
        if not record:
            raise HTTPException(status_code=404, detail="账号不存在")
        before = _safe_user(record)
        record.name = payload.name
        if payload.password:
            record.password = payload.password
        record.alias = payload.alias
        record.end_time = _parse_dt(payload.end_time)
        record.role = payload.role
        session.flush()
        _log(session, actor.id, "update", "user_account", {"before": before, "after": _safe_user(record)})
        session.commit()
        session.refresh(record)
        return {"item": _safe_user(record)}
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail="账号已存在") from exc
    finally:
        session.close()


@app.post("/api/accounts/{account_id}/disable")
def disable_account(account_id: int, x_user_id: Optional[str] = Header(None, alias="X-User-Id")):
    session = Session()
    try:
        actor = _get_actor(session, x_user_id)
        _require(actor, "account_manage")
        record = session.query(UserAccount).filter_by(id=account_id).first()
        if not record:
            raise HTTPException(status_code=404, detail="账号不存在")
        before = _safe_user(record)
        record.end_time = beijing_now()
        session.flush()
        _log(session, actor.id, "update", "user_account", {"before": before, "after": _safe_user(record)})
        session.commit()
        session.refresh(record)
        return {"item": _safe_user(record)}
    finally:
        session.close()


if __name__ == "__main__":
    try:
        import uvicorn
    except ImportError as exc:
        raise SystemExit("缺少 uvicorn，请先执行：python3 -m pip install uvicorn") from exc

    uvicorn.run("main:app", host="0.0.0.0", port=8765, reload=False)
