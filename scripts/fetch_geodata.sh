#!/usr/bin/env bash
# 重建 references/geographic_names.json
# 数据源：modood/Administrative-divisions-of-China（民政部行政区划整理）
# 用法：bash scripts/fetch_geodata.sh

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$(mktemp -d)"
BASE="https://raw.githubusercontent.com/modood/Administrative-divisions-of-China/master/dist"

echo "==> 下载省/市/县数据"
for f in provinces cities areas; do
  curl -sL --max-time 90 "$BASE/$f.json" -o "$WORK/$f.json"
done

echo "==> 生成 geographic_names.json"
python3 - "$WORK" "$ROOT/references/geographic_names.json" <<'PY'
import json, re, sys, pathlib
work, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])

prov = json.loads((work/'provinces.json').read_text(encoding='utf-8'))
cities = json.loads((work/'cities.json').read_text(encoding='utf-8'))
areas = json.loads((work/'areas.json').read_text(encoding='utf-8'))

prov_map = {
 '北京市':'北京','天津市':'天津','上海市':'上海','重庆市':'重庆','河北省':'河北',
 '山西省':'山西','辽宁省':'辽宁','吉林省':'吉林','黑龙江省':'黑龙江','江苏省':'江苏',
 '浙江省':'浙江','安徽省':'安徽','福建省':'福建','江西省':'江西','山东省':'山东',
 '河南省':'河南','湖北省':'湖北','湖南省':'湖南','广东省':'广东','海南省':'海南',
 '四川省':'四川','贵州省':'贵州','云南省':'云南','陕西省':'陕西','甘肃省':'甘肃',
 '青海省':'青海','台湾省':'台湾','内蒙古自治区':'内蒙古','广西壮族自治区':'广西',
 '西藏自治区':'西藏','宁夏回族自治区':'宁夏','新疆维吾尔自治区':'新疆',
 '香港特别行政区':'香港','澳门特别行政区':'澳门',
}
provinces = sorted(set(prov_map.get(p['name'], p['name'].rstrip('省市')) for p in prov) | {'台湾','香港','澳门'})

ETHNIC = ('朝鲜族|蒙古族|藏族|维吾尔族|苗族|侗族|彝族|白族|傣族|景颇族|傈僳族|哈尼族|壮族|回族|'
          '土家族|布依族|羌族|哈萨克|柯尔克孜|锡伯|塔吉克|怒族|独龙族|德昂族|阿昌族|普米族|'
          '纳西族|拉祜族|布朗族|佤族|瑶族|畲族|黎族|仡佬族|仫佬族|毛南族|京族|水族|东乡族|'
          '土族|撒拉族|保安族|裕固族|鄂温克族|达斡尔族|鄂伦春族|赫哲族|门巴族|珞巴族|基诺族')

def strip_city(name):
    if name in ('市辖区','省直辖县级行政区划','自治区直辖县级行政区划','县'):
        return None
    n = re.sub(rf'({ETHNIC})*自治州$', '', name)
    n = re.sub(r'(地区|盟|市)$', '', n)
    return n or None

prefectures = sorted({x for x in (strip_city(c['name']) for c in cities) if x})
def strip_county(name):
    return re.sub(r'(自治县|自治旗|林区|特区|区|县|市|旗)$', '', name) or None

counties_full = sorted({a['name'] for a in areas})
counties_bare = sorted({x for x in (strip_county(a['name']) for a in areas) if x and len(x) >= 2})

# 常见词：作为县级简称时按低置信处理，避免"东方甄选"这类误判抬高结论
common = set("""朝阳 和平 白云 长安 东方 前进 建设 新华 中山 南山 福田 海淀 西城 东城 新城
城关 兴隆 永安 幸福 光明 红星 红旗 团结 民主 文化 公园 金山 江宁 大同 双桥 龙泉 凤凰
金城 白塔 青山 秀英 龙华 宝安 顺德 南海 番禺 通州 昌平 顺义 大兴 房山 怀柔 平谷 密云
延庆 浦东 徐汇 静安 黄浦 长宁 普陀 虹口 杨浦 闵行 嘉定 松江 青浦 奉贤 崇明 越秀 荔湾
天河 黄埔 花都 从化 增城 罗湖 盐田 龙岗 坪山 香洲 斗门 金湾 思明 海沧 湖里 集美 同安
翔安 鼓楼 台江 仓山 马尾 晋安 长乐 玄武 秦淮 建邺 浦口 栖霞 雨花台 城区 郊区 矿区
新区 市中 开发区 高新区 风景区""".split())

data = {
 "source": "中华人民共和国民政部行政区划（经 modood/Administrative-divisions-of-China 整理）",
 "updated": __import__('datetime').date.today().isoformat(),
 "note": "provinces/prefecture_cities 用简称裸匹配；counties 同时提供全称与去后缀简称；common_bare 按低置信处理。",
 "provinces": provinces,
 "prefecture_cities": prefectures,
 "counties_full": counties_full,
 "counties_bare": counties_bare,
 "common_bare": sorted(common & set(counties_bare)),
}
out.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding='utf-8')
print(f"written: {out} (省 {len(provinces)} / 地级 {len(prefectures)} / 县级 {len(counties_full)})")
PY

rm -rf "$WORK"
echo "==> 完成"
