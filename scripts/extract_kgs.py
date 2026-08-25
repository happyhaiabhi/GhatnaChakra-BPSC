#!/usr/bin/env python3
"""
Extract the Khan Global Studies 'प्रहार' 72nd BPSC Prelims Test Series PDFs
(source_pdfs/) into ONE book 'KGS Test Series' with each test as a subject.

Book layout:
  books/kgs_test_series/data/chapters.json
  books/kgs_test_series/data/test_<n>.json

Each subject file has a single chapter (the test subject) with 150 questions.
The Ghatna Chakra app auto-renders Assertion-Reason, numbered-statement, and
List-I/List-II match structures directly from the cleaned question text.
"""
import fitz  # PyMuPDF
import glob, json, os, re, sys, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "source_pdfs"
OUT = ROOT / "books" / "kgs_test_series" / "data"
ASSETS = ROOT / "books" / "kgs_test_series" / "assets"
OUT.mkdir(parents=True, exist_ok=True)
ASSETS.mkdir(parents=True, exist_ok=True)

# (internal_test_number, subject label, emoji, qp_glob, sol_glob_or_None)
TESTS = [
    (1,  "Bihar Special",                                  "📜", "Test 1 Question.pdf",                                    "Test 1 English.pdf"),
    (2,  "World Geography",                                "🌍", "Test 2 Question.pdf",                                    "Test 2 English.pdf"),
    (3,  "Current Affairs",                                 "📰", "Test 3 Question.pdf",                                    "Test 3 English.pdf"),
    (4,  "Indian Geography I",                              "🗺️", "Test 4.pdf",                                            "Test 4 English.pdf"),
    (5,  "Indian Geography II",                             "🗺️", "Test 5.pdf",                                            "Test 5 english.pdf"),
    (6,  "Indian Economy",                                  "💰", "Test 6.pdf",                                            None),
    (7,  "Ancient History",                                 "🏛️", "Test 7.pdf",                                            "Test 7 English.pdf"),
    (8,  "Medieval History",                                "🏰", "Test_08_Medieval_History_Question_Paper_*.pdf",          "Test_08_Medieval_History_Solution_English_*.pdf"),
    (9,  "Current Affairs",                                 "📰", "Test 9.pdf",                                            "Test 9 English.pdf"),
    (10, "Biology + Science & Technology",                   "🧬", "Test - 10 __ Biology + Science and Tech __ Question Paper.pdf", "Test_10_Biology_+_Science_and_Tech_Solution_English.pdf"),
    (11, "Modern History I (Arrival of Europeans to 1885)", "📜", "Test_11_Modern_History_1_*Question_Paper.pdf",           "Test_11_*Solution_English.pdf"),
    (12, "Modern History II (1885 to 1947 & onwards)",      "📜", "Test_12_Modern_History_2_*Question_Paper.pdf",           "Test_12_*Solution_English.pdf"),
    (13, "Physics + Chemistry",                             "⚛️", "Test_16_Physics_+_Chemistry_Question_Paper_*.pdf",      "Test_16_Physics_+_Chemistry_Solution_English_*.pdf"),
    (14, "Current Affairs (Jan–Apr 2026)",                  "📰", "Test 14.pdf",                                           "Test 14 english.pdf"),
    (15, "Polity I",                                        "🏛️", "Test 15.pdf",                                           "Test 15 english.pdf"),
]

LIGATURES = {'\ufb00':'ff','\ufb01':'fi','\ufb02':'fl','\ufb03':'ffi','\ufb04':'ffl'}

def resolve(globpat):
    if not globpat: return None
    hits = sorted(glob.glob(str(SRC / globpat)))
    if not hits:
        # try basename match anywhere
        hits = sorted(glob.glob(str(SRC / ("*"+globpat.replace("*","")+"*"))))
    return hits[0] if hits else None

def is_devanagari(ch): return '\u0900' <= ch <= '\u097F'

def english_pages(doc):
    """Return joined text of English (non-Hindi) pages, skipping cover."""
    parts=[]
    for i in range(1, doc.page_count):  # skip cover (page 0)
        t = doc[i].get_text()
        if not t.strip(): continue
        deva = sum(1 for c in t if is_devanagari(c))
        latin = sum(1 for c in t if ('a'<=c.lower()<='z'))
        if deva > 5 and deva > latin*0.15:
            continue  # Hindi page
        parts.append(t)
    return "\n".join(parts)

def clean_text(s):
    if s is None: return ""
    s = s.replace('\r','\n')
    s = ''.join(LIGATURES.get(c,c) for c in s)
    # remove control chars except newline/tab
    s = ''.join(c for c in s if c=='\n' or c=='\t' or unicodedata.category(c)[0]!='C')
    s = s.replace('\u00a0',' ')
    # strip running footers/headers
    s = re.sub(r'(?m)^\s*Paper\s+I\s*/\s*\d+\s*$', '', s)
    # de-hyphenate line breaks
    s = re.sub(r'[-\u2013\u2014]\n(?=[A-Za-z])', '', s)
    # collapse spaces (keep newlines for now)
    lines = [re.sub(r'[ \t]+',' ',ln).strip() for ln in s.split('\n')]
    # drop empty-only lines into paragraph breaks
    out=[]; blank=0
    for ln in lines:
        if ln=='':
            blank+=1
            if blank<=1: out.append('')
        else:
            blank=0; out.append(ln)
    text='\n'.join(out).strip()
    text=re.sub(r'\n{3,}','\n\n',text)
    return text

def join_wrapped(s):
    """Join hard-wrapped lines into flowing text; blank line = paragraph."""
    s=clean_text(s)
    s=re.sub(r'\n{2,}\s*\d{1,2}\s*\n{2,}', ' ', s)
    s=re.sub(r'\n{2,}\s*\d{1,2}\s*$', '', s)
    s=re.sub(r'^\s*\d{1,2}\s*\n{2,}', '', s)
    paras=re.split(r'\n\s*\n', s)
    res=[]
    for p in paras:
        p=re.sub(r'\s*\n\s*',' ',p)
        p=re.sub(r'(^|\n)\s*3\s+(?=\d+[\.\)])', r'\1', p)
        p=re.sub(r'(^|\n)\s*3\s+(?=[A-Za-z\u00C0-\u024F])', r'\1• ', p)
        p=re.sub(r'[^\n\S]+([\.,;:!\?])', r'\1', p)
        p=re.sub(r'\(\s+', '(', p); p=re.sub(r'\s+\)', ')', p)
        p=re.sub(r'\[\s+', '[', p); p=re.sub(r'\s+\]', ']', p)
        p=re.sub(r'(?<![A-Z]\.[A-Z])(?<!\b[A-Za-z]\.[A-Za-z])(?<!\bi\.e)(?<!\be\.g)(?<!\bNo)(?<!\bno)(?<!\bRs)(?<!\bvs)([\.,;:!\?])([A-Za-z])', r'\1 \2', p)
        p=re.sub(r'\s+',' ',p).strip()
        if p: res.append(p)
    return '\n\n'.join(res)

def split_questions(text):
    """Split on '<num>.\\t\\n' question anchors at start of line. Returns dict num->block.

    Match-the-following tables sometimes contain spurious '1.\\t\\n' fragments from
    the two-column layout, which look like question restarts. We therefore choose
    the longest subsequence of anchors that forms a clean 1..N run.
    """
    text = text.replace('\r','\n')
    pat = re.compile(r'(?m)^[ \t]*(\d{1,3})\.\t[ \t]*\n')
    cand=[(int(m.group(1)),m) for m in pat.finditer(text)]
    # Greedy from each anchor numbered '1': pick the next anchor whose number is
    # exactly one greater, skipping out-of-sequence fragments (match-table noise).
    best=[]
    for s in range(len(cand)):
        if cand[s][0]!=1: continue
        chosen=[cand[s][1]]; expected=2; j=s+1
        while j<len(cand):
            if cand[j][0]==expected:
                chosen.append(cand[j][1]); expected+=1
            j+=1
        if len(chosen)>len(best):
            best=chosen
        if len(best)>=150: break
    qs={}
    for idx,m in enumerate(best):
        start=m.end()
        end=best[idx+1].start() if idx+1<len(best) else len(text)
        qs[int(m.group(1))]=text[start:end]
    return qs, len(best)

# Documented corrections for genuine PDF source defects (verified against the
# English solution PDFs). key=(test_number, question_number).
#   prefix:      prepended to the raw block before option parsing.
#   replacements: (old, new) string pairs applied to the raw block.
SOURCE_PATCHES = {
    # Test 5 Q46: option D is mislabeled "1." instead of "D." in the paper.
    (5,46):  {"replacements": [("1.\t Neither 1 nor 2", "D.\t Neither 1 nor 2")]},
    # Test 12 Q96: the question-number anchor "96." is missing in the paper, so
    # the block begins directly with the stem "C. Rajagopalachari Formula...".
    (12,96): {"prefix": "96.\t\n"},
}

def parse_options(block):
    """Return (stem_text, {A:..,B:..,..}) from a question block. Options are lines 'A.<ws>'.

    Some PDFs carry a portal artifact 'E. Unanswered'; it is dropped. We only keep
    A-D (these papers always have four real options).
    """
    opt_pat=re.compile(r'(?m)^[ \t]*([A-E])\.\t?[ \t]?')
    om=list(opt_pat.finditer(block))
    if not om:
        return join_wrapped(block), {}
    stem = block[:om[0].start()]
    opts={}
    for i,m in enumerate(om):
        key=m.group(1)
        if key>'D':  # drop E (Unanswered) and anything beyond
            continue
        s=m.end()
        e=om[i+1].start() if i+1<len(om) else len(block)
        val=join_wrapped(block[s:e])
        if val.strip().lower()=='unanswered':
            continue
        opts[key]=val
    return join_wrapped(stem), opts

# ---- question type taxonomy (controlled strings) ----
def detect_type(stem, options):
    low=stem.lower()
    if re.search(r'assertion\s*\(\s*a\s*\)', low) and re.search(r'reason\s*\(\s*r\s*\)', low):
        return "Assertion and Reason — Standard Relationship Evaluation"
    if re.search(r'match\s+list\s*[-–—]?\s*(?:i|1)\b', low) and re.search(r'list\s*[-–—]?\s*(?:ii|2)\b', low):
        return "Match the Following — Two-List Matching — Answer-Code Matrix"
    has_numbered = bool(re.search(r'(?m)^\s*1[\).]\s+\S', stem)) and bool(re.search(r'(?m)^\s*2[\).]\s+\S', stem))
    if has_numbered:
        if re.search(r'which of the (?:following )?statements? (?:given above )?(?:is|are)\s+incorrect', low) or re.search(r'which of the statements .*incorrect', low):
            return "Multiple Statements — Incorrect Combination by Code"
        if re.search(r'which of the (?:following )?statements? (?:given above )?(?:is|are)\s+correct', low):
            return "Multiple Statements — Correct Combination by Code"
    if re.search(r'\barrange\b', low) and re.search(r'chronolog', low):
        return "Chronological Order — Correct Sequence"
    if re.search(r'\barrange\b', low) or re.search(r'correct\s+order|correct\s+sequence|decreasing order|increasing order|north to south', low):
        return "Ordering/Ranking — Correct Sequence"
    if re.search(r'\bnot\b|\bexcept\b|\bincorrect\b', low):
        return "Negative/Exception MCQ — Single Correct"
    if '____' in stem or '\u2014\u2014' in stem:
        return "Fill in the Blank — Single Correct"
    if re.search(r'\bcalculate\b|\bcomputed?\b|\bvalue of\b|\bhow much\b|\bhow many\b', low):
        return "Numerical/Calculation — Single Correct"
    if re.search(r'study the (?:following )?(?:table|graph|chart|figure|diagram)', low):
        return "Data Interpretation — Single Correct"
    if re.search(r'\bfigure\b|\bdiagram\b|\bgraph\b|\bmap\b', low):
        return "Figure/Diagram/Formula — Single Correct"
    return "Standard MCQ — Direct Factual/Conceptual, Single Correct"

ANS_RE = re.compile(r'Q\s+(\d{1,3})\.[\s\S]{0,120}?Ans\.?\s*[:.]?\s*\(?([A-D])\)?', re.IGNORECASE)
HEADER_RE = re.compile(r'(?im)^.*BPSC\s+(?:PRELIMS\s+)?TEST[-\s]*\d+.*(?:SOLUTION|SOLUTIONS).*$')

def parse_solution(path):
    doc=fitz.open(path)
    full="\n".join(doc[i].get_text() for i in range(doc.page_count))
    full=full.replace('\r','\n')
    full=HEADER_RE.sub('', full)
    ans={}; exp={}
    ms=list(ANS_RE.finditer(full))
    for i,m in enumerate(ms):
        n=int(m.group(1)); letter=m.group(2).upper()
        start=m.end()
        end=ms[i+1].start() if i+1<len(ms) else len(full)
        body=full[start:end]
        # take from 'Explanation' onward if present
        em=re.search(r'Explanation\s*:?', body, re.IGNORECASE)
        body=body[em.end():] if em else body
        ans[n]=letter
        exp[n]=join_wrapped(body)
    return ans, exp

def main():
    report={"book":"kgs_test_series","title":"KGS Test Series","tests":[]}
    all_qtypes={}
    chapters_index=[]
    total_q=0; total_imported=0; total_unverified=0
    all_unverified=[]
    books_entry=None
    for num,subject,emoji,qp_pat,sol_pat in TESTS:
        qp_path=resolve(qp_pat)
        sol_path=resolve(sol_pat) if sol_pat else None
        if not qp_path:
            print(f"!! Test {num}: question paper not found ({qp_pat})"); continue
        doc=fitz.open(qp_path)
        eng=english_pages(doc)
        blocks,maxn=split_questions(eng)
        answers,explanations=({},{})
        if sol_path:
            answers,explanations=parse_solution(sol_path)
        questions=[]; unverified=[]
        for n in range(1,maxn+1):
            block=blocks.get(n)
            if not block:
                unverified.append({"test_number":num,"original_id":n,"reason":"question_not_parsed"}); continue
            patch=SOURCE_PATCHES.get((num,n))
            if patch:
                block=patch.get("prefix","")+block
                for old,new in patch.get("replacements",[]):
                    block=block.replace(old,new)
            stem,opts=parse_options(block)
            if len(opts)!=4 or not stem:
                unverified.append({"test_number":num,"original_id":n,"reason":"options_or_stem_malformed",
                                   "stem":stem[:200],"option_keys":list(opts.keys())}); continue
            ans=answers.get(n)
            if ans and ans not in opts: ans=None
            qtype=detect_type(stem,opts)
            all_qtypes[qtype]=all_qtypes.get(qtype,0)+1
            q={
                "q":stem,
                "question_type":qtype,
                "options":opts,
                "answer":ans if ans else None,
                "explanation":explanations.get(n,"") if ans else "",
                "exam":"72nd BPSC Prelims",
                "year":"2026",
                "note":"" if ans else "No answer key available for this test",
                "original_id":n,
                "test_number":num,
                "test_subject":subject,
            }
            if not ans: unverified.append({"test_number":num,"original_id":n,"reason":"missing_answer","q":stem[:300]})
            questions.append(q)
        # write subject file
        subject_name=f"Test {num} — {subject}"
        data={"subject":subject_name,"chapters":[{"chapter_name":subject,"questions":questions}]}
        fname=f"test_{num}.json"
        (OUT/fname).write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        chapters_index.append({
            "key":f"test_{num}","label":subject_name,"emoji":emoji,"file":fname,
            "chapters":[{"name":subject,"count":len(questions)}]
        })
        total_q+=maxn; total_imported+=len(questions); total_unverified+=len(unverified)
        all_unverified.extend(unverified)
        report["tests"].append({
            "test_number":num,"subject":subject,"file":fname,
            "question_paper":os.path.basename(qp_path),
            "solution":os.path.basename(sol_path) if sol_path else None,
            "questions_parsed":maxn,"questions_written":len(questions),
            "answers_found":len(answers),"unverified":len(unverified),
            "question_types":count_types(questions),
        })
        print(f"Test {num:2d} {subject[:34]:34s} parsed={maxn:3d} written={len(questions):3d} ans={len(answers):3d} unverified={len(unverified)}")
    (OUT/"chapters.json").write_text(json.dumps(chapters_index,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    report["total_questions_parsed"]=total_q
    report["total_valid_imported"]=total_imported
    report["total_unverified"]=total_unverified
    report["subjects"]=len(chapters_index)
    report["question_type_counts"]=dict(sorted(all_qtypes.items()))
    (ROOT/"kgs_import_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (ROOT/"kgs_taxonomy_report.json").write_text(json.dumps(
        {"book":"KGS Test Series","total_questions":total_imported,
         "question_types":dict(sorted(all_qtypes.items()))},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (ROOT/"kgs_unverified_questions.json").write_text(json.dumps(all_unverified,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"\nTOTAL parsed={total_q} imported={total_imported} unverified={total_unverified}")
    print("Wrote", OUT)

def count_types(qs):
    c={}
    for q in qs: c[q["question_type"]]=c.get(q["question_type"],0)+1
    return c

if __name__=="__main__":
    main()
