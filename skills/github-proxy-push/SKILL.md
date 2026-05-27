---
name: github-proxy-push
description: Diagnose GitHub network/proxy issues and provide stable push workflow for restricted networks.
metadata:
  surfaces:
    - ide
    - terminal
---

# GitHub Proxy Push

用于在网络受限或代理环境下，定位 `git push` 失败原因，并给出可复现的推送修复步骤。

## 适用场景

- `git push` 超时、TLS 握手失败、连接被重置
- 本地配置了代理，但 Git/GitHub 行为异常
- 需要区分是 DNS、代理、证书、还是认证问题

## 工作流程

1. **收集环境信息**
   - `git remote -v`
   - `git config --get http.proxy`
   - `git config --get https.proxy`
   - `git config --get credential.helper`

2. **快速连通性诊断**
   - 测试 HTTPS 到 GitHub 的连通性与延迟
   - 检查代理变量（如 `HTTP_PROXY`/`HTTPS_PROXY`）是否与 Git 配置冲突

3. **按场景修复**
   - 代理异常时，优先使用一次性命令覆盖：
     - `git -c http.proxy= -c https.proxy= push`
   - 需要走代理时，明确写入可用代理地址再推送
   - 认证失败时，优先修复 token/凭据，再重试推送

4. **输出最终命令**
   - 给出“可直接复制”的最终 push 命令
   - 同时给出回滚命令（撤销临时代理配置）

## 常用命令模板

```powershell
# 临时禁用代理推送（不污染全局配置）
git -c http.proxy= -c https.proxy= push
```

```powershell
# 查看当前 git 代理配置
git config --get http.proxy
git config --get https.proxy
```

```powershell
# 清除全局代理（若确认不需要）
git config --global --unset http.proxy
git config --global --unset https.proxy
```

## 输出要求

- 明确根因分类：`网络` / `代理` / `认证` / `远程地址`
- 提供最小变更修复方案（优先临时覆盖，不直接改全局）
- 给出可回滚步骤，避免影响其它仓库
