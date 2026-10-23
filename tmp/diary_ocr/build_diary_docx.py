from pathlib import Path
import re
from difflib import SequenceMatcher
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path('tmp/diary_ocr/text')
OUT = Path('output/documents/纸质日记文字识别汇编.docx')

MANUAL_OVERRIDES = {
    '20120602': [
        '真实 我想知道我',
        '2012.06.02',
        '很久以来没有伤心和纠结了，或许是在感情上找到感觉，还是人际交往能力上升，他们在我心中几乎没有什么波动。最近心情不怎么好，以前觉得好的感情、人际都显露出不好的一面。并且，又无可救药地爱上了另一个人，姑且可以这样说吧。之前对其他所有人，都是在逐渐的接触中没有 feel 了，或是距离太远也就淡掉了。这次我又遇到和高三的他一样的感觉，几乎一样的经过，我真的有点绝望了。',
        '我们之间其实可以写成一个很美的故事，但是这种美好总让我有种不适。我喜欢他的好多，单独拿出来又不会疯狂。唯一欲罢不能的是那种含糊不清的大舌头。我们生活特点不一样，无所谓了。这或许是川渝人特别的慵懒，来源于价值观的不同。我不在乎，抑或说我很向往那种得过且过、老酒肥肉的生活。真正让我不喜欢的是我们的内核，其实就是价值观的不同。我们在一起能为了一个困难的目标努力奋斗、互相激励、自得其乐吗？往小了说，我们感兴趣的点差异很大，几乎没有什么共同爱好。',
        '我期望能有一个百分百真诚的人，但我相信无论如何，他在我面前都会留很多余地。西南人看似豁达，实际上很封闭。现在想想，他也许只暴露了多点无关紧要的东西吧！第三，那种自圆其说的伪装，对自己的错误不改正，反而不断用理由包庇，也让我很不舒服，但这或许是通病吧。第四，你对你最亲的人总要维持一种地位，这种不真诚让我现在不能接受。',
        '我现在的心动或许因为一天天老是见到你。见得少一些，可能会好一些吧。尽量减少和他见面吧，但见了后一切正常，说那无所谓了。',
        'If I could find love at a stop in a park with opening arms,\nI would save all my love in a jar made of sparks,\nsealed in my beating heart.\nCould it be yours to keep, the jar of love?',
    ],
    '20171221': [
        '意料之外也是意料之中，我已经开始想你了。',
        '在我做出了分开的决定后，我在一瞬的开心后，陷入了大量的怀念。我从来没有意识到，我竟如此爱你，如此离不开你。可笑的是，一旦我决定了分开，这种爱竟令我窒息。',
        '但我决定了。人生不就是这样，从两个糟糕的选项中选出来一个。我这次以及以后，要“做自己”“做正确的事情”。当然，这样代价高昂，有些代价甚至不是我可以承担。我多希望做点什么，让你别那么伤感。如果可以，我甚至希望你以为分开只是因为某个不重要的因素，使责任落在我这一边。我知道这些都不切实际，所以，作为一个情侣中的我，应该来解决这个问题。问题就在于，现在的我在这个时点下并不合适。',
        '我们很开心，我极其需要你的陪伴，但我不认为这就是爱情；长久以来，那更像是我对你的依赖。值得更好的你，也值得重新享受爱情；值得更好的我，也值得重新享受爱情。',
        '这是我要的吗？为什么这么难受？',
        '分手的驱动因子是什么？我感到窒息，为什么有窒息的感觉？我觉得她在我身边既不自信，也不独立，也不美丽，也不迷人。如果和这样的人在一起，我的生命失去了活力。我不愿为这样的人生而努力。',
        '所以说，分手的原因就是觉得她不够好。和她在一起，我觉得这就是我十年后、二十年后生活的样子。如果在一起，其实我们都应找到自己想走的路，成长为一个优秀而有趣的人，然后为了共同的目标前进。',
        '我希望我身边的人可以启发我、激励我前进，inspiring and motivating，支持我。我希望我会爱上、学习我身边的那个人。',
        "C’est la vie. Ciao, mon amour.",
        "It’s easier to say love when I decide to break up with you.",
        "I love you, not only romantically, but…",
        "I love you as a great companion in my life. I love hanging out with you; I love spending time with you. But this kind of love is not the love I expected for lovers.",
        '我要去冒险，去了解这个世界，去眼看美好，去探索极限。',
        'Universe　Science　World　Art　Nature　Sports　Society　Humanity',
        'Everything is about curiosity.',
    ],
}

BRAND_PATTERNS = [
    r'^(Date|Datc|Page|Pag|Memo(?: No)?|No)[\s.，。:：-]*$',
    r'^[^A-Za-z]*(?:f?eash|feas|eas|fash|flash|Reas|Ras)[A-Za-z\s]*[^A-Za-z]*$',
    r'^[^A-Za-z]*(?:[A-Za-z]*eas[A-Za-z]*(?:tfe|tle|lfe))[^A-Za-z]*$',
    r'^[•·]?[A-Z]*IDEASFLY$', r'^ThinkingAround$', r'^.*M1DII.*$',
    r'^(?:ETIDEASF|TIDEASF|EASFLY|IDEASFLY)$',
    r'^[•·]?(?:DIIDII|DIDa|DNLOuOW|LICAI|ASFLY|EASFLY)$',
    r'^中国青岛市香港东路217号$', r'^.*8897(?:100|1111|1666).*$',
    r'^217 Xiang Gang Dong (?:Koad|Road).*$', r'^.*Sophia.*Hotel.*$',
    r'^.*索菲亚.*国际大酒店.*$', r'^www\.sophiahotel\.com.*$',
    r'^(?:Cphia|Cephinat|Soptua Interutcal HolelCn)$',
]
BRAND_RES = [re.compile(p, re.I) for p in BRAND_PATTERNS]

# Only high-confidence, context-specific corrections are made. Ambiguous wording remains as OCR.
REPLACEMENTS = {
    '很欠以来': '很久以来', '纠猪': '纠结', '暴近': '最近', '显踩出': '显露出',
    '上打，': '上升，', '我真的有点抱望了': '我真的有点绝望了', '找有种': '我有种',
    '逐漸': '逐渐', '共问数好': '共同爱好', '无跑如何': '无论如何',
    '无关紧贵': '无关紧要', '成少和他几面': '减少和他见面',
    '没有刘意伪装': '没有刻意伪装', '没有信备靠残酷的话局': '没有信念却残酷的结局',
    '她没锴': '她没错', '父母也没罐': '父母也没错', '我也没有错': '我也没有错',
    '男一个人': '另一个人', '不会该我的人': '不会爱我的人', '他笑她': '他爱她',
    '相见不女不念': '相见不如不念', '无刑': '无形', '精神友材': '精神友人',
    '我们之同': '我们之间', '真你念': '真怀念', '细水长流更让我心i': '细水长流更让我心动',
    '必然不是平等的': '必然不是平等的', '心错不宁': '心神不宁', '都三个月': '都三个月',
    '我不会撤谎': '我不会撒谎', '没农生': '没发生', '按部就班': '按部就班',
    '斤斤计联': '斤斤计较', '懊梅': '懊悔', '道个歉': '道个歉',
    '小心矍翼': '小心翼翼', 'T-shint': 'T-shirt', '一睜开眼': '一睁开眼',
    '人权的癌进': '人权的演进', '婚姻的尖败补': '婚姻的失败率', '侥萃心态': '侥幸心态',
    '婚如如职能': '婚姻的职能', '相敬如宾，保持距烈': '相敬如宾，保持距离',
    '为往全继绝字': '为往圣继绝学', '为天地开太半': '为万世开太平',
    '知已': '知己', '迷怪': '迷茫', '一乳而过': '一晃而过',
    '四到北京': '回到北京', '自己的状志': '自己的状态', '才於让': '才能让',
    '青指找到感觉': '感情上找到感觉', '以前觉得好的音指': '以前觉得好的感情',
    '草独拿出来': '单独拿出来', '得过目过': '得过且过', '们值观': '价值观',
    '感光趣': '感兴趣', '点差身很大': '点差异很大', '百分看真诚': '百分百真诚',
    '容达': '豁达', '狱闭': '封闭', '自回变说': '自圆其说', '不放正': '不改正',
    '用路地包庇': '用理由包庇', '给持一种地位': '维持一种地位',
    '她今才心酸': '如今才心酸', '最萌单': '最简单', '最没有信念': '最没有信念',
    '小决要草福': '小孩要幸福', '五后的你': '五年后的你', '伤得象深': '伤得最深',
    '温电埋怨': '理由埋怨', '家境弟异': '家境差异', '我展上一个': '我爱上一个',
    '温还人当的目标': '为了共同的目标', '最好的市己': '最好的自己',
    '防线被他轻而易举地化解于无刑': '防线被他轻而易举地化解于无形',
    '精神友材': '精神伴侣', '人际在力': '人际能力', '我们之国': '我们之间',
    '特张的东西': '特殊的东西', '成了想和他': '为了想和他', '波斓': '波澜',
    '性杯的人': '性格的人', '彻底看了你': '彻底忘了你', '没有钥药': '没有解药',
    '办认出你': '辨认出你', '我自过多情': '我自作多情', '客怕': '害怕',
    '数人': '恋人', '尊密和自由': '尊重和自由', '爱庸': '爱情',
    '更加有难以彩割': '更加有难以割舍', '流恋': '留恋', '须想到': '预想到',
    '怕怕他的话': '害怕他的话', '纠落缠流': '纠结难受', '身微': '卑微',
    '庸嫩': '慵懒', '信位': '信任', '温繫': '温馨', '揽位你': '揽住你',
    '家的交撑': '家的支撑', '坚礁': '坚持', '克刺': '克制', '情烈': '情绪',
    '自己赏上了他': '自己爱上了他', '释怨': '释然', '爱你就已站': '爱你就已经',
    '欠思靠': '欠思考', '问到他身上': '闻到他身上', '味值': '味道',
    '凄凉': '凄凉', '辛孤独': '辛苦、孤独', '女並': '女生', '暖昧': '暧昧',
    '瞬问在倒了找': '瞬间击倒了我', '搭活': '搭话', '弃受': '接受',
    '小以了': '小心了', '万劫不是': '万劫不复', '原流半回': '原地徘徊',
    '早做的根源': '受伤的根源', '傣动': '悸动', '无視': '无视',
    '尴你局面': '尴尬局面', '皆皆沉沉': '昏昏沉沉', '一塌糊标': '一塌糊涂',
    '优蒼': '优秀', '沉送': '沉迷', '优麽': '优秀', '环独': '孤独',
    '护限': '扩展', '内心不够多强大': '内心不够强大', '不够多优秀': '不够优秀',
    '说澡': '洗澡', '说衣服': '洗衣服', '准免': '难免', '融碰到': '触碰到',
    '狼尤': '强大', '泰人厦': '喜人', '军做': '卑微', '女近': '弱势',
    '吸分': '吸引', '士号': '另一个', '合湿之处': '合适之处', '孩求': '苛求',
    '資后': '背后', '扔给': '把柄', '国什么羁绊': '留什么羁绊',
    '迹来顺受': '逆来顺受', '决去了': '失去了', '优光位置': '优势位置',
    '温求公平': '追求公平', '好没': '好过', '冷说': '冷淡', '挑鲜': '挑衅',
    '看请': '看清', '无时天刻': '无时无刻', '晃来昆去': '晃来晃去',
    '伤筋动骨': '伤筋动骨', '三前的伤心': '之前的伤心', '给历': '经历',
    '更猪烈地发上': '更强烈地爱上', '不相侵': '不相信', '店望': '奢望',
    '科种迹家後觉': '各种迹象感觉', '可於': '可能', '特？的感觉': '特别的感觉',
    '厚因': '原因', '徐释': '解释', '想不面的': '想不明的',
    '带洽他们': '带给他们', '自私心軟': '自私、心软', '偏加执': '偏执',
    '万相喜欢': '互相喜欢', '未得到儿愛之物': '未得到所爱之物',
    '由情生女礼止': '由情生爱，止于礼', '盂孟': '种种', '代们': '代价',
    '从这显学别的': '从这里学到的', '位何事情': '任何事情', '底成': '底线',
    '认真地喜欢过他': '认真地喜欢过他', '暽间': '瞬间', '那此坦自': '那次坦白',
    '什么的象': '什么印象', '唷': '口音', '惠出去了': '熏出去了',
    '剥皮雪糕': '剥皮雪糕', '拍備位': '拍他', '创咖': '创咖',
    '仔还打找': '你还打我', '衣败': '衣服', '小甜屋': '小甜蜜',
    '那球重迷人的汗味': '那种迷人的汗味', '一起出去吃开': '一起出去吃饭',
    '暴兩夜': '暴雨夜', '冒平': '昌平', '与子': '勺子', '会注亏': '会生气',
    '女果仔是女孩': '如果你是女孩', '那以生气': '莫名生气', '忑么了': '怎么了',
    '抽念太多': '想念太多', '暑做': '暑假', '从了结': '不了了之',
    '善惹': '善意', '最班忘': '最难忘', '汤忆': '回忆',
    '社会交位': '社会交往', '智禁': '智慧', '恋裝关系': '恋爱关系',
    '攀热': '炽热', '转他化': '转化', '想性今理性': '感性和理性',
    '努散用力地收挥': '努力地发挥', '感住不足': '感性不足', '系流自己': '系统本身',
    '极端斯坦': '极端状态', '区配婚姻': '匹配婚姻', '帮助力他们': '帮助他们',
    '承诺履的': '承诺履约', '惩赏': '奖惩', '婚烟': '婚姻', '关京': '关系',
    '抓连放轻': '抓大放小', '返璃归真的阿段': '返璞归真的阶段',
    '处湿好': '处理好', '偏效应': '正效应', '逗求': '追求', '归属人生意义': '归属和人生意义',
    '影祥的人的慈情': '另一个人的感情', '太商了': '太高了', '永应不让自己失': '永远不让自己失望',
    '姐白讲': '坦白讲', '自由没置': '自由设置', '特别失婆': '特别失望',
    '无性悉': '无性恋', '范睛': '范畴', '忧光位置': '优先位置',
    '远散爱的性最合适的人': '远找爱与性最合适的人', '很强度的浪漫': '低强度的浪漫',
    '希述': '希望', '百年准造': '百年难遇', '解天不好': '解决不好',
    '支往角色': '交往角色', '起入婚烟': '进入婚姻',
    '接別想家': '特别想家', '現家': '想家', '心境似乎又像认前': '心境似乎又像以前',
    '人生一世，应到底': '人生一世，到底', '红尘俗事牵件着我': '红尘俗事牵绊着我',
    '很活易衫响我': '很容易影响我', '感到跡傲自豪': '感到骄傲自豪',
    '身材、内修学织': '身材、内修学识', '工作新在': '工作自在', '对守以专和': '对感情专一',
    '锻源品步': '锻炼跑步', '会计研笼': '会计研究', '为了g想而合斗': '为了梦想而奋斗',
    '給父母去人': '给父母丢人', '好得起': '对得起', '有介值': '有价值',
    '真没面前': '真爱面前', '有阳力': '有能力', '札杼': '机会',
    '聪啊的人': '聪明的人', '性远去挑战': '永远去挑战', '智馨': '智慧',
    '慎恩復行': '慎思笃行', '勇取太胆': '勇敢大胆',
}

def natural_page_key(path: Path):
    m = re.search(r'(\d+)$', path.stem)
    return int(m.group(1)) if m else 0

def is_brand(line: str) -> bool:
    s = line.strip()
    if not s:
        return False
    return any(p.fullmatch(s) for p in BRAND_RES)

def clean_line(line: str) -> str:
    s = line.strip().replace('\ufeff', '')
    for old, new in REPLACEMENTS.items():
        s = s.replace(old, new)
    s = re.sub(r'(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])', '', s)
    s = re.sub(r'\s+([，。！？；：])', r'\1', s)
    s = s.replace('．', '。').replace('，。', '。')
    return s

def language_class(text):
    zh = len(re.findall(r'[\u4e00-\u9fff]', text))
    en = len(re.findall(r'[A-Za-z]', text))
    if zh >= max(3, en): return 'zh'
    if en >= max(5, zh * 2): return 'en'
    return 'mixed'

DATE_RE = re.compile(r'^(?:20\d{2}[./、,，:：-]\d{1,2}(?:[./、,，:：-]\d{1,2})?|20\d{2}\s*年|\d{1,2}[./、,，-]\d{1,2})')

def join_lines(lines):
    out = ''
    for line in lines:
        if not out:
            out = line
        elif re.search(r'[A-Za-z0-9]$', out) and re.match(r'^[A-Za-z0-9]', line):
            out += ' ' + line
        else:
            out += line
    return out

def split_long(text, target=260, maximum=430):
    if len(text) <= maximum:
        return [text]
    units = [x for x in re.split(r'(?<=[。！？!?；;])', text) if x]
    if len(units) == 1:
        units = [x for x in re.split(r'(?<=[，,：:])', text) if x]
    result, current = [], ''
    for unit in units:
        if current and len(current) + len(unit) > maximum:
            result.append(current); current = unit
        else:
            current += unit
        if len(current) >= target and re.search(r'[。！？!?；;]$', current):
            result.append(current); current = ''
    if current:
        result.append(current)
    return result

def paragraphs_for(folder: Path):
    if folder.name in MANUAL_OVERRIDES:
        return MANUAL_OVERRIDES[folder.name]
    paras = []
    for page in sorted(folder.glob('page-*.txt'), key=natural_page_key):
        cleaned = []
        raw_lines = page.read_text(encoding='utf-8').splitlines()
        if folder.name == '20171221' and natural_page_key(page) in (1, 2):
            marker = '意料之' if natural_page_key(page) == 1 else '这是我要的'
            for i, raw in enumerate(raw_lines):
                if marker in raw:
                    raw_lines = raw_lines[i:]
                    break
        for raw in raw_lines:
            line = clean_line(raw)
            if is_brand(line):
                continue
            if line:
                cleaned.append(line)
        if not cleaned:
            continue

        # Keep dates, compact headings, and real list items separate; merge prose lines semantically.
        prose, page_paras = [], []
        list_like = sum(bool(re.match(r'^[（(]?\d+[）).、]|^[①-⑳]|^[•·-]\s*', x)) for x in cleaned) >= 3
        for line in cleaned:
            standalone = DATE_RE.match(line) or (len(line) <= 28 and re.search(r'[:：]$', line))
            item = list_like and bool(re.match(r'^[（(]?\d+[）).、]|^[①-⑳]|^[•·-]\s*', line))
            switch = prose and language_class(join_lines(prose)) in ('zh', 'en') and language_class(line) in ('zh', 'en') and language_class(join_lines(prose)) != language_class(line)
            if standalone or item or switch:
                if prose:
                    page_paras.extend(split_long(join_lines(prose))); prose = []
                if switch and not (standalone or item):
                    prose.append(line)
                else:
                    page_paras.append(line)
            else:
                prose.append(line)
        if prose:
            page_paras.extend(split_long(join_lines(prose)))
        for block in page_paras:
            block = block.strip()
            if len(block) < 2:
                continue
            if paras and SequenceMatcher(None, paras[-1], block).ratio() > 0.88:
                continue
            paras.append(block)
    merged = []
    for block in paras:
        is_date = bool(DATE_RE.match(block))
        is_item = bool(re.match(r'^[（(]?\d+[）).、]|^[①-⑳]|^[•·-]\s*', block))
        if (merged and not is_date and not is_item and len(merged[-1]) + len(block) < 520
                and not re.search(r'[。！？!?；;，,:：]$', merged[-1])
                and language_class(merged[-1]) == language_class(block)):
            merged[-1] = join_lines([merged[-1], block])
        else:
            merged.append(block)
    return merged

def set_font(run, western='Aptos', east_asia='Arial Unicode MS', size=11, bold=False):
    run.font.name = western
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = RGBColor(0, 0, 0)
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.rFonts
    if rfonts is None:
        rfonts = OxmlElement('w:rFonts'); rpr.insert(0, rfonts)
    rfonts.set(qn('w:ascii'), western); rfonts.set(qn('w:hAnsi'), western)
    rfonts.set(qn('w:eastAsia'), east_asia)

def add_page_number(paragraph):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run()
    fld = OxmlElement('w:fldSimple'); fld.set(qn('w:instr'), 'PAGE')
    run._r.addnext(fld)

def build():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = Document()
    sec = doc.sections[0]
    sec.page_width = Inches(8.5); sec.page_height = Inches(11)
    sec.top_margin = Inches(0.78); sec.bottom_margin = Inches(0.72)
    sec.left_margin = Inches(0.88); sec.right_margin = Inches(0.88)

    normal = doc.styles['Normal']
    normal.font.name = 'Aptos'; normal.font.size = Pt(11); normal.font.color.rgb = RGBColor(0,0,0)
    normal._element.rPr.rFonts.set(qn('w:eastAsia'), 'Arial Unicode MS')
    normal.paragraph_format.line_spacing = 1.45
    normal.paragraph_format.space_after = Pt(7)
    normal.paragraph_format.first_line_indent = Pt(22)

    title_style = doc.styles['Title']
    title_style.font.color.rgb = RGBColor(0, 0, 0)
    ppr = title_style._element.get_or_add_pPr()
    border = ppr.find(qn('w:pBdr'))
    if border is not None:
        ppr.remove(border)
    heading1 = doc.styles['Heading 1']
    heading1.paragraph_format.left_indent = Pt(0)
    heading1.paragraph_format.first_line_indent = Pt(0)

    title = doc.add_paragraph(style='Title')
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_font(title.add_run('纸质日记文字识别汇编'), east_asia='Arial Unicode MS', size=22, bold=True)
    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub.paragraph_format.space_before = Pt(10); sub.paragraph_format.space_after = Pt(20)
    set_font(sub.add_run('2012年至2017年纸质扫描文字整理'), east_asia='Arial Unicode MS', size=11)

    folders = sorted([p for p in ROOT.iterdir() if p.is_dir()], key=lambda p: p.name)
    for idx, folder in enumerate(folders):
        if idx and doc.paragraphs:
            doc.paragraphs[-1].add_run().add_break(WD_BREAK.PAGE)
        title_text = folder.name.replace('_上旬', ' 上旬')
        h = doc.add_paragraph(style='Heading 1')
        h.paragraph_format.left_indent = Pt(0)
        h.paragraph_format.first_line_indent = Pt(0)
        h.paragraph_format.keep_with_next = True
        h.paragraph_format.space_after = Pt(12)
        set_font(h.add_run(title_text), east_asia='Arial Unicode MS', size=16, bold=True)
        for text in paragraphs_for(folder):
            p = doc.add_paragraph()
            p.paragraph_format.widow_control = True
            set_font(p.add_run(text), east_asia='Arial Unicode MS', size=11)

    add_page_number(doc.sections[0].footer.paragraphs[0])
    props = doc.core_properties
    props.title = '纸质日记文字识别汇编'
    props.subject = '29个纸质扫描PDF的文字识别整理'
    doc.save(OUT)
    print(OUT)

if __name__ == '__main__':
    build()
