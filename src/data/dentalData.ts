// src/data/dentalData.ts — 口腔医学 & 口腔护理专属数据层
// 参考 Alohomora.live 的内容结构：论文、书籍、视频、案例、影像、护理

// ==================== 论文数据 ====================
export interface DentalPaper {
  id: string;
  title: string;
  authors: string;
  journal: string;
  date: string; // '08-10'
  url: string;
  abstract: string;
  type: '研究' | '综述' | '临床' | '实验室' | '政策';
  tags: string[];
}

export const dentalJournals = [
  'Journal of Dental Research',
  'Journal of Clinical Periodontology',
  'Journal of Endodontics',
  'Journal of Periodontology',
  'Journal of Prosthetic Dentistry',
  'International Journal of Paediatric Dentistry',
  'Community Dentistry and Oral Epidemiology',
  'Journal of Oral Rehabilitation',
  'Journal of Dental Sciences',
  'BMC Oral Health',
  'International Journal of Dental Hygiene',
  'Journal of Dental Hygiene',
  'Special Care in Dentistry',
  'Gerodontology',
  'Community Dental Health',
  'Journal of Clinical Nursing',
  'Journal of Advanced Nursing',
  'Nursing Open',
  'BMC Nursing',
  'Journal of Public Health Dentistry',
];

// 期刊中文名映射 (与 tracker JOURNALS.zh 一致)
export const dentalJournalZh: Record<string, string> = {
  'Journal of Dental Research': '牙科研究杂志',
  'Journal of Clinical Periodontology': '临床牙周病学杂志',
  'Journal of Endodontics': '牙髓病学杂志',
  'Journal of Periodontology': '牙周病学杂志',
  'Journal of Prosthetic Dentistry': '修复牙科杂志',
  'International Journal of Paediatric Dentistry': '国际儿童牙科杂志',
  'Community Dentistry and Oral Epidemiology': '社区口腔与流行病学',
  'Journal of Oral Rehabilitation': '口腔康复杂志',
  'Journal of Dental Sciences': '牙科科学杂志',
  'BMC Oral Health': 'BMC 口腔健康',
  'International Journal of Dental Hygiene': '国际牙科卫生杂志',
  'Journal of Dental Hygiene': '牙科卫生学杂志',
  'Special Care in Dentistry': '特需牙科学',
  'Gerodontology': '老年牙科学',
  'Community Dental Health': '社区牙科健康',
  'Journal of Clinical Nursing': '临床护理杂志',
  'Journal of Advanced Nursing': '高级护理杂志',
  'Nursing Open': '护理开放',
  'BMC Nursing': 'BMC 护理',
  'Journal of Public Health Dentistry': '公共卫生牙科杂志',
};

export const dentalPapers: DentalPaper[] = [
  {
    id: 'p1',
    title: 'Minimally invasive treatment of deep caries in permanent teeth: a randomized controlled trial',
    authors: 'Zhang Li, Maria González, Sarah Johnson',
    journal: 'Journal of Dental Research',
    date: '08-10',
    url: '#',
    abstract: '比较微创去龋与常规去龋治疗恒牙深龋的 3 年疗效：两组在疼痛、继发龋与牙髓存活率方面无显著差异，微创组牙本质保留更多。',
    type: '临床',
    tags: ['龋病', '微创', '随机对照'],
  },
  {
    id: 'p2',
    title: 'Machine learning for early detection of oral cancer from intraoral photographs: a multi-center validation study',
    authors: 'Amanda Zhang, David Chen, Hiroshi Tanaka',
    journal: 'Journal of Dental Research',
    date: '08-10',
    url: '#',
    abstract: '基于 15,842 张口内照片训练并验证深度学习模型用于口腔鳞状细胞癌早期筛查，7 中心外部验证 AUC 达 0.91。',
    type: '研究',
    tags: ['口腔癌', '人工智能', '早筛'],
  },
  {
    id: 'p3',
    title: 'Root surface conditioning with 2% chlorhexidine improves periodontal regeneration: a split-mouth study',
    authors: 'Elena Rodriguez, Wei Liu, Paul Müller',
    journal: 'Journal of Clinical Periodontology',
    date: '08-09',
    url: '#',
    abstract: '分口设计研究 2% 氯己定根面处理对牙周再生术的促进效果：18 个月后探诊深度与临床附着水平改善优于对照组。',
    type: '临床',
    tags: ['牙周', '再生', '氯己定'],
  },
  {
    id: 'p4',
    title: 'The global burden of oral diseases 2023: updates from GBD 2023',
    authors: 'Nicholas Kassebaum, Stein Atle Gislason, Amanda Zhang',
    journal: 'Community Dentistry & Oral Epidemiology',
    date: '08-09',
    url: '#',
    abstract: '2023 全球疾病负担研究更新：未经治疗的恒牙龋仍是全球最常见疾病，患病人数约 29 亿。',
    type: '综述',
    tags: ['流行病学', 'GBD', '全球健康'],
  },
  {
    id: 'p5',
    title: 'Effect of probiotic lozenges on peri-implant mucositis: a double-blind RCT',
    authors: 'Fatima Al-Nassar, Chen Wei, Maria Santos',
    journal: 'Journal of Periodontology',
    date: '08-08',
    url: '#',
    abstract: '双盲随机对照试验评估罗伊氏乳杆菌含片对种植体周围黏膜炎的作用：6 个月后探诊出血指数较安慰剂组显著下降。',
    type: '临床',
    tags: ['种植体', '益生菌', '黏膜炎'],
  },
  {
    id: 'p6',
    title: 'Gene therapy for dental pulp regeneration: CRISPR activation of Wnt signaling in human dental pulp stem cells',
    authors: 'Yuki Tanaka, Amanda Zhang, James Wilson',
    journal: 'Journal of Endodontics',
    date: '08-08',
    url: '#',
    abstract: '利用 CRISPRa 激活 Wnt 信号通路促进人牙髓干细胞成牙本质向分化，为牙髓再生提供新思路。',
    type: '实验室',
    tags: ['牙髓', '干细胞', 'CRISPR'],
  },
  {
    id: 'p7',
    title: 'Association between sleep apnea and tooth bruxism: a systematic review and meta-analysis',
    authors: 'Carlos Mendez, Sarah Kim, David Brown',
    journal: 'Journal of Oral Rehabilitation',
    date: '08-07',
    url: '#',
    abstract: '系统评价 52 项研究：阻塞性睡眠呼吸暂停与夜间磨牙之间存在中度正相关，提示二者可能存在共同神经机制。',
    type: '综述',
    tags: ['磨牙症', '睡眠呼吸暂停', 'Meta分析'],
  },
  {
    id: 'p8',
    title: 'Nanoparticle drug delivery in endodontic treatment: a comprehensive review',
    authors: 'Amanda Zhang, Lin Wei, Roberta Smith',
    journal: 'Journal of Endodontics',
    date: '08-07',
    url: '#',
    abstract: '综述脂质体、聚合物纳米粒等药物递送系统在根管治疗中的应用前景与挑战。',
    type: '综述',
    tags: ['根管治疗', '纳米药物', '缓释'],
  },
  {
    id: 'p9',
    title: 'Tele-dentistry effectiveness during the pandemic: a national survey of Chinese dental practices',
    authors: 'Wang Xiaoli, Liu Yang, Amanda Zhang',
    journal: 'BMC Oral Health',
    date: '08-06',
    url: '#',
    abstract: '全国性调查显示远程口腔咨询在疫情期间显著提升了复诊可及性，尤其对复诊患者与乡村地区人群。',
    type: '政策',
    tags: ['远程医疗', '公共卫生', '中国'],
  },
  {
    id: 'p10',
    title: 'AI-assisted diagnosis of periapical lesions from panoramic radiographs: a multi-center study',
    authors: 'Amanda Zhang, Chen Peng, Hiro Tanaka',
    journal: 'Journal of Dental Research',
    date: '08-05',
    url: '#',
    abstract: '基于 9 家医院全景片数据开发根尖周病变 AI 辅助诊断系统，检测灵敏度 0.93、特异度 0.89。',
    type: '研究',
    tags: ['人工智能', '全景片', '根尖周'],
  },
];

// 按日期排序输出 (模拟 Alohomora "08-xx" 日期卡片)
export const papersByDate = [...dentalPapers].sort((a, b) => b.date.localeCompare(a.date));

// ==================== 书籍资源 ====================
export interface DentalBook {
  id: string;
  title: string;
  author: string;
  cover: string;
  year: number;
  category: '教科书' | '临床' | '考试' | '研究';
  url: string;
  description: string;
}

export const dentalBooks: DentalBook[] = [
  {
    id: 'b1',
    title: 'Carranza\'s Clinical Periodontology',
    author: 'Robert J. Genco, Michael G. Newman',
    cover: '📚',
    year: 2023,
    category: '教科书',
    url: '#',
    description: '牙周病学经典教科书，覆盖诊断、治疗计划与外科技术全流程。',
  },
  {
    id: 'b2',
    title: 'Pathways of the Pulp (Cohen\'s)',
    author: 'Kenneth M. Hargreaves, Louis H. Berman',
    cover: '📚',
    year: 2024,
    category: '教科书',
    url: '#',
    description: '牙髓病学"圣经"，根管治疗临床决策的权威参考。',
  },
  {
    id: 'b3',
    title: '口腔护理学（第 4 版）',
    author: '人民卫生出版社',
    cover: '📖',
    year: 2022,
    category: '临床',
    url: '#',
    description: '国内口腔护理专业核心教材，四手操作与器械管理必备。',
  },
  {
    id: 'b4',
    title: '临床口腔医学彩色图谱',
    author: 'Edward J. Baum',
    cover: '📖',
    year: 2021,
    category: '临床',
    url: '#',
    description: '以临床照片为主的口腔疾病视觉诊断指南。',
  },
  {
    id: 'b5',
    title: '口腔执业医师资格考试实践技能',
    author: '国家医学考试中心',
    cover: '📖',
    year: 2025,
    category: '考试',
    url: '#',
    description: '口腔执业医师实践技能考试大纲与标准操作流程。',
  },
];

// ==================== 视频 / 讲座 ====================
export interface DentalVideo {
  id: string;
  title: string;
  channel: string;
  date: string;
  url: string;
  duration: string;
  category: '手术' | '讲座' | '教学' | '研讨';
}

export const dentalVideos: DentalVideo[] = [
  {
    id: 'v1',
    title: 'Step-by-step guided implant placement using dynamic navigation',
    channel: '种植手术演示',
    date: '08-09',
    url: '#',
    duration: '28:42',
    category: '手术',
  },
  {
    id: 'v2',
    title: 'Full mouth debridement under dental endoscopy',
    channel: '牙周内镜',
    date: '08-08',
    url: '#',
    duration: '19:15',
    category: '手术',
  },
  {
    id: 'v3',
    title: 'Management of amelogenesis imperfecta: a multidisciplinary approach',
    channel: '多学科联合治疗',
    date: '08-06',
    url: '#',
    duration: '41:33',
    category: '讲座',
  },
  {
    id: 'v4',
    title: 'Pediatric behavior management update',
    channel: '儿童牙科',
    date: '08-05',
    url: '#',
    duration: '33:18',
    category: '教学',
  },
];

// ==================== 临床案例 ====================
export interface DentalCase {
  id: string;
  title: string;
  patient: string; // '58M', '12F' 等
  diagnosis: string;
  specialty: string;
  date: string;
  url: string;
  image: string;
  summary: string;
}

export const dentalCases: DentalCase[] = [
  {
    id: 'c1',
    title: 'Complex maxillary reconstruction with free fibula flap',
    patient: '58M',
    diagnosis: '成釉细胞瘤术后缺损',
    specialty: '口腔颌面外科',
    date: '08-09',
    url: '#',
    image: '🦴',
    summary: '腓骨瓣游离移植重建上颌骨，术后 5 年随访功能与外形稳定。',
  },
  {
    id: 'c2',
    title: 'Full-arch implant rehabilitation with CAD-CAM prosthesis',
    patient: '67F',
    diagnosis: '重度牙周病致全口缺失',
    specialty: '种植修复',
    date: '08-08',
    url: '#',
    image: '🦷',
    summary: '数字化流程完成全口种植即刻负重，患者满意度高。',
  },
  {
    id: 'c3',
    title: 'Dental management of a child with osteogenesis imperfecta',
    patient: '8M',
    diagnosis: '成骨不全症',
    specialty: '儿童牙科',
    date: '08-07',
    url: '#',
    image: '🦷',
    summary: '成骨不全患儿的多学科口腔管理：全麻下完成牙体修复与预防。',
  },
  {
    id: 'c4',
    title: 'Endodontic treatment of dens invaginatus guided by CBCT',
    patient: '24F',
    diagnosis: '牙内陷伴根尖周炎',
    specialty: '牙体牙髓',
    date: '08-06',
    url: '#',
    image: '🦷',
    summary: 'CBCT 引导下非手术根管治疗牙内陷患牙，12 个月愈合良好。',
  },
];

// ==================== 牙科期刊分类 ====================
export const journalCategories = [
  { name: 'JDR', label: 'Journal of Dental Research', color: 'blue' },
  { name: 'JCP', label: 'Journal of Clinical Periodontology', color: 'green' },
  { name: 'JDE', label: 'Journal of Dental Education', color: 'purple' },
  { name: 'JE', label: 'Journal of Endodontics', color: 'cyan' },
  { name: 'JPR', label: 'Journal of Prosthetic Dentistry', color: 'gold' },
  { name: 'JP', label: 'Journal of Periodontology', color: 'rose' },
  { name: 'IPD', label: 'International Journal of Paediatric Dentistry', color: 'indigo' },
  { name: 'CDE', label: 'Community Dentistry & Oral Epidemiology', color: 'teal' },
];

// ==================== 口腔护理 ====================
export interface NursingItem {
  id: string;
  title: string;
  category: '预防' | '治疗' | '紧急' | '儿科' | '老年';
  date: string;
  summary: string;
  url: string;
}

export const nursingItems: NursingItem[] = [
  {
    id: 'n1',
    title: '儿童氟化钠漱口注意事项',
    category: '预防',
    date: '08-10',
    summary: '6 岁以上儿童使用 0.05% 氟化钠漱口液每日 1 次，含漱 1 分钟后吐出，30 分钟内不进食不饮水；监护人应在旁监督避免吞咽。',
    url: '#',
  },
  {
    id: 'n2',
    title: '拔牙术后出血的紧急处理流程',
    category: '紧急',
    date: '08-09',
    summary: '纱卷加压咬合 30 分钟；持续出血时检查牙槽窝是否有残留牙根或软组织撕裂，必要时棉卷+明胶海绵填塞，联系医生处理。',
    url: '#',
  },
  {
    id: 'n3',
    title: '老年患者治疗前血压评估标准',
    category: '老年',
    date: '08-08',
    summary: '治疗前常规测量血压：收缩压 ≥180mmHg 或舒张压 ≥110mmHg 应暂缓择期治疗并转诊内科评估；建议保持原有降压药规律服用。',
    url: '#',
  },
  {
    id: 'n4',
    title: '糖尿病患者口腔诊疗的血糖管理',
    category: '治疗',
    date: '08-07',
    summary: '择期治疗前空腹血糖建议 ≤7.8mmol/L，餐后 2h ≤10mmol/L；询问降糖药使用情况，预防低血糖发生，候诊区备糖果。',
    url: '#',
  },
  {
    id: 'n5',
    title: '正畸患者口腔清洁指导',
    category: '预防',
    date: '08-06',
    summary: '正畸固定矫治期间需使用正畸专用小头软毛牙刷、牙间刷与冲牙器；每次餐后 3 分钟内清洁，重点清理托槽周围与牙龈沟。',
    url: '#',
  },
];

// ==================== 影像病例 ====================
export interface ScanItem {
  id: string;
  title: string;
  modality: '全景片' | 'CBCT' | '根尖片';
  date: string;
  finding: string;
  url: string;
}

export const scanItems: ScanItem[] = [
  {
    id: 's1',
    title: '下颌骨囊肿全景片评估',
    modality: '全景片',
    date: '08-09',
    finding: '左侧下颌体可见边界清晰低密度影，累及 36-37 牙根尖区，牙根未见明显吸收，建议 CBCT 进一步定位。',
    url: '#',
  },
  {
    id: 's2',
    title: '上颌窦提升术前 CBCT 测量',
    modality: 'CBCT',
    date: '08-08',
    finding: '16 牙位剩余牙槽嵴高度约 3.2mm，上颌窦底黏膜未见增厚，可行经牙槽嵴顶入路上颌窦提升术。',
    url: '#',
  },
  {
    id: 's3',
    title: '根尖片显示根管充填效果',
    modality: '根尖片',
    date: '08-06',
    finding: '46 牙根管充填致密，恰填至根尖 1mm 内，根尖周未见明显透射影，充填效果满意。',
    url: '#',
  },
];
