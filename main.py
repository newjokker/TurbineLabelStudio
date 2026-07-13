# -*- coding: utf-8 -*-
"""TurbineLabelStudio FastAPI 服务入口。"""
import os
import io
import re
import uuid
import zipfile
from datetime import datetime
from datetime import timedelta
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import FileResponse, RedirectResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import func as sql_func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from dao import annotation, annotation_lock, buc_dataset, dataset, label, operation_log, user_account, wav_buc  # noqa: F401
from dao.annotation import Annotation
from dao.buc_dataset import BucDataset
from dao.annotation_lock import AnnotationLock
from dao.database import Session, beijing_now, create_all_tables, engine, json_text, json_value
from dao.dataset import Dataset
from dao.label import Label, ensure_label_color
from dao.operation_log import OperationLog
from dao.user_account import UserAccount
from dao.wav_buc import WAV_POSITION_ORDER, WavBuc, generate_next_buc
from scripts.cache_manager import get_img_path_by_buc_func, get_wav_path_by_md5
from scripts.format_transform import build_annotation_xml


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(BASE_DIR, "app")
STATIC_DIR = os.path.join(APP_DIR, "static")
DEFAULT_FUNC_NAMES = ["wh_jzp_before_20260708"]
LOCK_TTL = timedelta(minutes=5)
MD5_RE = re.compile(r"^[0-9a-f]{32}$")

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


class AnnotationPayload(BaseModel):
    buc: str
    func: str
    x1: float
    y1: float
    x2: float
    y2: float
    label_id: int
    difficult: bool = False
    update_reason: Optional[str] = None
    extra_info: Optional[Dict[str, Any]] = None


class AnnotationCommentPayload(BaseModel):
    comment: str = ""


class AnnotationLockPayload(BaseModel):
    buc: str
    func: str


class DatasetPayload(BaseModel):
    name: str
    des: Optional[str] = None
    extra_info: Optional[Dict[str, Any]] = None
    bucs: List[str] = Field(default_factory=list)


class DatasetBucsPayload(BaseModel):
    bucs: List[str] = Field(default_factory=list)


class WavBucPayload(BaseModel):
    wave_position_id: Dict[str, str]


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


def _get_actor(session, x_user_id, x_session_id):
    if not x_user_id:
        raise HTTPException(status_code=401, detail="未登录")
    if not x_session_id:
        raise HTTPException(status_code=401, detail="登录会话缺失，请重新登录")
    actor = session.query(UserAccount).filter_by(id=int(x_user_id)).first()
    if not actor:
        raise HTTPException(status_code=401, detail="用户不存在")
    if actor.end_time and actor.end_time <= beijing_now():
        raise HTTPException(status_code=403, detail="账号已停用")
    if actor.active_session_id != x_session_id:
        raise HTTPException(status_code=401, detail="账号已在其他设备登录，请重新登录")
    return actor


def _require(actor, permission):
    rules = ROLE_PERMISSIONS.get(actor.role, ROLE_PERMISSIONS["观察者"])
    if not rules.get(permission):
        raise HTTPException(status_code=403, detail="当前角色没有权限")


def _lock_expired(lock):
    return not lock.locked_at or lock.locked_at <= beijing_now() - LOCK_TTL


def _lock_owner_name(session, lock):
    owner = session.query(UserAccount).filter_by(id=lock.locked_by).first()
    return owner.alias or owner.name if owner else f"用户 {lock.locked_by}"


def _require_annotation_lock(session, actor, session_id, buc, func_name):
    lock = session.query(AnnotationLock).filter_by(buc=buc, func=func_name).first()
    if not lock or _lock_expired(lock):
        raise HTTPException(status_code=423, detail="当前图片未锁定或锁已过期，请重新进入编辑模式")
    if lock.locked_by != actor.id or lock.locked_session_id != session_id:
        raise HTTPException(status_code=423, detail=f"当前图片已被 {_lock_owner_name(session, lock)} 锁定，无法编辑")
    lock.locked_at = beijing_now()
    return lock


def _release_session_locks(session, actor, session_id, keep=None):
    locks = (
        session.query(AnnotationLock)
        .filter(
            AnnotationLock.locked_by == actor.id,
            AnnotationLock.locked_session_id == session_id,
        )
        .all()
    )
    for lock in locks:
        if keep and lock.buc == keep[0] and lock.func == keep[1]:
            continue
        session.delete(lock)


def _acquire_annotation_lock(session, actor, session_id, buc, func_name):
    if not session.query(WavBuc.buc).filter_by(buc=buc).first():
        raise HTTPException(status_code=400, detail="BUC 不存在")
    _release_session_locks(session, actor, session_id, keep=(buc, func_name))
    lock = session.query(AnnotationLock).filter_by(buc=buc, func=func_name).first()
    now = beijing_now()
    if lock:
        if (
            not _lock_expired(lock)
            and (lock.locked_by != actor.id or lock.locked_session_id != session_id)
        ):
            raise HTTPException(status_code=423, detail=f"当前图片已被 {_lock_owner_name(session, lock)} 锁定，无法编辑")
        lock.locked_by = actor.id
        lock.locked_session_id = session_id
        lock.locked_at = now
    else:
        lock = AnnotationLock(
            buc=buc,
            func=func_name,
            locked_by=actor.id,
            locked_session_id=session_id,
            locked_at=now,
        )
        session.add(lock)
    session.flush()
    return lock


@app.on_event("startup")
def startup():
    create_all_tables()
    ensure_runtime_schema()


def ensure_runtime_schema():
    """为已有 SQLite 数据库补充新版本需要的列。"""
    with engine.begin() as conn:
        columns = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(user_account)").fetchall()}
        if "active_session_id" not in columns:
            conn.exec_driver_sql("ALTER TABLE user_account ADD COLUMN active_session_id VARCHAR(64)")
        if "active_session_time" not in columns:
            conn.exec_driver_sql("ALTER TABLE user_account ADD COLUMN active_session_time DATETIME")


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


@app.get("/accounts.html")
def accounts_page():
    return _page("accounts.html")


@app.get("/datasets.html")
def datasets_page():
    return _page("datasets.html")


@app.get("/annotation_view.html")
def annotation_view_page():
    return _page("annotation_view.html")


@app.get("/annotation_changes.html")
def annotation_changes_page():
    return _page("annotation_changes.html")


@app.get("/api_docs.html")
def api_docs_page():
    return _page("api_docs.html")


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
        session_id = uuid.uuid4().hex
        record.active_session_id = session_id
        record.active_session_time = beijing_now()
        session.query(AnnotationLock).filter_by(locked_by=record.id).delete(synchronize_session=False)
        _log(session, record.id, "login", "user_account", {"name": record.name})
        session.commit()
        return {
            "user": _safe_user(record),
            "session_id": session_id,
            "permissions": ROLE_PERMISSIONS.get(record.role, ROLE_PERMISSIONS["观察者"]),
            "server_time": _format_dt(beijing_now()),
        }
    finally:
        session.close()


@app.get("/api/permissions")
def permissions(
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id"),
):
    session = Session()
    try:
        actor = _get_actor(session, x_user_id, x_session_id)
        return {
            "user": _safe_user(actor),
            "permissions": ROLE_PERMISSIONS.get(actor.role, ROLE_PERMISSIONS["观察者"]),
            "server_time": _format_dt(beijing_now()),
        }
    finally:
        session.close()


@app.get("/api/labels")
def list_labels(
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id"),
):
    session = Session()
    try:
        _get_actor(session, x_user_id, x_session_id)
        rows = session.query(Label).order_by(Label.id).all()
        return {"items": [_label_dict(row) for row in rows]}
    finally:
        session.close()


@app.post("/api/labels")
def create_label(
    payload: LabelPayload,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id"),
):
    session = Session()
    try:
        actor = _get_actor(session, x_user_id, x_session_id)
        _require(actor, "label_write")
        record = Label(
            label=payload.label,
            des=payload.des,
            update_by=actor.name,
            extra_info=json_text(ensure_label_color(payload.extra_info)),
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
def update_label(
    label_id: int,
    payload: LabelPayload,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id"),
):
    session = Session()
    try:
        actor = _get_actor(session, x_user_id, x_session_id)
        _require(actor, "label_write")
        record = session.query(Label).filter_by(id=label_id).first()
        if not record:
            raise HTTPException(status_code=404, detail="标签不存在")
        before = record.to_dict()
        record.label = payload.label
        record.des = payload.des
        record.update_by = actor.name
        record.extra_info = json_text(ensure_label_color(payload.extra_info))
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
def delete_label(
    label_id: int,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id"),
):
    session = Session()
    try:
        actor = _get_actor(session, x_user_id, x_session_id)
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


@app.get("/api/annotation-view/options")
def annotation_view_options(
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id"),
):
    session = Session()
    try:
        _get_actor(session, x_user_id, x_session_id)
        rows = (
            session.query(Annotation.buc, Annotation.func, sql_func.count(Annotation.id).label("count"))
            .group_by(Annotation.buc, Annotation.func)
            .order_by(Annotation.buc, Annotation.func)
            .all()
        )
        counts_by_key = {(row.buc, row.func): row.count for row in rows}
        label_rows = (
            session.query(Annotation.buc, Annotation.func, Label.id, Label.label)
            .join(Label, Label.id == Annotation.label_id)
            .group_by(Annotation.buc, Annotation.func, Label.id, Label.label)
            .order_by(Annotation.buc, Annotation.func, Label.id)
            .all()
        )
        labels_by_key = {}
        for row in label_rows:
            labels_by_key.setdefault((row.buc, row.func), []).append(
                {
                    "id": row.id,
                    "label": row.label,
                }
            )
        dataset_rows = session.query(Dataset).order_by(Dataset.id).all()
        dataset_map_rows = (
            session.query(BucDataset.buc, Dataset.id, Dataset.name)
            .join(Dataset, Dataset.id == BucDataset.dataset_id)
            .order_by(BucDataset.buc, Dataset.id)
            .all()
        )
        datasets_by_buc = {}
        for row in dataset_map_rows:
            datasets_by_buc.setdefault(row.buc, []).append(
                {
                    "id": row.id,
                    "name": row.name,
                }
            )
        buc_rows = session.query(WavBuc.buc).distinct().order_by(WavBuc.buc).all()
        option_keys = {(row.buc, func_name) for row in buc_rows for func_name in DEFAULT_FUNC_NAMES}
        option_keys.update(counts_by_key.keys())
        return {
            "datasets": [row.to_dict() for row in dataset_rows],
            "items": [
                {
                    "buc": buc,
                    "func": func_name,
                    "annotation_count": counts_by_key.get((buc, func_name), 0),
                    "labels": labels_by_key.get((buc, func_name), []),
                    "datasets": datasets_by_buc.get(buc, []),
                }
                for buc, func_name in sorted(option_keys)
            ]
        }
    finally:
        session.close()


def _annotation_change_snapshots(log_record):
    """把新旧格式的 annotation 日志统一为 before/after 两个快照。"""
    change = json_value(log_record.change_info)
    if not isinstance(change, dict):
        change = {}
    if "before" in change or "after" in change:
        before = change.get("before") if isinstance(change.get("before"), dict) else None
        after = change.get("after") if isinstance(change.get("after"), dict) else None
        return before, after
    if log_record.act == "create":
        return None, change
    if log_record.act == "delete":
        return change, None
    return change, change


@app.get("/api/annotation-changes")
def annotation_changes(
    user_id: Optional[int] = None,
    label_id: Optional[int] = None,
    buc: Optional[str] = None,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id"),
):
    """查询标注框审计日志，并按操作人员、标签和 BUC 筛选。"""
    session = Session()
    try:
        _get_actor(session, x_user_id, x_session_id)
        rows = (
            session.query(OperationLog, UserAccount)
            .join(UserAccount, UserAccount.id == OperationLog.role_id)
            .filter(OperationLog.table_name == "annotation")
            .order_by(OperationLog.id.desc())
            .all()
        )
        label_map = {record.id: record.label for record in session.query(Label).all()}
        filter_users = {}
        filter_label_ids = set()
        filter_bucs = set()
        items = []

        for log_record, user_record in rows:
            before, after = _annotation_change_snapshots(log_record)
            snapshots = [item for item in (before, after) if isinstance(item, dict)]
            snapshot_user_ids = {log_record.role_id}
            snapshot_label_ids = {item.get("label_id") for item in snapshots if item.get("label_id") is not None}
            snapshot_bucs = {item.get("buc") for item in snapshots if item.get("buc")}

            filter_users[log_record.role_id] = {
                "id": user_record.id,
                "name": user_record.name,
                "alias": user_record.alias,
            }
            filter_label_ids.update(snapshot_label_ids)
            filter_bucs.update(snapshot_bucs)

            if user_id is not None and user_id not in snapshot_user_ids:
                continue
            if label_id is not None and label_id not in snapshot_label_ids:
                continue
            if buc and buc not in snapshot_bucs:
                continue

            effective = after or before or {}
            effective_label_id = effective.get("label_id")
            items.append(
                {
                    "id": log_record.id,
                    "act": log_record.act,
                    "update_time": _format_dt(log_record.update_time),
                    "user": filter_users[log_record.role_id],
                    "annotation_id": effective.get("id"),
                    "buc": effective.get("buc"),
                    "func": effective.get("func"),
                    "label_id": effective_label_id,
                    "label": label_map.get(effective_label_id),
                    "box": {
                        "x1": effective.get("x1"),
                        "y1": effective.get("y1"),
                        "x2": effective.get("x2"),
                        "y2": effective.get("y2"),
                    },
                    "before": before,
                    "after": after,
                }
            )

        return {
            "filters": {
                "users": sorted(filter_users.values(), key=lambda item: item["id"]),
                "labels": [
                    {"id": item_id, "label": label_map.get(item_id) or f"标签 #{item_id}"}
                    for item_id in sorted(filter_label_ids)
                ],
                "bucs": sorted(filter_bucs),
            },
            "count": len(items),
            "items": items,
        }
    finally:
        session.close()


@app.get("/api/annotation-view/data")
def annotation_view_data(
    buc: str,
    func_name: str = Query(..., alias="func"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id"),
):
    session = Session()
    try:
        _get_actor(session, x_user_id, x_session_id)
        rows = (
            session.query(Annotation, Label, UserAccount)
            .outerjoin(Label, Label.id == Annotation.label_id)
            .outerjoin(UserAccount, UserAccount.id == Annotation.update_id)
            .filter(Annotation.buc == buc, Annotation.func == func_name)
            .order_by(Annotation.id)
            .all()
        )
        annotations = []
        for record, label_record, user_record in rows:
            label_extra = json_value(label_record.extra_info) if label_record else {}
            update_alias = user_record.alias if user_record else None
            update_name = user_record.name if user_record else None
            annotations.append(
                {
                    **record.to_dict(),
                    "label": label_record.label if label_record else None,
                    "label_des": label_record.des if label_record else None,
                    "label_color": label_extra.get("color", "#0f5f8a") if isinstance(label_extra, dict) else "#0f5f8a",
                    "update_by": update_alias or update_name,
                    "update_alias": update_alias,
                    "update_name": update_name,
                }
            )

        wav_rows = session.query(WavBuc.wave_md5, WavBuc.position_id).filter_by(buc=buc).all()
        position_md5 = {row.position_id: row.wave_md5 for row in wav_rows}
        channels = [
            {
                "position_id": position_id,
                "md5": position_md5.get(position_id),
                "audio_url": f"/api/annotation-view/wav/{position_md5[position_id]}" if position_id in position_md5 else None,
            }
            for position_id in WAV_POSITION_ORDER
        ]

        return {
            "buc": buc,
            "func": func_name,
            "image_url": f"/api/annotation-view/image?buc={buc}&func={func_name}",
            "annotations": annotations,
            "channels": channels,
        }
    finally:
        session.close()


@app.get("/api/annotation-view/image")
def annotation_view_image(buc: str, func_name: str = Query(..., alias="func")):
    image_path = get_img_path_by_buc_func(buc, func_name)
    if not image_path or not os.path.isfile(image_path):
        raise HTTPException(status_code=404, detail="图片缓存生成失败")
    return FileResponse(image_path, media_type="image/jpeg")


@app.get("/api/annotation-view/wav/{md5}")
def annotation_view_wav(md5: str):
    wav_path = get_wav_path_by_md5(md5)
    if not wav_path or not os.path.isfile(wav_path):
        raise HTTPException(status_code=404, detail="WAV 缓存获取失败")
    return FileResponse(wav_path, media_type="audio/wav")


@app.post("/api/annotation-lock/lock")
def lock_annotation_image(
    payload: AnnotationLockPayload,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id"),
):
    session = Session()
    try:
        actor = _get_actor(session, x_user_id, x_session_id)
        _require(actor, "label_write")
        lock = _acquire_annotation_lock(session, actor, x_session_id, payload.buc, payload.func)
        _log(session, actor.id, "update", "annotation_lock", lock.to_dict())
        session.commit()
        session.refresh(lock)
        return {"item": lock.to_dict(), "expires_in": int(LOCK_TTL.total_seconds())}
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=423, detail="当前图片刚刚被其他用户锁定，无法编辑") from exc
    except SQLAlchemyError as exc:
        session.rollback()
        raise HTTPException(status_code=500, detail="锁定图片失败") from exc
    finally:
        session.close()


@app.post("/api/annotation-lock/heartbeat")
def heartbeat_annotation_lock(
    payload: AnnotationLockPayload,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id"),
):
    session = Session()
    try:
        actor = _get_actor(session, x_user_id, x_session_id)
        _require(actor, "label_write")
        lock = _require_annotation_lock(session, actor, x_session_id, payload.buc, payload.func)
        session.commit()
        session.refresh(lock)
        return {"item": lock.to_dict(), "expires_in": int(LOCK_TTL.total_seconds())}
    finally:
        session.close()


@app.post("/api/annotation-lock/unlock")
def unlock_annotation_image(
    payload: AnnotationLockPayload,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id"),
):
    session = Session()
    try:
        actor = _get_actor(session, x_user_id, x_session_id)
        lock = session.query(AnnotationLock).filter_by(buc=payload.buc, func=payload.func).first()
        if lock and lock.locked_by == actor.id and lock.locked_session_id == x_session_id:
            before = lock.to_dict()
            session.delete(lock)
            _log(session, actor.id, "update", "annotation_lock", {"unlock": before})
        session.commit()
        return {"ok": True}
    finally:
        session.close()


@app.post("/api/annotations")
def create_annotation(
    payload: AnnotationPayload,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id"),
):
    session = Session()
    try:
        actor = _get_actor(session, x_user_id, x_session_id)
        _require(actor, "label_write")
        _require_annotation_lock(session, actor, x_session_id, payload.buc, payload.func)
        if not session.query(WavBuc.buc).filter_by(buc=payload.buc).first():
            raise HTTPException(status_code=400, detail="BUC 不存在")
        if not session.query(Label.id).filter_by(id=payload.label_id).first():
            raise HTTPException(status_code=400, detail="标签不存在")
        record = Annotation(
            buc=payload.buc,
            func=payload.func,
            x1=payload.x1,
            y1=payload.y1,
            x2=payload.x2,
            y2=payload.y2,
            label_id=payload.label_id,
            difficult=payload.difficult,
            update_id=actor.id,
            update_reason=payload.update_reason,
            extra_info=json_text(payload.extra_info),
        )
        session.add(record)
        session.flush()
        _log(session, actor.id, "create", "annotation", record.to_dict())
        session.commit()
        session.refresh(record)
        return {"item": record.to_dict()}
    except SQLAlchemyError as exc:
        session.rollback()
        raise HTTPException(status_code=500, detail="创建标注失败") from exc
    finally:
        session.close()


@app.delete("/api/annotations/{annotation_id}")
def delete_annotation(
    annotation_id: int,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id"),
):
    session = Session()
    try:
        actor = _get_actor(session, x_user_id, x_session_id)
        _require(actor, "label_write")
        record = session.query(Annotation).filter_by(id=annotation_id).first()
        if not record:
            raise HTTPException(status_code=404, detail="标注不存在")
        _require_annotation_lock(session, actor, x_session_id, record.buc, record.func)
        before = record.to_dict()
        session.delete(record)
        _log(session, actor.id, "delete", "annotation", before)
        session.commit()
        return {"ok": True}
    except SQLAlchemyError as exc:
        session.rollback()
        raise HTTPException(status_code=500, detail="删除标注失败") from exc
    finally:
        session.close()


@app.put("/api/annotations/{annotation_id}/comment")
def update_annotation_comment(
    annotation_id: int,
    payload: AnnotationCommentPayload,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id"),
):
    session = Session()
    try:
        actor = _get_actor(session, x_user_id, x_session_id)
        _require(actor, "label_write")
        record = session.query(Annotation).filter_by(id=annotation_id).first()
        if not record:
            raise HTTPException(status_code=404, detail="标注不存在")
        _require_annotation_lock(session, actor, x_session_id, record.buc, record.func)
        before = record.to_dict()
        extra_info = json_value(record.extra_info)
        if not isinstance(extra_info, dict):
            extra_info = {}
        comments = extra_info.get("comments")
        if not isinstance(comments, list):
            comments = []
        comments = [item for item in comments if isinstance(item, dict) and item.get("text")]

        # 兼容旧版单条评论，读取后统一写入多人评论列表。
        legacy_comment = extra_info.pop("comment", None)
        if isinstance(legacy_comment, str) and legacy_comment.strip():
            comments.append({"text": legacy_comment.strip(), "update_by": "未知用户"})
        elif isinstance(legacy_comment, dict) and legacy_comment.get("text"):
            legacy_id = legacy_comment.get("update_id")
            if not any(str(item.get("update_id")) == str(legacy_id) for item in comments):
                comments.append(legacy_comment)

        comment_text = (payload.comment or "").strip()
        own_index = next(
            (index for index, item in enumerate(comments) if str(item.get("update_id")) == str(actor.id)),
            None,
        )
        if comment_text:
            own_comment = {
                "text": comment_text,
                "update_id": actor.id,
                "update_by": actor.alias or actor.name,
                "update_time": _format_dt(beijing_now()),
            }
            if own_index is None:
                comments.append(own_comment)
            else:
                comments[own_index] = own_comment
        elif own_index is not None:
            comments.pop(own_index)

        if comments:
            extra_info["comments"] = comments
        else:
            extra_info.pop("comments", None)
        record.extra_info = json_text(extra_info)
        record.update_id = actor.id
        record.update_time = beijing_now()
        session.flush()
        after = record.to_dict()
        _log(session, actor.id, "update", "annotation_comment", {"before": before, "after": after})
        session.commit()
        session.refresh(record)
        return {"item": record.to_dict()}
    except SQLAlchemyError as exc:
        session.rollback()
        raise HTTPException(status_code=500, detail="更新评论失败") from exc
    finally:
        session.close()


def _dataset_dict(session, record):
    buc_rows = (
        session.query(BucDataset.buc)
        .filter_by(dataset_id=record.id)
        .order_by(BucDataset.buc)
        .all()
    )
    return {
        **record.to_dict(),
        "bucs": [row.buc for row in buc_rows],
    }


def _validate_dataset_bucs(session, bucs):
    normalized = []
    seen = set()
    for buc in bucs or []:
        value = str(buc).strip()
        if not value or value in seen:
            continue
        seen.add(value)
        normalized.append(value)
    if not normalized:
        return []

    existing = {
        row.buc
        for row in session.query(WavBuc.buc).filter(WavBuc.buc.in_(normalized)).distinct().all()
    }
    missing = [buc for buc in normalized if buc not in existing]
    if missing:
        raise HTTPException(status_code=400, detail=f"BUC 不存在: {', '.join(missing)}")
    return normalized


def _replace_dataset_bucs(session, dataset_id, bucs):
    session.query(BucDataset).filter_by(dataset_id=dataset_id).delete(synchronize_session=False)
    session.add_all([BucDataset(dataset_id=dataset_id, buc=buc) for buc in bucs])


def _get_buc_wav_rows(session, buc):
    rows = session.query(WavBuc).filter_by(buc=buc).order_by(WavBuc.position_id).all()
    if not rows:
        raise HTTPException(status_code=404, detail="BUC 不存在")
    return rows


def _get_public_annotation_items(session, buc, func_name):
    rows = (
        session.query(Annotation, Label)
        .outerjoin(Label, Label.id == Annotation.label_id)
        .filter(Annotation.buc == buc, Annotation.func == func_name)
        .order_by(Annotation.id)
        .all()
    )
    items = []
    for record, label_record in rows:
        label_extra = json_value(label_record.extra_info) if label_record else {}
        items.append(
            {
                **record.to_dict(),
                "label": label_record.label if label_record else None,
                "label_des": label_record.des if label_record else None,
                "label_extra_info": label_extra,
            }
        )
    return items


def _normalize_wave_position_id(wave_position_id):
    if not wave_position_id:
        raise HTTPException(status_code=400, detail="wave_position_id 不能为空")

    normalized = {}
    seen_positions = set()
    for raw_md5, raw_position_id in wave_position_id.items():
        md5 = str(raw_md5).strip().lower()
        position_id = str(raw_position_id).strip()
        if not MD5_RE.match(md5):
            raise HTTPException(status_code=400, detail=f"wave_md5 格式不正确: {raw_md5}")
        if position_id not in WAV_POSITION_ORDER:
            raise HTTPException(status_code=400, detail=f"position_id 不合法: {position_id}")
        if position_id in seen_positions:
            raise HTTPException(status_code=400, detail=f"position_id 重复: {position_id}")
        normalized[md5] = position_id
        seen_positions.add(position_id)

    missing = [position_id for position_id in WAV_POSITION_ORDER if position_id not in seen_positions]
    if missing:
        raise HTTPException(status_code=400, detail=f"缺少 position_id: {', '.join(missing)}")

    return normalized


def _normalize_md5_or_400(md5):
    value = str(md5).strip().lower()
    if not MD5_RE.match(value):
        raise HTTPException(status_code=400, detail="md5 格式不正确")
    return value


def _file_response(path, media_type, filename, not_found_detail):
    if not path or not os.path.isfile(path):
        raise HTTPException(status_code=404, detail=not_found_detail)
    return FileResponse(path, media_type=media_type, filename=filename)


@app.post("/api/public/datasets")
def public_create_dataset(
    payload: DatasetPayload,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id"),
):
    session = Session()
    try:
        actor = _get_actor(session, x_user_id, x_session_id)
        _require(actor, "account_manage")
        name = payload.name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="数据集名称不能为空")
        record = Dataset(name=name, des=payload.des, extra_info=json_text(payload.extra_info))
        session.add(record)
        session.flush()
        item = _dataset_dict(session, record)
        _log(session, actor.id, "create", "dataset", item)
        session.commit()
        session.refresh(record)
        return {"item": _dataset_dict(session, record)}
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail="数据集名称已存在") from exc
    finally:
        session.close()


@app.put("/api/public/datasets/{dataset_id}/bucs")
def public_replace_dataset_bucs(
    dataset_id: int,
    payload: DatasetBucsPayload,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id"),
):
    session = Session()
    try:
        actor = _get_actor(session, x_user_id, x_session_id)
        _require(actor, "account_manage")
        record = session.query(Dataset).filter_by(id=dataset_id).first()
        if not record:
            raise HTTPException(status_code=404, detail="数据集不存在")
        before = _dataset_dict(session, record)
        bucs = _validate_dataset_bucs(session, payload.bucs)
        _replace_dataset_bucs(session, dataset_id, bucs)
        session.flush()
        after = _dataset_dict(session, record)
        _log(session, actor.id, "update", "buc_dataset", {"before": before, "after": after})
        session.commit()
        return {"item": after}
    finally:
        session.close()


@app.post("/api/public/bucs")
def public_create_buc(
    payload: WavBucPayload,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id"),
):
    wave_position_id = _normalize_wave_position_id(payload.wave_position_id)
    session = Session()
    try:
        actor = _get_actor(session, x_user_id, x_session_id)
        _require(actor, "account_manage")
        existing = (
            session.query(WavBuc)
            .filter(WavBuc.wave_md5.in_(list(wave_position_id.keys())))
            .order_by(WavBuc.position_id)
            .all()
        )
        if existing:
            existed = [row.to_dict() for row in existing]
            raise HTTPException(status_code=409, detail={"message": "部分 wave_md5 已关联 BUC", "items": existed})

        buc = generate_next_buc(session)
        records = [
            WavBuc(wave_md5=md5, position_id=position_id, buc=buc)
            for md5, position_id in sorted(wave_position_id.items(), key=lambda item: WAV_POSITION_ORDER.index(item[1]))
        ]
        session.add_all(records)
        session.flush()
        items = [record.to_dict() for record in records]
        result = {"buc": buc, "items": items}
        _log(session, actor.id, "create", "wav_buc", result)
        session.commit()
        return result
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail="创建 BUC 失败，wave_md5 或 BUC 数据冲突") from exc
    except SQLAlchemyError as exc:
        session.rollback()
        raise HTTPException(status_code=500, detail="创建 BUC 失败") from exc
    finally:
        session.close()


@app.get("/api/public/wav-md5/{md5}/buc")
def public_get_buc_by_md5(
    md5: str,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id"),
):
    md5 = _normalize_md5_or_400(md5)
    session = Session()
    try:
        _get_actor(session, x_user_id, x_session_id)
        record = session.query(WavBuc).filter_by(wave_md5=md5).first()
        return {
            "wave_md5": md5,
            "exists": bool(record),
            "buc": record.buc if record else None,
            "item": record.to_dict() if record else None,
        }
    finally:
        session.close()


@app.get("/api/public/bucs/{buc}/wav-md5s")
def public_get_buc_wav_md5s(
    buc: str,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id"),
):
    session = Session()
    try:
        _get_actor(session, x_user_id, x_session_id)
        rows = _get_buc_wav_rows(session, buc)
        position_order = {position_id: idx for idx, position_id in enumerate(WAV_POSITION_ORDER)}
        items = sorted(rows, key=lambda row: position_order.get(row.position_id, len(WAV_POSITION_ORDER)))
        return {
            "buc": buc,
            "count": len(items),
            "items": [row.to_dict() for row in items],
        }
    finally:
        session.close()


@app.get("/api/public/bucs/{buc}/image")
def public_download_buc_image(
    buc: str,
    func_name: str = Query(DEFAULT_FUNC_NAMES[0], alias="func"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id"),
):
    session = Session()
    try:
        _get_actor(session, x_user_id, x_session_id)
        _get_buc_wav_rows(session, buc)
    finally:
        session.close()
    image_path = get_img_path_by_buc_func(buc, func_name)
    return _file_response(image_path, "image/jpeg", f"{buc}_{func_name}.jpg", "图片缓存生成失败")


@app.get("/api/public/bucs/{buc}/mel")
def public_download_buc_mel(
    buc: str,
    func_name: str = Query(DEFAULT_FUNC_NAMES[0], alias="func"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id"),
):
    session = Session()
    try:
        _get_actor(session, x_user_id, x_session_id)
        _get_buc_wav_rows(session, buc)
    finally:
        session.close()
    mel_path = get_img_path_by_buc_func(buc, func_name)
    return _file_response(mel_path, "image/jpeg", f"{buc}_{func_name}_mel.jpg", "Mel 图缓存生成失败")


@app.get("/api/public/bucs/{buc}/audio/{position_id}")
def public_download_buc_audio(
    buc: str,
    position_id: str,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id"),
):
    session = Session()
    try:
        _get_actor(session, x_user_id, x_session_id)
        row = session.query(WavBuc).filter_by(buc=buc, position_id=position_id).first()
        if not row:
            raise HTTPException(status_code=404, detail="BUC 对应通道音频不存在")
        md5 = row.wave_md5
    finally:
        session.close()
    wav_path = get_wav_path_by_md5(md5)
    return _file_response(wav_path, "audio/wav", f"{buc}_{position_id}_{md5}.wav", "WAV 缓存获取失败")


@app.get("/api/public/bucs/{buc}/audio")
def public_download_buc_audio_zip(
    buc: str,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id"),
):
    session = Session()
    try:
        _get_actor(session, x_user_id, x_session_id)
        rows = _get_buc_wav_rows(session, buc)
        wav_items = [(row.position_id, row.wave_md5) for row in rows]
    finally:
        session.close()

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for position_id, md5 in wav_items:
            wav_path = get_wav_path_by_md5(md5)
            if not wav_path or not os.path.isfile(wav_path):
                raise HTTPException(status_code=404, detail=f"WAV 缓存获取失败: {position_id}")
            zf.write(wav_path, arcname=f"{buc}_{position_id}_{md5}.wav")
    buffer.seek(0)
    headers = {"Content-Disposition": f'attachment; filename="{buc}_audio.zip"'}
    return StreamingResponse(buffer, media_type="application/zip", headers=headers)


@app.get("/api/public/bucs/{buc}/annotations")
def public_get_buc_annotations(
    buc: str,
    func_name: str = Query(DEFAULT_FUNC_NAMES[0], alias="func"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id"),
):
    session = Session()
    try:
        _get_actor(session, x_user_id, x_session_id)
        wav_rows = _get_buc_wav_rows(session, buc)
        annotations = _get_public_annotation_items(session, buc, func_name)
        return {
            "buc": buc,
            "func": func_name,
            "buc_audio": [row.to_dict() for row in wav_rows],
            "annotation_count": len(annotations),
            "annotations": annotations,
        }
    finally:
        session.close()


@app.get("/api/public/bucs/{buc}/annotations/xml")
def public_download_buc_annotations_xml(
    buc: str,
    func_name: str = Query(DEFAULT_FUNC_NAMES[0], alias="func"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id"),
):
    session = Session()
    try:
        _get_actor(session, x_user_id, x_session_id)
        _get_buc_wav_rows(session, buc)
        annotations = _get_public_annotation_items(session, buc, func_name)
    finally:
        session.close()

    image_path = get_img_path_by_buc_func(buc, func_name)
    if not image_path or not os.path.isfile(image_path):
        raise HTTPException(status_code=404, detail="图片缓存生成失败，无法生成 XML")

    xml_text = build_annotation_xml(buc, func_name, image_path, annotations)
    filename = f"{buc}_{func_name}.xml"
    return Response(
        content=xml_text,
        media_type="application/xml; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/datasets")
def list_datasets(
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id"),
):
    session = Session()
    try:
        _get_actor(session, x_user_id, x_session_id)
        rows = session.query(Dataset).order_by(Dataset.id).all()
        buc_rows = session.query(WavBuc.buc).distinct().order_by(WavBuc.buc).all()
        return {
            "items": [_dataset_dict(session, row) for row in rows],
            "all_bucs": [row.buc for row in buc_rows],
        }
    finally:
        session.close()


@app.post("/api/datasets")
def create_dataset(
    payload: DatasetPayload,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id"),
):
    session = Session()
    try:
        actor = _get_actor(session, x_user_id, x_session_id)
        _require(actor, "account_manage")
        name = payload.name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="数据集名称不能为空")
        bucs = _validate_dataset_bucs(session, payload.bucs)
        record = Dataset(name=name, des=payload.des, extra_info=json_text(payload.extra_info))
        session.add(record)
        session.flush()
        _replace_dataset_bucs(session, record.id, bucs)
        session.flush()
        item = _dataset_dict(session, record)
        _log(session, actor.id, "create", "dataset", item)
        session.commit()
        session.refresh(record)
        return {"item": _dataset_dict(session, record)}
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail="数据集名称已存在") from exc
    finally:
        session.close()


@app.put("/api/datasets/{dataset_id}")
def update_dataset(
    dataset_id: int,
    payload: DatasetPayload,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id"),
):
    session = Session()
    try:
        actor = _get_actor(session, x_user_id, x_session_id)
        _require(actor, "account_manage")
        record = session.query(Dataset).filter_by(id=dataset_id).first()
        if not record:
            raise HTTPException(status_code=404, detail="数据集不存在")
        name = payload.name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="数据集名称不能为空")
        before = _dataset_dict(session, record)
        bucs = _validate_dataset_bucs(session, payload.bucs)
        record.name = name
        record.des = payload.des
        record.extra_info = json_text(payload.extra_info)
        _replace_dataset_bucs(session, record.id, bucs)
        session.flush()
        after = _dataset_dict(session, record)
        _log(session, actor.id, "update", "dataset", {"before": before, "after": after})
        session.commit()
        session.refresh(record)
        return {"item": _dataset_dict(session, record)}
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail="数据集名称已存在") from exc
    finally:
        session.close()


@app.delete("/api/datasets/{dataset_id}")
def delete_dataset(
    dataset_id: int,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id"),
):
    session = Session()
    try:
        actor = _get_actor(session, x_user_id, x_session_id)
        _require(actor, "account_manage")
        record = session.query(Dataset).filter_by(id=dataset_id).first()
        if not record:
            raise HTTPException(status_code=404, detail="数据集不存在")
        before = _dataset_dict(session, record)
        session.query(BucDataset).filter_by(dataset_id=dataset_id).delete(synchronize_session=False)
        session.delete(record)
        _log(session, actor.id, "delete", "dataset", before)
        session.commit()
        return {"ok": True}
    finally:
        session.close()


@app.get("/api/accounts")
def list_accounts(
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id"),
):
    session = Session()
    try:
        _get_actor(session, x_user_id, x_session_id)
        rows = session.query(UserAccount).order_by(UserAccount.id).all()
        return {"items": [_safe_user(row) for row in rows]}
    finally:
        session.close()


@app.post("/api/accounts")
def create_account(
    payload: AccountPayload,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id"),
):
    session = Session()
    try:
        actor = _get_actor(session, x_user_id, x_session_id)
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
def update_account(
    account_id: int,
    payload: AccountPayload,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id"),
):
    session = Session()
    try:
        actor = _get_actor(session, x_user_id, x_session_id)
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
def disable_account(
    account_id: int,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id"),
):
    session = Session()
    try:
        actor = _get_actor(session, x_user_id, x_session_id)
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

    uvicorn.run("main:app", host="0.0.0.0", port=12502, reload=False)
