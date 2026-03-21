# Security Policy

如果你发现了安全漏洞，请不要直接提交公开 issue。

If you discover a security vulnerability, please do not open a public issue first.

## Reporting

请通过私下渠道联系项目维护者，并提供尽可能完整的信息：

- 问题描述
- 影响范围
- 复现步骤
- 可能的修复建议

Please contact the maintainers privately and include:

- a clear description of the issue
- affected areas
- reproduction steps
- any suggested mitigation or fix

如果当前仓库还没有单独公布安全邮箱，请先通过私信或私有沟通渠道联系维护者，再决定公开披露时间。

If no dedicated security contact has been published yet, contact the maintainers through a private channel first and coordinate disclosure timing before making the issue public.

## Scope

当前优先关注：

- 认证密钥、环境变量或敏感配置泄露
- 上传、解析或问答接口中的越权或输入校验问题
- 可能导致任意文件写入、路径穿越或远程代码执行的漏洞

Current priority areas include:

- leaked secrets or sensitive configuration
- authorization or input-validation issues in upload, parsing, or QA flows
- vulnerabilities that could lead to arbitrary file writes, path traversal, or remote code execution
