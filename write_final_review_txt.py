from pathlib import Path


out_path = Path(r"E:\MulTek\02设计文档\EAP通讯规格书\WebAPI\超毅项目Web API通讯规格书 v4.0 变更记录.txt")

content = """超毅项目 Web API 通讯规格书 v4.0 最终需修改清单
生成日期：2026-06-01

说明：
本清单已合并 Claude 自查结果与本次复查结果，并按用户确认排除了不需要修改的事项。

一、接口名称 / Message / URL 空格或复制错误
1. EQP-EAP-014：EQP_ InnerOuterBindingReport 改为 EQP_InnerOuterBindingReport。
2. EQP-EAP-015：EQP_ GetSetOrPcsInfo 改为 EQP_GetSetOrPcsInfo。
3. EQP-EAP-017：EQP_ IcCodeReport 改为 EQP_IcCodeReport。
4. EQP-EAP-020：EQP_ InnerGetOuterReport 改为 EQP_InnerGetOuterReport。
5. EAP-EQP-002：EAP_ DateTimeSyncCommand 改为 EAP_DateTimeSyncCommand。
6. EQP-EAP-028：示例 Message 从 EQP_IcCodeReport 改为 EQP_Reportcoding。
7. EQP-EAP-031：示例 URL / Message 从 EQP_DefectDataReport 改为 EQP_TaskCompleteReport。
8. EQP-EAP-036：示例 URL 从 EQP_BackDrillCompletionReport 改为 EQP_CTProcessDataReport。
9. EAP-EQP-011：示例 URL 从 EAP_JobDataDownload 改为 EAP_TaskDownload。
10. 基础地址：http://ip:port/api/ EAP_InitialDataRequest 删除 /api/ 后空格，改为 http://ip:port/api/EAP_InitialDataRequest。

二、字段名不一致
1. EQP-EAP-014：示例 Out_panel_ID 改为 OutPanelId，In_panel_ID 改为 InPanelId。
2. EQP-EAP-015：示例 PNLId 与定义 PNLID 不一致，需统一。
3. EQP-EAP-020：返回字段 OuPanelId 建议改为 OutPanelId。
4. EAP-EQP-001：返回定义为 EqpStatus，示例写 EQPStatus，需统一；示例值 "Run " 去掉尾部空格。
5. EQP-EAP-024：响应字段 " Result " 改为 "Result"，值 " Y" 改为 "Y"。
6. EQP-EAP-027：示例字段 " UserName "、" Password " 去掉前后空格。

三、JSON 示例格式错误
1. 全文所有中文引号、中文逗号、中文冒号需替换为标准 JSON 标点。
2. 删除 JSON 示例中的 // 注释，特别是 EQP-EAP-028。
3. 清理尾随逗号，例如 EQP-EAP-017、EQP-EAP-020、EQP-EAP-024、EQP-EAP-029。
4. EQP-EAP-006 响应示例 Content 结尾引号/括号错误，需要修正。
5. EQP-EAP-017 响应示例无法解析，需重写 AccountList 示例。
6. EQP-EAP-028 的 Codes 应为对象数组，当前写法不是合法 JSON。
7. EQP-EAP-031 示例 OkCount 没有值，需要补齐。
8. EQP-EAP-034 示例 FileType 后缺逗号。
9. EQP-EAP-035 示例缺逗号，且 AxisBindings 数组和 CompletionStatus 位置错误。
10. EAP-EQP-007 示例 BaseCopper 使用中文引号，需改标准 JSON。
11. EAP-EQP-009 响应 Result 使用中文引号，需修正。

四、参数编号 / 表格结构问题
1. EQP-EAP-027、EQP-EAP-028、EQP-EAP-029：返回值列表缺少 Content 序号 5。
2. EQP-EAP-031：PortId 字段缺少编号，建议补为 4.4。
3. EQP-EAP-034：DrillProgramInfo 子字段 4.2.1 应改为 4.4.1。
4. EQP-EAP-035：JobId 序号 4,5 改为 4.5；AxisBinding 子字段编号建议改为 4.3.1 / 4.3.2。
5. EAP-EQP-007：参数序号缺少 4.9，需补齐或重新连续编号。
6. EAP-EQP-010：返回值列表前混入 float | 任务数... 残留行，应删除。

五、描述 / 枚举 / 示例值问题
1. EQP-EAP-036 服务描述从“背钻每趟做完后上报完工信息”改为“CT检查机制程数据报告”。
2. EQP-EAP-035：CompletionStatus 定义为 Finished / Unfinished，示例不应写 Success。
3. EAP-EQP-008：ModifyType 枚举 Updata 建议改为 Update。
4. EQP-EAP-027 / EQP-EAP-028 / EQP-EAP-029：ture / fales 改为 true / false。
5. 变更记录“拆分拆分子任务接口”去掉重复“拆分”。

六、格式统一建议
1. DateTime 建议统一为 yyyy/MM/dd HH:mm:ss。目前 EQP-EAP-014、015、016、017、020、027、028、029 使用 yyyyMMddhhmmss。
2. RequestId 建议统一为 yyyyMMddHHmmssfff 17 位数字格式。目前 EQP-EAP-014、015、016、017、020、027、028、029 存在 UUID 示例。
3. EAP -> EQP 接口中 From 字段描述应统一为“调用接口来源（EAP）”，至少 EAP-EQP-002 到 EAP-EQP-005 存在错误；建议同时检查 EAP-EQP-001、006 到 011。

七、确认不修改 / 不纳入修改范围
以下内容用户已确认不需要修改，但保留在文档中作为范围说明：
1. EQP-EAP-025：EQP_MaterialLableReport 不改为 EQP_MaterialLabelReport。
2. EQP-EAP-021：LiquidDate 示例保持现状，不要求将格式占位改成真实示例时间。
3. EQP-EAP-030：定义为 int 的字段示例值保持现状，不要求将 BoardIdx、IsLayerA、IsScrap、IsDual、ID 等从字符串改成数字。
4. EQP-EAP-006：LoadRequest 状态下同时出现 CarrierId、JobId、OkCount、PanelList 的示例逻辑不要求拆分。
5. EQP-EAP-025：Lable / Label 拼写不作为本次修改项。
"""

out_path.write_text(content, encoding="utf-8-sig")
print(str(out_path))
