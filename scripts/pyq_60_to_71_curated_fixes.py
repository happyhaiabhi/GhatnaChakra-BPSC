#!/usr/bin/env python3
"""Curated data repairs, exam metadata, and verified editorial explanations
for the BPSC Prelims PYQ Master PDF (60th to 71st, 10 official papers).
"""
from __future__ import annotations

EXAM_META: list[dict[str, str]] = [
    {
        "exam": "60-62nd BPSC (Combined)",
        "code": "BPSC-60-62",
        "title": "60th–62nd BPSC Combined Preliminary Examination",
        "date": "12 February 2017",
        "year": "2017",
        "options_note": "5 Options (A–E); E = None of the above / More than one of the above",
    },
    {
        "exam": "63rd BPSC",
        "code": "BPSC-63",
        "title": "63rd BPSC Combined Preliminary Examination",
        "date": "1 July 2018",
        "year": "2018",
        "options_note": "5 Options (A–E); E = None of the above / More than one of the above",
    },
    {
        "exam": "64th BPSC",
        "code": "BPSC-64",
        "title": "64th BPSC Combined Preliminary Examination",
        "date": "16 December 2018",
        "year": "2018",
        "options_note": "5 Options (A–E); E = None of the above / More than one of the above",
    },
    {
        "exam": "65th BPSC",
        "code": "BPSC-65",
        "title": "65th BPSC Combined Preliminary Examination",
        "date": "15 October 2019",
        "year": "2019",
        "options_note": "5 Options (A–E); E = None of the above / More than one of the above",
    },
    {
        "exam": "66th BPSC",
        "code": "BPSC-66",
        "title": "66th BPSC Combined Preliminary Examination",
        "date": "27 December 2020",
        "year": "2020",
        "options_note": "5 Options (A–E); 131 recorded questions in master bank (Q.61–66 & Q.112–124 unrecorded in source workbook)",
    },
    {
        "exam": "67th BPSC",
        "code": "BPSC-67",
        "title": "67th BPSC Combined Preliminary Examination (Re-Exam)",
        "date": "30 September 2022",
        "year": "2022",
        "options_note": "5 Options (A–E); E = None of the above / More than one of the above",
    },
    {
        "exam": "68th BPSC",
        "code": "BPSC-68",
        "title": "68th BPSC Combined Preliminary Examination",
        "date": "12 February 2023",
        "year": "2023",
        "options_note": "5 Options (A–E); D = More than one of the above, E = None of the above",
    },
    {
        "exam": "69th BPSC",
        "code": "BPSC-69",
        "title": "69th BPSC Integrated Combined Preliminary Examination",
        "date": "30 September 2023",
        "year": "2023",
        "options_note": "4 Options (A–D) with negative marking",
    },
    {
        "exam": "70th BPSC",
        "code": "BPSC-70",
        "title": "70th BPSC Integrated Combined Preliminary Examination",
        "date": "13 December 2024",
        "year": "2024",
        "options_note": "4 Options (A–D) with negative marking",
    },
    {
        "exam": "71st BPSC (2025)",
        "code": "BPSC-71",
        "title": "71st BPSC Integrated Combined Preliminary Examination (Set E)",
        "date": "13 September 2025",
        "year": "2025",
        "options_note": "4 Options (A–D); 145 final-keyed answers + 5 officially deleted in BPSC Final Key (Q.11, Q.69, Q.75, Q.96, Q.118)",
    },
]

# Verified stem restorations where bpsc_parsed.json omitted List-I/List-II,
# omitted numbered/Roman statements, or abbreviated clauses with '...'.
# All restored stems preserve the exact option-key alignment of bpsc_parsed.json.
STEM_REPAIRS: dict[tuple[str, int], str] = {
    ("60-62nd BPSC (Combined)", 38): (
        "Match List-I with List-II and select the correct answer using the codes given below the lists:\n"
        "List-I (Substances): A. Aspartame, B. Freon, C. Neoprene, D. Benadryl\n"
        "List-II (Applications): 1. Synthetic rubber, 2. Antihistamine, 3. Artificial sweetener, 4. Refrigerant\n"
        "Code (A B C D):"
    ),
    ("60-62nd BPSC (Combined)", 44): (
        "Match List-I with List-II and select the correct answer using the codes given below the lists:\n"
        "List-I: A. Skin Cancer, B. Noise Pollution, C. Global Warming, D. Ozone Hole\n"
        "List-II: 1. Chlorofluorocarbons, 2. Ultraviolet light, 3. Decibel, 4. Carbon dioxide\n"
        "Code (A B C D):"
    ),
    ("60-62nd BPSC (Combined)", 105): (
        "Match the following places with industries and select the correct answer using the code given below:\n"
        "List-I (Place): A. Bengaluru, B. Korba, C. Jamshedpur, D. Malanjkhand\n"
        "List-II (Industry): 1. Iron & Steel, 2. Copper, 3. Aircraft, 4. Aluminium\n"
        "Code (A B C D):"
    ),
    ("60-62nd BPSC (Combined)", 121): (
        "Which of the following is/are listed among the Directive Principles in Part-IV of the Constitution of India?\n"
        "I. Equal Pay for Equal Work\n"
        "II. Uniform Civil Code\n"
        "III. Small family norm\n"
        "IV. Education through mother tongue at primary level"
    ),
    ("60-62nd BPSC (Combined)", 126): (
        "Choose the Fundamental Rights available to Indian citizens but NOT to aliens:\n"
        "I. Freedom of Speech and Expression\n"
        "II. Equality Before the Law\n"
        "III. Right of Minorities\n"
        "IV. Protection of Life and Liberty"
    ),
    ("68th BPSC", 22): "The maximum number of tea industries in Bihar is in which district?",
    ("69th BPSC", 42): (
        "Match List-I with List-II:\n"
        "List-I (Shoes / Fashion Accessories): a. Beret, b. Stilettos, c. Aviators, d. Chignon, e. Brogue\n"
        "List-II (Description): 1. A type of men's shoe, 2. A type of sunglasses, 3. A type of cap/hat, "
        "4. A type of women's shoe, 5. A type of hairstyle\n"
        "Choose the correct answer using the code given below:"
    ),
    ("69th BPSC", 92): (
        "The geographical structure of Bihar is made up of rock systems. Match the rock systems with their descriptions:\n"
        "a. Dharwar rock system — 1. Formed by rapid deposition of sediments by Himalayan and Peninsular rivers\n"
        "b. Vindhyan rock system — 2. Can be found in West Champaran district\n"
        "c. Quaternary rock system — 3. A part of the oldest Archaean rock system\n"
        "d. Tertiary rock system — 4. Sandstone, limestone, dolomite, quartzite and shale are the main components of this rock system\n"
        "Use the code given below and choose the correct answer:"
    ),
    ("69th BPSC", 93): (
        "Which one of the following is the world's richest region from a marine biodiversity perspective, comprising "
        "twenty-one islands with estuaries, beaches, forests of the nearshore environment, seagrasses, coral reefs, "
        "salt marshes and mangroves?"
    ),
    ("69th BPSC", 113): (
        "With reference to Infant Mortality Rate (IMR), consider the following statements:\n"
        "1. It is the probability of death of an infant between birth and exactly 1 year of age, expressed per 10,000 live births.\n"
        "2. In the year 1950, the infant mortality rate was 189.6.\n"
        "3. In the year 2019, the infant mortality rate was 30.\n"
        "4. According to the Sample Registration System (SRS) Bulletin of the Registrar General of India (RGI), "
        "Uttar Pradesh was the State with the highest infant mortality rate in 2019.\n"
        "Which of the above statements are correct?"
    ),
    ("69th BPSC", 115): (
        "Consider the following statements regarding insolvency and bankruptcy:\n"
        "1. Bankruptcy refers to a financial state in which an individual or entity is unable to pay off their debts as they become due.\n"
        "2. Insolvency refers to a legal process, where the assets of the debtor are liquidated or reorganized for the benefit of creditors.\n"
        "3. Bankruptcy is a state whereas insolvency is the conclusion.\n"
        "4. The Insolvency and Bankruptcy Board of India (IBBI) is the regulatory body responsible for overseeing insolvency and bankruptcy proceedings.\n"
        "Which of the above statements is/are correct?"
    ),
    ("69th BPSC", 117): (
        "Consider the following statements about the Production-Linked Incentive (PLI) scheme:\n"
        "1. The scheme offers a production-linked incentive to boost domestic manufacturing and attract large investments in mobile phone manufacturing and specified electronic components.\n"
        "2. The scheme has two categories of applicants, namely, global companies and domestic companies.\n"
        "3. The scheme shall extend an average incentive of around 8% on net incremental sales (over the base year) of goods manufactured in India and covered under the target segment, to eligible companies, for a period of six years.\n"
        "4. The target segment under PLI shall include (i) laptops, (ii) tablets, (iii) all-in-one PCs, (iv) servers and (v) Ultra-Small Form Factor (USFF).\n"
        "Which of the above statements are incorrect?"
    ),
    ("69th BPSC", 118): (
        "Consider the following statements regarding the SVAMITVA scheme:\n"
        "1. It is a Central Sector Scheme under the Ministry of Mines.\n"
        "2. This scheme seeks to create geo-positioning infrastructure like CORS network to benchmark the location and provides five-centimetre level accuracy.\n"
        "3. CORS means Cross-Origin Resource Sharing.\n"
        "4. The scheme is a reformatory step towards establishment of clear ownership of property in rural inhabited (Abadi) areas, by mapping of land parcels using drone technology.\n"
        "Which of the above statements are incorrect?"
    ),
    ("69th BPSC", 119): (
        "Which of the following is/are the consequence(s) of invoking Article 360, declaration of a financial emergency?\n"
        "1. The President may order the States to reduce the salaries and allowances of all or any class of employees serving in connection with the State affairs.\n"
        "2. Money Bills or other financial bills passed by the State Legislature are not required to be reserved for the consideration of the President.\n"
        "3. The President can issue directions for the reduction of salaries and allowances of all or any class of employees serving in connection with the affairs of the Union, including the Judges of the Supreme Court and the High Courts.\n"
        "4. Money Bills or other financial bills are to be reserved for the consideration of the President after they are passed by the Legislature of the State.\n"
        "Select the correct answer using the codes given below:"
    ),
    ("69th BPSC", 120): (
        "Which of the following factors could potentially contribute to stagflation in the Indian economy?\n"
        "1. High inflationary pressures due to increased Government spending\n"
        "2. Decline in industrial production and sluggish economic growth\n"
        "3. Decrease in aggregate demand and consumer spending\n"
        "4. Appreciation of the domestic currency leading to a reduction in export competitiveness\n"
        "Select the correct answer using the codes given below:"
    ),
    ("69th BPSC", 121): (
        "As per the Economic Survey, 2023, which of the following statements describe(s) the trend of Foreign Direct Investment in India?\n"
        "1. It has decreased due to the lower participation of the private sector.\n"
        "2. It has increased compared to the pre-pandemic levels.\n"
        "3. It has increased rapidly without decreasing in any Financial Year after the telecom sector was entirely reformed.\n"
        "4. It has decreased due to a weak global economic situation.\n"
        "Select the correct answer using the codes given below:"
    ),
    ("69th BPSC", 143): (
        "A man 'Ramesh', who owns a plot of land of 100 square yards, increases his plot of land by acquiring 10% more "
        "from his neighbour 'Suresh', who also owns 100 square yards of land. After 2 years, he sells back 10% of the "
        "total plot to the neighbour. Which of the following is correct?"
    ),
    ("71st BPSC (2025)", 46): (
        "Match List-I with List-II:\n"
        "List-I: (a) Perform, Achieve and Trade (PAT) scheme, (b) Mangrove Initiative for Shoreline Habitats & Tangible Incomes (MISHTI), "
        "(c) Lifestyle for Environment (LiFE) initiative, (d) National Clean Air Programme (NCAP)\n"
        "List-II: 1. Introduced in the Union Budget for 2023-24, 2. Aims to reduce emissions in energy-intensive industries, "
        "3. Launched in 2019 as a national-level strategy, 4. Launched at COP 26 in Glasgow in 2021"
    ),
    ("71st BPSC (2025)", 63): (
        "The Constitution of India provides for reasonable restrictions on Fundamental Rights, but reasonableness must keep in mind that:\n"
        "1. The interest of the general public is safeguarded\n"
        "2. Prevailing social value and also social needs are not barred\n"
        "3. Directive Principles can be bypassed\n"
        "4. Collective good is not greater\n"
        "Out of these:"
    ),
    ("71st BPSC (2025)", 96): (
        "Which of the following statements about Subhas Chandra Bose are correct?\n"
        "1. He was elected President of the Indian National Congress at Tripuri session of 1938 A.D.\n"
        "2. He escaped from home internment in January 1941 A.D.\n"
        "3. On October 21st, 1943 A.D. he constituted the Provincial Government of Free India in Singapore."
    ),
    ("71st BPSC (2025)", 98): (
        "Consider the following events of Modern Indian History:\n"
        "1. Death sentence to Raja Nand Kumar\n"
        "2. Treaty of Salbai\n"
        "3. Battle of Wandiwash\n"
        "4. Death of Tipu Sultan\n"
        "Which of the following is the correct chronological order of the above events?"
    ),
}

# Verified option repairs for the 15 questions where Excel auto-converted dates,
# fiscal years, fractions, or number pairs into 'YYYY-MM-DD 00:00:00'.
# Preserves the exact option-letter order of bpsc_parsed.json.
OPTION_REPAIRS: dict[tuple[str, int], dict[str, str]] = {
    ("60-62nd BPSC (Combined)", 2): {
        "A": "1 February, 1900",
        "B": "2 February, 1900",
        "C": "3 February, 1900",
        "D": "4 February, 1900",
        "E": "None of the above/More than one of the above",
    },
    ("60-62nd BPSC (Combined)", 17): {
        "A": "February 1942",
        "B": "March 1942",
        "C": "April 1942",
        "D": "May 1942",
        "E": "None of the above/More than one of the above",
    },
    ("60-62nd BPSC (Combined)", 123): {
        "A": "26th October",
        "B": "26th November",
        "C": "26th January",
        "D": "15th August",
        "E": "None of the above/More than one of the above",
    },
    ("63rd BPSC", 24): {
        "A": "2010-11",
        "B": "2011-12",
        "C": "2012-13",
        "D": "2013-14",
        "E": "None of the above/More than one of the above",
    },
    ("64th BPSC", 117): {
        "A": "2004-05",
        "B": "2006-07",
        "C": "2008-09",
        "D": "2009-10",
        "E": "None of the above/More than one of the above",
    },
    ("65th BPSC", 84): {
        "A": "1",
        "B": "5/8",
        "C": "39/4",
        "D": "39/8",
        "E": "None of the above/More than one of the above",
    },
    ("66th BPSC", 18): {
        "A": "3, 3",
        "B": "3, 6",
        "C": "12, 3",
        "D": "12, 6",
        "E": "None of the above/More than one of the above",
    },
    ("66th BPSC", 137): {
        "A": "1/10",
        "B": "1/3",
        "C": "3/20",
        "D": "3/25",
        "E": "None of the above/More than one of the above",
    },
    ("68th BPSC", 35): {
        "A": "August 1947",
        "B": "January 1948",
        "C": "June 1948",
        "D": "More than one of the above",
        "E": "None of the above",
    },
    ("68th BPSC", 142): {
        "A": "5, 6",
        "B": "2, 15",
        "C": "10, 3",
        "D": "More than one of the above",
        "E": "None of the above",
    },
    ("70th BPSC", 5): {
        "A": "15 August, 2022",
        "B": "10 August, 2019",
        "C": "26 January, 2023",
        "D": "10 August, 2020",
    },
    ("70th BPSC", 77): {
        "A": "14 August, 1946",
        "B": "15 August, 1947",
        "C": "16 August, 1946",
        "D": "More than one of the above",
    },
    ("70th BPSC", 111): {
        "A": "1 April, 1912",
        "B": "1 April, 1911",
        "C": "1 March, 1912",
        "D": "More than one of the above",
    },
    ("70th BPSC", 135): {
        "A": "26 November, 1950",
        "B": "24 January, 1950",
        "C": "26 January, 1950",
        "D": "22 July, 1947",
    },
    ("71st BPSC (2025)", 33): {
        "A": "15 January",
        "B": "27 January",
        "C": "10 February",
        "D": "More than one of the above",
    },
}

# Officially deleted questions in BPSC's Final Answer Key for 71st BPSC (Set E)
DELETED_71ST_QUESTIONS: set[int] = {11, 69, 75, 96, 118}

# Verified editorial explanations for questions not covered by existing repo JSON banks
# plus authoritative notes for the 5 officially deleted 71st BPSC questions.
EDITORIAL_EXPLANATIONS: dict[tuple[str, int], str] = {
    ("60-62nd BPSC (Combined)", 22): (
        "Each letter is coded by the digital root (repeated digit sum) of its alphabetical position (A=1 ... Z=26): "
        "S(19->1+9=10->1), U(21->3), R(18->9), G(7), I(9), C(3), A(1), L(12->3) gives 13979313; STRIKE gives 129925. "
        "Applying the same rule to METRO: M(13->4), E(5), T(20->2), R(18->9), O(15->6) = 45296; "
        "and TRAIN: T(20->2), R(18->9), A(1), I(9), N(14->5) = 29195. Thus METRO-TRAIN = 45296-29195."
    ),
    ("60-62nd BPSC (Combined)", 24): (
        "In A26H, C24F, G20B: the first letters advance by +2, +4, +6 (A(1) -> C(3) -> G(7) -> M(13)), the middle number "
        "equals 27 minus the first letter's position (26, 24, 20 -> 14), and the last letters step backward by -2, -4, -6 "
        "(H(8) -> F(6) -> B(2) -> V(22)), giving M14V (or if doubling +2, +4, +8: O12T). Neither appears in options A–D, so Option (E) is correct."
    ),
    ("60-62nd BPSC (Combined)", 26): (
        "In the original Venn diagram of three intersecting sets (Government employees, Own-house residents, Graduates), "
        "the triple-intersection region representing persons satisfying all three conditions simultaneously is a single letter "
        "(region F), rather than any of the multi-region combinations listed in A–D; hence Option (E) is correct."
    ),
    ("60-62nd BPSC (Combined)", 27): (
        "Substituting the operators (+ -> ×, × -> +, - -> ÷, ÷ -> -, > -> =, = -> >): in Option (B), the left side "
        "11 × 2 ÷ 4 - 2 + 1 becomes 11 + 2 - 4 ÷ 2 × 1 = 11 + 2 - 2 = 11 (in the printed booklet the RHS was 1, giving 11 > 1, "
        "which holds true; options A, C, and D evaluate to 11 = 12, 6 > 7, and 8 = 4, all false)."
    ),
    ("60-62nd BPSC (Combined)", 51): (
        "Donald Trump contested and won the November 2016 United States Presidential Election as the nominee of the Republican Party, "
        "defeating Democratic Party nominee Hillary Clinton to become the 45th US President."
    ),
    ("60-62nd BPSC (Combined)", 52): (
        "The Iran–Pakistan gas pipeline (originally conceived as the Iran–Pakistan–India or IPI pipeline stretching from "
        "Iran's South Pars gas field to Pakistan and India) is widely known as the 'Peace Pipeline'."
    ),
    ("60-62nd BPSC (Combined)", 53): (
        "In the inaugural 2016 Sustainable Development Goals (SDG) Index published by the Sustainable Development Solutions Network (SDSN) "
        "and Bertelsmann Stiftung across 149 countries, India ranked 110th (Sweden topped the index)."
    ),
    ("60-62nd BPSC (Combined)", 55): (
        "American singer-songwriter Bob Dylan won the 2016 Nobel Prize in Literature 'for having created new poetic expressions "
        "within the great American song tradition'."
    ),
    ("60-62nd BPSC (Combined)", 59): (
        "In May 2016, Sikkim was officially declared India's first 100% Open Defecation Free (ODF) State under the Swachh Bharat Mission "
        "(followed later in 2016 by Himachal Pradesh and Kerala)."
    ),
    ("60-62nd BPSC (Combined)", 60): (
        "At the time of the 60th–62nd BPSC exam (February 2017), Lithuania was the newest (19th) member of the Eurozone, having adopted "
        "the Euro on 1 January 2015. (Note: Croatia subsequently joined as the 20th member on 1 January 2023 and Bulgaria later)."
    ),
    ("60-62nd BPSC (Combined)", 61): (
        "At the time of the examination in 2017, Queen Elizabeth II (reigned 1952–2022) was the constitutional monarch and Head of State "
        "of the United Kingdom."
    ),
    ("60-62nd BPSC (Combined)", 62): (
        "India's first and Asia's longest cycle highway—a 207-km dedicated cycling track running between Agra and Etawah (Lion Safari)—was "
        "inaugurated in Uttar Pradesh in November 2016."
    ),
    ("60-62nd BPSC (Combined)", 64): (
        "In the Union Budget 2016–17 presented by Finance Minister Arun Jaitley, the Government of India set the fiscal deficit target "
        "for FY 2016–17 at 3.5% of GDP (down from 3.9% in FY 2015–16)."
    ),
    ("60-62nd BPSC (Combined)", 66): (
        "The 'MAA' (Mothers' Absolute Affection) nationwide programme was launched in August 2016 by the Union Ministry of Health and "
        "Family Welfare to promote optimal breastfeeding practices and infant health."
    ),
    ("60-62nd BPSC (Combined)", 67): (
        "Masala Bonds are rupee-denominated bonds issued outside India by Indian entities, enabling issuers to raise funds in offshore "
        "markets while shifting currency exchange-rate risk to the foreign investor. The first Masala Bond was issued by IFC in 2014."
    ),
    ("60-62nd BPSC (Combined)", 68): (
        "Indian Railways launched 'Tri-Netra' (Terrain Imaging for Diesel Drivers — Infrared, Enhanced Optical & Radar Assisted System) "
        "to help locomotive pilots detect track obstructions during fog, heavy rain, and night operations."
    ),
    ("60-62nd BPSC (Combined)", 69): (
        "In February 2016, the Government of India and RBI constituted a seven-member task force headed by Neeraj Kumar Gupta "
        "(Secretary, Department of Investment and Public Asset Management) to promote cashless transactions and card acceptance."
    ),
    ("60-62nd BPSC (Combined)", 70): (
        "Argentina won its maiden Davis Cup title in November 2016 by defeating Croatia 3–2 in the final held in Zagreb."
    ),
    ("60-62nd BPSC (Combined)", 71): (
        "LIGO-India (Laser Interferometer Gravitational-Wave Observatory) was approved for construction in Hingoli district (Aundha Nagnath) "
        "of Maharashtra as a collaboration between Indian research institutions and the US LIGO Laboratory."
    ),
    ("60-62nd BPSC (Combined)", 72): (
        "At the 2016 Rio de Janeiro Summer Olympics, the United States finished at the top of the medal table with 46 gold medals "
        "(121 medals overall), ahead of Great Britain (27 golds) and China (26 golds)."
    ),
    ("60-62nd BPSC (Combined)", 73): (
        "Qatar hosted the 2022 FIFA World Cup (November–December 2022), becoming the first Middle Eastern nation to stage the tournament."
    ),
    ("60-62nd BPSC (Combined)", 75): (
        "India won the 2016 Kabaddi World Cup held in Ahmedabad (Gujarat) in October 2016, defeating Iran 38–29 in the final."
    ),
    ("60-62nd BPSC (Combined)", 76): (
        "China's women's national badminton team won the 2016 Uber Cup held in Kunshan, China, defeating South Korea 3–1 in the final "
        "to claim its 14th Uber Cup title."
    ),
    ("60-62nd BPSC (Combined)", 77): (
        "Renowned Gujarati novelist, poet, and critic Raghuveer Chaudhari was conferred the 51st Jnanpith Award for the year 2015 "
        "(famous for his trilogy 'Amrita')."
    ),
    ("60-62nd BPSC (Combined)", 78): (
        "'Six Machine: I Don't Like Cricket... I Love It' (published 2016) is the autobiography of West Indies batting star Chris Gayle."
    ),
    ("60-62nd BPSC (Combined)", 79): (
        "Javelin thrower Devendra Jhajharia (F46 category) became the first Indian athlete to win two Paralympic gold medals, winning "
        "gold at the 2004 Athens Paralympics and again with a world record at the 2016 Rio Paralympics."
    ),
    ("60-62nd BPSC (Combined)", 80): (
        "The central theme of the 2016 Rio Olympics Opening Ceremony was 'World Peace and Environment' (highlighting climate change, "
        "reforestation, and global harmony alongside the official motto 'A New World')."
    ),
    ("60-62nd BPSC (Combined)", 112): (
        "Commercial saffron (kesar) cultivation in India is concentrated in the Karewa lacustrine deposits (especially Pampore) of "
        "Jammu & Kashmir, which holds a Geographical Indication (GI) tag for Kashmir Saffron."
    ),
    ("60-62nd BPSC (Combined)", 142): (
        "Tamil Nadu has the largest number of cotton textile (especially spinning) mills in India (centred around Coimbatore, Tiruppur, "
        "and Madurai), followed by Maharashtra. Since Tamil Nadu is not among options A–D, Option (E) is correct."
    ),
    ("63rd BPSC", 77): (
        "Amount after 2 years (A2) = ₹ 4,624 and after 3 years (A3) = ₹ 4,913. Therefore 1 + r/100 = A3 / A2 = 4913 / 4624 = 17 / 16 "
        "(since 17^3 = 4913 and 17 × 16^2 = 4624, giving r = 6.25% p.a.). Principal P = A2 × (16/17)^2 = 4624 × 256 / 289 = 16 × 256 = ₹ 4,096."
    ),
    ("63rd BPSC", 78): (
        "Face value of 1 share = ₹ 20; annual dividend = 9% of ₹ 20 = ₹ 1.80 per share. Since the investor desires a 12% return on his "
        "investment (market value M), 12% of M = ₹ 1.80 => M = (1.80 × 100) / 12 = ₹ 15."
    ),
    ("64th BPSC", 26): (
        "In August 2018, the United Kingdom (Great Britain) proposed reforms to its Human Tissue / Organ Transplantation framework "
        "(moving toward an 'opt-out' deemed-consent system in England) with specific outreach to Black, Asian, and Indian-origin minority communities."
    ),
    ("64th BPSC", 35): (
        "According to the India State of Forest Report (ISFR) 2017 released in February 2018, total forest and tree cover was 24.39% of "
        "India's geographical area (forest cover alone was 21.54%; rounded to two decimal places in fraction form = 0.24, i.e., 24%)."
    ),
    ("64th BPSC", 118): (
        "According to DIPP (DPIIT) quarterly FDI statistics for April–June 2018, the Services sector attracted the highest share of "
        "FDI equity inflows."
    ),
    ("65th BPSC", 57): (
        "Bihar's three-day 'Krishi Kumbha Mela 2019' was inaugurated in February 2019 at Gandhi Maidan, Motihari (East Champaran) "
        "jointly by Union Agriculture Minister Radha Mohan Singh and Bihar Governor Lalji Tandon."
    ),
    ("66th BPSC", 89): (
        "Among Indian States (excluding the Union Territory of Andaman & Nicobar Islands, which has 96+), Maharashtra has the highest "
        "number of notified wildlife sanctuaries (~48–49 sanctuaries), ahead of Karnataka, Tamil Nadu, and Madhya Pradesh."
    ),
    ("67th BPSC", 148): (
        "All three statements are correct: (1) Project Tiger was launched by the Government of India on 1 April 1973; "
        "(2) the UN International Day for Biological Diversity 2022 theme was 'Building a shared future for all life'; and "
        "(3) Project Tiger is India's flagship centrally sponsored tiger conservation programme."
    ),
    ("68th BPSC", 61): (
        "YUVA 2.0 (Young, Upcoming and Versatile Authors)—the Prime Minister's Scheme for Mentoring Young Authors under age 30—was "
        "launched on 2 October 2022 by the Union Ministry of Education (Department of Higher Education) with the National Book Trust as implementing agency."
    ),
    ("68th BPSC", 63): (
        "The Kirit Parikh Committee on Domestic Natural Gas Pricing submitted its report in November 2022, recommending floor and ceiling "
        "prices for legacy APM gas in the interim and complete deregulation (pricing freedom) from 1 January 2026."
    ),
    ("68th BPSC", 64): (
        "In Swachh Survekshan 2022, six cities received the 5-star Garbage-Free City rating: Surat, Bhopal, Navi Mumbai, Mysuru, "
        "Vijayawada, and Tirupati (while Indore received 7-star). Since Surat, Bhopal, and Navi Mumbai all received 5-star status, "
        "none of options A–C was excluded; hence Option (E) 'None of the above' is correct."
    ),
    ("68th BPSC", 65): (
        "Prime Minister Narendra Modi inaugurated Arunachal Pradesh's first greenfield airport—Donyi Polo Airport (named after the Sun 'Donyi' "
        "and Moon 'Polo')—at Hollongi, Itanagar, in November 2022."
    ),
    ("68th BPSC", 66): (
        "In November 2022, the Food Safety and Standards Authority of India (FSSAI) approved the Himalayan Yak (Bos grunniens) as a "
        "'food animal', helping curb its population decline by integrating yak milk and meat into conventional value chains."
    ),
    ("68th BPSC", 67): (
        "India Post Payments Bank (IPPB) conducted India's first floating financial literacy camp in November 2022 on Dal Lake in Srinagar "
        "(Jammu & Kashmir) under the 'Niveshak Didi' initiative."
    ),
    ("68th BPSC", 69): (
        "On the 90th Indian Air Force Day (8 October 2022), the ceremonial parade and a flypast of ~80 aircraft were held outside "
        "Delhi NCR for the first time over Sukhna Lake in Chandigarh."
    ),
    ("68th BPSC", 70): (
        "September is observed annually across India as 'Rashtriya Poshan Maah' (National Nutrition Month) under POSHAN Abhiyaan "
        "(National Nutrition Mission) to combat malnutrition among children, adolescent girls, pregnant women, and lactating mothers."
    ),
    ("68th BPSC", 73): (
        "Sri Lankan author Shehan Karunatilaka won the 2022 Booker Prize for his satirical supernatural novel 'The Seven Moons of Maali Almeida', "
        "set amid the Sri Lankan civil war in 1990."
    ),
    ("68th BPSC", 74): (
        "World Space Week (observed annually from 4 to 10 October) had the 2022 theme 'Space and Sustainability', focusing on "
        "achieving sustainability in space (orbital debris mitigation) and sustainability from space (Earth observation)."
    ),
    ("68th BPSC", 75): (
        "In December 2022, scientists at the National Ignition Facility (NIF) of Lawrence Livermore National Laboratory (California, USA) "
        "achieved historic nuclear fusion ignition (net energy gain, producing ~3.15 MJ from 2.05 MJ of laser input)."
    ),
    ("68th BPSC", 76): (
        "Collins Dictionary named 'permacrisis'—defined as 'an extended period of instability and insecurity'—as its Word of the Year 2022."
    ),
    ("68th BPSC", 77): (
        "Spain and Senegal jointly launched the International Drought Resilience Alliance (IDRA) in November 2022 at the UNFCCC COP27 "
        "summit in Sharm el-Sheikh, Egypt, to shift global response from emergency drought relief to long-term preparedness."
    ),
    ("68th BPSC", 78): (
        "In October 2022, the Embassy of Japan in New Delhi filed an application with the Geographical Indications Registry in Chennai "
        "seeking a GI tag for 'Nihonshu' (authentic Japanese sake)—the first time Japan's embassy applied for a GI tag in India."
    ),
    ("68th BPSC", 81): (
        "Bihar's first floating solar power plant (~1.6–2 MW capacity, combined with fish farming below the solar panels) was commissioned "
        "at Kadirabad in Darbhanga district."
    ),
    ("68th BPSC", 83): (
        "In the NITI Aayog SDG India Index 2020–21 (third edition), Bihar scored 52 out of 100 overall (up from 50 in 2019–20), "
        "placing in the 'Performer' category (50–64 score band)."
    ),
    ("68th BPSC", 84): (
        "Track Cycling was included for the first time in the Khelo India Women's Tournament in December 2022 across four zonal legs, "
        "promoted by the Department of Sports under the 'Sports for Women' component."
    ),
    ("68th BPSC", 85): (
        "In August 2022, the Geographical Indications Registry granted the GI Tag to 'Mithila Makhana' (fox nut / Euryale ferox cultivated "
        "in the Mithila region of Bihar and adjoining Nepal), benefiting lakhs of makhana farmers."
    ),
    ("68th BPSC", 86): (
        "None of the listed Bihar sites was added to the UNESCO World Heritage List in 2022: Mahabodhi Temple Complex was inscribed in 2002, "
        "Nalanda Mahavihara in 2016, and the claim regarding Langat Singh College's observatory in 2022 was officially refuted by UNESCO. "
        "Hence Option (E) 'None of the above' is correct."
    ),
    ("68th BPSC", 87): (
        "In the Business Reforms Action Plan (BRAP) State Rankings released in September 2020 (for BRAP 2019), Bihar ranked 26th out of "
        "36 States/UTs. Since 26th is not among options A–C (23rd, 24th, 25th), Option (E) 'None of the above' is correct."
    ),
    ("68th BPSC", 88): (
        "Chief Minister Nitish Kumar inaugurated the ambitious 'Har Ghar Gangajal' (Ganga Jal Aapurti Yojana) on 27 November 2022 at "
        "Rajgir and on 28 November 2022 at Bodh Gaya; per the official BPSC 68th Final Answer Key, Option (B) Rajgir was keyed."
    ),
    ("68th BPSC", 89): (
        "In October 2022, the Board of Control for Cricket in India (BCCI) announced a landmark pay-equity policy granting centrally "
        "contracted Indian women cricketers the exact same match fees as men (₹ 15 lakh Test, ₹ 6 lakh ODI, ₹ 3 lakh T20I)."
    ),
    ("68th BPSC", 92): (
        "Project Tiger, launched in India on 1 April 1973 under Prime Minister Indira Gandhi (initially across 9 tiger reserves), is "
        "one of the world's best-publicised wildlife conservation campaigns (also directly referenced in NCERT Class 10 Geography)."
    ),
    ("68th BPSC", 93): (
        "The troposphere is the lowest (not topmost) layer of Earth's atmosphere; its height is ~8 km near the poles and ~18 km at the "
        "equator, giving an average height of 13 km, and temperature generally decreases with altitude at ~6.5°C per km (normal lapse rate)."
    ),
    ("68th BPSC", 97): (
        "The Gulf of Mannar Biosphere Reserve (located between southeastern Tamil Nadu and Sri Lanka) comprises 21 islands with estuaries, "
        "beaches, nearshore forests, seagrass beds, coral reefs, salt marshes, and mangroves, making it one of the world's richest marine biodiversity regions."
    ),
    ("68th BPSC", 98): (
        "Under Köppen's climate classification, the Gangetic plains of Uttar Pradesh and Bihar fall in the 'Cwg' zone (Monsoon type with "
        "dry winters: mesothermal 'C', winter dry 'w', hottest month before summer solstice / Gangetic temperature regime 'g')."
    ),
    ("69th BPSC", 33): (
        "Yevgeny Prigozhin was the founder and leader of Russia's Wagner Private Military (Mercenary) Group; he died in an aircraft "
        "crash in Tver Oblast in August 2023 shortly after leading a brief mutiny in June 2023."
    ),
    ("69th BPSC", 40): (
        "In colour theory: (a) Magenta = Red and blue (2); (b) Teal = Blue, green and white/dark cyan (3); (c) Mauve = Blue, red and white "
        "(pale purple, 4); (d) Cyan = Green and blue (1). Thus the correct matching code is a-2, b-3, c-4, d-1."
    ),
    ("69th BPSC", 59): (
        "Among the three listed currencies (Euro, Pound Sterling, US Dollar), the British Pound Sterling (GBP) has the highest exchange "
        "value per unit (1 GBP > 1 EUR > 1 USD)."
    ),
    ("69th BPSC", 60): (
        "The Bihar Government signed an MoU with UNEP to prepare a climate-resilient and low-carbon development pathway; while draft state "
        "climate policy targeted net-zero carbon emissions by 2040, BPSC's official 69th Final Answer Key selected 2047 (Option D), "
        "aligning with India's centenary year among the given options."
    ),
    ("69th BPSC", 69): (
        "Matching ancient Indian scholars with their primary domains: (a) Charaka — Medicine (Charaka Samhita, 2); "
        "(b) Brahmagupta — Mathematics/Astronomy (Brahmasphutasiddhanta, 1); (c) Varahamihira — Astrology/Astronomy (Brihat Samhita, Panchasiddhantika, 4); "
        "(d) Vishakhadatta — Sanskrit Playwright (Mudrarakshasa, 3). Correct code: a-2, b-1, c-4, d-3."
    ),
    ("69th BPSC", 83): (
        "Matching explorers with their birthplaces/nationalities: (a) Christopher Columbus — Genoa, Italy (3); "
        "(b) Jacques Cartier — Saint-Malo, France (4); (c) Sir Francis Drake — Devon, United Kingdom (2); "
        "(d) Ferdinand Magellan — Portugal (1). Correct code: a-3, b-4, c-2, d-1."
    ),
    ("69th BPSC", 84): (
        "The United Arab Emirates (UAE), formed in 1971–72, is a federation of seven emirates: Abu Dhabi (capital), Dubai, Sharjah, "
        "Ajman, Umm Al-Quwain, Fujairah, and Ras Al-Khaimah. (Cities/countries like Jeddah, Riyadh, Kuwait, and Bahrain in B–D are outside the UAE)."
    ),
    ("69th BPSC", 87): (
        "The Gangetic River Dolphin (Platanista gangetica), India's National Aquatic Animal (declared 2009), is classified as 'Endangered' "
        "on the IUCN Red List, lacks a crystalline eye lens (is functionally blind), hunts and navigates via echolocation (ultrasonic sound), "
        "and serves as a key indicator of riverine ecosystem health; hence all four statements are correct."
    ),
    ("69th BPSC", 109): (
        "Foundation years of India's national political parties: (a) CPI (Marxist) — 1964 (split from CPI, 1); "
        "(b) Communist Party of India (CPI) — December 1925 at Kanpur (3); (c) Bahujan Samaj Party (BSP) — 14 April 1984 by Kanshi Ram (4); "
        "(d) All India Trinamool Congress (AITC) — 1 January 1998 by Mamata Banerjee (2). Correct code: a-1, b-3, c-4, d-2."
    ),
    ("69th BPSC", 112): (
        "Under WTO agreements, Rules of Origin are the criteria used to determine the national source of a product (1); they guide "
        "customs authorities on applicable duties/regulations (2), are used for compiling trade statistics (3), and are essential because "
        "tariffs, anti-dumping duties, and preferential trade concessions depend on the country of origin (4). All four statements are correct."
    ),
    ("69th BPSC", 114): (
        "Per NCERT Indian Economic Development, human capital formation is the process of acquiring and increasing the number of persons "
        "who have the skills, education, knowledge, and experience (capacities) crucial for the economic and political development of a country."
    ),
    ("69th BPSC", 136): (
        "Matching socio-religious/nationalist organisations with their founders: (a) Servants of India Society (1905) — Gopal Krishna Gokhale (2); "
        "(b) Tattwabodhini Sabha (1839) — Debendranath Tagore (1); (c) Atmiya Sabha (1815) — Raja Ram Mohan Roy (3). Correct code: a-2, b-1, c-3."
    ),
    ("70th BPSC", 11): (
        "In the Union Budget 2024–25 speech, Finance Minister Nirmala Sitharaman announced a strategy to achieve 'Atmanirbharta' (self-reliance) "
        "for oilseeds covering mustard, groundnut, sesame, soybean, and sunflower—thus Coconut was NOT among the oilseeds listed."
    ),
    ("70th BPSC", 28): (
        "Longitudinal sequence from East to West: 1. Garo Hills (Meghalaya, ~90°E) -> 2. Nanda Devi (Kumaon Himalayas, Uttarakhand, ~79°58'E) -> "
        "3. Kamet (Garhwal Himalayas, Uttarakhand, ~79°35'E) -> 4. K2 / Godwin-Austen (Karakoram Range, ~76°30'E). Correct East-to-West order: 1 2 3 4."
    ),
    ("70th BPSC", 29): (
        "Matching Bihar districts with associated economic activities/resources: (a) Vaishali — Floriculture (4); (b) Bhagalpur — Silk Textile ('Silk City', 1); "
        "(c) Jamui — Largest gold ore reserves in Bihar/India (2); (d) Madhepura — Electric locomotive / rail factory (3). Correct code: a-4, b-1, c-2, d-3."
    ),
    ("70th BPSC", 47): (
        "The nationalist booklet 'Gharib Hindustan' (criticising British colonial exploitation), proscribed and banned in Bihar in 1930 "
        "during the Civil Disobedience era, was authored by Mohd. Wali Hassan."
    ),
    ("70th BPSC", 144): (
        "The 1944 'Bombay Plan' (A Plan of Economic Development for India) was authored by eight leading Indian industrialists: J.R.D. Tata, "
        "G.D. Birla, Ardeshir Dalal, Lala Shri Ram, Kasturbhai Lalbhai, A.D. Shroff, Sir Purshottamdas Thakurdas, and John Mathai. "
        "Dhirubhai Ambani (born 1932; founded Reliance later) was NOT one of its architects."
    ),
    ("71st BPSC (2025)", 6): (
        "Total students in class = 39. Joginder's rank from the last = 17th, so Joginder's rank from the beginning = (39 - 17) + 1 = 23rd. "
        "Since Nitin is 7 ranks ahead of Joginder, Nitin's rank from the beginning = 23 - 7 = 16th."
    ),
    ("71st BPSC (2025)", 11): (
        "[Officially Deleted in BPSC 71st Final Answer Key] This question was deleted by BPSC in the Final Answer Key dated 31 October 2025 "
        "because the actual medal tally of Bihar athletes at the National Junior Athletics Championship did not match the single-choice options provided."
    ),
    ("71st BPSC (2025)", 13): (
        "In October 2024, the Union Cabinet approved Classical Language status for five additional languages—Marathi, Pali, Prakrit, Assamese, "
        "and Bengali—joining Tamil (2004), Sanskrit (2005), Kannada (2008), Telugu (2008), Malayalam (2013), and Odia (2014) (total 11 Classical Languages). "
        "Hence Telugu, Marathi, and Bengali are all Classical Languages -> Option (D) 'More than one of the above'."
    ),
    ("71st BPSC (2025)", 69): (
        "[Officially Deleted in BPSC 71st Final Answer Key] Conceptually, a Censure Motion differs from a No-Confidence Motion (it requires "
        "stating specific reasons for adoption, can be moved against an individual minister or group of ministers, and need not cause resignation "
        "of the Council of Ministers), while leave/permission of the House is required. BPSC deleted Q.69 in the Final Answer Key."
    ),
    ("71st BPSC (2025)", 75): (
        "[Officially Deleted in BPSC 71st Final Answer Key] 'Young India' was originally started as an English journal in 1916 in Bombay "
        "by the Home Rule League circle (Jamnadas Dwarkadas, Shankarlal Banker, and Indulal Yagnik, associated with Annie Besant) and was taken over "
        "and edited as a famous nationalist weekly by Mahatma Gandhi from October 1919 to 1931. Owing to this dual historical attribution between "
        "options (A) and (B), BPSC officially deleted Q.75 in the Final Answer Key."
    ),
    ("71st BPSC (2025)", 96): (
        "[Officially Deleted in BPSC 71st Final Answer Key] Statement 1 is factually incorrect because Subhas Chandra Bose presided over the "
        "Haripura Congress Session in 1938 and the Tripuri Session in 1939; Statement 2 (escaped from Calcutta house arrest in January 1941) and "
        "Statement 3 (proclaimed the Provisional Government of Free India / Azad Hind in Singapore on 21 October 1943) are correct (making 'Only 2 and 3' "
        "accurate). BPSC officially deleted Q.96 in the Final Answer Key."
    ),
    ("71st BPSC (2025)", 118): (
        "[Officially Deleted in BPSC 71st Final Answer Key] Bihar (primarily Rohtas district—Amjhore) holds ~94%–95% of India's total pyrite "
        "resources (Indian Minerals Yearbook cites ~94% of resources while state compilations cite ~95% of production). Due to data-source "
        "ambiguity after cessation of active mining, BPSC officially deleted Q.118 in the Final Answer Key."
    ),
    ("60-62nd BPSC (Combined)", 63): (
        "In 2016–17, the Gujarat government announced plans to establish India's first dedicated Textile University at Surat "
        "(India's synthetic textile hub) with an investment of ₹ 800–900 crore."
    ),
    ("60-62nd BPSC (Combined)", 74): (
        "According to Census 2011, Bihar's total population was 10,40,99,452 (~10.41 crore, 8.60% of India's population), ranking "
        "3rd (III) among Indian States after Uttar Pradesh (1st) and Maharashtra (2nd)."
    ),
    ("60-62nd BPSC (Combined)", 120): (
        "According to Census 2011, Madhepura recorded the highest decadal population growth rate among Bihar's 38 districts during "
        "2001–2011 at 31.12% (followed by Kishanganj at 30.40%), while Gopalganj recorded the lowest (19.02%)."
    ),
    ("60-62nd BPSC (Combined)", 136): (
        "According to Census 2011, Haryana recorded the lowest sex ratio among all Indian States at 879 females per 1,000 males "
        "(while Kerala recorded the highest at 1,084; India's overall sex ratio was 943)."
    ),
    ("60-62nd BPSC (Combined)", 138): (
        "According to the provisional/final Census 2011 figures used in BPSC keys, India's decadal population growth rate during "
        "2001–2011 was 17.64% (provisional) / 17.7% (final), down from 21.54% during 1991–2001."
    ),
    ("63rd BPSC", 25): (
        "According to Census 2011, Bihar recorded the lowest overall literacy rate (61.80%), as well as the lowest male literacy rate "
        "(71.20%) and lowest female literacy rate (51.50%, along with Rajasthan at 52.1% overall female—Bihar lowest at 51.5%) in India."
    ),
    ("63rd BPSC", 39): (
        "The Census year 1921 is called the 'Year of the Great Demographic Divide' in Indian demography because 1911–1921 was the only "
        "census decade in modern Indian history to record a negative population growth (-0.31%, due to famine and the 1918 influenza pandemic), "
        "after which India's population grew continuously."
    ),
    ("64th BPSC", 55): (
        "As recorded in the Nalanda Copper Plate inscription of Pala ruler Devapala, the Sailendra king Balaputradeva of Suvarnabhumi "
        "(Sumatra/Java) built a Buddhist monastery at Nalanda and requested Devapala to grant five villages for its upkeep."
    ),
    ("64th BPSC", 79): (
        "According to Census 2011, India's urban population stood at 377.1 million, accounting for 31.16% (approximately 31%) of "
        "India's total population (with rural population at 68.84%)."
    ),
    ("64th BPSC", 88): (
        "According to Census 2011, Bihar ranked first from the bottom (i.e., the State with the lowest literacy rate in India) with "
        "an overall literacy rate of 61.80%."
    ),
    ("64th BPSC", 99): (
        "The State of Jharkhand was carved out of southern Bihar on 15 November 2000 (the birth anniversary of Birsa Munda) as India's "
        "28th State under the Bihar Reorganisation Act, 2000."
    ),
    ("64th BPSC", 119): (
        "According to the Bihar Economic Survey 2017–18 / NSSO workforce estimates, around 74%–77% of Bihar's workforce was engaged "
        "in agriculture and allied activities. Since this figure does not match 65%, 67%, 68%, or 70%, Option (E) is correct."
    ),
    ("65th BPSC", 24): (
        "The Ganga river flows through 12 districts of Bihar (from west to east: Buxar, Bhojpur, Saran, Patna, Vaishali, Samastipur, "
        "Begusarai, Munger, Khagaria, Lakhisarai, Bhagalpur, and Katihar)."
    ),
    ("65th BPSC", 27): (
        "Kaimur district (followed by West Champaran and Rohtas) has the largest geographical area under forest cover (predominantly "
        "tropical deciduous forests across the Kaimur plateau) in Bihar."
    ),
    ("65th BPSC", 28): (
        "Out of the total ~445 km course of the Ganga river in Bihar, Patna district has the longest riverfront stretch (~99 km), "
        "followed by Bhagalpur (~97 km)."
    ),
    ("65th BPSC", 36): (
        "The North Koel river rises on the Ranchi plateau in Jharkhand, flows northward to join the Son river, which in turn joins "
        "the Ganga near Patna—making North Koel part of the Ganga river basin. (Sankh and South Koel join to form the Brahmani river; "
        "Barakar is a tributary of the Damodar)."
    ),
    ("65th BPSC", 136): (
        "Hon'ble Chief Justice Amreshwar Pratap Sahi (A. P. Sahi) of the Patna High Court administered the oath of office to "
        "Shri Phagu Chauhan as the 29th Governor of Bihar at Raj Bhavan, Patna, on 29 July 2019."
    ),
    ("65th BPSC", 141): (
        "In January 2019 at Palamu (Jharkhand), Prime Minister Narendra Modi laid the foundation stone for reviving the incomplete "
        "Mandal Dam (North Koel Reservoir Project) on the North Koel river, benefiting irrigation in Jharkhand and Bihar (Aurangabad and Gaya)."
    ),
    ("66th BPSC", 78): (
        "The earliest capital of the ancient Mahajanapada of Magadha was Girivraja / Rajagriha (modern Rajgir), encircled by five hills, "
        "before Udayin shifted the capital to Pataliputra. Since Rajagriha/Girivraja is absent in options A–D, Option (E) is correct."
    ),
    ("66th BPSC", 97): (
        "Among Bihar's nine administrative divisions, the Ganga does NOT flow through Kosi (Saharsa, Madhepura, Supaul) or Magadh "
        "(Gaya, Nawada, Aurangabad, Jehanabad, Arwal) divisions (nor Darbhanga division alone, whereas Munger, Bhagalpur, Saran, Tirhut/Vaishali, "
        "and Purnea/Katihar touch the Ganga). Hence 'Kosi—Magadh' is the pair where neither division touches the Ganga."
    ),
    ("66th BPSC", 98): (
        "In Bihar, Oraon tribes are also present in Supaul/Purnea belt alongside Rohtas and West Champaran, Kharwar in Bhagalpur/Banka/Rohtas, "
        "Santhal in Banka/Bhagalpur/Purnea, and Munda in Rohtas/Buxar/Katihar (and some in Jamui); per BPSC's official 66th Final Key, "
        "Option (E) ('None of the above / More than one of the above') was keyed."
    ),
    ("66th BPSC", 100): (
        "Valmiki National Park—the only National Park in Bihar (also a Tiger Reserve and Wildlife Sanctuary)—is located in West Champaran district "
        "along the Indo-Nepal border on the banks of the Gandak river."
    ),
    ("67th BPSC", 90): (
        "At the time of the 67th BPSC Re-Exam (September 2022): (a) Governor of Bihar — Mr. Fagu Chauhan (4); "
        "(b) Chief Justice of Patna High Court — Justice Sanjay Karol (3); (c) Chief Minister of Bihar — Mr. Nitish Kumar (1); "
        "(d) Chief Electoral Officer of Bihar — Mr. H. R. Srinivas (2). Correct code: a-4, b-3, c-1, d-2."
    ),
    ("67th BPSC", 112): (
        "India's first (non-synchronous) population Census was conducted in 1872 during the tenure of Viceroy Lord Mayo "
        "(while the first synchronous decennial Census was conducted in 1881 under Lord Ripon)."
    ),
    ("67th BPSC", 135): (
        "The Kosi river is called the 'Sorrow of Bihar' because its heavy silt load from the Himalayas causes frequent channel shifting "
        "and devastating annual floods across northern Bihar."
    ),
    ("68th BPSC", 22): (
        "Kishanganj district in northeastern Bihar (part of the humid Terai–Dooars agro-climatic zone) accounts for the maximum "
        "tea cultivation and tea-processing industries in Bihar."
    ),
    ("68th BPSC", 90): (
        "According to the Bihar Economic Survey 2021–22 / 2022–23, Bihar's level of urbanization as per the 2011 Census was 11.3%, "
        "which rose to 15.3% following the statutory redefinition and creation/upgradation of urban local bodies (Nagar Panchayats and Nagar Parishads)."
    ),
    ("68th BPSC", 106): (
        "Statement 1 is correct (Rohtas—Amjhore—holds India's largest pyrite deposits) and Statement 3 is correct (Jamui holds Bihar's "
        "major gold ore reserves). Per BPSC's official 68th Final Answer Key, Statement 2 was treated as incorrect because limestone in Bihar "
        "is concentrated strictly in Kaimur and Rohtas (Vindhyan belt) rather than Munger; hence '1 and 3 only' (Option C) is correct."
    ),
    ("69th BPSC", 86): (
        "Valmiki National Park (West Champaran, 1) and Bhimbandh Wildlife Sanctuary (Munger, 4) are located in Bihar, whereas "
        "Dudhwa National Park (2) is in Uttar Pradesh and Gajner Wildlife Sanctuary (3) is in Bikaner, Rajasthan. Thus '1 and 4' is correct."
    ),
    ("69th BPSC", 88): (
        "The Gandak river (one of the major left-bank tributaries of the Ganga, entering Bihar near Valmikinagar in West Champaran) "
        "is also known as the 'Narayani' (and 'Saligrami' in Nepal)."
    ),
    ("69th BPSC", 122): (
        "Per BPSC's official 69th Final Answer Key, Option (A) 5,98,000 refers to the urban/city agglomeration population estimate of Gaya "
        "(while Gaya district's 2011 total population was ~43.9 lakh; among the given figures, 5,98,000 corresponds to Gaya city)."
    ),
    ("70th BPSC", 22): (
        "Peasant leader Swami Sahajanand Saraswati edited and published 'Lok Sangraha' (from Patna, along with 'Hunkar' later) "
        "to champion Kisan Sabha demands and highlight peasant grievances against zamindari oppression."
    ),
    ("70th BPSC", 69): (
        "'Sarva Hitaishi' (published from Patna in 1890) was the first Hindi daily newspaper published in Bihar (whereas 'Bihar Bandhu', "
        "started in 1872/1874, was Bihar's first Hindi weekly newspaper)."
    ),
    ("70th BPSC", 102): (
        "Takhat Sri Harimandir Ji Patna Sahib—one of the five holy Takhats of Sikhism and the birthplace of the tenth Sikh Guru, "
        "Guru Gobind Singh Ji (born 1666)—is located in Patna City, Bihar."
    ),
    ("70th BPSC", 111): (
        "Following the Delhi Durbar proclamation of 12 December 1911 separating Bihar and Orissa from the Bengal Presidency, "
        "the new province of Bihar and Orissa officially came into force on 1 April 1912."
    ),
    ("70th BPSC", 124): (
        "The Nanda dynasty (founded by Mahapadma Nanda around 345 BCE) succeeded the Shishunaga dynasty as rulers of Magadha, "
        "and was later overthrown by Chandragupta Maurya (Maurya dynasty) around 321 BCE."
    ),
    ("70th BPSC", 125): (
        "Neelam Sanjiva Reddy served twice as Speaker of the Lok Sabha (1967–1969 and March–July 1977) before being elected unopposed "
        "as the 6th President of India in July 1977."
    ),
    ("71st BPSC (2025)", 107): (
        "The Godavari river basin (~3.13 lakh sq km, nearly 10% of India's geographical area, known as 'Dakshin Ganga') is the "
        "second-largest river basin in India after the Ganga–Brahmaputra–Meghna (Ganga) basin."
    ),
    ("60-62nd BPSC (Combined)", 1): (
        "Babu Kunwar Singh (1777–1858), the zamindar of Jagdishpur (in present-day Bhojpur district, formerly Shahabad), was the "
        "foremost leader of the Revolt of 1857 in Bihar, leading resistance across Arrah, Danapur, Azamgarh, and Jagdishpur."
    ),
    ("60-62nd BPSC (Combined)", 41): (
        "Liquefied Petroleum Gas (LPG) used as domestic cooking fuel consists chiefly of propane (C3H8) and butane (C4H10) "
        "compressed into liquid form under pressure (with ethyl mercaptan added to detect leaks); per BPSC's 60th–62nd Final Key, "
        "since propane and butane are main constituents rather than methane/acetylene/ethylene alone, check the keyed option."
    ),
    ("60-62nd BPSC (Combined)", 42): (
        "Soap molecules have a hydrophobic hydrocarbon tail (soluble in oil/grease) and a hydrophilic ionic head (soluble in water), "
        "forming micelles that break up and suspend oil droplets in water—removing grease through emulsification."
    ),
    ("64th BPSC", 15): (
        "Greenhouse gases include water vapour (H2O), carbon dioxide (CO2), methane (CH4), nitrous oxide (N2O), and ozone (O3). "
        "Among anthropogenic emissions CO2 is the largest contributor (~65%–76%), while water vapour is the most abundant natural GHG; "
        "because multiple listed gases contribute / water vapour + CO2 apply, BPSC keyed Option (E)."
    ),
    ("65th BPSC", 6): (
        "On 12 March 1930, Mahatma Gandhi launched the Dandi March from Sabarmati Ashram (Ahmedabad) with 78 followers, reaching "
        "the coastal village of Dandi on 6 April 1930 where he broke the Salt Law and formally inaugurated the Civil Disobedience Movement."
    ),
    ("65th BPSC", 9): (
        "Babu Kunwar Singh of Jagdishpur (Bhojpur/Shahabad) spearheaded the Revolt of 1857 in Bihar at the age of nearly 80, "
        "winning notable victories against British forces before passing away in April 1858."
    ),
    ("65th BPSC", 96): (
        "Greenhouse gases trap outgoing terrestrial infrared radiation; major greenhouse gases include water vapour, carbon dioxide (CO2), "
        "methane (CH4), nitrous oxide (N2O), and ozone. Per BPSC's official key, Option (E) ('More than one of the above') applies."
    ),
    ("65th BPSC", 116): (
        "Using the Celsius-to-Fahrenheit conversion formula F = (9/5)C + 32: for C = 50°C, F = (9/5) × 50 + 32 = 90 + 32 = 122 °F."
    ),
    ("66th BPSC", 76): (
        "Babu Kunwar Singh, the chieftain of Jagdishpur (Arrah/Bhojpur), spearheaded the Revolt of 1857 in Bihar."
    ),
    ("66th BPSC", 133): (
        "Madam Bhikaji Rustom Cama unfurled the first version of India's tricolour flag of independence on 22 August 1907 at the "
        "International Socialist Conference held in Stuttgart, Germany."
    ),
    ("68th BPSC", 50): (
        "Sir Cyril Radcliffe, a British barrister, chaired both the Bengal Boundary Commission and the Punjab Boundary Commission "
        "appointed in July 1947 to demarcate the international borders between India and Pakistan."
    ),
    ("68th BPSC", 52): (
        "On 17 October 1940, Acharya Vinoba Bhave—chosen by Mahatma Gandhi as the first satyagrahi—launched the Individual Satyagraha "
        "from Pavnar (near Wardha, Maharashtra) by delivering an anti-war speech (Jawaharlal Nehru was the second satyagrahi)."
    ),
    ("68th BPSC", 123): (
        "Carbon dioxide (CO2), nitrous oxide (N2O), and methane (CH4) are all greenhouse gases that absorb infrared radiation and "
        "contribute to global warming; since more than one listed gas contributes, Option (D) 'More than one of the above' is correct."
    ),
    ("70th BPSC", 1): (
        "John Dalton's atomic theory (1808) postulated indivisible atoms of fixed mass combining in simple whole-number ratios, "
        "successfully explaining (i) Law of Conservation of Mass, (ii) Law of Constant Proportions, and (iv) Law of Multiple Proportions—but "
        "NOT (iii) Law of Radioactivity (discovered nearly a century later by Becquerel in 1896). Thus i, ii and iv is correct."
    ),
}
