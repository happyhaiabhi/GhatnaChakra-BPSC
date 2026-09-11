#!/usr/bin/env python3
"""Study-unit curriculum for the UPSC Polity + Geography 6-hr/day sprint.

One *unit* = one topic cluster identified by scripts/analyse_polity_geo_pyqs.py
(unit ids P01-P24 / G01-G24 are shared between the two scripts).  A unit is
broken into 100-minute *blocks*; scripts/build_pg_sprint_plan.py derives the
block count as

    blocks = max(1, ceil(pages / PAGES_PER_BLOCK), ceil(prelims_last10 / PYQ_PER_BLOCK))

so a topic earns more time when it is long in the book OR heavy in the last ten
Prelims papers - and never less than one block.

  pages  first-reading volume in the locked source
         (Laxmikanth 6th ed for polity; NCERT XI-XII + G.C. Leong + Atlas for geography)
  focus  what must be retrievable at the end of the unit
  traps  the classic "which is NOT correct" traps for that unit
  mains  the recurring Mains demand, used from Sprint 3 onwards

Content is deliberately factual and citation-light: the plan is a *schedule*,
not a textbook. Verify anything time-sensitive (Ramsar counts, tiger numbers,
scheme details) against the current monthly compilation on the day you study it.
"""
from __future__ import annotations

POLITY: list[dict] = [
    dict(id="P07", pages=95,
         focus="LS/RS composition and their exclusive powers (RS: Art 249 national-interest resolution, Art 312 All India "
               "Service; LS: money bills, no-confidence, budget); sessions and the 6-month maximum gap; Question Hour vs "
               "Zero Hour; the motion family (no-confidence, censure, adjournment, calling-attention, privilege, "
               "half-an-hour, special mention, motion of thanks); parliamentary privileges under Art 105 (individual and "
               "collective, still uncodified); joint sitting Art 108; anti-defection under the 10th Schedule; quorum of "
               "1/10; casting vote; pro tem Speaker.",
         traps="No joint sitting for Money Bills or Constitution Amendment Bills; the RS Chairman never presides over a "
               "joint sitting; a no-confidence motion lies only in the LS and needs 50 members' support; RS is not subject "
               "to dissolution (one-third retire every two years); privileges are still not codified by statute.",
         mains="Parliamentary productivity and disruption; privileges vs press freedom; role of the Opposition; "
               "declining sitting days; committee scrutiny of bills."),
    dict(id="P03", pages=70,
         focus="Six Fundamental Rights (property removed by the 44th); Art 12 definition of State; Art 13; Arts 14-18 "
               "(titles abolished); Art 19 six freedoms with reasonable restrictions; Arts 20-22 (no double jeopardy, no "
               "self-incrimination, preventive detention limits); Art 21 and its expansion (privacy - Puttaswamy 2017, "
               "dignity, health, clean environment); Arts 25-28; Arts 29-30; Art 32 and the five writs; citizens-only "
               "rights (15, 16, 19, 29, 30).",
         traps="Art 19 is suspended automatically only during war/external aggression (44th Amendment); Arts 20-21 can "
               "never be suspended; Right to Property is now a legal right under Art 300A; habeas corpus lies against "
               "private detention too; mandamus does not lie against the President, a Governor or a purely private body; "
               "certiorari and prohibition run only against judicial/quasi-judicial authorities; Art 32 (SC) is narrower "
               "than Art 226 (HC).",
         mains="Right to privacy and surveillance; free speech vs sedition and hate speech; preventive detention; "
               "internet shutdowns (Anuradha Bhasin 2020); minority rights."),
    dict(id="P23", pages=30,
         focus="A rolling scheme register - name, ministry, year, target group, funding pattern (Centrally Sponsored vs "
               "Central Sector). Flagships: MGNREGA (a statutory right, 60:40 wage-material, unemployment allowance of "
               "1/4 wage, social audit by the Gram Sabha), PM-KISAN, PM-JAY, PMAY-G/U, Jal Jeevan Mission. Report and "
               "publisher pairs: NFHS (IIPS, MoHFW), ASER (Pratham), SDG India Index (NITI Aayog), State of Forest Report "
               "(FSI, biennial), PLFS (NSO), ADSI (NCRB), World Economic Outlook (IMF).",
         traps="Centrally Sponsored (shared) vs Central Sector (100% Centre) schemes; MGNREGA is demand-driven and a "
               "legal right, not a discretionary welfare scheme; NFHS is run by IIPS, ASER by Pratham, the SDG Index by "
               "NITI Aayog; 'launched by' answers change every year - re-verify against the latest compilation.",
         mains="Last-mile welfare delivery and exclusion errors; DBT and JAM; cooperative vs competitive federalism in "
               "scheme design."),
    dict(id="P12", pages=45,
         focus="Composition (maximum 34 judges); the collegium (CJI + four seniormost) and the Memorandum of Procedure; "
               "NJAC struck down in 2015; jurisdictions - original (Art 131), writ (Art 32), appellate (Arts 132-136), "
               "special leave, advisory (Art 143), court of record (Art 129), review (Art 137), curative (Rupa Hurra "
               "2002); Art 142 complete justice; contempt powers; independence safeguards (retirement at 65, salary "
               "charged, removal by special majority after a three-member inquiry); Master of the Roster; Constitution "
               "Benches of five or more judges.",
         traps="Art 32 protects only Fundamental Rights while Art 226 extends to 'any other purpose'; an advisory opinion "
               "does not bind the President; a retired SC judge cannot practise anywhere in India; the removal ground is "
               "proved misbehaviour or incapacity.",
         mains="Pendency, vacancies and the AIJS demand; collegium transparency; judicial activism vs overreach; "
               "live-streaming and case-listing reform."),
    dict(id="P24", pages=35,
         focus="Rule of law (Dicey's three pillars, Art 14 as its Indian form, Art 361 immunity as an exception); "
               "separation of powers and checks and balances (Ram Jawaya Kapur 1955); constitutionalism; 'procedure "
               "established by law' (A.K. Gopalan 1950) transformed into due process by Maneka Gandhi 1978 (just, fair "
               "and reasonable); doctrines - severability, eclipse, waiver (no waiver of FR), colourable legislation, pith "
               "and substance, harmonious construction.",
         traps="Rule of law and judicial review are basic structure, so Parliament cannot abrogate them; due process is "
               "now read into Art 21; constitutionalism is not the same as merely having a constitution; Arts 19 and 21 "
               "are read together, not in isolation.",
         mains="Constitutional morality; liberty vs security; the basic structure doctrine at 50; delegated legislation "
               "and tribunals."),
    dict(id="P10", pages=40,
         focus="Appointment of the PM (Art 75 - the President appoints the member most likely to command a majority); "
               "collective responsibility to the LS (Art 75(3)) and individual responsibility to the President; Council of "
               "Ministers vs Cabinet vs kitchen cabinet; Art 78 (the PM's duty to communicate); Cabinet Committees; "
               "Attorney General under Art 76 (not a full-time government servant, right of audience in all courts, may "
               "speak in Parliament but not vote).",
         traps="A minister must become an MP within six months or cease to hold office; the PM's resignation dissolves the "
               "whole Council; the AG holds office during the President's pleasure with no fixed term; 'Cabinet' is not "
               "defined in the Constitution.",
         mains="Coalition dharma and government stability; the growth of the PMO and groups of ministers; "
               "cabinet government in practice."),
    dict(id="P14", pages=60,
         focus="Quasi-federal design; the three lists of the 7th Schedule and residuary powers (Art 248); Parliament in "
               "the state field - Arts 249 (national interest), 250 (emergency), 252 (two or more states), 253 (treaties), "
               "356; Inter-State Council under Art 263 (set up 1990 on the Sarkaria recommendation); Zonal Councils "
               "(statutory, States Reorganisation Act 1956) and the North Eastern Council (1971); Finance Commission "
               "(Art 280); GST Council (Art 279A - chaired by the Union FM, decisions by a three-fourths weighted "
               "majority, Centre one-third and states two-thirds); UTs under Arts 239, 239AA, 239AB; NITI Aayog (2015, by "
               "executive resolution - neither constitutional nor statutory); inter-state river disputes (Art 262).",
         traps="The Inter-State Council is constitutional but NITI Aayog and the Zonal Councils are not; new states can be "
               "created by a simple majority under Arts 2-3, not by constitutional amendment; GST Council recommendations "
               "are persuasive rather than binding (SC 2022); the Finance Commission only recommends; NITI Aayog cannot "
               "allocate funds.",
         mains="Governor-CM friction; cess and surcharge outside devolution; asymmetric federalism; Delhi's LG-CM "
               "conflict; river-water tribunals; one nation one election."),
    dict(id="P17", pages=65,
         focus="Election Commission (Art 324 - CEC plus two ECs; the CEC can be removed only like a Supreme Court judge; "
               "the Chief Election Commissioner and Other Election Commissioners Act 2023 changed the selection panel to "
               "PM + a Union Minister + Leader of Opposition); UPSC and SPSCs (Arts 315-323, advisory); CAG (Arts "
               "148-151, six years or 65 years, reports to the President); Attorney General (Art 76); Finance Commission "
               "(Art 280, five members, constituted every fifth year); NCSC and NCST (Arts 338, 338A) and NCBC (Art 338B, "
               "made constitutional by the 102nd Amendment; the 105th restored state power over SEBC lists); Special "
               "Officer for Linguistic Minorities (Art 350B).",
         traps="The ECI does not conduct panchayat or municipal elections - State Election Commissions do (Arts 243K, "
               "243ZA); Finance Commission recommendations are not binding; UPSC and SPSC reports are advisory; ECs can be "
               "removed only on the CEC's recommendation; NCBC is constitutional while the National Commission for "
               "Minorities is statutory.",
         mains="ECI independence and the appointment law; the Finance Commission and state finances; CAG and "
               "accountability; delimitation after the freeze ends."),
    dict(id="P11", pages=70,
         focus="The Governor's dual role (constitutional head and Centre's agent); appointment by the President and "
               "removal at pleasure (no impeachment); discretionary situations; ordinance power (Art 213); assent options "
               "under Art 200 (assent, withhold, reserve for the President); creation of a Legislative Council under "
               "Art 169 (LS special majority, not a constitutional amendment); Advocate General (Art 165); State Finance "
               "and State Election Commissions; Lieutenant Governors and Administrators in UTs (Art 239AA Delhi, "
               "Art 239AB, Art 239A Puducherry).",
         traps="A Governor cannot pardon a death sentence - only the President can (Art 72); a bill reserved for the "
               "President does not lapse on dissolution of the assembly; Anglo-Indian nomination to legislatures was "
               "abolished by the 104th Amendment; the Governor holds no fixed tenure and may be transferred.",
         mains="Misuse of the Governor's office; floor tests and the Bommai standard; bills kept pending or reserved; "
               "Punchhi and Sarkaria recommendations; Delhi and Puducherry LG-CM conflict."),
    dict(id="P06", pages=55,
         focus="Presidential election - electoral college of elected MPs plus elected MLAs/MLCs of states and UTs with "
               "legislatures, vote-value arithmetic, proportional representation by single transferable vote, secret "
               "ballot, disputes decided by the Supreme Court; impeachment under Art 61 (one-fourth of members give "
               "notice, 14 days, two-thirds of the total membership of either House); pardoning power under Art 72 "
               "(pardon, reprieve, respite, remit, commute - judicial review available on limited grounds, Epuru "
               "Sudhakar); veto types (absolute, suspensive, pocket; none over constitutional amendment bills after the "
               "24th Amendment); ordinance power under Art 123 (same force as an Act, six weeks from reassembly, cannot "
               "amend the Constitution); Vice-President (ex-officio RS Chairman, elected by members of both Houses "
               "including nominated members).",
         traps="Nominated members vote for the Vice-President but not for the President; the President may ask the Council "
               "to reconsider advice once (44th Amendment) but is then bound; a Governor cannot pardon a death sentence; "
               "the pocket veto has no time limit; an ordinance cannot amend the Constitution.",
         mains="Ordinance-making as legislative bypass; delays and transparency in pardoning petitions; "
               "the President's role in a hung Parliament."),
    dict(id="P20", pages=30,
         focus="Fifth Schedule (Scheduled Areas in states other than the four Sixth-Schedule states; the President may "
               "modify areas and statutes; Tribes Advisory Council of up to 20 members; the Governor's annual report); "
               "Sixth Schedule (Assam, Meghalaya, Tripura, Mizoram - Autonomous District Councils with legislative, "
               "judicial and financial powers, subject to the Governor's assent); Forest Rights Act 2006 (individual and "
               "community rights, claims initiated by the Gram Sabha, critical wildlife habitat); Arts 29 and 30; the end "
               "of Anglo-Indian representation (104th Amendment); the National Commission for Minorities (statutory, "
               "1992) and its notified communities.",
         traps="The Sixth Schedule covers only Assam, Meghalaya, Tripura and Mizoram; Tribes Advisory Councils exist in "
               "Fifth-Schedule areas while ADCs exist in Sixth-Schedule areas; FRA claims start with the Gram Sabha, not "
               "the forest department; Art 30 rights are subject to reasonable regulation.",
         mains="FRA implementation and gram sabha consent; PESA and tribal self-governance; minority institutions and "
               "Art 30; tribal land alienation."),
    dict(id="P01", pages=45,
         focus="Constituent Assembly timeline (Cabinet Mission Plan 1946; first meeting 9 December 1946; Objectives "
               "Resolution 13 December 1946 moved by Nehru; Drafting Committee 29 August 1947; adopted 26 November 1949; "
               "commenced 26 January 1950); borrowings (UK - parliamentary system, rule of law; US - Fundamental Rights, "
               "judicial review, impeachment; Ireland - DPSP; Canada - strong Centre and residuary powers; Australia - "
               "concurrent list and joint sitting; Weimar Germany - emergency suspension of rights; USSR - Fundamental "
               "Duties; Japan - procedure established by law; France - republic and liberty-equality-fraternity; South "
               "Africa - amendment procedure); the Preamble's wording and the three words added by the 42nd Amendment; "
               "salient features (one Constitution, single citizenship, integrated judiciary).",
         traps="Berubari (1960) held the Preamble is not part of the Constitution; Kesavananda (1973) and LIC (1995) held "
               "it is; the Preamble is amendable under Art 368 but not enforceable in a court; 'socialist' and 'secular' "
               "were added in 1976, not 1950; the Constituent Assembly was indirectly elected, partly nominated.",
         mains="Constitutional morality and the founding compact; 75 years of the Constitution; the basic structure."),
    dict(id="P04", pages=40,
         focus="DPSP classification (socialist, Gandhian, liberal-intellectual) and the key articles (38, 39, 39A, 40, "
               "41, 42, 43, 43A, 44, 45, 46, 47, 48, 48A, 49, 50, 51); post-1976 additions (39A legal aid, 43A workers' "
               "participation, 48A environment); the 86th Amendment moved education into Art 21A and recast Art 45 as "
               "early childhood care; Fundamental Duties in Art 51A (42nd Amendment on the Swaran Singh Committee's "
               "advice, the eleventh added by the 86th); non-justiciability; FR-DPSP conflicts and harmonious "
               "construction (Art 31C, Minerva Mills).",
         traps="Neither DPSP nor Fundamental Duties are enforceable by courts, but Parliament may legislate to give "
               "duties legal sanction; Art 45 today is early childhood care, not education; 'to develop scientific "
               "temper' is a duty, not a directive; the UCC in Art 44 is a directive, not a right.",
         mains="The FR-DPSP balance; the Uniform Civil Code debate; Fundamental Duties and citizenship education."),
    dict(id="P16", pages=55,
         focus="73rd Amendment (in force 24 April 1993) - three tiers, Gram Sabha of all registered voters, direct "
               "election to seats, indirect election of chairpersons at block and district levels, SC/ST reservation by "
               "population ratio, one-third reservation for women, five-year term, State Election Commission, State "
               "Finance Commission, District Planning Committee (Art 243ZD), 11th Schedule (29 subjects); 74th Amendment "
               "- Nagar Panchayat, Municipal Council, Municipal Corporation, Ward Committees above three lakh, "
               "Metropolitan Planning Committee (Art 243ZE), 12th Schedule (18 subjects); PESA 1996 in Fifth-Schedule "
               "areas of ten states; SVAMITVA scheme and e-GramSwaraj.",
         traps="PESA applies to Fifth-Schedule areas, not to Sixth-Schedule ADC areas; the State Election Commissioner can "
               "be removed only like a High Court judge; the Gram Sabha is the village electorate, not its elected "
               "representatives; constitutional reservation for women in local bodies is one-third, though many states "
               "have moved to half.",
         mains="Devolution of funds, functions and functionaries; women's leadership in PRIs; the Gram Sabha as direct "
               "democracy; urban local bodies' fiscal capacity."),
    dict(id="P02", pages=55,
         focus="The twelve Schedules and the amendments that added the ninth (1st, land reforms), tenth (52nd, "
               "anti-defection), eleventh (73rd, panchayats) and twelfth (74th, municipalities); citizenship under Arts "
               "5-11 and the Citizenship Act 1955 (acquisition, loss, single citizenship, CAA 2019, NPR and NRC); "
               "official language provisions (Art 343 Hindi in Devanagari, Arts 344-351, the 22 languages of the 8th "
               "Schedule, classical-language criteria); Union and its territory under Arts 1-4.",
         traps="Laws in the Ninth Schedule ceased to be immune after IR Coelho (2007) for entries made after 24 April "
               "1973; the Sixth Schedule covers only four states; classical-language status is conferred by the Union "
               "government on expert recommendation; Parliament's power under Art 3 needs only a simple majority and the "
               "state legislature's view is advisory.",
         mains="CAA-NRC-NPR; language policy and the three-language formula; boundary reorganisation and federalism."),
    dict(id="P19", pages=30,
         focus="RPA 1950 (registration, delimitation, rolls) and RPA 1951 (conduct, qualifications, disqualifications, "
               "offences); Section 8 disqualifications on conviction and Lily Thomas (2013) striking down the saving "
               "clause; Section 10A election accounts; Section 123 corrupt practices; electoral bonds (struck down by the "
               "Supreme Court in February 2024 as violative of Art 19(1)(a)); EVM and VVPAT; NOTA (2013); the Model Code "
               "of Conduct; delimitation frozen on the 2001 census until the first census after 2026.",
         traps="The Model Code of Conduct has no statutory backing; electoral bonds no longer exist; a candidate may "
               "contest from at most two constituencies; disqualification under the 10th Schedule is decided by the "
               "Speaker while RPA disqualification runs through the President on the ECI's opinion; election petitions "
               "go to the High Court.",
         mains="The electoral-reform agenda; criminalisation of politics; state funding of elections; "
               "one nation one election; EVM credibility."),
    dict(id="P15", pages=30,
         focus="National Emergency (Art 352 - war, external aggression, armed rebellion; written Cabinet advice; one "
               "month then Parliament's special majority, renewable every six months; revocation by simple majority; one "
               "tenth of LS members can force a special sitting); effects under Arts 358 and 359 (Art 19 suspended "
               "automatically only for war or external aggression; Arts 20-21 can never be suspended); President's Rule "
               "(Art 355 duty, Art 356 power - two months, three years maximum, S.R. Bommai 1994); Financial Emergency "
               "(Art 360, never proclaimed).",
         traps="Arts 20-21 are beyond suspension; 'internal disturbance' was deleted as a ground by the 44th Amendment; "
               "President's Rule does not automatically dissolve the assembly; a Financial Emergency has never been used; "
               "proclamations are justiciable after the 44th Amendment.",
         mains="Federal consequences of President's Rule; Art 355 duty vs Art 356 power; floor tests and the Bommai "
               "standard."),
    dict(id="P18", pages=45,
         focus="NHRC (Protection of Human Rights Act 1993; chairperson a retired CJI or SC judge; suo motu cognisance; "
               "recommendatory only); NCW; Central and State Information Commissions under the RTI Act 2005; Lokpal and "
               "Lokayuktas Act 2013 (chairperson a former CJI or SC judge, eight members, half judicial); CVC (statutory "
               "2003, advisory); CBI (works under the DSPE Act 1946 and needs a state's consent under Section 6); Law "
               "Commission (non-statutory); NITI Aayog; National Development Council; NABARD (1981 Act); SEBI (1992); "
               "National Green Tribunal (2010); Central Administrative Tribunal (1985).",
         traps="The CBI needs a state's consent to investigate inside that state; the NHRC and the Lokpal can only "
               "recommend; the Law Commission is neither constitutional nor statutory; the CVC is statutory but the CBI's "
               "origin is an executive order under the DSPE Act; the NGT is a statutory tribunal, not a constitutional "
               "court.",
         mains="The Lokpal's effectiveness and delayed appointments; NHRC accreditation under the Paris Principles; "
               "CBI federalism and consent withdrawals; RTI transparency."),
    dict(id="P08", pages=60,
         focus="Four kinds of bills (ordinary, money under Art 110, financial under Art 117, constitutional amendment); "
               "stages of an ordinary bill including the committee stage; deadlock and the joint sitting; money-bill "
               "certification by the Speaker (final) and the RS's fourteen-day limit; the financial cycle - annual "
               "financial statement (Art 112), demands for grants, cut motions (policy, economy, token), the guillotine, "
               "appropriation and finance bills, vote on account, excess and supplementary grants; Consolidated Fund "
               "(Art 266(1)), Contingency Fund (Art 267) and Public Account (Art 266(2)); charged vs voted expenditure.",
         traps="A money bill cannot originate in the RS and needs the President's prior recommendation; the President "
               "cannot return a money bill for reconsideration; a bill pending in the RS but not passed by the LS does not "
               "lapse on dissolution, while one pending in the LS does; a bill awaiting assent never lapses; cut motions "
               "lie only in the LS.",
         mains="Budgetary accountability and the guillotine; passing the budget without discussion; cess and surcharge "
               "outside devolution; parliamentary scrutiny of expenditure."),
    dict(id="P22", pages=30,
         focus="All India Services under Art 312 (IAS, IPS, IFoS - recruited by the UPSC, controlled jointly, discipline "
               "with the Centre's concurrence); Art 311 safeguards; Central services; the Central Administrative "
               "Tribunal; Cabinet Secretariat, PMO and DoPT; Second ARC reports (Right to Information, Ethics in "
               "Governance, Citizen-Centric Administration, e-Governance); social audit; DBT and the JAM trinity; "
               "CPGRAMS; state Right to Service Acts.",
         traps="Art 311 protection does not extend to defence personnel; states cannot recruit to the All India Services; "
               "CAT decisions are appealable to High Courts after L Chandra Kumar (1997); the Cabinet Secretary chairs "
               "the Civil Services Board.",
         mains="Civil-services reform and lateral entry; generalist vs specialist; bureaucratic neutrality; "
               "e-governance and citizen services."),
    dict(id="P21", pages=35,
         focus="Bharatiya Nyaya Sanhita 2023 (replaces the IPC; adds terrorism and organised crime; sedition replaced by "
               "offences endangering sovereignty, unity and integrity; mob lynching and hit-and-run penalties; community "
               "service as a new punishment); Bharatiya Nagarik Suraksha Sanhita 2023 (replaces the CrPC; Zero FIR and "
               "e-FIR made statutory; handcuffing permitted in defined cases; trials in absentia; timelines for judgment; "
               "police custody within the first forty or sixty days); Bharatiya Sakshya Adhiniyam 2023 (replaces the "
               "Evidence Act; electronic records as primary evidence; DNA evidence); RTI Act 2005 (Sections 4, 8, "
               "two-tier appeal); RTE Act 2009 with Art 21A; Juvenile Justice Act 2015; POCSO 2012.",
         traps="The BNS retains capital punishment; the BNSS allows police custody in parts within the first forty or "
               "sixty days; sedition was renamed and narrowed, not abolished; Zero FIR and e-FIR are now statutory; the "
               "RTE no-detention rule was reversed by the 2019 amendment.",
         mains="Criminal-law reform and due process; police reform (Prakash Singh); undertrials and bail reform; "
               "trial in absentia and fair-trial standards."),
    dict(id="P13", pages=40,
         focus="High Courts (Arts 214-231; appointment of the Chief Justice after consultation with the CJI and the "
               "Governor; writ jurisdiction under Art 226 is wider than Art 32; superintendence under Art 227; court of "
               "record under Art 215; retirement at 62); the subordinate judiciary (Art 233 district judges appointed by "
               "the Governor; Art 235 control vested in the High Court); tribunals under Arts 323A-323B and L Chandra "
               "Kumar (1997) on judicial review as basic structure; Lok Adalats (Legal Services Authorities Act 1987); "
               "Gram Nyayalayas Act 2008; e-Courts; legal aid under Art 39A with NALSA and DLSAs.",
         traps="A retired High Court judge cannot practise in the court where he served or in any court except the Supreme "
               "Court; tribunals cannot replace High Court judicial review; a High Court's writ power is wider than the "
               "Supreme Court's; district judges are appointed by the Governor, not the High Court.",
         mains="Pendency and arrears; tribunal reform; legal aid and access to justice; the All India Judicial Service; "
               "digital courts."),
    dict(id="P09", pages=30,
         focus="Public Accounts Committee (22 members - 15 LS and 7 RS; chairperson from the Opposition by convention "
               "since 1967; examines CAG reports; cannot fix responsibility); Estimates Committee (30 members, all from "
               "the LS; chairperson from the ruling party; a post-mortem of the budget); Committee on Public Undertakings "
               "(15 members - 10 LS and 5 RS); 24 Departmentally Related Standing Committees of 45 members each (30 LS, "
               "15 RS); Business Advisory Committee; Committee on Privileges; Committee on Subordinate Legislation; "
               "Ethics Committees; ad hoc Joint Parliamentary Committees; ministry-wise Consultative Committees; Action "
               "Taken Reports.",
         traps="A minister cannot be a member of the PAC or the Estimates Committee; the Estimates Committee has no RS "
               "members; the PAC chairperson convention is not a rule; referring a bill to a DRSC is discretionary; "
               "committee recommendations do not bind the government.",
         mains="Fewer bills referred to committees and weak scrutiny; strengthening the PAC and Estimates Committee; "
               "committee-based budgeting."),
    dict(id="P05", pages=25,
         focus="Art 368 procedure - introduction in either House, special majority (a majority of total membership plus "
               "two-thirds of those present and voting), ratification by half the state legislatures for federal "
               "provisions, mandatory presidential assent after the 24th Amendment, no joint sitting; the three majority "
               "types; the basic structure line of cases - Shankari Prasad 1951, Sajjan Singh 1965, Golaknath 1967, 24th "
               "Amendment 1971, Kesavananda Bharati 1973, Indira Gandhi v Raj Narain 1975, Minerva Mills 1980, Waman Rao "
               "1981, IR Coelho 2007.",
         traps="Only Parliament can amend the Constitution; state legislatures cannot initiate amendments; the President "
               "must give assent; no joint sitting is possible for amendment bills; Ninth Schedule laws added after 24 "
               "April 1973 are open to review.",
         mains="The basic structure doctrine at 50; judicial review of amendments; the NJAC verdict; federal provisions "
               "and state ratification."),
]

GEOGRAPHY: list[dict] = [
    dict(id="G22", pages=50,
         focus="Daily atlas drill: seas with their bordering countries (Adriatic, Aegean, Ionian, Tyrrhenian, Ligurian, "
               "Black Sea's six states, the Caspian's five, the Red Sea's six, the Persian Gulf's eight, the Baltic's "
               "nine); conflict and news regions (Donbas, Kachin, Tigray, Nagorno-Karabakh, Golan, West Bank, Gaza, "
               "Sinai, Wakhan); landlocked countries by continent, with Uzbekistan doubly landlocked; capitals; "
               "memberships (EU, NATO, ASEAN, SCO, BRICS, OPEC, BIMSTEC, GCC, Organization of Turkic States); border "
               "lines (Radcliffe, McMahon, Durand, 38th parallel, Line of Actual Control); sequencing tasks - cities "
               "south to north, rivers west to east, ranges north to south.",
         traps="Croatia, Montenegro and Slovenia border the Adriatic, not the Aegean; the Caspian is legally a lake "
               "treated as a sea by the 2018 Aktau convention; Uzbekistan is doubly landlocked; Moldova is not a Black "
               "Sea littoral state; membership lists change - check the latest before every test.",
         mains="Supports IR and mapping questions rather than a direct Mains demand."),
    dict(id="G24", pages=45,
         focus="The climate regime - UNFCCC, Kyoto Protocol (Annex I binding targets), Paris Agreement (NDCs, the 1.5-2 "
               "degreeC goal, global stocktake, Article 6 markets) and recent COP outcomes including the Loss and Damage "
               "Fund (agreed at COP27, operationalised at COP28); India's targets (net zero by 2070, 500 GW non-fossil "
               "capacity by 2030, a 45% cut in emission intensity of GDP, the National Green Hydrogen Mission); carbon "
               "markets and the Carbon Credit Trading Scheme; pollution governance (NAQI, the National Clean Air "
               "Programme, e-waste and plastic-waste rules, single-use plastic ban); ozone (Montreal Protocol, Kigali "
               "Amendment on HFCs); disaster management under the DM Act 2005 (NDMA chaired by the PM, SDMA, DDMA, NDRF), "
               "the Sendai Framework 2015-2030 and the India-led CDRI.",
         traps="The Loss and Damage Fund was agreed at COP27 and operationalised at COP28, hosted by the World Bank; "
               "Kyoto's binding targets applied only to Annex I countries; the Kigali Amendment targets HFCs, which are "
               "climate rather than ozone-depleting substances; CDRI is India-led but not a UN body; cyclone names come "
               "from WMO/ESCAP member panels, not from IMD alone.",
         mains="Climate justice and CBDR-RC; India's climate diplomacy; disaster resilience; air-quality governance; "
               "green growth vs growth."),
    dict(id="G15", pages=60,
         focus="Cropping seasons (kharif, rabi, zaid) and ICAR agro-climatic zones; crop requirements and leading states "
               "for rice, wheat, millets (2023 was the International Year of Millets), pulses, oilseeds, sugarcane, "
               "cotton, jute, tea, coffee and spices; the colour revolutions (White - Operation Flood, Blue, Pink, "
               "Golden, Evergreen, Yellow - oilseeds); GM crops (Bt cotton the only approved commercial crop, GM mustard "
               "DMH-11, GEAC under MoEFCC); MSP mechanics (A2, A2+FL and C2 costs, 23 crops, the CACP); the Agricultural "
               "Census 2015-16 (86% small and marginal holdings, average holding 1.08 hectares); dryland farming and the "
               "watershed approach; natural and organic farming (Paramparagat Krishi Vikas Yojana, Sikkim as the first "
               "fully organic state).",
         traps="Groundnut is grown in both kharif and rabi; Gujarat leads groundnut while Madhya Pradesh leads pulses and "
               "soybean; Assam leads tea by area; India is the largest producer of milk, pulses, jute and spices but also "
               "the largest importer of pulses; MSP is announced for 23 crops yet procurement is concentrated in wheat "
               "and rice; the C2 cost, not A2+FL, includes rent and interest on owned capital.",
         mains="Cropping-pattern diversification away from rice-wheat; MSP and its fiscal trade-offs; food security and "
               "PDS reform; climate-resilient agriculture; GM crop regulation; land fragmentation and FPOs."),
    dict(id="G09", pages=60,
         focus="The six physiographic divisions; the Himalayas - Trans-Himalaya (Karakoram with K2), Himadri/Great "
               "(Kanchenjunga, India's highest), Himachal/Middle (Pir Panjal, Dhauladhar) and the Shiwaliks (dun valleys, "
               "landslide-prone); syntaxial bends at Nanga Parbat and Namcha Barwa; passes and what they cross (Shipki La "
               "- Sutlej, Mana - Alakananda, Lipulekh, Nathu La, Zoji La, Banihal, Khardung La, Bhor Ghat, Pal Ghat); the "
               "northern plains (Bhabar, Terai, Bhangar with kankar, Khadar, doabs, Majuli the largest river island); the "
               "Peninsular plateau (Deccan Trap basalt, Chotanagpur, Malwa, Bundelkhand, the Meghalaya plateau separated "
               "by the Malda gap); the Western Ghats (a continuous escarpment, Anaimudi the highest peak of the south) "
               "vs the Eastern Ghats (discontinuous, lower); the Aravalli as an old residual range; the Vindhya and "
               "Satpura block ranges with the Narmada rift valley; coastal plains (Konkan with creeks and rias, Malabar "
               "with backwaters, Coromandel wide with deltas and lagoons); the Thar; the Andaman and Nicobar (volcanic "
               "and coral, Barren Island India's only active volcano, Saddle Peak, Indira Point) and Lakshadweep (36 "
               "coral islands, Kavaratti headquarters, Minicoy, the Duncan Passage); BIS seismic zones V to II.",
         traps="K2 is higher than Kanchenjunga but lies in Pakistan-administered territory; the Western Ghats are an "
               "escarpment and are continuous, the Eastern Ghats are discontinuous and lower; the Aravalli is residual, "
               "not young; Narmada and Tapi flow in rift valleys and form estuaries, not deltas; Barren is active while "
               "Narcondam is dormant; Lakshadweep is coral and the Andamans are volcanic plus coral.",
         mains="Himalayan carrying capacity (Char Dham, Joshimath subsidence); coastal-zone regulation; the Western Ghats "
               "and the Gadgil-Kasturirangan reports; disaster vulnerability by region."),
    dict(id="G03", pages=55,
         focus="Atmospheric composition and the layers with their signatures (troposphere and weather, lapse rate 6.5 "
               "degreeC per km, tropopause highest at the equator; stratosphere and the ozone layer; mesosphere the "
               "coldest with meteors burning; thermosphere and the ionosphere; exosphere); insolation and the heat budget "
               "in NCERT's 100-unit accounting; Earth's albedo of about 30%; factors affecting insolation; temperature "
               "distribution and isotherms; annual range highest in continental interiors; normal, dry and saturated "
               "adiabatic lapse rates; types of temperature inversion and their consequences (fog, smog, frost, trapped "
               "pollution); greenhouse gases and global warming potential; urban heat islands.",
         traps="The mesosphere, not the thermosphere, is the coldest layer; ozone sits in the stratosphere; the hottest "
               "belt shifts north of the equator in the northern summer; water vapour is the most abundant greenhouse gas "
               "while CO2 is the largest anthropogenic contributor; inversion means temperature rising with height, and it "
               "suppresses convection.",
         mains="Urban heat islands and city climate action; heat-wave governance; greenhouse-gas accounting; "
               "communicating climate science."),
    dict(id="G17", pages=45,
         focus="Mineral classification (ferrous, non-ferrous, non-metallic, energy); iron ore grades (haematite, "
               "magnetite, limonite, siderite) and the Odisha-Chhattisgarh-Karnataka-Jharkhand belt; coal (Gondwana "
               "coalfields of the Damodar, Mahanadi and Godavari basins hold almost all reserves; tertiary coal in the "
               "north-east; Jharia for coking coal; lignite at Neyveli; coal gasification policy); petroleum and gas "
               "(Mumbai High offshore, Barmer onshore, the KG basin, Assam and Gujarat fields; coastal vs inland "
               "refineries and why they sit where they do); nuclear minerals (uranium at Jaduguda and Tummalapalle, "
               "thorium-bearing monazite in the Kerala and Tamil Nadu beach sands, the three-stage programme); renewables "
               "(Bhadla and Pavagada solar parks, Muppandal wind farm, the International Solar Alliance headquartered at "
               "Gurugram, the National Green Hydrogen Mission); critical minerals and the 2023 list; the lithium find at "
               "Reasi.",
         traps="Odisha has both the largest reserves and the largest production of iron ore; Jharia has the best coking "
               "coal and long-running mine fires; Neyveli is lignite, not bituminous coal; Khetri in Rajasthan is copper "
               "while zinc comes from Zawar; Malanjkhand in Madhya Pradesh is the largest copper deposit; monazite is the "
               "thorium source; India belongs to the MTCR, the Wassenaar Arrangement and the Australia Group but not the "
               "NSG.",
         mains="Energy security and import dependence; coal phase-down vs development; critical minerals and supply "
               "chains; renewable integration and storage; mining's environmental and tribal costs."),
    dict(id="G16", pages=45,
         focus="Irrigation status (groundwater supplies about 60% of irrigated area, canals about 28%); methods "
               "(canals, tanks, wells and tube-wells, micro-irrigation saving 55-75% water) and PMKSY's twin components "
               "(Har Khet Ko Pani, Per Drop More Crop); major canals including the Indira Gandhi Canal from the Harike "
               "barrage; multipurpose projects (Bhakra-Nangal, Hirakud the longest earthen dam, Sardar Sarovar, "
               "Nagarjuna Sagar, Mettur, Tehri the highest dam, Koyna, Idukki India's first arch dam, Polavaram a "
               "national project); river interlinking and the Ken-Betwa project as the first approved link; groundwater "
               "governance (CGWB monitoring, over-exploited blocks, Atal Bhujal Yojana, aquifer mapping, groundwater as a "
               "state subject); traditional water systems (johad, ahar-pyne, kul and zing, khadin, bamboo drip, "
               "surangam, eri); Jal Jeevan Mission; flood and drought management, and the Dam Safety Act 2021.",
         traps="The Indira Gandhi Canal draws from the Harike barrage at the Sutlej-Beas confluence; Hirakud on the "
               "Mahanadi is the longest earthen dam and Tehri on the Bhagirathi the highest; Idukki is the first arch "
               "dam; Ken-Betwa submerges part of Panna Tiger Reserve; groundwater is a state subject; Polavaram is on "
               "the Godavari.",
         mains="Water governance and scarcity; river interlinking - feasibility, ecology and federalism; groundwater "
               "depletion and pricing; dam rehabilitation; Jal Jeevan Mission outcomes."),
    dict(id="G11", pages=50,
         focus="Peninsular drainage traits (rain-fed, seasonal, mature graded rivers in hard rock, mostly east-flowing "
               "with deltas, west-flowing with estuaries); Narmada and Tapi in rift valleys; the west-flowing Sabarmati, "
               "Mahi, Luni and Ghaggar-Hakra; Godavari (the longest peninsular river, the Dakshin Ganga, seven states in "
               "its basin); Krishna with the Tungabhadra as its largest tributary; Cauvery (born in Karnataka, delta in "
               "Tamil Nadu, the tribunal and the 2018 Supreme Court verdict, the Cauvery Water Management Authority); "
               "Mahanadi with Hirakud; Subarnarekha, Damodar and the DVC as India's first multipurpose river valley "
               "authority; lakes - Wular the largest freshwater, Loktak with floating phumdis and Keibul Lamjao, Chilika "
               "the largest coastal lagoon, Pulicat, Vembanad the longest lake, Sambhar the salt lake, Lonar the basaltic "
               "impact crater, Ansupa the largest oxbow; Ramsar sites (India's first two in 1981 were Chilika and "
               "Keoladeo; the Montreux Record lists Chilika, Keoladeo and Loktak); the Wetland Rules 2017.",
         traps="Narmada and Tapi form estuaries rather than deltas; Godavari drains the largest peninsular basin; the "
               "Tungabhadra is Krishna's largest tributary; Damodar is the sorrow of Bengal while Kosi is the sorrow of "
               "Bihar; Lonar is saline and basaltic, not freshwater; Chilika is brackish; Loktak's phumdis are floating "
               "biomass, not coral; Vembanad is Kerala's largest lake.",
         mains="Inter-state water disputes and tribunal delays; wetlands vs urban expansion; riverfront development and "
               "ecology; groundwater-linked lake decline."),
    dict(id="G08", pages=40,
         focus="Causes of ocean currents (planetary winds first, then temperature, salinity, Coriolis and basin shape); "
               "warm and cold currents by ocean (Kuroshio and Oyashio, Gulf Stream and Labrador, California and Peru, "
               "Canary and Benguela, Brazil and Falkland, Agulhas and the seasonally reversing Somali current); effects "
               "- warm currents milden north-west Europe, cold currents create coastal deserts on tropical western "
               "margins, warm-cold convergence produces fog and rich fishing grounds (Newfoundland, Hokkaido); straits "
               "and what they connect (Gibraltar, Bosporus and Dardanelles, Hormuz, Bab-el-Mandeb, Malacca, Sunda, "
               "Lombok, Bering, Magellan, Palk); gulfs, bays and seas including the Sargasso, the only sea without a "
               "coastline; coral reefs (fringing, barrier, atoll; temperature above 20 degreeC, salinity 27-30 ppt, "
               "depth under 60 m, clear sediment-free water; India's reef areas in the Gulf of Mannar, Palk Bay, the "
               "Gulf of Kutch, Andaman-Nicobar and Lakshadweep); UNCLOS zones (12 nm territorial, 24 nm contiguous, 200 "
               "nm EEZ) and India's 2.02 million sq km EEZ.",
         traps="Cold currents, not warm ones, cause deserts on tropical western margins; the Sargasso Sea has no "
               "coastline; deltas have no coral reefs because of sediment and freshwater; the Gulf Stream keeps "
               "north-west Europe ice-free; the Labrador is cold; the Somali current reverses with the monsoon; "
               "Lakshadweep's reefs are atolls while the Andamans' are fringing.",
         mains="Blue economy and ocean governance; Indo-Pacific maritime security; coral bleaching and coastal "
               "livelihoods; EEZ management."),
    dict(id="G05", pages=55,
         focus="Humidity measures and their behaviour; condensation processes; cloud classification by height and form; "
               "precipitation types (convectional, orographic, frontal) and cloud seeding; air masses and fronts (cold, "
               "warm, stationary, occluded); temperate cyclones along the polar front moving west to east - the source of "
               "India's western disturbances; tropical cyclones and their requirements (sea surface temperature above "
               "26.5 degreeC to a depth of about 60 m, Coriolis force, low vertical wind shear, a pre-existing "
               "disturbance), structure (calm cloud-free eye, the eyewall with the strongest winds, spiral rainbands), "
               "IMD wind-speed categories from depression to super cyclonic storm, and the WMO/ESCAP naming panels; the "
               "Bay of Bengal being more cyclone-prone than the Arabian Sea; storm surge in shallow funnel-shaped coasts; "
               "India's warning and evacuation architecture (IMD, INCOIS, NDRF, Odisha's zero-casualty model); "
               "thunderstorms, squalls, hail and tornadoes; the El Nino-cyclone relationship.",
         traps="Tropical cyclones cannot form at the equator and weaken rapidly over land, whereas temperate cyclones "
               "persist over land; tropical cyclones move east to west and then recurve poleward, "
               "while temperate cyclones move west to east; western disturbances are temperate cyclones of Mediterranean "
               "origin; IMD wind thresholds are in knots; the highest storm surges occur on shallow funnel-shaped coasts.",
         mains="Cyclone preparedness and the Odisha model; climate change and cyclone intensity; urban flooding; "
               "last-mile early warning; disaster-resilient infrastructure."),
    dict(id="G21", pages=45,
         focus="Continental physiography (the Alpide and Circum-Pacific belts, the Tibetan plateau as the Third Pole, the "
               "Great Rift Valley, the Andes as the longest continental range, the Appalachians as old and eroded, the "
               "Great Lakes, the Great Dividing Range, the Antarctic Treaty 1959 and India's stations); world grasslands "
               "(steppe, prairie, pampas, llanos, campos, veld, downs, savannah); hot and cold deserts; major rivers with "
               "their mouths and countries (Nile with the White and Blue Nile and the GERD dispute, Amazon, Yangtze, "
               "Yellow, Mekong, Congo, Niger, Zambezi, Danube through the most countries, Rhine, Volga, Mississippi, "
               "Parana); world lakes (Caspian largest, Baikal deepest, Superior largest freshwater by area, Titicaca "
               "highest navigable, Dead Sea lowest land point); peaks and volcanic belts (Everest, K2, Aconcagua, Elbrus, "
               "Kilimanjaro, Denali; the Ring of Fire, the Mediterranean belt, hotspots such as Hawaii and Reunion); "
               "ocean trenches; major islands and archipelagos; the Suez and Panama canals and their economics.",
         traps="The Danube flows through the most countries and reaches the Black Sea while the Rhine reaches the North "
               "Sea; Elbrus is Europe's highest peak, Mont Blanc the highest in the Alps; Baikal is the deepest and holds "
               "about a fifth of unfrozen freshwater; Antarctica is the driest, coldest and on average the highest "
               "continent; Greenland is the largest island and Australia the smallest continent; the Llanos are in the "
               "Orinoco basin, the Campos in Brazil, the Pampas in Argentina.",
         mains="Underpins resource diplomacy (GERD, Mekong, Indus) and world-geography questions in GS-1."),
    dict(id="G13", pages=45,
         focus="Forest types and their climatic drivers (tropical wet evergreen above 200 cm with no dry season on the "
               "windward Western Ghats, the north-east and the Andamans; semi-evergreen; moist deciduous as India's "
               "largest type with teak and sal; dry deciduous; thorn and scrub below 70 cm in the north-west; the dry "
               "evergreen scrub of the Coromandel coast that gets winter rain; subtropical pine and broad-leaved hill "
               "forests; montane wet temperate; sub-alpine and alpine); State of Forest Report figures (forest cover "
               "about 21.7% and tree cover about 2.9% of the geographical area, with Madhya Pradesh leading by area and "
               "Mizoram by percentage); mangroves and their adaptations (pneumatophores, prop roots, vivipary, salt "
               "excretion) with the Sundarbans the largest, Bhitarkanika second, then Pichavaram, the Gulf of Kutch and "
               "the Godavari-Krishna-Cauvery deltas; blue carbon; the shola-grassland complex; India's four biodiversity "
               "hotspots; endemism in the Western Ghats and the north-east; grasslands including the Banni; forest law "
               "and finance (Indian Forest Act 1927, Forest Conservation Act 1980 as amended in 2023, CAMPA, the Forest "
               "Rights Act 2006, Green India Mission, Nagar Van).",
         traps="Tropical dry evergreen forests are on the east coast because they receive winter rain; moist deciduous is "
               "the largest forest type by area; mangrove pneumatophores are breathing roots; the Sundarbans is a UNESCO "
               "World Heritage Site, not a biosphere reserve; the Nilgiri was India's first biosphere reserve in 1986; "
               "the Western Ghats are both a biodiversity hotspot and a World Heritage Site; Banni is a grassland in "
               "Kutch, not a forest.",
         mains="Forest rights and the FRA-CAMPA conflict; afforestation vs natural regeneration; the Western Ghats "
               "reports; mangroves and coastal protection; grassland neglect; forest fires."),
    dict(id="G12", pages=35,
         focus="Soil-forming factors; the ICAR's eight groups with area share, parent material, chemistry and crops - "
               "alluvial (the largest, rich in potash but poor in nitrogen, phosphorus and humus; khadar vs bhangar with "
               "kankar), black/regur (Deccan basalt, cotton soil, moisture-retentive and self-ploughing, rich in lime, "
               "iron, magnesia and alumina, poor in nitrogen, phosphorus and organic matter), red and yellow (iron "
               "diffusion gives the colour, porous and poor in N, P and humus), laterite (intense leaching under "
               "alternating wet and dry conditions, rich in iron and aluminium, poor in humus and bases, good for cashew, "
               "tea and coffee with manure), arid and desert (sandy, saline, kankar sub-layer), saline and alkaline "
               "(rehs, kallar and usar in inland-drainage areas, corrected with gypsum), forest and mountain, and peaty "
               "or marshy (Kari soils of Kuttanad, very high organic matter and acidic); soil degradation types and "
               "ISRO's land-degradation atlas; conservation methods (contour bunding, terracing, strip cropping, shelter "
               "belts, mulching, cover crops, zero tillage, gully plugging); the Soil Health Card Scheme.",
         traps="Black soil is rich in lime, iron, magnesia and alumina but poor in nitrogen, phosphorus and humus; red "
               "soil is poor in nitrogen, phosphorus and humus; laterite is formed by leaching and is poor in humus and "
               "bases; alluvial soil is rich in potash but deficient in nitrogen; saline soils need gypsum, not lime; "
               "ISRO, not the agriculture ministry, publishes the desertification atlas.",
         mains="Soil health and fertiliser subsidy reform; land degradation neutrality; salinisation from canal "
               "irrigation; natural farming and soil organic carbon."),
    dict(id="G10", pages=50,
         focus="Himalayan drainage traits (snow-fed and perennial, antecedent rivers cutting across rising ranges, deep "
               "gorges, huge sediment loads, braided channels in the plains); the Indus system and the Indus Waters Treaty "
               "1960 (India got the eastern rivers Ravi, Beas and Sutlej; Pakistan the western Indus, Jhelum and Chenab; "
               "the World Bank is a signatory; neutral expert and Court of Arbitration mechanisms; Kishanganga and Ratle "
               "disputes); the Ganga system (Panch Prayag, Bhagirathi plus Alakananda at Devprayag; right-bank "
               "tributaries Yamuna and Son, left-bank Gomti, Ghaghara, Gandak and Kosi; Ghaghara is the largest by "
               "volume; Yamuna's tributaries Chambal, Betwa and Ken; the Damodar and the DVC; the Ganga Action Plan and "
               "Namami Gange); the Brahmaputra (Tsangpo in Tibet, the deepest gorge at Namcha Barwa, Siang and Dihang in "
               "Arunachal, tributaries Subansiri, Manas and Teesta which joins in Bangladesh, braided channels with chars "
               "and Majuli, becoming the Jamuna and forming the world's largest delta with the Ganga); Himalayan river "
               "hydropower and its ecological cost; glacial lake outburst floods (South Lhonak, Sikkim 2023; Chamoli "
               "2021); national waterways on these rivers (NW1 Ganga, NW2 Brahmaputra, NW3 the West Coast Canal - the only "
               "24-hour navigable waterway).",
         traps="Ghaghara, not the Yamuna, is the Ganga's largest tributary by volume; the Yamuna is the longest "
               "right-bank tributary; the Son is the only major south-bank tributary; Kosi is the sorrow of Bihar and "
               "Damodar the sorrow of Bengal; the Teesta joins the Brahmaputra in Bangladesh; the Indus Waters Treaty "
               "gave India the eastern rivers; the Indus, Sutlej and Brahmaputra are antecedent; the Ganga gets its name "
               "at Devprayag.",
         mains="Transboundary water sharing; flood management in Bihar and Assam; Ganga cleaning outcomes; hydropower and "
               "Himalayan ecology; inland waterways and logistics."),
    dict(id="G14", pages=35,
         focus="Categories and their legal basis (national parks and wildlife sanctuaries under the Wild Life Protection "
               "Act 1972 as amended in 2022, conservation and community reserves, tiger reserves under Project Tiger "
               "1973 with the NTCA statutory since 2006, elephant reserves under Project Elephant 1992, biosphere "
               "reserves, Ramsar sites, UNESCO natural and mixed sites); high-yield parks by state with their signature "
               "species (Kaziranga and the one-horned rhino; Manas with four designations; the Sundarbans; Simlipal; "
               "Bhitarkanika and saltwater crocodiles; Gahirmatha and olive ridley nesting; Jim Corbett as the first "
               "national park; Hemis as the largest; Van Vihar as the smallest; Kanha and the barasingha; Bandhavgarh's "
               "tiger density; Ranthambore; Keoladeo; the Desert National Park and the great Indian bustard; Gir and the "
               "Asiatic lion; Kuno and reintroduced African cheetahs; Silent Valley and the lion-tailed macaque; "
               "Periyar; Eravikulam and the Nilgiri tahr; Nagarjunasagar-Srisailam as the largest tiger reserve by area; "
               "Namdapha with four big cats; Khangchendzonga as India's only mixed World Heritage site); instruments and "
               "bodies (CITES, the Bonn Convention and flyways, the IUCN Red List categories, the Kunming-Montreal 30x30 "
               "target, the WCCB, CAMPA, eco-sensitive zones).",
         traps="Khangchendzonga is India's only mixed cultural and natural World Heritage Site; Jim Corbett (1936) was the "
               "first national park; Hemis is the largest and Van Vihar the smallest; Nagarjunasagar-Srisailam is the "
               "largest tiger reserve by area; Nilgiri (1986) was the first biosphere reserve and the Gulf of Mannar the "
               "first marine biosphere reserve; Chilika and Keoladeo were India's first Ramsar sites; Keibul Lamjao on "
               "Loktak is the only floating national park; Kuno's cheetahs are African, not Asiatic; eco-sensitive zone "
               "widths are site-specific rather than a uniform ten kilometres; CAMPA exists at both national and state "
               "levels.",
         mains="Human-wildlife conflict and compensation; eco-sensitive zones vs livelihoods; Project Tiger and Project "
               "Elephant outcomes; the cheetah reintroduction debate; conservation finance and community conservation."),
    dict(id="G20", pages=45,
         focus="Census 2011 headline figures (population 121.09 crore, decadal growth 17.7%, sex ratio 943, child sex "
               "ratio 918, literacy 74.04%, density 382 per sq km, urban share 31.16%) and the Census Act 1948; NFHS-5 "
               "findings (total fertility rate at 2.0, below replacement; 1020 women per 1000 men; anaemia levels); the "
               "demographic transition and India's dividend window, ageing and the India Ageing Report; migration "
               "(marriage as the dominant reason for female migration, work for males; the UP-Bihar to "
               "Maharashtra-Delhi-Gujarat corridors; circular and seasonal migration; the Inter-State Migrant Workmen "
               "Act; the e-Shram portal; One Nation One Ration Card; India as the largest recipient of remittances); "
               "settlement types (clustered, semi-clustered, hamleted, dispersed) and the census definition of a census "
               "town; the urban hierarchy (statutory town, census town, urban agglomeration, metropolitan area of ten "
               "lakh or more under Art 243P) and programmes (Smart Cities Mission, AMRUT 2.0, PMAY-U, Rurban, "
               "Svamitva); tribes (Negrito, Proto-Australoid, Mongoloid and Dravidian groups; 75 Particularly Vulnerable "
               "Tribal Groups with Odisha hosting the most; Bhils the largest tribal group and Gonds second; matrilineal "
               "Khasi, Jaintia and Garo; transhumant Gujjar, Gaddi, Bakarwal and Changpa; the PM-PVTG scheme).",
         traps="NFHS-5 recorded more women than men for the first time while Census 2011 gave 943; India's fertility rate "
               "is below replacement but the population still grows through momentum; a census town meets urban criteria "
               "without a municipality; Bhils are the largest tribal group and Gonds second; only Parliament can modify "
               "the Scheduled Tribe list under Art 342(2); the Sentinelese and Jarawa are Andamanese Negrito groups.",
         mains="Demographic dividend and skilling; ageing and social security; urbanisation - housing, water, flooding, "
               "heat; migration policy and benefit portability; PVTG development and tribal rights; the census delay."),
    dict(id="G19", pages=35,
         focus="Roads (the world's second-largest network; national highways about 2% of length carrying around 40% of "
               "traffic; Bharatmala Pariyojana; the Golden Quadrilateral and the North-South and East-West corridors; "
               "expressways - Yamuna as the first, Agra-Lucknow as among the longest, Delhi-Mumbai under construction; "
               "Atal Tunnel Rohtang, the Pir Panjal rail tunnel, the Chenab rail bridge, Mumbai Trans Harbour Link, the "
               "Bogibeel and Dhola-Sadiya bridges); railways (the fourth-largest network, eighteen zones, near-complete "
               "broad-gauge electrification, the Eastern and Western Dedicated Freight Corridors, Vande Bharat and Amrit "
               "Bharat, the Mumbai-Ahmedabad high-speed line, the three UNESCO Mountain Railways of India, the Konkan "
               "Railway as a separate entity and not a zone); waterways (111 national waterways, Jal Marg Vikas on NW1, "
               "multi-modal logistics parks); ports (twelve major ports under the Major Port Authority Act 2021; "
               "non-major ports under state control with Gujarat leading; Mundra the largest by cargo volume, JNPT the "
               "largest container port, Ennore/Kamarajar the first corporatised major port, Pipavav the first private "
               "port, Vizhinjam India's first deep-water transshipment port; Sagarmala and port-led development; "
               "dependence on Colombo, Singapore and Tanjung Pelepas for transshipment); airports (UDAN regional "
               "connectivity, Cochin as India's first fully solar-powered airport, greenfield airports at Mopa, "
               "Hollongi, Pakyong and Jewar); pipelines (HVJ and Urja Ganga gas pipelines, the Kudremukh iron-ore "
               "slurry pipeline); digital and submarine cable landing points.",
         traps="Mundra is the largest port by cargo but is a non-major (state) port, while JNPT is the largest container "
               "port and a major port; Ennore/Kamarajar was the first corporatised major port and Pipavav the first "
               "private port; Vizhinjam is the first deep-water transshipment port; Cochin is the first fully solar "
               "airport; Atal Tunnel is the longest highway tunnel above 10,000 feet while Pir Panjal is the longest rail "
               "tunnel; the Konkan Railway is not a zone; NW3 is the only 24-hour navigable national waterway.",
         mains="Port-led development and logistics costs under PM Gati Shakti; dedicated freight corridors and modal shift; "
               "UDAN and regional connectivity; transshipment dependence; coastal regulation."),
    dict(id="G18", pages=35,
         focus="Location factors and the classical theories (Weber's least cost, Losch's profit maximisation, footloose "
               "industries); iron and steel plants with their collaboration partners and locational logic (TISCO "
               "Jamshedpur 1907 as the first modern plant, IISCO Burnpur, Bhilai with Soviet aid, Rourkela with German, "
               "Durgapur with British, Bokaro, Vijayanagar, Vishakhapatnam as the first port-based plant, Salem); the "
               "Chotanagpur belt as the Ruhr of India; textiles (the Mumbai-Ahmedabad cotton belt and its humid climate "
               "and port access, Coimbatore as the Manchester of South India, Kanpur as the Manchester of the East, the "
               "Hooghly jute belt with water for retting and the Kolkata port, Ludhiana for hosiery, Tiruppur for "
               "knitwear, the silk and handloom clusters); sugar and the westward shift of mills, plus ethanol blending; "
               "cement, fertilisers (the revived coal-gasification units at Gorakhpur, Sindri, Ramagundam, Talcher and "
               "Barauni; nano urea at Kalol), petrochemicals and refining (Jamnagar as the world's largest refining hub, "
               "Panipat as the largest inland refinery, PCPIRs); automobiles and EV clusters; electronics and the "
               "semiconductor push (Micron's Sanand assembly and test plant); IT and ITES cities; pharmaceuticals "
               "(Hyderabad's Genome Valley, the Himachal cluster at Baddi, India as the pharmacy of the world and its "
               "dependence on imported APIs); industrial corridors (the Delhi-Mumbai Industrial Corridor with Dholera "
               "and Shendra-Bidkin, Amritsar-Kolkata, Chennai-Bengaluru, Visakhapatnam-Chennai, the East Coast Economic "
               "Corridor), SEZs, PM MITRA textile parks and the two defence corridors; GI-tagged products and the GI "
               "Registry at Chennai.",
         traps="TISCO Jamshedpur (1907) was the first modern iron and steel plant; Visakhapatnam is the first port-based "
               "plant; the Chotanagpur belt is the Ruhr of India; Coimbatore is the Manchester of South India and Kanpur "
               "of the East; India has no potash reserves and imports all of it; Dholera SIR is on the Delhi-Mumbai "
               "corridor in Gujarat while GIFT City is a financial services centre; Darjeeling tea was India's first "
               "GI-tagged product; Micron's Sanand plant is India's first semiconductor assembly and test facility.",
         mains="Manufacturing's share of GDP and the China-plus-one opportunity; industrial corridors and land "
               "acquisition; MSME formalisation; PLI outcomes and job intensity; decarbonising steel and cement."),
    dict(id="G07", pages=45,
         focus="Ocean distribution and relief (the Pacific largest and deepest with the Mariana Trench and the Ring of "
               "Fire; the Atlantic S-shaped with the Mid-Atlantic Ridge as the longest mountain chain on earth and the "
               "Puerto Rico Trench as its deepest point; the Indian Ocean the warmest and monsoon-driven; the Southern "
               "Ocean with the Antarctic Circumpolar Current; the Arctic the smallest and shallowest); relief subdivision "
               "(continental shelf to about 200 m depth holding roughly nine-tenths of the fish catch and most offshore "
               "oil and gas, continental slope with submarine canyons, abyssal plains as the largest subdivision with "
               "oozes and red clay, deeps and trenches, ridges and rises including the Carlsberg and Ninety East ridges, "
               "seamounts, guyots, atolls, hydrothermal vents); ocean temperature (surface controls, the mixed layer, the "
               "thermocline, the cold deep layer holding about 90% of the ocean's volume, Ocean Mean Temperature to the "
               "26 degreeC isotherm as a monsoon predictor, ocean heat content and marine heatwaves); salinity (average "
               "35 ppt, controls, maximum in landlocked hot seas and in the subtropics rather than at the equator, "
               "vertical profile and halocline); waves (fetch, swell, tsunami generation and shoaling, the 2004 Indian "
               "Ocean tsunami and INCOIS's warning system); tides (the Moon's tide-generating force about 2.2 times the "
               "Sun's, spring tides at syzygy and neap at quadrature, semi-diurnal, diurnal and mixed tides, the Bay of "
               "Fundy's record range, the Gulf of Khambhat and Kutch in India, tidal bores, tidal energy); gyres, the "
               "Ekman spiral and upwelling zones.",
         traps="The continental shelf yields about nine-tenths of the fish catch; the deep-sea plain is the largest "
               "subdivision; the Mid-Atlantic Ridge is the longest mountain chain on Earth; salinity peaks in the "
               "subtropical high-evaporation belt, not at the equator, and the Dead Sea is a hypersaline lake rather than "
               "a sea; spring tides occur at new and full moon; the Moon's tide-generating force exceeds the Sun's; "
               "upwelling makes western continental margins nutrient-rich yet arid on land.",
         mains="Deep-sea mining and the International Seabed Authority regime; ocean warming and marine heatwaves; "
               "tsunami preparedness; tidal energy; the blue economy."),
    dict(id="G04", pages=50,
         focus="Pressure belts (equatorial low or doldrums with the shifting ITCZ, sub-tropical high or horse latitudes "
               "where deserts form on western margins, sub-polar low with the polar front, polar high with katabatic "
               "winds); semi-permanent pressure cells and their seasonal reversal over Asia; planetary winds (trade winds "
               "converging at the ITCZ and steering tropical cyclones westward, westerlies steering temperate cyclones "
               "eastward and stronger in the Southern Hemisphere, polar easterlies); the Coriolis force (zero at the "
               "equator, maximum at the poles, deflects right in the north, hence no cyclones within five degrees of the "
               "equator; Buys Ballot's law); the tri-cellular model (Hadley, Ferrel, Polar); the pressure gradient force "
               "and geostrophic wind; upper-air circulation, Rossby waves and jet streams (the subtropical westerly jet "
               "bifurcated by the Tibetan plateau in winter bringing western disturbances and shifting north in summer; "
               "the polar front jet; the tropical easterly jet over peninsular India; the Somali or Findlater low-level "
               "jet); local and seasonal winds with a table (Loo, Sirocco with its dust rain, Harmattan the doctor wind, "
               "Chinook the snow eater, Foehn, Mistral, Bora, Zonda, Santa Ana, Khamsin, Berg, Pampero, Cape Doctor; "
               "Indian pre-monsoon showers - Kal Baisakhi or Nor'westers, mango showers, blossom showers, Bordoisila); "
               "sea and land breeze, valley and mountain breeze; cyclones and anticyclones at the surface; the Walker "
               "circulation, the Southern Oscillation Index and ENSO teleconnections.",
         traps="Coriolis is zero at the equator, so tropical cyclones cannot form there; Chinook belongs to the Rockies "
               "and Foehn to the Alps; Harmattan is called the doctor because it lowers humidity and malaria incidence; "
               "Sirocco brings red dust rain to southern Europe; Mistral is cold and blows from France to the "
               "Mediterranean; westerlies are stronger in the Southern Hemisphere; trade winds steer tropical cyclones "
               "westward and westerlies recurve them; a negative Southern Oscillation Index means higher pressure at "
               "Darwin, which is El Nino; Kal Baisakhi benefits tea, jute and rice in Bengal and Assam.",
         mains="Climate variability and agriculture; pollution transport and stubble burning; ENSO forecasting; "
               "heatwaves and urban ventilation."),
    dict(id="G23", pages=30,
         focus="Earth's shape and dimensions (oblate spheroid, equatorial bulge, 71% water, perihelion in January and "
               "aphelion in July - distance is not the cause of seasons); latitudes and the key parallels (the equator, "
               "the Tropics of Cancer and Capricorn, the Arctic and Antarctic Circles), the Tropic of Cancer's passage "
               "through eight Indian states, and the equator's countries; longitudes, the Prime Meridian, the "
               "International Date Line and its deviations, IST at 82.5 degrees E passing through Mirzapur-Sonbhadra, "
               "the four-minutes-per-degree rule and nautical miles, time-zone anomalies (Nepal at +5:45, China's single "
               "zone, France spanning the most zones because of overseas territories); great circles and great-circle "
               "routes; rotation (a sidereal day four minutes shorter than a solar day, the Coriolis effect, tides, time "
               "differences) and revolution (the axial tilt of 23.44 degrees as the cause of seasons, solstices, "
               "equinoxes, the circle of illumination, midnight sun and polar night); the solar system's basics (Venus "
               "hottest, Mercury's greatest day-night range, Jupiter largest, Uranus tilted, Venus retrograde, the "
               "asteroid belt, dwarf planets); eclipses (solar only at new moon, lunar only at full moon, umbra and "
               "penumbra, annular eclipses at apogee); India's space programme in geography terms (Sriharikota's coastal "
               "equatorial location, Thumba near the magnetic equator, NavIC as a regional seven-satellite system, "
               "Chandrayaan-3's south-pole landing, Aditya-L1 at the first Lagrange point); mapping and contour reading "
               "(contour interval, V-shaped contours pointing upstream, closely spaced contours for steep slopes, "
               "saddles, spot heights, toposheets, GPS trilateration).",
         traps="Perihelion falls in January yet the north has winter, because the axial tilt and not distance drives "
               "seasons; the Tropic of Cancer passes through eight Indian states including Madhya Pradesh but not "
               "Maharashtra or Odisha; a sidereal day is four minutes shorter than a solar day; Venus is hotter than "
               "Mercury; Thumba was chosen for being near both the geographic and magnetic equator; NavIC is regional, "
               "not global; the Date Line deviates from 180 degrees to keep island groups on one date; France spans the "
               "most time zones.",
         mains="Rarely direct, but lat-long and earth-motion logic underpins climate, time-zone, satellite and GIS "
               "questions."),
    dict(id="G01", pages=55,
         focus="Sources of knowledge about the interior (deep mines and drilling, volcanoes, seismic waves, meteorites); "
               "seismic wave behaviour (P waves through solids and liquids, S waves only through solids which proves the "
               "outer core is liquid, surface waves most destructive) and shadow zones (P between 105 and 145 degrees, S "
               "beyond 105 degrees); the layered structure and its discontinuities (Mohorovicic between crust and mantle, "
               "Repetti within the mantle, Gutenberg-Wiechert at 2900 km, Lehmann between the outer and inner core); the "
               "lithosphere and asthenosphere; the rock cycle with Indian examples (Deccan Traps as Cretaceous flood "
               "basalt from the Reunion hotspot, the Dharwar as the oldest complex, the Aravalli as old fold mountains, "
               "Gondwana sedimentaries holding almost all coal, Tertiary rocks holding petroleum and lignite); "
               "metamorphic pairs (limestone to marble, shale to slate, sandstone to quartzite, granite to gneiss, coal "
               "to graphite); fossils only in sedimentary rocks; endogenic forces (orogeny and epeirogeny, folds, "
               "faults, rift valleys and block mountains); plate tectonics (Wegener's evidence and its objections, "
               "Holmes' convection currents, Hess's sea-floor spreading, palaeomagnetic striping, boundary types and "
               "their landforms, the Wilson cycle, hotspots - Hawaii and Reunion, the Himalayas from continent-continent "
               "collision); earthquakes (focus and epicentre, Richter's logarithmic scale and moment magnitude, Mercalli "
               "intensity, seismic belts, India's BIS zones V to II with Latur 1993 and Koyna 1967 as intraplate "
               "examples); volcanoes (shield, composite, caldera, flood basalt provinces, intrusive forms - batholith, "
               "sill, dyke, laccolith, phacolith; the Ring of Fire, Iceland's ridge-plus-hotspot setting, Barren Island "
               "as India's only active volcano and Narcondam dormant; geothermal provinces such as Puga and Manikaran); "
               "weathering and mass wasting; landslides (susceptibility mapping, the Himalayan combination of young "
               "tectonics, heavy rain and unplanned construction, Joshimath subsidence, early warning systems).",
         traps="S waves cannot travel through liquids, which is how we know the outer core is liquid; the P-wave shadow "
               "zone is 105-145 degrees; fossils occur only in sedimentary rocks; the Deccan Traps are hotspot flood "
               "basalts, not subduction volcanism; the Himalayas are young fold mountains from continent-continent "
               "collision and so have few volcanoes; Barren is active and Narcondam dormant; Latur and Koyna occurred in "
               "low seismic zones showing intraplate risk; each Richter unit means ten times the amplitude and about "
               "thirty-two times the energy; the plate moves over a fixed hotspot, not the reverse.",
         mains="Himalayan tectonics and infrastructure risk; landslide and earthquake preparedness; deep-sea mining; "
               "critical minerals; reservoir-induced seismicity and dam siting."),
    dict(id="G02", pages=40,
         focus="The cycle of erosion and Davis's geographical cycle (structure, process, stage), rejuvenation and "
               "polycyclic landforms, the graded profile of a river; fluvial landforms (erosional - V-shaped valleys, "
               "gorges such as the Tsangpo's at Namcha Barwa and the Kali Gandaki, canyons including Gandikota on the "
               "Pennar, Chambal's ravines and badlands, potholes as at Nighoj, waterfalls with Kunchikal the highest in "
               "India and Jog the segmented one on the Sharavathi, Nohkalikai the tallest plunge; depositional - "
               "alluvial fans including the Kosi megafan, floodplains and natural levees, meanders with cut banks and "
               "point bars, oxbow lakes such as Kanwar Taal and Ansupa, yazoo tributaries, braided channels with chars "
               "and majulis, deltas by type - arcuate for the Ganga-Brahmaputra and Nile, bird's foot for the "
               "Mississippi, estuarine for the Amazon, and why deltas need sediment supply, a shallow shelf and low wave "
               "energy); glacial landforms (cirque with a bergschrund and tarn, arete, horn, U-shaped troughs, hanging "
               "valleys, roche moutonnee, fjords as submerged glacial troughs; depositional - lateral, medial, terminal "
               "and ground moraines, drumlins, eskers, kames, kettle lakes, outwash plains; till unsorted and "
               "unstratified vs outwash sorted; India's glaciers - Siachen the longest outside the polar regions, "
               "Gangotri, Zemu the largest in the eastern Himalaya, and the Karakoram anomaly); periglacial features and "
               "permafrost; aeolian landforms (mushroom rocks, zeugen and yardangs, deflation hollows, inselbergs, "
               "barchans with horns downwind, seif and star dunes, loess, playa and sabkha as in the Rann of Kutch, "
               "pediments and pediplains, mesas and buttes); karst (lapies, sinkholes, polje, uvala, caves with "
               "stalactites from the ceiling and stalagmites from the floor, India's Belum Caves as the longest on the "
               "plains and Meghalaya's Krem Liat Prah as the longest overall, the Khasi living root bridges, terra rossa "
               "soil, tower karst); coastal landforms (swash and backwash, longshore drift, wave-cut platforms and "
               "cliffs, cave-arch-stack-stump sequences, beaches with Marina as India's longest natural urban beach and "
               "Varkala's laterite cliffs, spits and bars including Dhanushkodi and Adam's Bridge, lagoons such as "
               "Chilika and Pulicat, estuaries of the Narmada, Tapi, Mandovi and Zuari, rias of the Konkan, emergent and "
               "submergent coasts, coral coasts with Darwin's subsidence theory); geological monuments and crater lakes "
               "(Lonar as the only hyper-velocity basaltic impact crater, St Mary's Islands' columnar basalt formed when "
               "India rifted from Madagascar, the Eparchaean unconformity at Tirumala, the Karewa deposits of Kashmir "
               "used for saffron).",
         traps="An oxbow lake is a cut-off meander loop; Narmada and Tapi form estuaries rather than deltas because they "
               "flow through rift valleys of hard rock with little silt and high tidal energy; stalactites hang from the "
               "ceiling and stalagmites rise from the floor; till is unsorted while outwash is sorted; a drumlin's long "
               "axis points in the direction of ice movement; a yardang is streamlined parallel to the wind; barchans "
               "migrate with horns pointing downwind; Lonar is a basaltic impact crater with saline-alkaline water; "
               "fjords are glacial while rias are drowned river valleys, so India's Konkan coast has rias and no fjords.",
         mains="Coastal erosion and management; sand mining and river rejuvenation; glacial retreat and water security; "
               "geoheritage conservation and geoparks; landslide risk."),
    dict(id="G06", pages=45,
         focus="Definition and share (the seasonal reversal of winds; the south-west monsoon of June to September brings "
               "about three-quarters of India's annual rainfall); mechanisms and theories (differential heating, the "
               "northward shift of the ITCZ over the Tibetan plateau with south-east trades crossing the equator and "
               "becoming the south-west monsoon, Flohn's jet-stream theory with the subtropical westerly jet bifurcated "
               "by the plateau in winter and displaced north in summer, the Tibetan plateau as an elevated heat source, "
               "the Somali or Findlater low-level jet, the Mascarene High); ENSO (El Nino weakening the monsoon, La Nina "
               "generally strengthening it, El Nino Modoki), the Indian Ocean Dipole (a positive IOD can offset an El "
               "Nino, as in 1997 and 2015), EQUINOO, the Madden-Julian Oscillation driving active and break spells, and "
               "Eurasian snow cover as a predictor; the two branches (the Arabian Sea branch giving orographic rain on "
               "the windward Western Ghats with Agumbe the wettest in the south and a rain shadow over the Deccan, and the "
               "Bay branch giving the north-east its rainfall through the funnel-shaped Khasi hills); onset at Kerala "
               "around 1 June, advance across India within a month and withdrawal from September; the monsoon trough and "
               "break conditions; distribution (Mawsynram the wettest on record, Ladakh and western Rajasthan the "
               "driest, high variability in the arid west); the retreating and north-east monsoon that gives Tamil Nadu "
               "most of its rain; western disturbances as extra-tropical cyclones of Mediterranean origin bringing winter "
               "rain and snow vital for the rabi crop; pre-monsoon showers (Kal Baisakhi, mango showers, blossom "
               "showers) and the Loo; IMD's forecasting (the long-period average, the four homogeneous regions, "
               "statistical plus dynamical models, the Monsoon Mission at IITM Pune); Koppen's classification of India "
               "(Amw on the west coast, As on the Coromandel coast with a dry summer, Aw over most of the peninsula, "
               "BShw semi-arid steppe, BWhw hot desert, Cwg humid subtropical, Et tundra and H highland); climate-change "
               "projections for the monsoon (more total rain but greater variability, longer dry spells and more intense "
               "bursts, a warming Arabian Sea driving more cyclones there); drought assessment criteria and heatwave "
               "criteria, heat action plans and lightning mortality.",
         traps="Tamil Nadu receives most of its rain from the retreating or north-east monsoon, which is why Chennai "
               "floods in November-December; Mawsynram, not Cherrapunji, holds the wettest-place record and both are in "
               "the East Khasi Hills; Ladakh is a cold desert in the rain shadow of the Himalaya and Karakoram; western "
               "Rajasthan is arid because the Arabian Sea branch runs parallel to the Aravalli with no orographic lift; a "
               "positive IOD can offset an El Nino; western disturbances are extra-tropical, not tropical, cyclones; the "
               "Loo is a hot dry pre-monsoon wind of the north-west plains, not a monsoon wind; Agumbe is the Cherrapunji "
               "of the south; Koppen's As with a dry summer is the Coromandel coast while Amw is the west coast south of "
               "Goa; lightning kills more Indians than any other natural hazard.",
         mains="Monsoon variability and agricultural risk; climate change and the monsoon's future; drought management "
               "under the DM Act; heatwaves and heat action plans; urban flooding and the monsoon-drainage nexus."),
]

UNIT_SOURCES = {
    "Polity": "M. Laxmikanth, Indian Polity (6th ed.) + NCERT XI Indian Constitution at Work + newspaper",
    "Geography": "NCERT XI Physical Geography and India: Physical Environment + NCERT XII India: People and Economy "
                 "+ G.C. Leong + Oxford/Orient Blackswan Atlas",
}
