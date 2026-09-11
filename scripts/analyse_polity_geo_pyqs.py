#!/usr/bin/env python3
"""Topic-wise analysis of every UPSC *Polity* and *Geography* previous-year
question held in this repository.  Its output drives the 6-hr/day
Polity + Geography sprint plan (see scripts/build_pg_sprint_plan.py).

Inputs (already in the repository):
  data/prelims.json             Prelims 1995-2026, 3,200 records, subject-tagged
  data/mains.json               Mains 2011-2025 (GS1-GS4 + Essay), tag-tagged
  data/pyq_backsolve/GS_*.json  per-question recurrence tier / coverage produced
                                by scripts/pyq_backsolve.py (2015-2026)

Outputs (build_upsc_pg/):
  pyq_analysis.csv      one row per Polity/Geography Prelims question: study
                        unit, bucket (core syllabus vs spill-over), matched
                        keywords, backsolve recurrence tier, answer, source URL
  pyq_summary.json      topic ranking over 3 windows (all 32 papers / last 10 /
                        last 5), year-wise counts, spill-over profile, mains
                        clusters, recurrence ranking, unit catalogue
  PYQ_TOPIC_AUDIT.md    4 sample questions per unit + per spill-over bucket, so
                        the keyword rules can be eyeballed instead of trusted

How classification works
------------------------
Rule based, not hand labelled.  Every study unit owns a list of
``(weight, regex)`` rules and is scored against ``question + options``:
  weight 5 = definitional term (an Article number, an institution's name, a
             geography term of art) - a single hit dominates;
  weight 3 = strong topical term;  weight 1 = weak/contextual term.
Highest score wins; ties break towards the unit listed earlier, and the lists
are therefore ordered *most specific first* so that "Public Accounts Committee"
beats a generic "committee" hit.

The repository's own ``subject`` tag is generous, so a second layer sorts every
question into a *bucket*:
  core             - answerable from the locked Polity/Geography booklist
  core-weak        - one weak keyword hit only; counted as core, low confidence
  spill:<bucket>   - really environment/biodiversity, international orgs &
                     places, schemes/governance current affairs, economy or
                     science-tech.  These still sit in the same GS paper, so the
                     plan has to pay for them - but not with Laxmikanth hours.
  unclassified     - matched nothing; reported in the audit file for rule fixes

Run ``python3 scripts/analyse_polity_geo_pyqs.py --sample 5`` to print examples.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "build_upsc_pg"

POLITY_SUBJECTS = {"polity-and-governance", "polity"}
GEO_SUBJECTS = {"geography"}
ENV_SUBJECTS = {"environment"}          # counted with Geography, then re-bucketed

WINDOWS = [
    ("all", 1995, 2026, "all 32 papers (1995-2026)"),
    ("last10", 2017, 2026, "last 10 papers (2017-2026)"),
    ("last5", 2022, 2026, "last 5 papers (2022-2026)"),
]

CORE_BUCKETS = ("core", "core-weak")

# ---------------------------------------------------------------------------
# Study units.  One unit = one 90-minute deep-study block in the sprint plan and
# maps onto real chapters of the locked booklist (Laxmikanth / NCERT / Leong /
# Atlas).  The PYQ count per unit is what ranks the plan - not opinion.
# Lists are ordered MOST SPECIFIC FIRST (that is the tie-break order).
# ---------------------------------------------------------------------------

POLICY_UNITS = [
    ("P09", "Parliamentary committees & delegated legislation",
     "Laxmikanth ch. 24 + 33", [
        # a named parliamentary committee is more specific than a body it merely
        # mentions (the 2013 PAC question also names the CAG) - hence weight 7
        (7, r"\b(public accounts committee|committee on public accounts|estimates committee|committee on public undertakings|public undertakings committee|departmentally-? ?related (parliamentary )?standing committee|departmental (parliamentary )?standing committee|business advisory committee|committee on privileges|privileges committee|committee on subordinate legislation|joint parliamentary committee|select committee|consultative committee)\b"),
        (3, r"\b(parliamentary committee|committee of parliament|jpc\b|delegated legislation)\b"),
     ]),
    ("P17", "Constitutional bodies - ECI, UPSC, CAG, AG, Finance Commission, NCs",
     "Laxmikanth ch. 42-50", [
        (5, r"\b(election commission of india|chief election commissioner|election commissioner|union public service commission|upsc|state public service commission|comptroller (and|&)? auditor general|cag\b|attorney general|solicitor general|finance commission|article 280\b|article 148\b|article 324\b|national commission for scheduled castes|national commission for scheduled tribes|national commission for backward classes|ncsc|ncst|ncbc|special officer for linguistic minorities|delimitation commission)\b"),
        (3, r"\b(constitutional (body|bodies)|audit(ed)? (of|by) the cag|consolidated fund.*audit)\b"),
     ]),
    ("P18", "Non-constitutional, statutory & regulatory bodies",
     "Laxmikanth ch. 51-57", [
        (5, r"\b(national human rights commission|nhrc|state human rights commission|national commission for women|ncw\b|central information commission|state information commission|information commissioner|lokpal|lokayukta|central vigilance commission|cvc\b|central bureau of investigation|cbi\b|law commission|national commission for minorities|nabard|sebi\b|insolvency and bankruptcy board|competition commission|central administrative tribunal|national green tribunal|ngt\b)\b"),
        (3, r"\b(statutory body|regulatory (body|authority)|autonomous body|quasi-judicial)\b"),
     ]),
    ("P19", "Elections, Representation of the People Act & electoral reforms",
     "Laxmikanth ch. 43 + RPA 1950/51", [
        (5, r"\b(representation of the people act|rpa\b|electoral (reform|bond|roll|literacy|offence|malpractice)|e\.?v\.?m\.?|electronic voting machine|vvp(at)?\b|voter verifiable|model code of conduct|nota\b|disqualification of (a )?(member|mla|mp|legislator)|office of profit|paid news|criminali[sz]ation of politics|first past the post|proportional representation|universal adult (suffrage|franchise)|secret ballot|by-?election|repoll)\b"),
        (3, r"\b(delimitation|voter|polling|election (process|conduct|commissioner)'?s?)\b"),
     ]),
    ("P15", "Emergency provisions - National, State & Financial",
     "Laxmikanth ch. 38", [
        (5, r"\b(emergency provisions?|national emergency|article 35[2-9]\b|article 360\b|proclamation of emergency|financial emergency|armed rebellion|internal disturbance|state emergency|president'?s rule)\b"),
        (3, r"\b(44th amendment.*emergency|emergency.*fundamental rights?)\b"),
     ]),
    ("P16", "Local self-government - 73rd/74th Amendment, PESA, urban bodies",
     "Laxmikanth ch. 39-40", [
        (5, r"\b(panchayat|panchayati raj|73rd (constitutional )?amendment|74th (constitutional )?amendment|municipalit\w*|nagar (palika|nigam|panchayat)|gram(a)? sabha|district planning committee|metropolitan planning committee|state election commission|state finance commission|pesa\b|provisions of the panchayats|notified tribal area)\b"),
        (3, r"\b(decentrali[sz]ation|balwant rai|ashok mehta|l\.? ?m\.? singhvi|local self-government|local bodies|urban local)\b"),
     ]),
    ("P20", "5th & 6th Schedule, tribal and minority protections",
     "Laxmikanth ch. 11, 41 + special areas", [
        (5, r"\b(sixth schedule|fifth schedule|scheduled areas|tribal advisory council|autonomous district council|anglo-indian|religious minorit\w*|linguistic minorit\w*|forest rights act|scheduled tribes and other traditional forest dwellers)\b"),
        (3, r"\b(scheduled tribes?\b.*constitution|minority institutions)\b"),
     ]),
    ("P21", "New criminal & rights-era laws (BNS / BNSS / BSA, RTI, RTE, JJ)",
     "Current affairs + bare acts", [
        (5, r"\b(bharatiya nyaya sanhita|bharatiya nagarik suraksha sanhita|bharatiya sakshya adhiniyam|bnss|zero fir|first information report|anticipatory bail|arrest (procedure|guidelines)|sedition|right to information act|rti act|right to education act|rte act|juvenile justice|protection of children from sexual offences|posh act|whistle ?blowers? protection|prevention of atrocities act)\b"),
        (3, r"\b(cognis(z|a)ble offence|cognizable offence|criminal procedure|dk basu|arnesh kumar|criminal law)\b"),
     ]),
    ("P12", "Judiciary I - Supreme Court: jurisdiction, powers, judicial review",
     "Laxmikanth ch. 31", [
        (5, r"\b(supreme court|chief justice of india|collegium|national judicial appointments commission|njac|judicial review|judicial activism|judicial overreach|article 12[4-9]\b|article 13[0-9]\b|article 14[0-3]\b|special leave petition|curative petition|review petition|contempt of court|master of the roster|appellate jurisdiction|advisory jurisdiction|original jurisdiction|writ jurisdiction|court of record)\b"),
        (3, r"\b(judgment|judgement|verdict|bench of the court|apex court|constitutional (interpretation|bench))\b"),
     ]),
    ("P13", "Judiciary II - High Courts, subordinate courts & tribunals",
     "Laxmikanth ch. 32-33", [
        (5, r"\b(high court|article 21[4-9]\b|article 22[0-9]\b|article 23[01]\b|district (judge|judiciary|court)|subordinate court|tribunal\w*|article 323a?\b|lok adalat|gram nyayalaya|fast track court|all india judicial service|bar council|e-?courts|virtual court)\b"),
        (3, r"\b(judicial appointment|judicial (infrastructure|vacanc\w+))\b"),
     ]),
    ("P06", "President & Vice-President - election, powers, pardoning, ordinance",
     "Laxmikanth ch. 18-19", [
        (5, r"\b(president of india|president'?s? (power|veto|pardon|suspensive|pocket|assent)|pardoning power|article 72\b|article 61\b|article 123\b|ordinance|vice-?president|electoral college (for|of) the president|impeachment (of|procedure against) the president|clemency)\b"),
        (3, r"\b(article 6[02-9]\b|article 7[013-9]\b|presidential (election|form of government|proclamation))\b"),
     ]),
    ("P08", "Legislative procedure - Bills, budget & financial business",
     "Laxmikanth ch. 23 + 35", [
        (5, r"\b(ordinary bill|money bill|finance bill|constitution(al)? amendment bill|article 110\b|article 117\b|budget\b|annual financial statement|appropriation bill|vote on account|cut motion|guillotine|consolidated fund|contingency fund|public account|charged (expenditure|on the consolidated)|private member'?s bill|bill (lapses|lapsing|introduced in)|assent of the president)\b"),
        (3, r"\b(financial business|passed by both houses|joint committee on (a )?bill|legislative procedure)\b"),
     ]),
    ("P07", "Parliament - composition, sessions, devices, motions & privileges",
     "Laxmikanth ch. 22-23 + 25", [
        (5, r"\b(lok sabha|rajya sabha|parliament of india|speaker|deputy speaker|chairman of rajya sabha|pro tem speaker|motion of no-confidence|no-confidence motion|censure motion|adjournment motion|calling attention (notice|motion)|privilege motion|question hour|zero hour|short duration discussion|half an hour discussion|special mention|motion of thanks|point of order|quorum|casting vote|parliamentary privilege\w*|joint sitting|article 108\b|joint session|anti-defection|tenth schedule|parliamentary (forum|forum s)|dissolution of (the )?lok sabha)\b"),
        (3, r"\b(session of parliament|members of parliament|mp\b|mplads|parliamentary (practice|procedure|democracy))\b"),
        (1, r"\b(bill\b|legislation|law making)\b"),
     ]),
    ("P10", "Union Executive - Prime Minister, Council of Ministers, Cabinet",
     "Laxmikanth ch. 20-21", [
        (5, r"\b(prime minister|council of ministers|union cabinet|cabinet (secretary|secretariat|rank|decision)|kitchen cabinet|collective responsibility|article 7[45]\b|article 78\b)\b"),
        (3, r"\b(ministry of [a-z]+|minister of [a-z]+|cabinet committee)\b"),
     ]),
    ("P11", "Governor, State Executive & State Legislature",
     "Laxmikanth ch. 26-30", [
        (5, r"\b(governor|lieutenant governor|chief minister|state council of ministers|advocate general|legislative assembly|legislative council|vidhan (sabha|parishad)|speaker of (the )?legislative assembly|article 15[3-9]\b|article 16[0-9]\b|article 17[0-9]\b|article 20[01]\b|pleasure of the (president|governor))\b"),
        (3, r"\b(state legislature|deputy chief minister|state (cabinet|ministers)|article 2[01]\d\b)\b"),
     ]),
    ("P14", "Federalism - Centre-State relations, Inter-State bodies, UTs, GST Council",
     "Laxmikanth ch. 10, 16-17, 41", [
        (5, r"\b(federalis(z|m)|centre-state relation\w*|center-state relation\w*|union list|state list|concurrent list|seventh schedule|inter-?state council|zonal council|gst council|niti aayog|planning commission|union territor\w+|article 239aa?\b|article 2[4-9]\d\b|article 30[01]\b|government of national capital territory|cooperative federalism|competitive federalism|sarkaria commission|punchhi commission|all india service\w*|inter-?state (water )?(dispute|river water)|article 262\b)\b"),
        (3, r"\b(rajamannar|residuary powers|federal (structure|feature|spirit)|new state formation|reorganisation act)\b"),
     ]),
    ("P05", "Amendment of the Constitution & Basic Structure doctrine",
     "Laxmikanth ch. 12 + amendment register", [
        (7, r"\b(basic structure|kesavananda|minerva mills|golak nath)\b"),
        (5, r"\b(amendment of the constitution|constitutional amendment|article 368\b|special majority|ratified by (half the )?states)\b"),
        (3, r"\b((\d{1,3})(st|nd|rd|th) amendment|amendment act)\b"),
     ]),
    ("P03", "Fundamental Rights - classification, Articles 12-35 & enforcement",
     "Laxmikanth ch. 11", [
        (5, r"\b(fundamental right\w*|article 1[2-9]\b|article 2[0-9]\b|article 3[0-2]\b|right to equality|right to freedom|freedom of speech|right against exploitation|right to (religion|constitutional remedies)|cultural and educational right\w*|habeas corpus|mandamus|certiorari|prohibition\b|quo warranto|writ\w*|public interest litigation|p\.?i\.?l\.?|minority educational institution|untouchability|preventive detention)\b"),
        (3, r"\b(martial law|article 33\b|article 34\b|justiciable|rights? (of|for) (citizens|minorities))\b"),
     ]),
    ("P04", "DPSP, Fundamental Duties & the FR-DPSP balance",
     "Laxmikanth ch. 12-14", [
        (5, r"\b(directive principle\w*|dpsp\b|part iv of the constitution|article 3[6-9]\b|article 4[0-9]\b|article 5[01]\b|fundamental dut\w+|article 51a\b|uniform civil code|welfare state)\b"),
        (3, r"\b(gandhian principle|socialist|liberal-intellectual|instrument of instructions|rights and duties|non-justiciable)\b"),
     ]),
    ("P01", "Constitution: making, sources, features & Preamble",
     "Laxmikanth ch. 1-5", [
        (5, r"\b(constituent assembly|making of the constitution|constitution (was )?(adopted|enacted|came into force)|preamble|salient features? of the constitution|sources? of the (indian )?constitution|objective resolution|cabinet mission plan|government of india act,? 19(19|35)|indian independence act|mountbatten plan|fundamental rights committee)\b"),
        (3, r"\b(quasi-federal|unitary (in nature|spirit)|federal polity|26th november|drafting committee|constitution day)\b"),
     ]),
    ("P02", "Schedules & Parts, Union territory, Citizenship, Official language",
     "Laxmikanth ch. 6-9 + Schedules", [
        (5, r"\b((first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth) schedule|schedules? (to|of) the (indian )?constitution|articles? of the constitution|citizenship|article [5-9]\b|article 1[01]\b|single citizenship|official language|eighth schedule language\w*|classical language|union and its territory|article [1-4]\b)\b"),
        (3, r"\b(domicile|national language|hindi|scheduled language|language\w* of (the union|states))\b"),
     ]),
    ("P22", "Public administration & governance machinery (services, funds, audit)",
     "Laxmikanth ch. 58-70", [
        (5, r"\b(all india services?|civil services?|i\.?a\.?s\.?|i\.?p\.?s\.?|i\.?f\.?s\.?|department of personnel|cabinet secretariat|prime minister'?s office|citizen charter|social audit|grievance redress\w*|e-?governance|digital india land records|direct benefit transfer|dbt\b|public procurement|vigilance (commission|mechanism)|public financial management|administrative reform\w*)\b"),
        (3, r"\b(second arc|bureaucracy|weberian|civil servant|government machinery)\b"),
     ]),
    ("P24", "Constitutional theory - rule of law, liberty, democracy, constitutionalism",
     "Laxmikanth ch. 1-5 + NCERT XI", [
        (5, r"\b(rule of law|constitutionalism|liberty|liberal democracy|separation of powers|checks and balances|due process of law|procedure established by law|best safeguard of|main purpose of the constitution|chief purpose of the constitution|parliamentary form of government|presidential form of government|sovereign\w*|democracy|democratic (rights|values|polity)|natural rights|social contract|doctrine of severability|doctrine of eclipse|colourable legislation|pith and substance)\b"),
        (3, r"\b(freedom|equality|justice|fraternity|articles? of the constitution|constitutional (value|ideal|spirit|morality))\b"),
     ]),
    ("P23", "Schemes, ministries, indices & reports (current-affairs polity)",
     "Newspaper + monthly compilation", [
        (3, r"\b(scheme\w*|programme\w*|mission\b|initiative\w*|portal\w*|abhiyan|yojana|launched by|ministry of|department of|nodal (ministry|agency)|flagship)\b"),
        (2, r"\b(index\b|report (by|of)|ranking|committee (headed|chaired)|task force|national policy on|guidelines)\b"),
     ]),
]

GEO_UNITS = [
    ("G06", "Monsoon, ENSO & the climate of India",
     "NCERT XI India: Physical Env ch. 4; Leong Pt 2", [
        (5, r"\b(monsoon\w*|south-?west monsoon|north-?east monsoon|retreating monsoon|monsoon trough|itcz|inter-?tropical convergence zone|el nino|la nina|enso\b|indian ocean dipole|monsoon break|onset of (the )?monsoon|withdrawal of (the )?monsoon|koppen|climate (classification|of india)|rainfall distribution|western disturbance\w*|kal baisakhi|mango shower|cherry blossom|nor'?westers?)\b"),
        (3, r"\b(seasonal rainfall|average annual rainfall|wettest|driest (place|region)|rainfall (pattern|variability))\b"),
     ]),
    ("G08", "Oceanography II - currents, straits, gulfs, seas & marine mapping",
     "Atlas + NCERT XI ch. 14", [
        (5, r"\b(ocean current\w*|gulf stream|kuroshio|oyashio|labrador current|benguela|canary current|california current|peru current|humboldt|north atlantic drift|strait\w*|isthmus|suez canal|panama canal|coral reef\w*|great barrier reef|bleaching|upwelling|downwelling|sea bordering|bordering countr\w+|exclusive economic zone|eez\b|gulf of|bay of bengal|cape of good hope)\b"),
        (3, r"\b(sea\w*|ocean\w*|coastline|maritime (boundary|zone)|archipelago)\b"),
     ]),
    ("G07", "Oceanography I - relief, temperature, salinity, waves & tides",
     "NCERT XI Physical ch. 13-14", [
        (5, r"\b(salinity|tide\w*|spring tide|neap tide|continental shelf|continental slope|deep sea plain|abyssal|ocean(ic)? trench|mid-?oceanic ridge|guyot|atoll\b|ocean (floor|bottom|relief)|ocean mean temperature|thermohaline|ocean (temperature|heat content))\b"),
        (3, r"\b(wave\w*|swell|lagoon|ocean\w*|marine (deposit|resource))\b"),
     ]),
    ("G04", "Climatology II - pressure belts, winds, jet streams & Coriolis",
     "NCERT XI Physical ch. 10-11; Leong Pt 2", [
        (5, r"\b(pressure belt\w*|equatorial low|sub-?tropical high|polar (easterlies|front|high)|trade wind\w*|westerlies|coriolis|ferrel cell|hadley cell|geostrophic wind|jet stream\w*|local wind\w*|chinook|foehn|fohn|mistral|sirocco|harmattan|bora|loo\b|horse latitudes|doldrums|pressure gradient|anticyclone|planetary wind\w*|seasonal wind\w*)\b"),
        (3, r"\b(wind\w*|atmospheric (circulation|pressure)|high pressure|low pressure)\b"),
     ]),
    ("G05", "Climatology III - humidity, clouds, precipitation, fronts & cyclones",
     "NCERT XI Physical ch. 11-12; Leong Pt 2", [
        (5, r"\b(humidity|relative humidity|dew point|condensation|cloud\w*|cumulus|stratus\b|nimbus|cirrus|precipitation|convectional rainfall|orographic (rainfall|rain)|frontal rain|air mass\w*|weather front|cyclone\w*|hurricane|typhoon|tornado|temperate cyclone|extra-?tropical|tropical cyclone|storm surge|eye of the (storm|cyclone)|fog\b|frost\b|inversion of temperature|thunderstorm|hailstorm)\b"),
        (3, r"\b(rainfall\b|rain\b|drought\b|depression\b|low pressure system)\b"),
     ]),
    ("G03", "Climatology I - atmosphere, insolation, heat budget & temperature",
     "NCERT XI Physical ch. 8-9; Leong Pt 2", [
        (5, r"\b(atmosphere\w*|troposphere|stratosphere|mesosphere|thermosphere|ionosphere|exosphere|ozone layer|ozonosphere|insolation|albedo|heat budget|greenhouse (gas|effect)|global warming|temperature inversion|isotherm|lapse rate|specific heat|solar radiation|short-?wave radiation|long-?wave radiation|radiation balance|water vapou?r)\b"),
        (3, r"\b(temperature|altitude|upper atmosphere|climate change)\b"),
     ]),
    ("G01", "Geomorphology I - earth's interior, rocks, tectonics, quakes & volcanoes",
     "NCERT XI Physical ch. 1-5; Leong Pt 1", [
        (5, r"\b(plate tectonics|continental drift|sea floor spreading|earthquake\w*|seismic\w*|richter scale|pacific ring of fire|volcano\w*|volcanism|magma|lava\b|lithosphere|asthenosphere|mantle\b|earth'?s crust|igneous|sedimentary|metamorphic|rock cycle|weathering|mass wasting|landslide\w*|tsunami)\b"),
        (3, r"\b(rock\w*|mineral\w*|earth'?s interior|core of the earth|geolog\w+|pangaea|gondwana\w*)\b"),
     ]),
    ("G02", "Geomorphology II - exogenic processes & landforms",
     "NCERT XI Physical ch. 6-7; Leong Pt 1", [
        (5, r"\b(glacial landform\w*|moraine|cirque|fjord|esker|drumlin|aeolian|sand dune\w*|barchan|loess|karst|stalactite|stalagmite|fluvial landform\w*|meander|oxbow (lake)?|delta formation|estuary|coastal landform\w*|sea cliff|beach\b|inselberg|mushroom rock|playa|gorge\b|canyon|pothole\b|valley\b)\b"),
        (3, r"\b(landform\w*|deposition\b|erosion\b|erosional feature|graded profile|rejuvenation)\b"),
     ]),
    ("G23", "Latitude / longitude & earth-as-a-planet logic",
     "NCERT XI Fundamentals ch. 1-2", [
        (5, r"\b(latitude\w*|longitude\w*|equator\b|tropic of cancer|tropic of capricorn|arctic circle|antarctic circle|prime meridian|international date line|ist\b|gmt\b|utc\b|great circle|earth'?s (rotation|revolution|axis)|length of the day|solstice|equinox|perihelion|aphelion|inclination of the (earth|axis)|standard meridian|time zone\w*|easternmost|westernmost|northernmost|southernmost)\b"),
        (3, r"\b(passes through|traverses|does not pass through|along the (coast|border)|meridian\w*|solar system|sunrise|day and night|milky way|planet\w*|hemisphere\w*)\b"),
     ]),
    ("G09", "Indian physiography - Himalayas, plains, plateau, Ghats, coasts, islands",
     "NCERT XI India: Physical Env ch. 2", [
        (5, r"\b(himalaya\w*|western ghats|eastern ghats|deccan plateau|chotanagpur|indo-?gangetic|northern (plains|plain)|thar desert|coastal plain\w*|konkan|malabar coast|coromandel|andaman|nicobar|lakshadweep|shipki la|nathu la|zojila|zoji la|bhor ghat|pal ghat|k2\b|kanchenjunga|nanda devi|doddabetta|anaimudi|guru shikhar|mahendragiri|aravalli\w*|vindhya\w*|satpura\w*|shillong plateau|bhabar|terai\b|bhangar|khadar|siachen|gangotri|yamunotri|physiographic (division|region|province)|dun valley)\b"),
        (3, r"\b(mountain (range|peak)|peak\b|pass\b|plateau\b|plain\w*|island\w*|glacier\w*|hillock|ghat\w*)\b"),
     ]),
    ("G10", "Drainage I - Himalayan rivers, basins, tributaries & river linking",
     "NCERT XI India: Physical Env ch. 3", [
        (5, r"\b(ganga\b|ganges|yamuna|brahmaputra|indus\b|sutlej|beas\b|ravi\b|chenab|jhelum|ghaghara|gandak|kosi\b|son river|alakananda|bhagirathi|tributar\w+|river basin|drainage basin|watershed\b|inter-?linking of rivers|river link\w*|doab\b|antecedent drainage|himalayan river\w*|himalayan drainage)\b"),
        (3, r"\b(river\w*|delta\b|confluence|distributar\w+|catchment|left bank|right bank)\b"),
     ]),
    ("G11", "Drainage II - Peninsular rivers, lakes & wetlands",
     "NCERT XI India: Physical Env ch. 3", [
        (5, r"\b(narmada|tapi\b|tapti|godavari|krishna river|cauvery|kaveri|mahanadi|peninsular river\w*|west flowing river\w*|east flowing river\w*|rift valley|pulicat|chilika|sambhar|loktak|wular|dal lake|vembanad|kolleru|tsomoriri|hirakud|backwater\w*|wetland\w*|ramsar\b|oxbow lake)\b"),
        (3, r"\b(lake\w*|river\w*|lagoon|marsh\w*|reservoir)\b"),
     ]),
    ("G12", "Soils - formation, classification, erosion & conservation",
     "NCERT XI India: Physical Env ch. 6", [
        (5, r"\b(soil\w*|alluvial soil|black soil|regur|red soil|laterite\w*|arid soil|saline soil|forest soil|peat\b|soil erosion|soil conservation|mulching|contour (ploughing|bund)|terracing|strip cropping|shelter belt|salinity|alkalinity|icar (soil )?classification|soil (horizon|profile|texture|health card))\b"),
        (3, r"\b(humus|leaching|land degradation|desertification)\b"),
     ]),
    ("G13", "Natural vegetation, forest types & biogeography",
     "NCERT XI India: Physical Env ch. 5; Leong", [
        (5, r"\b(forest (type|cover|area)|natural vegetation|tropical (evergreen|deciduous|thorn)|montane (forest|vegetation)|alpine (vegetation|forest)|grassland\w*|savannah|steppe\b|prairie\b|pampas|llanos|campos|veld\b|downs\b|taiga|tundra|coniferous|mangrove\w*|sundarban\w*|biodiversity hotspot|biome\b|leaf litter|shola\b|deciduous forest|evergreen forest)\b"),
        (3, r"\b(flora\b|fauna\b|vegetation|ecosystem\b|tree species|deciduous\b|evergreen\b|jackfruit|mahua|teak\b|sal tree|neem\b|banyan|peepal|mango tree|sandal\w*|ebony|rosewood|bamboo|cork oak|chir pine|deodar|chinar|rhododendron)\b"),
     ]),
    ("G14", "Protected areas - parks, reserves, biospheres, mangroves & coral (mapping)",
     "Atlas + MoEFCC list", [
        (5, r"\b(national park\w*|wildlife sanctuary|tiger reserve\w*|biosphere reserve\w*|elephant reserve|bird sanctuary|ramsar site|world heritage site|project tiger|project elephant|kaziranga|periyar|bandipur|nagarhole|silent valley|great nicobar|pichavaram|bhitarkanika|gulf of mannar|nilgiri\w*|anamalai|mudumalai|rajaji\b|corbett\b|kanha\b|pench\b|satpura|valmiki|dudhwa)\b"),
        (3, r"\b(protected area\w*|conservation reserve|community reserve|reserve forest)\b"),
     ]),
    ("G15", "Agriculture I - cropping patterns, crop requirements & belts",
     "NCERT XII India: People & Economy ch. 4", [
        (5, r"\b(crop\w*|kharif|rabi\b|zaid\b|rice\b|paddy|wheat\b|maize|cotton|jute\b|sugarcane|groundnut|mustard|pulses|millets?|oilseeds?|plantation (crop|agriculture)|horticulture|sericulture|cropping (pattern|system|intensity)|green revolution|gm crop\w*|genetically modified|high yielding variet\w+|nitrogen-fixing|agriculture\b)\b"),
        (3, r"\b(mixed farming|shifting cultivation|jhum\b|subsistence|commercial agriculture|dryland|farm\b|agricultural)\b"),
     ]),
    ("G16", "Agriculture II - irrigation, water resources & agro-climatic zones",
     "NCERT XII ch. 5 + GS-3 overlap", [
        (5, r"\b(irrigation|canal (irrigation|network)|tube ?well\w*|drip irrigation|sprinkler|micro-?irrigation|water conservation|water harvesting|water table|watershed (management|development)|groundwater|aquifer\w*|water-?logging|command area|agro-?climatic zone|food security|food corporation|minimum support price|reservoir\w*|dam\b|multipurpose (project|river valley)|per drop more crop)\b"),
        (3, r"\b(water\b|canal\w*|flood (control|plain)|drought management|irrigated area|barrage\b|weir\b|check dam|tank irrigation)\b"),
     ]),
    ("G17", "Resources, minerals & energy geography",
     "NCERT XII ch. 5-6 + atlas", [
        (5, r"\b(mineral\w*|ore\b|iron ore|coal\b|lignite|bauxite|manganese|copper|zinc\b|lead\b|chromite|mica\b|limestone|dolomite|uranium|thorium|monazite|petroleum|crude oil|natural gas|refiner\w+|solar (energy|park|power)|wind (energy|farm|power)|geothermal|tidal energy|hydroelectric|nuclear (plant|power|reactor)|renewable energy)\b"),
        (3, r"\b(mining|mine\b|reserve\w*|deposit\w*|belt\b|energy (resource|security))\b"),
     ]),
    ("G18", "Industries & location factors",
     "NCERT XII ch. 6-7; Leong Pt 2", [
        (5, r"\b(industr\w+|steel plant|textile (mill|industr\w+)|cement (plant|industr\w+)|fertiliser (plant|industr\w+)|sugar mill|petrochemical|automobile (industr\w+|hub)|information technology park|footloose industr\w+|location (factor|theory)|weber'?s|industrial (corridor|region|township|belt)|special economic zone|sez\b)\b"),
        (3, r"\b(factory|manufacturing|agro-based industr\w+|cottage industr\w+|small scale)\b"),
     ]),
    ("G19", "Transport, ports & communication geography",
     "NCERT XII ch. 8-10 + atlas", [
        (5, r"\b(railway\w*|national highway\w*|expressway\w*|waterway\w*|inland waterway\w*|port\w*|harbour|sagarmala|airport\w*|pipeline\w*|haldia|kandla|mundra|jnpt|jawaharlal nehru port|ennore|paradip|visakhapatnam|tuticorin|kochi\b|mormugao|new mangalore|shipping|maritime|bharatmala|golden quadrilateral|multi-?modal|logistics)\b"),
        (3, r"\b(transport\w*|road\w*|connectivity|corridor)\b"),
     ]),
    ("G20", "Human geography - population, migration, settlements & tribes",
     "NCERT XII ch. 1-3", [
        (5, r"\b(population\b|census\b|density of population|sex ratio|literacy rate|age (structure|composition)|demographic (transition|dividend)|fertility (rate|decline)|mortality|infant mortality|migration\b|migrant\w*|urbani[sz]ation|urban (agglomeration|sprawl)|metropolitan city|slum\w*|rural settlement|settlement pattern|tribe\w*|tribal (population|group)|jarawa|sentinelese|gond\b|bhil\b|santhal|toda\b|siddi|ong\w+|great andamanese|van gujjars?)\b"),
        (3, r"\b(working population|dependency ratio|people\b|inhabitants|demograph\w+|life expectancy|human settlement\w*|un-habitat|urban growth|city\w*|town\w*|metropolitan\w*)\b"),
     ]),
    ("G21", "World physical geography - continents, ranges, deserts, grasslands, rivers",
     "Leong Pt 1-2 + NCERT XI Fundamentals", [
        (5, r"\b(andes|rockies|appalachian\w*|alps\b|atlas mountains|kilimanjaro|sahara|kalahari|gobi\b|atacama|great dividing range|urals?\b|caucasus|carpathian|great lakes|lake (victoria|baikal|tangan\w+|malawi|superior|ontario)|amazon\b|nile\b|congo\b|mississippi|yangtze|mekong|danube|rhine|volga|dead sea|caspian|aral sea|continent\w*|tundra\b|taiga\b|mediterranean (region|climate)|temperate grassland)\b"),
        (3, r"\b(mountain range\w*|desert\w*|grassland\w*|highland\w*|plateau\w*|river\w*)\b"),
     ]),
    ("G22", "World regional geography & places in the news (mapping)",
     "Atlas daily drill", [
        (5, r"\b(countr\w+|bordering|landlocked|shares a (land )?border|towns? sometimes mentioned in (the )?news|mentioned in the news|correctly matched.*country|capital of|member\w* of (the )?(organization|organisation|association|group|union)|west bank|golan|crimea|donbas|nagorno-?karabakh|south china sea|east china sea|region\w* (in|of) the news|baltic (sea|states)|black sea|red sea|mediterranean sea|persian gulf)\b"),
        (3, r"\b(located in|situated in|place\w* in (the )?news|border\w*|neighbour\w*|region\b|shares boundar\w+|correct sequence of\w*|proceeds from (south|north|east|west)|administrative capital|new capital|south-?east asia|west asia|central asia|latin america|sub-?saharan|african countr\w+|european countr\w+|cities? in)\b"),
     ]),
    ("G24", "Environment-geography overlap: climate impacts, pollution & disasters",
     "NCERT + one environment compilation", [
        (5, r"\b(climate change|carbon (credit|market|footprint|sink)|kyoto protocol|paris agreement|unfccc|cop\s?\d+|ozone depletion|montreal protocol|acid rain|pollution|smog\b|e-?waste|plastic pollution|microplastic|biomagnification|eutrophication|disaster (management|risk)|hazard\w*|vulnerability|mitigation (and|&) adaptation|sustainable development|green (bond|hydrogen)|net zero|tsunami\b)\b"),
        (3, r"\b(environment\w*|ecolog\w+|emissions?|climate)\b"),
     ]),
]

# ---------------------------------------------------------------------------
# Current-affairs smell test: high score = the question is dynamic, so it is
# paid for out of newspaper/magazine time, not book time.
# ---------------------------------------------------------------------------
CA_RULES = [
    (3, r"\b(launched (by|in)|recently|introduced (by|in)|in the news|mentioned in the news|consider the following (statements|pairs|countries|organisations|organizations)|with reference to)\b"),
    (2, r"\b(scheme|programme|program|mission|initiative|portal|app\b|platform|index|report|ranking|committee|task force|declaration|summit|conference|treaty|convention|agreement)\b"),
    (2, r"\b(ministry|department of|nodal agency|autonomous body|statutory body|constitutional body)\b"),
]

# ---------------------------------------------------------------------------
# Spill-over buckets (see module docstring).
# ---------------------------------------------------------------------------
SPILL_RULES = {
    "environment-biodiversity": [
        (3, r"\b(species|endemic|herbivore|carnivore|detritivore|decomposer|pollinator|food (chain|web)|trophic|ecosystem service|biodiversity|wild ?life (protection )?act|iucn|red list|conservation status|invasive (species|alien)|captive breeding|breeding season|habitat (loss|fragmentation))\b"),
        (3, r"\b(orchid|turtle|tortoise|dolphin|porpoise|whale|shark|ray\b|elephant|rhino|lion|tiger|leopard|cheetah|bear|wolf|fox|camel|deer|antelope|hornbill|crane|stork|ibis|vulture|owl|bat\b|butterfly|bee\b|ant\b|termite|earthworm|millipede|woodlice|jellyfish|seahorse|phytoplankton|zooplankton|seagrass|algae|fungi|lichen|moss|bamboo|sandalwood|red sanders|dugong|pangolin|gibbon|squirrel|insectivorous plant|herbivorous|camel breed|kharai|jackfruit|mahua|teak|camphor|chicory|vanilla|jatropha|pongamia|biodiesel plant|organism\w*|species of)\b"),
        (2, r"\b(flyway|vermin|cites\b|cms\b|itpgrfa|nagoya protocol|cartagena protocol|biosafety|bioprospecting|gene pool|germplasm|schedule (i|ii|iii|iv|v|vi) of the wild ?life)\b"),
        (2, r"\b(carbon (credit|sink|sequestration|market)|kyoto|paris agreement|unfccc|cop\s?\d+|montreal protocol|kigali|basel convention|rotterdam convention|stockholm convention|minamata|green (bond|hydrogen|credit)|esg\b|net zero|climate (finance|adaptation fund|vulnerable forum|action))\b"),
        (2, r"\b(pollutant|pollution|smog|e-?waste|plastic|microplastic|biomagnification|eutrophication|acid rain|heavy metal|particulate matter|pm\s?2\.5|ozone depletion|effluent)\b"),
    ],
    "international-orgs-IR": [
        (3, r"\b(united nations|un (agency|body|organs|security council|general assembly)|bimstec|asean|european union|nato|shanghai cooperation|sco\b|brics|g-?(7|8|20)\b|opec|quad\b|ior-?arc|aiib|world bank|imf\b|wto\b|who\b|unesco|unicef|unep|undp|iaea|opcw|interpol|world economic forum|davos|transparency international|amnesty international|reporters without borders|commonwealth|saarc|african union|organization of (turkic states|islamic cooperation|petroleum exporting)|regional (organisation|organization)|international (organisation|organization|agency|tribunal|court of justice))\b"),
        (2, r"\b(member (states?|nations?|countries?)|founding member|headquarter\w* (in|of)|treaty\b|convention\b|protocol\b|declaration\b|summit (of|in)|joint (military )?exercise|military base|ceasefire|sanctions|peacekeeping|peace-keeping|gulf cooperation council|european stability mechanism|alma-?ata|hague convention|area of conflict|separatist (organisation|organization|movement)|basque|kurdi\w+|conflict mentioned in (the )?news|international agreement)\b"),
        (2, r"\b(chad|guinea|mali|sudan|niger|burkina faso|myanmar|afghanistan|yemen|syria|israel|gaza|ukraine|armenia|azerbaijan|georgia|kazakhstan|uzbekistan|kyrgyzstan|tajikistan|turkmenistan|venezuela|nicaragua|ethiopia|somalia|eritrea|libya|congo|haiti|solomon islands|taiwan|philippines|vietnam|laos|cambodia)\b"),
    ],
    "schemes-governance-CA": [
        (3, r"\b(scheme|programme|program|mission|initiative|portal|abhiyan|yojana|launched by|ministry of|department of|nodal (ministry|agency)|flagship|direct benefit transfer|dbt\b|jan dhan|ayushman bharat|swachh bharat|skill india|make in india|digital india|start-?up india|pradhan mantri|pm-?(kisan|jayani|garib|abhyudaya|wani|gati shakti|poshan|ayu))\b"),
        (2, r"\b(index\b|report (by|of)|ranking|global (report|index)|committee (headed|chaired)|task force|national policy on|guidelines (issued|by)|cabinet (approved|note)|budget (allocation|provision))\b"),
    ],
    "economy": [
        (3, r"\b(gdp|inflation|fiscal deficit|monetary policy|repo rate|interest rate|bond\w*|banking|rbi\b|currency|exchange rate|balance of payments|fdi\b|fpi\b|tax (rate|collection|reform)|gst (rate|compensation)|subsidy|disinvestment|market (capital|regulator)|sebi\b|msme|labour (force|market)|employment|unemployment|provident fund|pension|insurance|credit\b|loan\b|npa\b|farm (income|loan waiver))\b"),
    ],
    "science-tech": [
        (3, r"\b(satellite\w*|launch vehicle|isro|nasa\b|espace|telescope|genome|dna\b|crispr|gene editing|vaccine|virus|bacteria|antibiotic|nanotechnolog\w*|artificial intelligence|blockchain|cryptocurrenc\w*|quantum|semiconductor|missile\w*|drone\w*|robot\w*|biotechnolog\w*|stem cell|in vitro|cloning)\b"),
    ],
}


CURLED = str.maketrans({
    "\u2019": "'", "\u2018": "'", "\u201b": "'", "\u2032": "'",
    "\u201c": '"', "\u201d": '"', "\u2013": "-", "\u2014": "-",
    "\u00a0": " ", "\u2009": " ", "\u2026": "...",
})


def norm(text: str) -> str:
    """Lower-case and de-curly the text so regexes like ``earth'?s`` match the
    Unicode apostrophes that the scraped question bank actually contains."""
    return re.sub(r"\s+", " ", text.translate(CURLED)).lower()


def load_prelims() -> list[dict]:
    d = json.loads((DATA / "prelims.json").read_text(encoding="utf-8"))
    recs: list[dict] = []
    for _year, lst in d["records_by_year"].items():
        recs.extend(lst)
    return recs


def load_backsolve() -> dict[str, dict]:
    """qid -> {tier, cov_flat, dup} from the existing back-solve engine output."""
    out: dict[str, dict] = {}
    for f in sorted((DATA / "pyq_backsolve").glob("GS_*.json")):
        try:
            blob = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        for q in blob.get("questions", []):
            out[q["qid"]] = {"tier": q.get("tier", ""),
                             "cov_flat": q.get("cov_flat", 0.0),
                             "dup": q.get("dup", 0.0)}
    return out


def score(text: str, units: list[tuple]):
    """Return (best_unit, source, score, matched_keywords, all_scores)."""
    t = norm(text)
    scores: Counter = Counter()
    hits_by_unit: dict[str, list[str]] = defaultdict(list)
    for uid, _title, _src, rules in units:
        s = 0
        for w, pat in rules:
            m = re.search(pat, t)
            if m:
                s += w
                hits_by_unit[uid].append(m.group(0).strip())
        scores[uid] = s
    ordered = [u for u, s in scores.most_common() if s > 0]     # stable: list order on ties
    best = ordered[0] if ordered else ""
    src = dict((u[0], u[2]) for u in units).get(best, "")
    return best, src, scores[best] if best else 0, hits_by_unit.get(best, []), scores


def spill_scores(text: str) -> dict[str, int]:
    t = norm(text)
    out = {}
    for bucket, rules in SPILL_RULES.items():
        s = sum(w for w, pat in rules if re.search(pat, t))
        out[bucket] = s
    return out


def ca_score(text: str) -> int:
    t = norm(text)
    return sum(w for w, pat in CA_RULES if re.search(pat, t))


def extended_pool(recs: list[dict], skip_subjects: set[str]) -> dict:
    """Questions tagged as something else (economy, sci-tech, history, ...) that a
    Polity/Geography student can still answer because the *content* is polity or
    geography.  Only definitional hits (score >= 5) are counted, and only when the
    subject really is polity/geo rather than a spill-over bucket.
    """
    per_unit: Counter = Counter()
    per_subject: Counter = Counter()
    examples: dict[str, list[str]] = defaultdict(list)
    n = 0
    for r in recs:
        if r.get("subject", "") in skip_subjects:
            continue
        text = f"{r.get('question', '')} {' '.join(r.get('options') or [])}"
        best_uid, best_sc, best_subj = "", 0, ""
        for subj_label, units in (("Polity", POLICY_UNITS), ("Geography", GEO_UNITS)):
            uid, _src, sc, _hits, _all = score(text, units)
            if sc > best_sc:
                best_uid, best_sc, best_subj = uid, sc, subj_label
        if best_sc < 5 or not best_uid:
            continue
        uid, sc, subject = best_uid, best_sc, best_subj
        sp = spill_scores(text)
        if max(sp.values()) >= sc:
            continue
        n += 1
        per_unit[uid] += 1
        per_subject[r.get("subject", "") or "(untagged)"] += 1
        if len(examples[uid]) < 3:
            examples[uid].append(f"[{r['year']}] ({r.get('subject','')}) "
                                 f"{re.sub(chr(92) + 's+', ' ', r.get('question', ''))[:150]}")
    return {"total": n, "by_unit": dict(per_unit.most_common()),
            "by_tagged_subject": dict(per_subject.most_common()),
            "examples": dict(examples)}


def mains_clusters() -> dict:
    m = json.loads((DATA / "mains.json").read_text(encoding="utf-8"))["papers_by_year"]
    POL_TAGS = {"polity", "indian polity", "constitutional law", "constitution",
                "governance", "political science", "law", "law &amp; legislation",
                "social justice"}
    GEO_TAGS = {"geography", "urbanization", "disaster management", "agriculture",
                "environment", "infrastructure", "industry", "resources"}
    by_paper: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    per_year: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    detail: list[dict] = []
    for y in sorted(m, key=int):
        for paper in ("GS1", "GS2", "GS3"):
            pv = m[y].get(paper) or {}
            for q in pv.get("questions", []):
                tags = {t.strip().lower() for t in q.get("tags", [])}
                if tags & POL_TAGS:
                    cluster = "polity"
                elif tags & GEO_TAGS:
                    cluster = "geography"
                else:
                    continue
                by_paper[paper][cluster] += 1
                by_paper[paper][f"{cluster}_marks"] += int(q.get("marks") or 0)
                per_year[y][f"{paper}_{cluster}"] += 1
                detail.append({"year": int(y), "paper": paper, "cluster": cluster,
                               "q_no": q.get("q_no"), "marks": q.get("marks"),
                               "tags": sorted(tags), "question": q.get("question", ""),
                               "url": q.get("url", "")})
    return {"by_paper": {k: dict(v) for k, v in by_paper.items()},
            "per_year": {k: dict(v) for k, v in sorted(per_year.items(), key=lambda kv: int(kv[0]))},
            "questions": detail}


def mains_unit_themes(mc: dict) -> dict:
    """Score every Mains question with the same unit rules used for Prelims, so a
    study unit can show both its Prelims PYQ count and its Mains question count.
    Only questions inside the polity/geography mains clusters are scored."""
    per_unit: Counter = Counter()
    marks: Counter = Counter()
    recent: Counter = Counter()            # 2019-2025 only
    samples: dict[str, list[str]] = defaultdict(list)
    for q in mc["questions"]:
        units = POLICY_UNITS if q["cluster"] == "polity" else GEO_UNITS
        uid, _src, sc, _hits, _all = score(q["question"], units)
        if sc < 3 or not uid:
            uid = "OTHER-" + ("polity" if q["cluster"] == "polity" else "geography")
        per_unit[uid] += 1
        marks[uid] += int(q.get("marks") or 0)
        if q["year"] >= 2019:
            recent[uid] += 1
        if len(samples[uid]) < 4:
            samples[uid].append(f"[{q['year']} {q['paper']} {q.get('marks')}m] "
                                f"{re.sub(chr(92) + 's+', ' ', q['question'])[:210]}")
    return {"per_unit": dict(per_unit.most_common()),
            "marks": dict(marks), "recent": dict(recent), "samples": dict(samples)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=0,
                    help="print N example questions per unit to stdout")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    recs = load_prelims()
    bs = load_backsolve()
    titles = {u[0]: u[1] for u in POLICY_UNITS + GEO_UNITS}
    sources = {u[0]: u[2] for u in POLICY_UNITS + GEO_UNITS}

    rows: list[dict] = []
    samples: dict[str, list[str]] = defaultdict(list)
    for r in recs:
        subj = r.get("subject", "")
        if subj in POLITY_SUBJECTS:
            subject, units = "Polity", POLICY_UNITS
        elif subj in GEO_SUBJECTS or subj in ENV_SUBJECTS:
            subject, units = "Geography", GEO_UNITS
        else:
            continue
        text = f"{r.get('question', '')} {' '.join(r.get('options') or [])}"
        uid, src, sc, hits, all_scores = score(text, units)
        label = uid or "UNCLASSIFIED"
        sp = spill_scores(text)
        top_spill = max(sp, key=lambda k: sp[k])
        top_spill_score = sp[top_spill]
        if sc >= 3 and sc >= top_spill_score:
            bucket = "core"
        elif top_spill_score >= 3:
            bucket = f"spill:{top_spill}"
        elif sc > 0:
            bucket = "core-weak"
        else:
            bucket = "unclassified"
        rows.append({
            "qid": r["id"], "year": r["year"], "subject": subject,
            "tagged_subject": subj, "unit": label,
            "unit_title": titles.get(label, "unclassified"),
            "source": src, "score": sc, "bucket": bucket,
            "spill_top": top_spill if bucket.startswith("spill") else "",
            "spill_score": top_spill_score,
            "secondary": ",".join([u for u, s in all_scores.most_common() if s > 0][1:4]),
            "keywords": "; ".join(hits[:6]), "ca_score": ca_score(text),
            "tier": bs.get(r["id"], {}).get("tier", ""),
            "cov_flat": bs.get(r["id"], {}).get("cov_flat", ""),
            "dup": bs.get(r["id"], {}).get("dup", ""),
            "answer": r.get("answer", ""), "url": r.get("reference_url", ""),
            "question": re.sub(r"\s+", " ", r.get("question", ""))[:400],
        })
        key = f"{subject}|{label}" if bucket in CORE_BUCKETS else f"{subject}|{bucket}"
        if len(samples[key]) < 6:
            samples[key].append(f"[{r['year']}] {re.sub(chr(92) + 's+', ' ', r.get('question', ''))[:180]}")

    # ---- CSV ---------------------------------------------------------------
    with (OUT / "pyq_analysis.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    # ---- summaries ---------------------------------------------------------
    def in_window(r, lo, hi):
        return lo <= int(r["year"]) <= hi

    def window_counts(subj, lo, hi, core_only=True) -> Counter:
        return Counter(r["unit"] for r in rows
                       if r["subject"] == subj and in_window(r, lo, hi)
                       and (not core_only or r["bucket"] in CORE_BUCKETS))

    def bucket_counts(subj, lo, hi) -> Counter:
        return Counter(r["bucket"] for r in rows
                       if r["subject"] == subj and in_window(r, lo, hi))

    def per_year(subj) -> dict:
        c: dict[int, Counter] = defaultdict(Counter)
        for r in rows:
            if r["subject"] == subj and r["bucket"] in CORE_BUCKETS:
                c[r["year"]][r["unit"]] += 1
        return {str(y): dict(v) for y, v in sorted(c.items())}

    def per_year_totals() -> dict:
        out: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for r in rows:
            kind = "core" if r["bucket"] in CORE_BUCKETS else r["bucket"]
            out[r["year"]][f"{r['subject'].lower()}_{kind}"] += 1
        return {str(y): dict(v) for y, v in sorted(out.items())}

    def recurrence(subj) -> dict:
        core = [r for r in rows if r["subject"] == subj and r["bucket"] in CORE_BUCKETS]
        tier = Counter(r["tier"] for r in core if r["tier"])
        cov = [float(r["cov_flat"]) for r in core if r["cov_flat"] != ""]
        by_unit: dict[str, list[float]] = defaultdict(list)
        tier_by_unit: dict[str, Counter] = defaultdict(Counter)
        for r in core:
            if r["tier"]:
                tier_by_unit[r["unit"]][r["tier"]] += 1
            if r["cov_flat"] != "":
                by_unit[r["unit"]].append(float(r["cov_flat"]))
        avg = {u: round(sum(v) / len(v), 3) for u, v in by_unit.items() if len(v) >= 5}
        recurring = {u: round((c["strict"] + c["medium"] + c["recurring"]) / sum(c.values()), 2)
                     for u, c in tier_by_unit.items() if sum(c.values()) >= 5}
        return {"tiers": dict(tier),
                "avg_cov_flat": round(sum(cov) / len(cov), 3) if cov else 0,
                "by_unit_avg_cov": dict(sorted(avg.items(), key=lambda kv: -kv[1])),
                "by_unit_recurring_share": dict(sorted(recurring.items(), key=lambda kv: -kv[1]))}

    def ranking(subj) -> list[dict]:
        c_all = window_counts(subj, 1995, 2026)
        c10 = window_counts(subj, 2017, 2026)
        c5 = window_counts(subj, 2022, 2026)
        units = POLICY_UNITS if subj == "Polity" else GEO_UNITS
        out = []
        for u in units:
            uid = u[0]
            if not c_all[uid]:
                continue
            out.append({"unit": uid, "title": titles[uid], "source": sources[uid],
                        "all": c_all[uid], "last10": c10[uid], "last5": c5[uid],
                        "per_year_last10": round(c10[uid] / 10, 2)})
        return sorted(out, key=lambda d: (-d["last10"], -d["all"]))

    mc = mains_clusters()
    ext = extended_pool(recs, POLITY_SUBJECTS | GEO_SUBJECTS | ENV_SUBJECTS)
    mc["unit_themes"] = mains_unit_themes(mc)

    summary = {
        "generated_on": date.today().isoformat(),
        "prelims_bank": {
            "total_records": len(recs),
            "polity_rows": sum(1 for r in rows if r["subject"] == "Polity"),
            "geography_rows": sum(1 for r in rows if r["subject"] == "Geography"),
            "polity_core": sum(1 for r in rows if r["subject"] == "Polity" and r["bucket"] in CORE_BUCKETS),
            "geography_core": sum(1 for r in rows if r["subject"] == "Geography" and r["bucket"] in CORE_BUCKETS),
            "polity_unclassified": sum(1 for r in rows if r["subject"] == "Polity" and r["bucket"] == "unclassified"),
            "geography_unclassified": sum(1 for r in rows if r["subject"] == "Geography" and r["bucket"] == "unclassified"),
            "polity_ca_flavoured": sum(1 for r in rows if r["subject"] == "Polity" and r["ca_score"] >= 3),
            "geography_ca_flavoured": sum(1 for r in rows if r["subject"] == "Geography" and r["ca_score"] >= 3),
        },
        "spillover": {s: {w[0]: dict(bucket_counts(s, w[1], w[2])) for w in WINDOWS}
                      for s in ("Polity", "Geography")},
        "windows": {w[0]: {"label": w[3], "years": [w[1], w[2]],
                           "polity_tagged": bucket_counts("Polity", w[1], w[2]).total(),
                           "geography_tagged": bucket_counts("Geography", w[1], w[2]).total(),
                           "polity_core": sum(v for k, v in bucket_counts("Polity", w[1], w[2]).items() if k in CORE_BUCKETS),
                           "geography_core": sum(v for k, v in bucket_counts("Geography", w[1], w[2]).items() if k in CORE_BUCKETS)}
                    for w in WINDOWS},
        "per_year": {"Polity": per_year("Polity"), "Geography": per_year("Geography")},
        "per_year_totals": per_year_totals(),
        "ranking": {"Polity": ranking("Polity"), "Geography": ranking("Geography")},
        "recurrence": {"Polity": recurrence("Polity"), "Geography": recurrence("Geography")},
        "mains": mc,
        "extended_pool": ext,
        "units": [{"id": u[0], "title": u[1], "source": u[2],
                   "subject": "Polity" if u[0].startswith("P") else "Geography",
                   "rank_order": i + 1}
                  for i, u in enumerate(POLICY_UNITS + GEO_UNITS)],
    }
    (OUT / "pyq_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False),
                                          encoding="utf-8")

    # ---- audit markdown ----------------------------------------------------
    L = ["# Polity + Geography PYQ topic audit", "",
         "Rule-based classification of every Polity/Geography-tagged Prelims question in",
         "`data/prelims.json` (1995-2026). If a unit's samples look wrong, tighten its regex",
         "in `scripts/analyse_polity_geo_pyqs.py` and re-run.", ""]
    for subj in ("Polity", "Geography"):
        L += [f"## {subj} - core units", ""]
        for row in summary["ranking"][subj]:
            L += [f"### {row['unit']} - {row['title']}",
                  f"all {row['all']} | last-10 {row['last10']} | last-5 {row['last5']} | source: {row['source']}", ""]
            for s in samples.get(f"{subj}|{row['unit']}", [])[:4]:
                L.append(f"- {s}")
            L.append("")
        L += [f"## {subj} - spill-over & unclassified", ""]
        for b, n in summary["spillover"][subj]["all"].items():
            L += [f"### {b} - {n} questions (all papers)", ""]
            for s in samples.get(f"{subj}|{b}", [])[:4]:
                L.append(f"- {s}")
            L.append("")
    L += ["## Mains questions scored against the same study units (2011-2025)", "",
          "| unit | Mains Qs | marks | since 2019 |", "|---|---:|---:|---:|"]
    for u, n in mc["unit_themes"]["per_unit"].items():
        L.append(f"| {u} | {n} | {mc['unit_themes']['marks'].get(u, 0)} | "
                 f"{mc['unit_themes']['recent'].get(u, 0)} |")
    L.append("")
    for u, ex in mc["unit_themes"]["samples"].items():
        L.append(f"### {u}")
        L += [f"- {e}" for e in ex]
        L.append("")
    L += ["## Cross-subject leak - geography/polity content tagged under another subject", "",
          f"Total: **{ext['total']}** questions (definitional keyword match, spill-over excluded).",
          "By original tag: " + ", ".join(f"{k} {v}" for k, v in ext["by_tagged_subject"].items()), "",
          "| unit | extra Qs |", "|---|---:|"]
    L += [f"| {u} | {n} |" for u, n in ext["by_unit"].items()]
    L.append("")
    for u, ex in ext["examples"].items():
        L.append(f"### {u}")
        L += [f"- {e}" for e in ex]
        L.append("")
    (OUT / "PYQ_TOPIC_AUDIT.md").write_text("\n".join(L), encoding="utf-8")

    # ---- console -----------------------------------------------------------
    for subj in ("Polity", "Geography"):
        print(f"\n=== {subj} core-topic ranking (last 10 papers, 2017-2026) ===")
        for row in summary["ranking"][subj]:
            print(f"{row['unit']:6s} all={row['all']:4d} l10={row['last10']:4d} l5={row['last5']:3d} "
                  f"{row['per_year_last10']:5.2f}/yr  {row['title'][:62]}")
    print("\n=== windows ===")
    print(json.dumps(summary["windows"], indent=1))
    print("\n=== spill-over ===")
    for subj in ("Polity", "Geography"):
        for w in ("all", "last10", "last5"):
            print(f"{subj:10s} {w:7s} {json.dumps(summary['spillover'][subj][w])}")
    print("\n=== recurrence (backsolve, core rows) ===")
    for subj in ("Polity", "Geography"):
        rc = summary["recurrence"][subj]
        print(f"{subj}: tiers={rc['tiers']} avg_cov={rc['avg_cov_flat']}")
        print(f"   most recurring units: {list(rc['by_unit_recurring_share'].items())[:6]}")
    print("\n=== mains questions per study unit (2011-2025) ===")
    print("polity:", {k: v for k, v in mc["unit_themes"]["per_unit"].items() if k.startswith("P") or k.endswith("polity")})
    print("geo:   ", {k: v for k, v in mc["unit_themes"]["per_unit"].items() if k.startswith("G") or k.endswith("geography")})
    print(f"\n=== cross-subject leak (geo/polity content tagged elsewhere) ===")
    print(f"total {ext['total']}  by tag {ext['by_tagged_subject']}")
    print("by unit:", ext["by_unit"])
    if args.sample:
        for k, v in sorted(samples.items()):
            print(f"\n--- {k} ---")
            for s in v[:args.sample]:
                print(" ", s)


if __name__ == "__main__":
    main()
