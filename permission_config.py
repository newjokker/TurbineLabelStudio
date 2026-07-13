# -*- coding: utf-8 -*-
"""权限目录与角色默认模板。

这里只定义系统支持哪些权限，以及新账号选择角色时使用的默认值。
每个账号最终生效的权限存放在 user_permission 表，可在页面中实时修改。
"""

PERMISSION_DEFINITIONS = {
    "annotation_view": {"group": "标注", "name": "查看标注", "description": "查看标注图片、标注框并播放通道音频"},
    "annotation_edit": {"group": "标注", "name": "编辑标注", "description": "锁定图片、新增或删除标注框、编辑评论"},
    "annotation_export": {"group": "标注", "name": "导出标注", "description": "下载图片、Mel、WAV、ZIP、标注 JSON 和 XML"},
    "audit_view": {"group": "审计", "name": "查看变动记录", "description": "查看并筛选标注框变动记录"},
    "label_view": {"group": "标签", "name": "查看标签", "description": "查看标签名称、描述和颜色"},
    "label_manage": {"group": "标签", "name": "管理标签", "description": "新增、修改和删除标签"},
    "dataset_view": {"group": "数据集", "name": "查看数据集", "description": "查看数据集及其 BUC"},
    "dataset_manage": {"group": "数据集", "name": "管理数据集", "description": "新增、修改、删除数据集并分配 BUC"},
    "buc_view": {"group": "BUC", "name": "查看 BUC 映射", "description": "查询 WAV MD5、点位和 BUC 映射"},
    "buc_manage": {"group": "BUC", "name": "管理 BUC", "description": "将 WAV MD5 入库并创建 BUC"},
    "account_view": {"group": "账号", "name": "查看账号", "description": "查看账号、角色、状态和权限"},
    "account_manage": {"group": "账号", "name": "管理账号", "description": "新增、修改、停用账号并配置个人权限"},
    "backup_manage": {"group": "系统", "name": "管理备份", "description": "主动创建、下载和删除数据库备份"},
}

PERMISSION_DEPENDENCIES = {
    "annotation_edit": ("annotation_view",),
    "annotation_export": ("annotation_view",),
    "label_manage": ("label_view",),
    "dataset_manage": ("dataset_view",),
    "buc_manage": ("buc_view",),
    "account_manage": ("account_view",),
}


def _permissions(*enabled):
    enabled = set(enabled)
    return {key: key in enabled for key in PERMISSION_DEFINITIONS}


ROLE_PERMISSION_PRESETS = {
    "观察者": _permissions(
        "annotation_view", "audit_view", "label_view", "dataset_view", "buc_view",
    ),
    "编辑者": _permissions(
        "annotation_view", "annotation_edit", "annotation_export", "audit_view",
        "label_view", "label_manage", "dataset_view", "buc_view",
    ),
    "管理员": _permissions(*PERMISSION_DEFINITIONS.keys()),
}
