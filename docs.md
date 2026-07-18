# ME Frp 5.0 开放 API 文档

## Docs
- [有关此文档的说明](https://apidoc.mefrp.com/%E6%9C%89%E5%85%B3%E6%AD%A4%E6%96%87%E6%A1%A3%E7%9A%84%E8%AF%B4%E6%98%8E-6889388m0.md): 
- [数据时效性](https://apidoc.mefrp.com/%E6%95%B0%E6%8D%AE%E6%97%B6%E6%95%88%E6%80%A7-6352174m0.md): 
- [有关人机验证的提醒](https://apidoc.mefrp.com/%E6%9C%89%E5%85%B3%E4%BA%BA%E6%9C%BA%E9%AA%8C%E8%AF%81%E7%9A%84%E6%8F%90%E9%86%92-6889302m0.md): 
- 登录 [Magic Link 登陆相关](https://apidoc.mefrp.com/magic-link-%E7%99%BB%E9%99%86%E7%9B%B8%E5%85%B3-6352159m0.md):

## API Docs
- 公共信息 [统计信息](https://apidoc.mefrp.com/%E7%BB%9F%E8%AE%A1%E4%BF%A1%E6%81%AF-277844658e0.md): 获取用户数量、节点数量、隧道数量、已承载流量
- 公共信息 [获取商城商品](https://apidoc.mefrp.com/%E8%8E%B7%E5%8F%96%E5%95%86%E5%9F%8E%E5%95%86%E5%93%81-380546276e0.md): 获取商城商品
- 登录 [密码登录](https://apidoc.mefrp.com/%E5%AF%86%E7%A0%81%E7%99%BB%E5%BD%95-277868573e0.md): > 此端点需要进行人机验证传参，详见[此文档](%E6%9C%89%E5%85%B3%E4%BA%BA%E6%9C%BA%E9%AA%8C%E8%AF%81%E7%9A%84%E6%8F%90%E9%86%92-6889302m0)
- 登录 [找回账户](https://apidoc.mefrp.com/%E6%89%BE%E5%9B%9E%E8%B4%A6%E6%88%B7-277874930e0.md): 找回账户
- 隧道相关 [获取创建隧道所需的所有数据](https://apidoc.mefrp.com/%E8%8E%B7%E5%8F%96%E5%88%9B%E5%BB%BA%E9%9A%A7%E9%81%93%E6%89%80%E9%9C%80%E7%9A%84%E6%89%80%E6%9C%89%E6%95%B0%E6%8D%AE-418624811e0.md): 
- 隧道相关 [获取隧道列表](https://apidoc.mefrp.com/%E8%8E%B7%E5%8F%96%E9%9A%A7%E9%81%93%E5%88%97%E8%A1%A8-380471021e0.md): 获取隧道列表
- 隧道相关 [创建隧道](https://apidoc.mefrp.com/%E5%88%9B%E5%BB%BA%E9%9A%A7%E9%81%93-416605311e0.md): 创建隧道（新版本，适用于 ME Frp 0.65.0+
- 隧道相关 [删除隧道](https://apidoc.mefrp.com/%E5%88%A0%E9%99%A4%E9%9A%A7%E9%81%93-380471224e0.md): 删除指定隧道 ID
- 隧道相关 [强制下线隧道](https://apidoc.mefrp.com/%E5%BC%BA%E5%88%B6%E4%B8%8B%E7%BA%BF%E9%9A%A7%E9%81%93-380471477e0.md): 强制下线指定隧道
- 隧道相关 [启用/禁用隧道](https://apidoc.mefrp.com/%E5%90%AF%E7%94%A8%E7%A6%81%E7%94%A8%E9%9A%A7%E9%81%93-380471489e0.md): 启用/禁用指定隧道
- 隧道相关 [获取单一隧道配置](https://apidoc.mefrp.com/%E8%8E%B7%E5%8F%96%E5%8D%95%E4%B8%80%E9%9A%A7%E9%81%93%E9%85%8D%E7%BD%AE-380471527e0.md): 获取单一隧道配置，对于快速启动，您应当获取 frpToken 拼接启动命令
- 隧道相关 [获取多个隧道配置](https://apidoc.mefrp.com/%E8%8E%B7%E5%8F%96%E5%A4%9A%E4%B8%AA%E9%9A%A7%E9%81%93%E9%85%8D%E7%BD%AE-380471947e0.md): > **Beta feature** 这是一个测试功能，可能不按预期工作，请反馈任何错误。
- 隧道相关 [创建隧道](https://apidoc.mefrp.com/%E5%88%9B%E5%BB%BA%E9%9A%A7%E9%81%93-380470674e0.md): 创建隧道
- 隧道相关 [更新隧道](https://apidoc.mefrp.com/%E6%9B%B4%E6%96%B0%E9%9A%A7%E9%81%93-380471440e0.md): 修改隧道，注意不是切换是否禁用
- 账户相关 [获取用户信息](https://apidoc.mefrp.com/%E8%8E%B7%E5%8F%96%E7%94%A8%E6%88%B7%E4%BF%A1%E6%81%AF-310657624e0.md): 获取对应用户的信息
- 账户相关 [签到](https://apidoc.mefrp.com/%E7%AD%BE%E5%88%B0-310659905e0.md): > 此端点需要进行人机验证传参，详见[此文档](%E6%9C%89%E5%85%B3%E4%BA%BA%E6%9C%BA%E9%AA%8C%E8%AF%81%E7%9A%84%E6%8F%90%E9%86%92-6889302m0)
- 账户相关 [获取用户 frpToken](https://apidoc.mefrp.com/%E8%8E%B7%E5%8F%96%E7%94%A8%E6%88%B7-frptoken-380471988e0.md): 获取对应用户的信息
- 账户相关 [获取用户组信息](https://apidoc.mefrp.com/%E8%8E%B7%E5%8F%96%E7%94%A8%E6%88%B7%E7%BB%84%E4%BF%A1%E6%81%AF-380471996e0.md): 获取用户组信息
- 账户相关 [重置访问密钥](https://apidoc.mefrp.com/%E9%87%8D%E7%BD%AE%E8%AE%BF%E9%97%AE%E5%AF%86%E9%92%A5-310678792e0.md): > 此端点需要进行人机验证传参，详见[此文档](%E6%9C%89%E5%85%B3%E4%BA%BA%E6%9C%BA%E9%AA%8C%E8%AF%81%E7%9A%84%E6%8F%90%E9%86%92-6889302m0)
- 账户相关 [修改密码](https://apidoc.mefrp.com/%E4%BF%AE%E6%94%B9%E5%AF%86%E7%A0%81-310678793e0.md): 修改账户密码，这将 **重置启动令牌和访问密钥**
- 账户相关 [获取用户操作日志](https://apidoc.mefrp.com/%E8%8E%B7%E5%8F%96%E7%94%A8%E6%88%B7%E6%93%8D%E4%BD%9C%E6%97%A5%E5%BF%97-380546726e0.md): 获取用户自己的操作审计日志
- 账户相关 [获取用户日志统计](https://apidoc.mefrp.com/%E8%8E%B7%E5%8F%96%E7%94%A8%E6%88%B7%E6%97%A5%E5%BF%97%E7%BB%9F%E8%AE%A1-380549153e0.md): 获取用户操作日志统计，涵盖今日、本周、本月和总统计。目前只有条目数这一项。
- 账户相关 [权益抽取](https://apidoc.mefrp.com/%E6%9D%83%E7%9B%8A%E6%8A%BD%E5%8F%96-460367818e0.md): 权益抽取(抽奖)接口  仅单抽
- 账户相关 [剩余抽奖次数](https://apidoc.mefrp.com/%E5%89%A9%E4%BD%99%E6%8A%BD%E5%A5%96%E6%AC%A1%E6%95%B0-460370545e0.md): 
- 节点相关 [获取节点列表](https://apidoc.mefrp.com/%E8%8E%B7%E5%8F%96%E8%8A%82%E7%82%B9%E5%88%97%E8%A1%A8-380472186e0.md): 
- 节点相关 [获取节点连接地址列表](https://apidoc.mefrp.com/%E8%8E%B7%E5%8F%96%E8%8A%82%E7%82%B9%E8%BF%9E%E6%8E%A5%E5%9C%B0%E5%9D%80%E5%88%97%E8%A1%A8-380472242e0.md): 仅能获取已创建隧道的节点连接地址
- 节点相关 [获取节点状态](https://apidoc.mefrp.com/%E8%8E%B7%E5%8F%96%E8%8A%82%E7%82%B9%E7%8A%B6%E6%80%81-380472258e0.md): 
- 节点相关 [获取节点 Token](https://apidoc.mefrp.com/%E8%8E%B7%E5%8F%96%E8%8A%82%E7%82%B9-token-380472299e0.md): 获取节点 Token（不是管理密码）和服务端口（实际连接到服务器的端口）。看上去没什么用的接口，不过还是建议请求一下。
- 系统相关 [获取系统状态](https://apidoc.mefrp.com/%E8%8E%B7%E5%8F%96%E7%B3%BB%E7%BB%9F%E7%8A%B6%E6%80%81-380472142e0.md): > **Beta feature** 这是一个测试功能，会在前端 `v5.14.6` 中引入
- 系统相关 [获取系统公告](https://apidoc.mefrp.com/%E8%8E%B7%E5%8F%96%E7%B3%BB%E7%BB%9F%E5%85%AC%E5%91%8A-458861592e0.md): 返回内容需要使用 Markdown 渲染器渲染。
- 系统相关 [获取重要公告](https://apidoc.mefrp.com/%E8%8E%B7%E5%8F%96%E9%87%8D%E8%A6%81%E5%85%AC%E5%91%8A-380472951e0.md): > **Beta feature** 这是一个测试功能，会在前端 `v5.14.6` 中引入

## Schemas
- [userInfo](https://apidoc.mefrp.com/%E7%94%A8%E6%88%B7%E4%BF%A1%E6%81%AF-177208496d0.md): 
- [proxy](https://apidoc.mefrp.com/%E9%9A%A7%E9%81%93%E6%95%B0%E6%8D%AE-156645213d0.md): 