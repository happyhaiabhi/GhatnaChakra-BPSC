#!/usr/bin/env python3
"""Compile supplied sources; pip install pypdf openpyxl. Usage: script INPUT_DIR OUTPUT.xlsx"""
import sys,re,csv,json,unicodedata
from pathlib import Path
from pypdf import PdfReader
from openpyxl import Workbook
from openpyxl.styles import Font,PatternFill,Alignment
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table,TableStyleInfo
D=Path(sys.argv[1]); out=Path(sys.argv[2]); clean=lambda s:re.sub(r'\s+',' ',str(s or '')).strip()
def norm(s):return re.sub(r'[^a-z0-9]+','',unicodedata.normalize('NFKD',clean(s)).lower())
# Chapter numbers after 24 are omitted when the supplied index does not list them.
rules=[('2. Making of the Constitution',r'constituent assembly|drafting committee|constitution (?:was )?(?:adopted|making)|constitution day'),('8. Fundamental Rights',r'fundamental right|article (?:14|15|16|17|19|20|21|22|23|24|25|26|27|28|29|30|32)\b|writ|right to (?:equality|freedom|education|property|constitutional remed)|habeas corpus'),('9. Directive Principles of State Policy',r'directive principle|welfare state|uniform civil code'),('10. Fundamental Duties',r'fundamental dut'),('5. Preamble of the Constitution',r'preamble|preface|sovereign socialist|liberty, equality and fraternity'),('11. Amendment of the Constitution',r'amend(?:ment|ed|ing) (?:of |to )?(?:the )?constitution|constitutional amendment|article 368'),('Emergency Provisions',r'emergency|president.s rule'),('Local Government — Panchayati Raj',r'panchayat|gram sabha|73rd amendment|73rd constitutional|ashok mehta|balwant rai mehta'),('Local Government — Municipalities',r'municipal|urban local|74th amendment'),('Election Commission',r'election commission|chief election commissioner|voter verified|vvpat'),('Political Parties',r'political part|anti.defection|tenth schedule'),('Finance Commission',r'finance commission'),('State Public Service Commission',r'state public service commission'),('Union Public Service Commission',r'union public service commission|upsc'),('Comptroller and Auditor General of India',r'comptroller and auditor|\bcag\b'),('Attorney General of India',r'attorney.general'),('Supreme Court',r'supreme court|chief justice of india|judicial review|collegium'),('High Court',r'high court'),('Governor',r'governor'),('State Legislature',r'legislative (?:council|assembly)|vidhan (?:sabha|parishad)'),('Chief Minister',r'chief minister'),('19. Vice-President',r'vice.president|vice president'),('20. Prime Minister',r'prime minister'),('18. President',r'president of india|indian president|president.s|presidential election|impeachment of the president'),('24. Parliamentary Committees',r'public accounts committee|parliamentary committee'),('23. Parliament',r'lok sabha|rajya sabha|parliament|money bill|speaker of the house|speaker of lok'),('15. Centre-State Relations',r'centre.state|center.state|concurrent list|union list|state list|seventh schedule'),('7. Citizenship',r'citizenship|citizen of india'),('6. Union and Its Territory',r'union territor|reorgani[sz]ation of states|new state|state of sikkim'),('Historical Background',r'simon commission|government of india act|regulating act|pitt.s india act|montagu.chelmsford|cabinet mission'),('14. Federal System',r'federal(?:ism| system| structure)|unitary'),('13. Parliamentary System',r'parliamentary (?:system|government)|presidential system')]
def classify(q, fallback='Review / outside Laxmikanth chapter scope'):
 for title,p in rules:
  if re.search(p,q,re.I):return title
 return fallback
ranges=[(9,'2. Making of the Constitution'),(24,'4. Salient Features of the Constitution'),(33,'15. Centre-State Relations'),(42,'5. Preamble of the Constitution'),(50,'4. Salient Features of the Constitution'),(56,'6. Union and Its Territory'),(59,'7. Citizenship'),(75,'8. Fundamental Rights'),(81,'9. Directive Principles of State Policy'),(86,'10. Fundamental Duties'),(107,'18. President'),(114,'19. Vice-President'),(117,'20. Prime Minister'),(122,'21. Central Council of Ministers'),(124,'Review / outside Laxmikanth chapter scope'),(128,'Attorney General of India'),(130,'Review / outside Laxmikanth chapter scope'),(171,'23. Parliament'),(175,'24. Parliamentary Committees'),(179,'6. Union and Its Territory'),(201,'Supreme Court'),(207,'Governor'),(218,'State Legislature'),(223,'High Court'),(225,'15. Centre-State Relations'),(229,'Emergency Provisions'),(232,'Finance Commission'),(233,'Review / outside Laxmikanth chapter scope'),(240,'Election Commission'),(246,'Political Parties'),(253,'11. Amendment of the Constitution'),(255,'Official Language'),(303,'Local Government — Panchayati Raj'),(306,'Special Provisions Relating to Certain Classes'),(324,'Review / outside Laxmikanth chapter scope')]
# PDF: discard the unextractable Hindi-layer preamble on each page, not the English continuation.
pdf=PdfReader(str(next(D.glob('*.pdf')))); chunks=[]
exam_re=re.compile(r'(?:B\.?\s*P\.?\s*[SC]\.?(?:\s*[SC]\.?)?|U\.P\.P\.C\.S\.)',re.I)
for i in range(1,52):
 lines=pdf.pages[i].extract_text().splitlines(); start=0
 for j,line in enumerate(lines):
  s=line.strip()
  if not s or 'KGS' in s or s.startswith('Mob.') or exam_re.search(s) or re.fullmatch(r'\([a-e]\)',s,re.I) or re.fullmatch(r'[-–IVX\s]+',s):continue
  # Hindi layer may contain isolated roman labels or fragments.
  if len(s)<5:continue
  start=j;break
 lines=lines[start:]
 if i==16: lines=[re.sub(r'^11\.\s*(?=If the post of President)', '99.',x) for x in lines]
 chunks.extend((i+1,x) for x in lines)
# Identify only consecutive question numbers, avoiding numbered statements within questions.
starts=[]; expected=1
for pos,(page,line) in enumerate(chunks):
 if re.match(r'^\s*'+str(expected)+r'\.\s*\S',line):starts.append(pos);expected+=1
assert expected==325, f'PDF extraction stopped at {expected}'
key={}
for page in pdf.pages[52:54]:
 for n,a in re.findall(r'(\d+)\.\s*\(([a-e*/]+)\)',page.extract_text(),re.I):key[int(n)]=a.upper()
records=[]
for k,pos in enumerate(starts):
 n=k+1; segment=chunks[pos:starts[k+1] if k+1<len(starts) else len(chunks)]; page=segment[0][0]; lines=[]; refs=[]
 for _,line in segment:
  s=line.strip()
  if not s or 'KGS Campus' in s or s.startswith('Mob.'):continue
  if exam_re.search(s) and not re.match(r'^\d+\.',s):refs.append(s);continue
  # all-caps section labels only; retain numbered list labels and codes
  if re.fullmatch(r'[A-Z][A-Z ,&()\-/]{5,}',s) and not re.match(r'^[A-D][ .]',s):continue
  lines.append(s)
 text='\n'.join(lines);text=re.sub(r'^\d+\.\s*','',text); text=re.sub(r'-\n(?=[a-z])','',text)
 m=re.search(r'\([aA]\)\s*\S',text)
 question=clean(text[:m.start()] if m else text); options=clean(text[m.start():] if m else '')
 fallback=next(c for end,c in ranges if n<=end)
 records.append(dict(chapter=fallback,question=question,options=options,answer=key.get(n,''),answer_text='',refs=f"KGS polity PDF p.{page}, Q{n}"+(' | '+ '; '.join(refs) if refs else ''),notes='PDF key as printed; check source for OCR, options, and answer accuracy.',origin='PDF'))
# Restrict PDF outside-scope material only by marking it, not silently dropping it.
js=json.load(open(next(D.glob('*.json')),encoding='utf-8-sig'))
for e in js['exams']:
 for q in e['questions']:
  if q.get('subject')!='polity':continue
  opts=q.get('options') or {}; options=' '.join(f'({k.lower()}) {v}' for k,v in opts.items() if v)
  records.append(dict(chapter=classify(q.get('question','')),question=clean(q.get('question')),options=clean(options),answer=clean(q.get('answer_letter')),answer_text=clean(q.get('answer_text')),refs=f"JSON: {e['exam']} Q{q['q_no']}",notes='Source subject is polity; chapter and answer require review. JSON may abbreviate 71st questions; compare CSV. '+clean(q.get('verification_note')),origin='JSON',exam=e['exam'],qno=str(q['q_no'])))
for q in csv.DictReader(open(next(D.glob('*.csv')),encoding='utf-8-sig',newline='')):
 if q['subject'].lower()!='polity':continue
 options=' '.join(f'({x}) {q.get("option_"+x,"")}' for x in 'abcde' if q.get('option_'+x))
 records.append(dict(chapter=classify(q['question']),question=clean(q['question']),options=clean(options),answer=clean(q['answer_key']),answer_text=clean(q['answer_text']),refs=f"CSV: {q['exam']} Q{q['q_no']} ({q['id']})",notes='CSV subtopic: '+q['subtopic']+'; '+clean(q['status'])+'; answer source: '+clean(q['explanation_source']),origin='CSV',exam=q['exam'],qno=q['q_no']))
# Match only identical full question + options (normalized punctuation/whitespace). Never merge just by topic.
unique=[]; seen={}; same_exam={}; removed=0
for r in records:
 key1=(norm(r['question']),norm(r['options']))
 # JSON and CSV of the same exam/Q may differ in metadata or truncated choices; merge only when question and options match.
 if key1[0] and key1[1] and key1 in seen:
  u=unique[seen[key1]];u['refs']+=' | '+r['refs'];removed+=1
  if r['answer'] and u['answer'] and r['answer']!=u['answer']:u['notes']+=' | CONFLICT: '+r['refs']+' answer '+r['answer']
  elif not u['answer']:u['answer']=r['answer'];u['answer_text']=r['answer_text']
  continue
 seen[key1]=len(unique);unique.append(r)
unique.sort(key=lambda r:(r['chapter'],r['refs']))
w=Workbook();s=w.active;s.title='Polity PYQ';s.append(['Chapter (best fit)','Question','Options / statements','Answer key (source)','Answer text (source)','Source / exam / question','Review notes'])
for r in unique:s.append([r['chapter'],r['question'],r['options'],r['answer'],r['answer_text'],r['refs'],r['notes']])
s.freeze_panes='B2';s.auto_filter.ref=s.dimensions
for c in s[1]:c.font=Font(bold=True,color='FFFFFF');c.fill=PatternFill('solid',fgColor='17365D');c.alignment=Alignment(wrap_text=True,vertical='top')
for row in s.iter_rows(min_row=2):
 for c in row:c.alignment=Alignment(vertical='top',wrap_text=True)
for i,width in enumerate([32,70,70,18,30,55,55],1):s.column_dimensions[get_column_letter(i)].width=width
s.sheet_view.showGridLines=False
w.save(out)
print('PDF',len(starts),'keys',len(key),'total source records',len(records),'duplicates removed',removed,'unique',len(unique),'review',sum(r['chapter'].startswith('Review') for r in unique))
