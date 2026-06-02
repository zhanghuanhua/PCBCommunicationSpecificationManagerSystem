from pathlib import Path


TXT = Path(r"E:\MulTek\02设计文档\EAP通讯规格书\WebAPI\超毅项目Web API通讯规格书 v4.0 变更记录.txt")

section = """\n\n八、版式与字体优化（2026-06-01 补充）\n1. 普通接口表格整体优化：统一描述区域字体为 Microsoft YaHei / 微软雅黑，8号；收紧单元格边距、段落前后距、行距和列宽，使表格更紧凑。\n2. 日志示例表格整体优化：所有示例区域统一为 Cambria，7号；重新压缩 JSON 示例排版，示例内容列宽更合理。\n3. 清理重复标题：已清理“返回值列表表表表表”等重复文字问题。\n4. 分页优化：减少不必要的手工分页符，降低出现大面积空白页的概率。\n5. 页眉版本同步：将页眉中的 Version: 3.8 更新为 Version: 4.0。\n6. 更新后复查：重复“返回值列表表表表”不存在；示例 JSON、URL/Message、RequestId 一致性检查通过。\n"""


def main() -> None:
    text = TXT.read_text(encoding="utf-8-sig")
    marker = "八、版式与字体优化（2026-06-01 补充）"
    if marker in text:
        text = text[: text.index(marker)].rstrip() + section
    else:
        text = text.rstrip() + section
    TXT.write_text(text, encoding="utf-8-sig")
    print(TXT)


if __name__ == "__main__":
    main()
