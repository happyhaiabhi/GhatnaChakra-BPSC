/**
 * Sub-topic keyword rules for the KGS "प्रहार" test series.
 * Each test maps to an ordered list of [topic, regex] rules. The haystack is
 * `question + options + explanation + note` lower-cased; the FIRST matching
 * rule wins, so specific topics must come before broad catch-alls.
 * Use flexible endings (s?, a?, ies?) — \b boundaries fail on plurals.
 */
const RULES = {
  // ═══════════════════════ TEST 1 — BIHAR SPECIAL ═══════════════════════
  test_1: [
    ['Census & Population', /\b(census|population|literac|sex ratio|decadal|urbanis|urbaniz|demograph|density of population|slum|migration|child mortality|infant|mortality rate|age structure|birth rate|death rate|bpl)\b/],
    ['Forests & Wildlife', /\b(forest|wildlife|sanctuar|national park|tiger reserve|valmiki|bird sanctuary|gogabil|gangetic dolphin|gharial|deer park|bhimbandh|jheel|biosphere|endangered|van vibhag)\b/],
    ['Physical Geography', /\b(rock types?|dharwar|gneiss|oldest rocks|physiographic divisions?)\b/],
    ['Schemes & Policies', /\b(yojana|scheme|saat nischay|sat nischay|mukhyamantri|har ghar|jal jeevan|scholarship|pension|mission|abhiyan|amrit|smart city|credit card|matsya|mnrega|aawas|housing|swachh|bihar semiconductor|aviation hub|wings india)\b/],
    ['Agriculture & Irrigation', /\b(agricultur|crops?|paddy|rice|wheat|maize|irrigat|canal|sowing|harvest|fertili[sz]er|litchi|makhana|sugarcane|oilseed|pulses|sericul|horticul|dairy|milk production|fisher|farms?|kisan|organic farm|seed|tractor|krishi)\b/],
    ['Transport', /\b(national highways?|highways?|expressway|railways?|rail |trains?|station|airport|airway|bridge|port|waterway|nh-?\d|katihar division|danapur division|metro|ropeway|transport)\b/],
    ['Minerals', /\b(minerals?|mines|mining|quarry|mica|bauxite|kyanite|feldspar|pyrites?|limestone|dolomite|chromite|monazite|magnetite|hematite|limonite|siderite|copper ore|placer|uranium|jadugoda|graphite|apatite|asbestos|steatite|saltpetre|saltpeter|fireclay|china clay|kaolin|building material)\b/],
    ['Rivers, Lakes & Waterfalls', /\b(rivers?|ganga|ganges|kosi|gandak|ghaghara|punpun|falgu|phalgu|karmanasa|bagmati|mahananda|kiul|burhi|tributar|confluence|lakes?|waterfall|kakolat|karkat|dhua|amjhor|sugwa|barkagaon|anti?cedent drainage|drainage|flood|diara|tal area|mokama tal|chaurs?|ox-?bow|bhairvi|durgawati|kamla|balan|baya|morhar|lilajan|niranjana|mohane|koel)\b/],
    ['Art, Culture & Language', /\b(festival|dance|madhubani|mithila painting|painting|folk|chhath|sama chakeva|teej|bihula|bidesia|biraha|jat jatin|nacha|launda|ramlila|tusu|sankranti|chau|saree|baluchari|tussar|bhojpuri|maithili|magahi|angika|bajjika|dialect|theatre|music|instrument|craft|handicraft|sculpture|idol|mela|cuisine|litti|khaja|silao|son papdi|belgrami|khurma|anarsa|malpua|thekua|chhau|statue)\b/],
    ['Books, Authors & Press', /\b(books?|novel|author|written by|literature|literary|magazine|journal|newspaper|press|doordarshan|broadcast|television|radio|bihar bandhu|dinkar|phanishwar|renu|nagarjun|ramdhari|publisher|biography|autobiography|sahitya akademi)\b/],
    ['Polity & Elections', /\b(legislative assembly|vidhan sabha|vidhan parishad|chief minister|cabinet of bihar|governor of bihar|mla|mp from|lok sabha|rajya sabha|constituenc|election|bye-?election|by-?poll|electoral|speaker of|leader of opposition|legislative council|panchayat|municipal|raj bhavan|patna high court|chief secretary|zila parishad|mukhiya|nagar nigam|state election|grievance|prashasan|sushasan|good governance)\b/],
    ['Economy & Industry', /\b(economy|gdp|gsdp|industr|factory|handloom|weaver|investment|mou|bank|finance|per capita income|poverty|unemploy|brewery|sugar mill|leather|footwear|toy park|it park|startup|msme|export|trade|manufactur|textile|fodder|economic survey|budget|gst|tourism|development authority|buidco|bsphcl|refinery)\b/],
    ['Modern Bihar & Freedom Struggle', /\b(1857|revolt of|rebellion|sepoy|mutiny|kunwar singh|british|east india company|congress|gandhi|gandhiji|mahatma|champaran|satyagraha|quit india|non-?cooperation|azad|revolutionar|jayaprakash|jaya prakash|jp movement|emergency|kisan sabha|swadeshi|partition|independence|swaraj|sahajanand|anushilan|jugantar|khilafat|peasant|indigo|rajendra prasad|anugrah narayan|shri krishna singh|batukeshwar|khudiram|sachchidanand|mazharul haque|lalit narayan|karpuri thakur|ram manohar lohiya|lok nayak|naval mutiny| INA |azad hind)\b/],
    ['Medieval Bihar', /\b(sultans?|sultanate|khalji|khilji|bakhtiyar|mughal|akbar|jahangir|shah jahan|aurang[sz]eb|sher shah|shershah|suri|azimabad|bihar sharif|tughlaq|firoz shah|sikandar lodi|ibrahim lodi|daud khan|husain shah|saadat khan|shuja|mir qasim|nawab|rohtas fort|maner sharif|pathan|muhammad bin|delhi sultanate|malik|firishta|iqta|jizya|faujdar|kotwal|qazi|madrasa|sufi|silsila|khanqah|chakladar)\b/],
    ['Ancient Bihar', /\b(ancient|maurya|magadh|magadha|nalanda|vikramshila|vikrama[sz]ila|odantapuri|ashoka|asoka|bimbisara|ajatashatru|shishunaga|nanda dynas|gupta|licchavi|lichchhavi|vajji|malla|anga|vaishali|rajgir|girivraja|pataliputra|bodh ?gaya|buddha|buddhis|mahavir|jain|chandragupta|samudragupta|skandagupta|kumargupta|megalithic|neolithic|chalcolithic|paleolithic|stone age|6th century|b\.c\.|before christ|cha?mpa|pitaka|abhidhamma|vihara|monaster|stupa|barabar|saptanga|arthashastra|kautilya|chanakya|fa-?hien|hiuen tsang|xuanzang|shunga|kanva|kushana?|pgw|northern black polished|shreni|gana-?sangha|videha|mithila|janaka|yajnavalkya|pala dynas|palas?|devapala|dharmapala|gopala|harsha|harshavardhana|aryabhatta|aryabhata|sushruta|charaka)\b/],
    ['Physical Geography', /\b(physiographic|shivalik|siwalik|terai|bhabar|doab|gangetic plain|alluvial|soil|plateau|kaimur|rohtas|rajgir hills|hills?|earthquake|seismic|laterite|saline|alkaline|usara|bangar|khadar|rocks?|geolog|climate of bihar|rainfall in bihar|monsoon in bihar|drought|map of bihar|districts? of bihar|boundary of bihar|area of bihar|latitude|longitude|neighbouring state|division of bihar|commissionary|tehsil|block)\b/],
    ['Current Affairs (Bihar)', /\b(2023|2024|2025|2026|appointed|inaugurat|launched|flagged off|signed|award|brand ambassador|khelo|championship|tournament|hosted in bihar|summit in patna|unveiled|foundation stone|cabinet approv|bihar diwas|ranji|trophy|cricket|kabaddi|hockey|medal|youth games|national games|olympic|asian games|players?|sports|statue|promoted)\b/],
  ],

  // ═══════════════════════ TEST 2 — WORLD GEOGRAPHY ═══════════════════════
  test_2: [
    ['Environment & Conservation', /\b(environment|conservation|biodivers|endangered|red list|iucn|biosphere|ozone|climate change|global warming|kyoto|rio summit|cites|wetland|ramsar|national park)\b/],
    ['Oceans & Currents', /\b(oceans?|currents?|gulf stream|labrador current|kuroshio|tides?|coral|reefs?|salinity|tsunami|mariana|sargasso|continental shelf|abyssal|pelagic|el ni[nñ]o|la ni[nñ]a|fisheries?|ports? and harbou?rs?)\b/],
    ['Agriculture & Economy', /\b(agricultur|farming|crops?|plantation|wheat|rice|dairy|pastoral|ranching|viticulture|industry|industrial region|manufactur|trade|export|seaway|canal|panama|suez|trans-?siberian|railways?| silk road|economic)\b/],
    ['Rivers & Lakes', /\b(rivers?|lakes?|waterfalls?|nile|amazon|congo|mississippi|yangtze|missouri|ob|yenisei|lena|amur|mackenzie|danube|rhine|volga|thames|seine|zambezi|niger|murray-?darling|tributar|deltas?|estuaries?|estu?ary|caspian|superior|baikal|tanganyika|victoria lake)\b/],
    ['Climate', /\b(climate|climatic|monsoon|cyclones?|hurricane|typhoon|tornado|rainfall|precipitation|el ni[nñ]o|jet stream|atmosphere|isobars?|isotherms?|temperature|dew point|humidity|frontogenesis|weather|mid-?latitudes|temperate|tropical|equatorial|tundra|taiga|savanna|deserts?|arid|mediterranean)\b/],
    ['Minerals & Resources', /\b(minerals?|mining|coal|petroleum|natural gas|oil fields?|iron ore|bauxite|copper|uranium|diamonds?|gold fields?|hydropower|energy resources|renewable|fisheries?|resource|power resources)\b/],
    ['Population & Settlement', /\b(population|demograph|literac|migration|urbanis|urbaniz|human settlement|settlement pattern|nomads?|tribes?|races?|language family|religion|refugees?|density of population|human development|hdi|fertility)\b/],
    ['Physical Landforms', /\b(landforms?|plateaus?|mountains?|ranges?|fold|block mountain|fault|rift valley|volcano|earthquake|seismic|glaciers?|erosion|weathering|karst|stalactite|stalagmite|aeolian|loess|deltas?|plain|geomorph|rocks?|strait|isthmus|peninsula|archipelago|islands?|continent)\b/],
    ['Continents & Regions', /\b(continent|africa|asia|europe|america|australia|antarctica|sahara|gobi|kalihari|kalahari|namib|atacama|dispute|country|countries|capital|landlocked|boundar|neighbouring|region of|siberia|scandinavia|amazon basin|congo basin|great plains|prairies|pampas|veld|downs|steppes|savanna)\b/],
  ],

  // ═══════════ TEST 3 / 9 / 14 — CURRENT AFFAIRS ═══════════
  test_3: CURRENT_AFFAIRS(),
  test_9: CURRENT_AFFAIRS(),
  test_14: CURRENT_AFFAIRS(),

  // ═══════════════ TEST 4 / 5 — INDIAN GEOGRAPHY ═══════════════
  test_4: INDIAN_GEOGRAPHY(),
  test_5: INDIAN_GEOGRAPHY(),

  // ═══════════════════ TEST 6 — INDIAN ECONOMY ═══════════════════
  test_6: [
    ['Planning & Economic Reforms', /\b(five-?year plans?|plan holiday|annual plans?|planning commission|niti aayog|mahalanobis|bombay plan|gandhian plan|peoples? plan|industrial policy resolution|ipr of 1956|new economic policy|liberalis|privatis|privatiz|disinvest|maharatna|navratna|miniratna|cpse|nimz|ppp|public-?private partnership|toll-?operate|invit|infrastructure investment trust|usof|harrod)/],
    ['Economic Concepts & Public Finance', /\b(aggregate supply|aggregate demand|public goods?|free-?rider|gini|lorenz|automatic stabili|national product|gross value added|gva|index of industrial production|iip|debt-?equity|consumer durable|inferior goods?|giffen|recession|business cycle|subsid|public expenditure|multiplier|elasticity|demand curve|supply curve|law of demand|utility|consumer.?s equilibrium|production possibility|fiscal policy|counter-?cyclical|progressive tax|proportional tax|regressive tax)/],

    ['International Institutions & Trade Bodies', /\b(imf|world bank|wto|adb|aiib|brics|nep? bank|world economic forum|g7|g20|opec|unctad|unido|fatf|basel|international monetary|international bank|multilateral)\b/],
    ['Banking & Finance', /\b(rbi|reserve bank|repo rate|reverse repo|bank rate|cash reserve ratio|crr|slr|monetary policy|npci|upi|digital payment|credit rating|npa|insolvency|ibc|sebi|stock exchange|mutual fund|sip|ipo|insurance|irdai|lic|pension fund|nabard|sidbi|mudra|payment bank|small finance bank|neft|recurring deposit|commercial bank|crar|capital to risk|money market|categories of loans|cheque|kyc|base rate|marginal cost of funds|priority sector|lead bank|cooperative bank|cryptocurrenc|digital rupee|cbdc)\b/],
    ['Budget & Taxation', /\b(budget|finance commission|gst|tax|customs duty|excise|direct tax|indirect tax|cess|fiscal deficit|revenue deficit|primary deficit|expenditur|appropriation bill|finance bill|capital budget|union budget)\b/],
    ['External Sector & Trade', /\b(exports?|imports?|trade deficit|current account|balance of payment|forex|foreign exchange|rupee|currency|devaluation|fdi|fpi|external debt|special economic zone|sezs?|tariff|free trade agreement|fta|rcep)\b/],
    ['Money & Capital Markets', /\b(money supply|m1|m2|m3|m4|inflation|cpi|wpi|cpi-?i|price index|deflation|stagflation|liquidity|bond|yield|gilt|treasury|call money|commercial paper|certificate of deposit|primary market|secondary market|bullion)\b/],
    ['Agriculture & Rural Economy', /\b(agricultur|farmers?|crop|msp|minimum support price|kisan|pm-?kisan|irrigat|fertiliser|fertilizer|monsoon and agriculture|rural|food security|pd?s|ration|public distribution|fcI|food corporation|harvest|horticulture|allied sector|fisheries|dairy|livestock)\b/],
    ['Industry & Infrastructure', /\b(industr|manufactur|factory|msme|startup|production linked incentive|pli|logistics|national infrastructure|infrastructur|roadways|railways?|port|airport|power sector|coal sector|steel|cement|textile|defence production|semiconductor|electric vehicle|hyperloop|metro)\b/],
    ['Poverty & Employment', /\b(poverty|below poverty|bpl|employment|unemploy|jobless|mgnrega|labour force|workforce|informal sector|gig economy|skill india|health and education|human development|social sector)\b/],
    ['Growth & National Income', /\b(gdp|gva|national income|per capita income|economic growth|growth rate|base year|constant price|real gdp|nominal gdp|economic survey|csO|mospi|estimates|gsva|bihar.?s gross|state value added)\b/],
    ['Schemes & Policies', /\b(scheme|yojana|mission|abhiyan|pmay|awaas|jal jeevan|ayushman|swachh|pm poshan|atmanirbhar|vocal for local|make in india|start-up india|stand-up india|plb scheme|pm kisan maandhan)\b/],
  ],

  // ═══════════════════ TEST 7 — ANCIENT HISTORY ═══════════════════
  test_7: [
    ['Art & Architecture', /\b(stupa|chaitya|vihara|pillars? of ashoka|cave|barabar|karle|bhaja|ajanta|ellora|sanchi|bharhut|amravati|nagarjunakonda|gandhara|mathura school|sculpture|temple architecture|nagara|dravida|vesara|garbhagriha|shikhara|mandapa|gopuram|fresco|mural|pottery|terracotta|coins? of|numismatic)\b/],
    ['Literature', /\b(vedas?|rigveda|samaveda|yajurveda|atharvaveda|brahmanas?|aranyakas?|upanishad|epic|ramayana|mahabharata|puranas?|smriti|kalpasutra|sutra|kautilya|arthashastra|indica|megasthenes|ashtadhyayi|panini|mahavamsa|dipavamsa|buddhacharita|kamasutra|abhijnana|malavikagnimitra|mrichchhakatika|gathasaptashati|charaka samhita|sushruta samhita|aryabhatiya|literature|literary|sangam literature|tolkappiyam|silappadikaram|manimekalai|playwright|poet)\b/],
    ['Buddhism & Jainism', /\b(buddha|buddhis|bodh|mahayana|hinayana|theravada|vajrayana|sangha|monastery|nalanda|sarnath|kushinagar|lumbini|bodh gaya|jaina|jainism|mahavira|tirthankara|digambara|shvetambara|ahimsa|triratna|panchsheel|anjali)\b/],
    ['Science & Math', /\b(aryabhata|zero|decimal|geometry|algebra|astronom|sulbasutra|charaka|sushruta|ayurved|metallurgy|iron pillar|wootz|scientific)\b/],
    ['Indus Valley', /\b(indus|harappan|mohenjo|haryana sites|rakhigarhi|dholavira|lothal|kalibangan|chanhudaro|banawali|surkotada|daimabad|cities of indus|great bath|granary|seals? of indus)\b/],
    ['Vedic Age', /\b(vedic|rigvedic|later vedic|aryan|aryans?|dasas?|dasyu|rajanya|vaishya|shudra|varna|sabha|samiti|gavishti|brahmana|upanishad|gotra|ashrama|purusha sukta)\b/],
    ['Mauryan Empire', /\b(maurya|mauryan|chandragupta|bindusara|ashoka|asoka|kalinga|edicts?|dhamma|megasthenes|kautilya|chanakya|arthashastra|samrat|suvarnagiri|kumara|dasharatha)\b/],
    ['Invasions (Persian & Greek)', /\b(darius|persian|achaemenid|alexander|greek|ambhi|porus|selucus|seleucus|megasthenes indic|indo-?greek|menander|demetrius|shaka|scythian|parthian|kushana?|hud|hunas?)\b/],
    ['Post-Mauryan Period', /\b(shunga|kanva|satavahana|kharavela|ching|indo-?greek|indo-?parthian|kushana?|kanishka|hud|gaud|nagas? of padmavati|vakataka)\b/],
    ['Gupta & Post-Gupta', /\b(gupta|chandragupta ii|samudragupta|skandagupta|kumargupta|ramagupta|shakas?|nalkonda|harsha|harshavardhana|pushyabhuti|thanesar|vakataka|mauryas? of konkan|maitraka|maitrakas of valabhi|pushyamitra)\b/],
    ['South India', /\b(chola|cholas?|pallava|chalukya| Rashtrakuta|rashtrakuta|sangam|pandyas?|cheras?|pallavas?|mahabalipuram|kanchipuram|tanjavur|rajrajeshwara| brihadeshwara|local assemblies?|ur|sabha of south|madan)\b/],
    ['Mahajanapadas & Magadh', /\b(mahajanapada|magadh|magadha|bimbisara|ajatashatru|haryanka|shishunaga|nanda|vaishali|vajji|licchavi|malla|angutara|gana-?sangha|republics? of 6th|sixteen kingdoms|rajgir|girivraja|pataliputra)\b/],
    ['Prehistoric & Stone Age', /\b(palaeolithic|paleolithic|mesolithic|neolithic|chalcolithic|megalithic|stone age|prehistory|prehistoric|microlith|quartzite|hunter-?gatherer|bhimbetka|rock paintings?|bronze age|iron age|copper hoard|ochre coloured pottery|ocp)\b/],
    ['Philosophy & Religion', /\b(philosoph|vedanta|mimamsa|sankhya|yoga|nyaya|vaisheshika|upanishadic|bhagavad|bhagavata|shaivism|vaishnavism|shaktism|tantrism|worship|cult|ritual|sacrifice|yajna|agnostic|charvaka|ajivika|pasupata)\b/],
  ],

  // ═══════════════ TEST 8 — MEDIEVAL HISTORY ═══════════════
  test_8: [
    ['Bhakti & Sufi Movements', /\b(bhakti|sufi|sufism|sant|kabir|nanak|ramanuja|nimbarka|madhvacharya|vallabhacharya|chaitanya|mirabai|tulsidas|surdas|namdev|tukaram|jnanesvar|silsila|qadiri|chishti|suhrawardi|naqshbandi|khanqah|dargah|wali|mystic|devotional)\b/],
    ['Art, Culture & Literature', /\b(architecture|arch|music|musical|painting|miniature|pahari|mughal painting|literature|literary|poet|court poet|amir khusrau|persian literature|vernacular|kathak|sitar|sarod|tabli|dhrupad|qawwali|calligraphy|gardens? of|charbagh|pietra dura|jali|pachchikari|fort|palace|tombs?|mosque|masjid|gateway|arch|dome|minaret)\b/],
    ['Marathas & Sikhs', /\b(maratha|marathas?|shivaji|shahu|peshwa|bajirao|balaji|sambhaji|rajaram|tarabai|anglo-?maratha|confederac|sikh|guru nanak|guru tegh|guru gobind|khalsa|adal|ranjit singh|misl|anglo-?sikh)\b/],
    ['Vijayanagar & Regional Kingdoms', /\b(vijayanagar|hampi|krishnadeva|raya|bahmani|bahmanid|deccan sultanate|bijapur|golkonda|ahmadnagar|berar|bidar|qutb shahi|adil shahi|nim shahi|gajapati|reddy|kakatiya|hoysala|yadava|seuna|pandyas? of madurai|zamindars? of south)\b/],
    ['Delhi Sultanate', /\b(delhi sultanate|iltutmish|aibak|qutub|qutb-?ud-?din|razia|balban|khalji|khilji|ala-?ud-?din|jalaluddin|tughlaq|muhammad bin|firoz shah|firuz shah|sayyid|lodhi|lodi|iqta|iqtedar|diwan-?i-?wizarat|diwan-?i-?arz|amir|umara|qazi|kotwal|naib|muqti|bandagan|charai|ghari|gharra|kharaj|jizya|khums|zakat)\b/],
    ['Mughal Empire', /\b(mughal|babur|humayun|akbar|jahangir|shah jahan|aurangzeb|shershah|sher shah|suri|mansabdari|mansab|jagir|zabti|dahsala|todar|todarmal|ain-?i-?akbari|akbarnama|baburnama|tuzuk|diwan-?i-?khas|subah|sarkar|pargana|amat|krori|bania|nur jahan|jahanara|raja man singh|birbal|tansen|todarmal|mahr|irani|turani|rajput policy|sulh-?i-?kul|din-?i-?ilahi|fatehpur sikri)\b/],
    ['Arrival of Turks & Early Sultanate', /\b(mahmud|ghazni|ghori|ghurid|muhammad ghori|qutb-?ud-?din aibak|turk|turkish|khilji revolution|second battle of tarain|first battle of tarain|prithviraj|jaichand|bakhtiyar khalji|slave dynasty|gulam)\b/],
    ['Administration, Economy & Society', /\b(administrat|revenue|land revenue|zabti|raya|qanungo|patwari|muqaddam|khut|chaudhri|iqta|jagir|inam|madad-?i-?maash|trade|commerce|surat|hooghly|merchant|guild|coins?|currency|tanka|jital|society|social structure|slavery|ulema|nobility|zamindar|raiyat| peasant)\b/],
  ],

  // ═══════════ TEST 10 — BIOLOGY + SCIENCE & TECHNOLOGY ═══════════
  test_10: [
    ['Space & Defence Technology', /\b(isro|nasa|chandrayaan|gaganyaan|aditya|pslv|gslv|cryogenic|satellite|spacecraft|orbit|launch vehicle|drdo|missile|agni|prithvi|brahmos|rafale|tejas|fighter|submarine|aircraft carrier|defence|artillery|drone|uav)\b/],
    ['IT, Electronics & New Tech', /\b(semiconductor|chip|transistor|quantum computing|quantum computer|blockchain|cryptocurrenc|artificial intelligence|machine learning|neural network|5g|6g|internet|web 3|web3|big data|cloud computing|supercomputer|operating system|software|bluetooth|wifi|gps|robot|drone delivery|3d printing|nanotechnology|virtual reality|augmented reality|cyber)\b/],
    ['Nuclear & Energy Technology', /\b(nuclear|fission|fusion|reactor|thorium|uranium enrichment|tokamak|renewable|solar cell|photovoltaic|wind energy|hydrogen fuel|biofuel|battery|lithium-?ion|grid)\b/],
    ['Biotechnology', /\b(biotechnolog|genetic engineering|crispr|gene editing|genome|recombinant|dna technology|transgenic|gm crops?|cloning|stem cell|pcr|vaccine technolog|mRNA|monoclonal|hybridoma|enzyme technolog|bioreactor|fermentation|biopiracy|biopatent)\b/],
    ['Microbiology', /\b(bacteriophage|virus structure|capsid|lytic|lysogenic|protozoa|amoeba|plasmodium|microbiolog|culture medium|gram stain|fermentation by|yeast|curd|antibiotic production|penicillin)\b/],
    ['Genetics & Heredity', /\b(genetics|heredity|gene|dna|rna|allele|dominant|recessive|mendel|mutation|down.?s syndrome|klinefelter|turner|haemophilia|color blindness|blood group|abo|rh factor|genotype|phenotype|linkage|crossing over)\b/],
    ['Diseases & Health', /\b(disease|cancer|diabetes|tuberculosis|malaria|dengue|cholera|typhoid|hepatitis|aids|hiv|covid|corona|virus|viral|bacteria|bacterial|infection|pathogen|antibiotic|symptom|deficiency disease|goitre|rickets|scurvy|beriberi|night blindness|obesity|mental health|who)\b/],
    ['Human Physiology', /\b(human body|physiolog|heart|blood|circulat|respirat|lung|digest|stomach|liver|kidney|excret|nervous|brain|neuron|hormone|endocrine|thyroid|adrenal|insulin|pancreas|muscle|skeleton|bone|joint|skin|eye|ear|immun|antibody|vaccin|lymph)\b/],
    ['Cell & Biomolecules', /\b(cells?|cell membrane|cell wall|organelle|mitochondria|ribosome|golgi|endoplasmic|lysosome|nucleus|chromosome|prokaryote|eukaryote|plasmid|cell division|mitosis|meiosis|protein synthesis|carbohydrate|lipid|protein|enzyme|amino acid|nucleic acid|atp)\b/],
    ['Plant Biology', /\b(photosynthesis|plant|root|stem|leaf|stomata|guard cells?|xylem|phloem|transpiration|flower|pollination|seed|germinat|plant hormone|auxin|phototrop|tropism|respiration in plants?|plant tissue|meristem|bryophyt|pteridophyt|gymnosperm|angiosperm|algae|fungi|mushroom|lichen)\b/],
    ['Nutrition & Vitamins', /\b(vitamin|nutrition|nutrient|mineral requirement|balanced diet|protein energy|malnutrition|calorie|fat|roughage|iodine|iron deficiency|anaemia|fluoride)\b/],
    ['Ecology & Environment', /\b(ecolog|ecosystem|food chain|food web|biomagnificat|biodivers|conservation|national park|sanctuary|endangered|pollution|climate change|global warming|ozone|biogeochemical|carbon cycle|nitrogen cycle|sustainable)\b/],
    ['Evolution & Taxonomy', /\b(evolution|darwin|natural selection|origin of species|lamark|lamarck|speciation|fossil|taxonomy|classification|binomial|nomenclature|kingdom|species|genus|five kingdom|whittaker)\b/],
  ],

  // ═══════════ TEST 11 — MODERN HISTORY I (Europeans → 1885) ═══════════
  test_11: [
    ['Revolt of 1857', /\b(1857|revolt|sepoy|mutiny|rising of|mangal pandey|nana saheb|tantia tope|rizia|rani laxmi|lakshmibai|jhansi|kanpur|bareilly|kunwar singh|bahadur shah|generalService enlistment|general service enlistment|doctrine of lapse)\b/],
    ['Socio-Religious Reform', /\b(ram mohan|brahmo|aryasamaj|arya samaj|dayanand|ramakrishna|vivekananda|prarthana samaj|satyashodhak|jyotiba|phule|theosophical|annie besant|sikh reform|singh sabha|ahmadiya|aligarh|syed ahmed|sayyid ahmed|deoband|widow remarriage|vidyasagar|sati|child marriage|widow|caste reform|depressed class|reform movement|social reform|young bengal|derozio)\b/],
    ['Press, Education & Literature', /\b(press|newspaper|journal|vernacular press act|newspaper act|censorship|printin|education|universit|calcutta university|wood.?s despatch|macaulay|hunter commission|sadler commission|english education|literature|novel|bengali literature|hindi literature)\b/],
    ['Peasant, Tribal & Civil Rebellions', /\b(indigo|deccan riots|riot|sanyasi|faqir|moplah|santhal|santal|kol|munda|birsa|bhil|rampa|poligar|revolt of|uprising|peasant|ryot|pabna|fachna|kuka|wahabi|farazi|faraidi)\b/],
    ['European Companies & Conquest', /\b(portugue|dutch|english east india|french|carnatic|battle of plassey|buxar|bengal treaty of|treaty of allahabad|dual government|bombay|madras|calcutta presidenc|factory|fort william|fort st|charters? of|regulating act|pitt.?s india act|amritsar treaty of 1806|subsidiary alliance|wellesley|dalhousie|doctrine of lapse|anglo-?mysore|anglo-?maratha|anglo-?sikh|tipu|haider|hyder|war of|conquest|colonial)\b/],
    ['Economic Policies & Exploitation', /\b(land revenue|permanent settlement|ryotwari|mahalwari|cornwallis|ryot|zamindar|drain of wealth|deindustrialis|economic critique|tariff|free trade|opium|indigo planters|famine|railways? introduction|telegraph|postal|deprivation)\b/],
    ['Governors-General & Administration', /\b(governor|governor-?general|viceroy|warren hastings|cornwallis|wellesley|minto|william bentinck|dalhousie|curzon|canning|lytton|ripon|acts? of 17|acts? of 18|charter act|regulating act|pitt|administrative|civil service|ics|haileybury|leftwich)\b/],
    ['Early Political Associations', /\b(landholders|british india association|east india association|indian association|surendranath|randhir|dadabhai|naoroji|pheroze|wc bonnerjea|indian national congress|inc founded|congress session|moderate|extremist|aits|political association|national movement)\b/],
    ['Personalities & Miscellaneous', /\b(who among|which of the following personalities?|founded by|associated with)\b/],
  ],

  // ═══════════ TEST 12 — MODERN HISTORY II (1885 → 1947+) ═══════════
  test_12: [
    ['Partition & Independence', /\b(partition|pakistan|mountbatten|plan of 3 june|3rd june plan|radcliffe|transfer of power|independence act|14 august|15 august|divided india|communal riot|direct action day)\b/],
    ['Constitutional Reforms (1892–1935)', /\b(act of 1892|act of 1909|morley|minto|montagu|chelmsford|act of 1919|act of 1935|government of india act|communal award|poona pact|round table|simon commission|dyarchy|diarchy|provincial autonomy|separate electorate|franchise)\b/],
    ['Gandhi & Mass Movements', /\b(gandhi|gandhiji|mahatma|champaran|kheda|ahmedabad mill|rowlatt|jallianwala|amritsar massacre|non-?cooperation|chauri chaura|civil disobedience|dandi|salt march|salt satyagraha|round table and gandhi|poona pact|quit india|do or die|august revolution|individual satyagraha|harijan|constructive programme)\b/],
    ['Revolutionary Nationalism', /\b(revolutionar|hsra|bhagat singh|chandrashekhar azad|azad|rajguru|sukhdev|batukeshwar|khudiram|praak|prafulla|anushilan|jugantar|ghadar|kartar singh|madan lal|udham singh|chittagong|surya sen|kalyan das|vaisakha| INA |azad hind|subhas|subhash|bose|ras behari|v.d. savarkar|abhina|mitra mela|hindustan republican|hra)\b/],
    ['Congress & National Movement Phases', /\b(congress|congress session|moderates?|extremists?|surat split|lucknow pact|home rule|swadeshi|boycott|divide and rule|lagan|tilak|gokhale|naoroji|besant|lal-?bal-?pal|pal|lajpat|aurbindo|arabindo|sri aurobindo|khilafat|non-?cooperation|swaraj|swarajya|cripps|cabinet mission|wavell|lahore session|purna swaraj|karachi session|faizpur|tripuri|haripura)\b/],
    ['Peasant, Worker & Tribal Movements', /\b(kisan|peasant| sabha|workers?|labour|trade union|aituc|strike|mill worker|champaran? dup|bardoli|no-?tax|ekt|forest satyagraha|tribal|adivasi|uprising)\b/],
    ['Princely States & Integration', /\b(princely|native state|junagadh|hyderabad|kashmir accession|patel|integration of states|instrument of accession|raja of|nizam)\b/],
    ['Post-Independence India', /\b(after independence|post-?independence|first cabinet|planning commission|five year plan|first amendment|reorganisation of states|sardar patel|b.r. ambedkar|ambedkar|constitution|constituent assembly|republic|1947|1950|sarkaria)\b/],
    ['Personalities & Books', /\b(personalit|autobiography|biography|written by|books?|memoir|gandhi.?s work|works of)\b/],
    ['Bihar & the National Movement', /\b(bihar|patna|champaran|munger|bhagalpur|muzaffarpur|darbhanga|bihar congress|jayaprakash|swami sahajanand|shri krishna singh|anugrah|rajendra prasad|mazharul)\b/],
  ],

  // ═══════════════ TEST 13 — PHYSICS + CHEMISTRY ═══════════════
  test_13: [
    ['Metals, Non-Metals & Metallurgy', /\b(alloys?|brass|bronze|solder|amalgam|stainless steel)\b/],
    ['Organic & Everyday Chemistry', /\b(catenation|ability of carbon to form)\b/],
    ['Electricity & Magnetism', /\b(dry cell|torch)\b/],
    ['Units, Measurement & Instruments', /\b(unit|si |cgs|dimension|measur|vernier|thermocouple|pyrometer|screw gauge|micrometer|barometer|manometer|ammeter|voltmeter|thermometer|galvanometer|sphygmomanometer|odometer|speedometer|lactometer|hydrometer|dynamometer|seismograph|instrument|prefix|significant figures?|error)\b/],
    ['Optics', /\b(optic|light|mirror|lens|refract|reflect|total internal reflection|dispersion|spectrum|prism|focal|convex|concave|myopia|hypermetropia|presbyopia|interference|diffraction|polarisation|polarization|huygens|photometer|luminous|illuminat)\b/],
    ['Sound & Waves', /\b(sound|wave|wavelength|frequency|amplitude|vibration|echo|sonar|ultrason|infrason|pitch|loudness|doppler|resonance|harmo?nic|longitudinal wave|transverse wave|compression|rarefaction|periodic|oscillat|simpl? harmonic|shm|pendulum)\b/],
    ['Heat & Thermodynamics', /\b(heat|thermodynat|thermodynamic|temperature|thermometer|calorimet|specific heat|latent|fusion of ice|boiling|melting|evaporat|condensat|sublimat|conduction|convection|radiation of heat|carnot|entropy|isotherm|adiabatic|regelation|kelvin|celsius|thermal expan|kinetic theory)\b/],
    ['Modern & Nuclear Physics', /\b(radioact|nuclear|fission|fusion|isotope|rutherford|bohr.?s model|quantum|photoelectric|x-?ray|gamma|alpha particle|beta particle|half-?life|electron|proton|neutron|nucleus|planck|de broglie|heisenberg|cathode ray|anode ray|particle physic)\b/],
    ['Metals, Non-Metals & Metallurgy', /\b(metal|non-?metal|alloys?|brass|bronze|steel|solder|amalgam|platinum|tungsten|nichrome|rust|corrosion|galvanis|galvaniz|metallurg|ore|smelting|roasting|calcination|refining|thermite|extraction of|activity series|reactivity series|sodium|potassium|calcium|magnesium|aluminium|aluminum|zinc|copper|iron|lead|mercury)\b/],
    ['Electricity & Magnetism', /\b(electric|current|voltage|resistance|ohm|volt|ampere|circuit|fuse|magnet|magnetic|electromagnet|induction|motor|dynamo|generator|transformer|capacitor|condenser|coulomb|faraday|kirchhoff|galvanometer|ammeter|voltmeter|superconduct|semiconductor|diode|transistor|insulator|conduct\b)/],
    ['Motion, Forces & Mechanics', /\b(motion|velocity|acceleration|force|newton.?s|momentum|inertia|friction|gravity|gravitation|projectile|circular motion|centripetal|centrifugal|torque|moment of force|work|energy|power|collision|elasticity|stress|strain|young.?s modulus|poisson|pressure|archimedes|buoyan|floatation|viscosity|surface tension|capillar|bernoulli|pascal|equilibrium|displacement|uniform|retardation)\b/],
    ['Everyday Physics & Scientists', /\b(scientist|invention|discovered|nobel prize in physics|cavendish|einstein|faraday|newton|edison|tesla|marconi|raman|raman effect|chandrasekhar|bose|everyday|daily life|cricket ball|ceiling fan|bicycle)\b/],
    ['Atomic Structure & Periodic Table', /\b(atom|atomic|proton|neutron|electron shell|orbital|quantum number|aufbau|pauli|hund|mendeleev|modern periodic|periodic table|periodic law|group and period|atomic number|mass number|isobar|isotone|valency|electron configuration)\b/],
    ['Chemical Bonding & Reactions', /\b(bond|bonding|covalent|ionic|metallic bond|hydrogen bond|vanderwaals|van der waals|hybridis|hybridiz|vsepr|molecular orbital|reaction|oxidation|reduction|redox|catalyst|equilibrium|le chatelier|stoichiometr|mole concept|avogadro|molarity|molality|ph|acid|base|salt|neutralis|neutraliz|titration|buffer)\b/],
    ['Organic & Everyday Chemistry', /\b(organic|hydrocarbon|catenation|alkane|alkene|alkyne|benzene|aromatic|polymer|plastic|rubber|fibre|alcohol|phenol|ether|aldehyde|ketone|carboxylic|ester|soap|detergent|cosmetic|fuel|coal|petroleum|refinery|lpg|cng|biogas|hydrogen as fuel|fertiliser|fertilizer|pesticide|insecticide|dye|paint|varnish|glass|cement|ceramic|explosive|matchstick|candle|chemistry in|carbon compound)\b/],
    ['States of Matter & Gas Laws', /\b(states of matter|solid|liquid|gas|plasma|boyle|charles|avogadro.?s law|ideal gas|real gas|critical temperature|diffusion|effusion|graham|kinetic theory of gas|liquefact|evaporation of|vapour pressure|boiling point|freezing|melting|sublimation of|condensation of|intermolecular)\b/],
    ['Solutions & Electrochemistry', /\b(solution|solvent|solute|saturated|unsaturated|supersaturated|colloid|suspension|emulsion|aerosol|gel|sol|tyndall|brownian|dialysis|electrolysis|electrode|electroplat|galvanic|cell|battery|dry cell|lead storage|faraday.?s law of electrolys)\b/],
  ],

  // ═══════════════════════ TEST 15 — POLITY ═══════════════════════
  test_15: [
    ['Fundamental Rights, Duties & DPSP', /\b(fundamental rights?|fundamental duties|directive principles|dpsp|article 14|article 19|article 21|article 32|right to equality|right to freedom|right against exploitation|right to religion|cultural and educational rights?|right to constitutional remedies|writ|habeas corpus|mandamus|certiorari|prohibition|quo warranto|reasonable restriction)\b/],
    ['Judiciary', /\b(supreme court|high court|chief justice|judge|judicial review|pil|public interest litigation|writ jurisdiction|original jurisdiction|appellate|collegium|tribunal|lok adalat|legal aid|contempt|curative petition|review petition)\b/],
    ['Parliament', /\b(parliament|lok sabha|rajya sabha|speaker|question hour|zero hour|act of parliament|no-?confidence motion|censure motion|joint sitting|quorum|session of parliament|budget session|parliamentary committee|public accounts committee|estimates committee|private member|money bill|financial bill|adjournment)\b/],
    ['Union Executive', /\b(president|vice[- ]president|prime minister|council of ministers|cabinet|attorney general|comptroller|cag|governor|impeachment|ordinance|pardon|veto|election of president|electoral college|oath)\b/],
    ['State Government', /\b(state government|chief minister|governor of|state legislative assembly|state legislature|vidhan|state council of ministers|advocate general|state public service|secretariat of state)\b/],
    ['Local Government', /\b(panchayat|panchayati raj|municipalit|municipal corporation|zila parishad|block samiti|gram sabha|gram panchayat|73rd|74th|local government|urban local|ward committee|mayor|municipal commissioner)\b/],
    ['Elections & Representation', /\b(election|election commission|eci|voter|electoral roll|election symbol|nota|vvpn|evm|bye-?election|delimitation|universal adult franchise|representation of people|rp act|disqualification)\b/],
    ['Constitutional & Statutory Bodies', /\b(election commission|upsc|sp.|state public service commission|finance commission|national commission for human rights|nhrc|national commission for women|ncw|sc commission|st commission|backward classes commission|cag|attorney general|solicitor|advocate general|linguistic minorities?|official language commission)\b/],
    ['Amendments & Special Provisions', /\b(amendment|42nd|44th|52nd|61st|73rd|74th|86th|101st|106th|schedule|scheduled area|sixth schedule|fifth schedule|emergency provision|article 356|president.?s rule|national emergency|financial emergency|anti-?defection|10th schedule|jammu and kashmir|370|nrc|caa)\b/],
    ['Centre-State & Misc Provisions', /\b(centre|center-?state|federal|unitary|concurrent list|state list|union list|seventh schedule|residuary|inter-?state council|zonal council|trade and commerce in india|services? under|all india services|administrative tribunal|official language|hindu personal)\b/],
    ['Constitution & Preamble', /\b(preamble|constituent assembly|drafting committee|ambedkar|framers? of|basic structure|sources? of constitution|constituent assembly|drafting committee|ambedkar|basic structure|sources? of (the )?constitution|frames? of the constitution|sovereign|socialist|secular|republic|fraternity|citizenship|single citizenship)\b/],
  ],
};

// Current affairs tests share one table (they repeat across the year).
function CURRENT_AFFAIRS(){return [
  ['Sports', /\b(sport|cricket|olympic|paralympic|asian games|medal|tournament|championship|cup|fifa|hockey|kabaddi|wrestling|boxing|shooting|archery|badminton|tennis|chess|athlete|player|match|series|ranji|ipl|world cup|grand slam|grandmaster|khelo)\b/],
  ['Awards & Honours', /\b(award|prize|honour|honor|padma|bharat ratna|nobel|pulitzer|ramon magsaysay|dronacharya|arjuna award|khel ratna|jnanpith|sahitya akademi|man booker|oscar|grammy|emmy|citation|laureate|felicitat)\b/],
  ['Appointments & Persons in News', /\b(appoint|resign|sworn|took charge|chief justice|governor appointed|ambassador|chairman of|chairperson|ceo of|md and ceo|director general|comptroller|election commissioner|new chief|vice president of|president of|heads?)\b/],
  ['Obituaries', /\b(died|passes away|passed away|death of|obituary|veteran|demise|condolence)\b/],
  ['Summits, Conferences & Meetings', /\b(summit|conference|meet of|meeting of|g7|g20|brics|sco|asean|cop\d*|united nations general assembly|unga|wef|davos|bilateral talk|multilateral|hosted in|held in|concluded)\b/],
  ['Defence & Security', /\b(defence|defense|military|army|navy|air force|drdo|missile|tank|submarine|fighter jet|rafale|exercise|joint exercise|border|ceasefire|terror|insurgency|naxal|security forces?|crpf|bsf|itbp|coast guard|nsg)\b/],
  ['Space & Nuclear', /\b(isro|nasa|spacecraft|satellite|launch|chandrayaan|gaganyaan|aditya-?l1|pslv|gslv|spacex|orbit|cosmic|asteroid|planet|telescope|nuclear|reactor|uranium|thorium|bhavini)\b/],
  ['Science & Technology', /\b(scientist|research|study|discovery|developed|invented|technology|ai |artificial intelligence|machine learning|quantum|robot|vaccine|drug|clinical trial|genome|fossil|species discovered|innovat|patent|supercomputer)\b/],
  ['Economy, Banking & Finance', /\b(economy|gdp|inflation|repo|bank|rbi|sebi|stock market|ipo|rupee|dollar|export|import|trade|gst|tax|budget|fiscal|growth|investment|fdi|imf|world bank|credit rating|npa|merger of banks|insolvency)\b/],
  ['Reports, Indices & Data', /\b(report|index|indices|ranking|ranked|survey|census data|estimate|world economic outlook|global hunger|human development|hdi|ease of doing business|sustainable development|sdg index|released by|published by|data released)\b/],
  ['Schemes & Policies', /\b(scheme|yojana|mission|abhiyan|programme|policy|initiative|portal|launched by|inaugurat|flagged off|foundation stone|dedicated to the nation|pradhan mantri|mukhyamantri|cabinet approved|cleared by)\b/],
  ['Agreements & Appointments (Intl)', /\b(mou|agreement|pact|deal signed|treaty|cooperation|partnership|memorandum|bilateral|trilateral)\b/],
  ['Environment & Health', /\b(environment|climate|pollution|wildlife|species|forest|biodivers|wetland|ramsar|health|ministry of health|vaccination|disease|outbreak|epidemic|pandemic|who )\b/],
  ['States & Governance', /\b(state government|chief minister|governor|assembly|legislature|bill passed by state|state assembly|high court|police|district|city|village of|statehood|border dispute)\b/],
  ['Books, Days & Misc', /\b(book|launched book|written by|author|world .* day|international .* day|day is observed|observed on|theme of|festival|art|culture|heritage|unesco)\b/],
];}

// Indian geography tests share one table.
function INDIAN_GEOGRAPHY(){return [
  ['Environment & Wildlife', /\b(environment|wildlife|sanctuar|national park|tiger reserve|biosphere|endangered|iucn|red list|conservation|biodivers|ramsar|wetland|pollution|gir|kaziranga|sundarban|corbett)\b/],
  ['Rivers & Drainage', /\b(river|drainage|ganga|ganges|yamuna|brahmaputra|godavari|krishna|kaveri|kaveri delta|narmada|tapi|tapti|mahanadi|damodar|son|ghaggar|luni|indus|tributar|delta|estuary|waterfall|lake|backwater|lagoon|canal|barrage|dam|multipurpose project|river valley project|ganga plain drainage)\b/],
  ['Climate & Monsoon', /\b(climate|monsoon|rainfall|precipitation|cyclone|drought|flood|el ni[nñ]o|la ni[nñ]a|jet stream|western disturbance|loois|kalbaisakhi|mango shower|blossom shower|retreating monsoon|onset of|temperature distribution|isotherm|seasons? of india| IMD |meteorolog)\b/],
  ['Soils & Natural Vegetation', /\b(soil|alluvial soil|black soil|regur|red soil|laterite|arid soil|forest soil|saline soil|erosion|conservation of|forest|vegetation|types of forest|timber|bamboo|mangrove|grassland|national forest policy|forest cover)\b/],
  ['Agriculture', /\b(agricultur|crop|cropping season|kharif|rabi|zaid|paddy|wheat|rice|cotton|jute|sugarcane|tea|coffee|rubber|spices?|pulse|oilseed|green revolution|white revolution|operation flood|horticultur|sericultur|fisheries?|dairy|animal husbandry|livestock|poultry|msp|irrigation)\b/],
  ['Minerals & Energy', /\b(mineral|iron ore|bauxite|mica|copper|gold|silver|zinc|lead|manganese|limestone|coal|petroleum|natural gas|uranium|thorium|atomic energy|nuclear power|thermal power|hydel|hydropower|solar energy|wind energy|biogas|tidal energy|geothermal|power grid|refinery|mining belt|bellary|jharia|bailadila)\b/],
  ['Industry', /\b(industr|manufactur|cotton textile|jute mill|sugar industry|steel plant|iron and steel|cement|fertiliser|fertilizer|petrochemical|pharmaceutical|automobile|shipbuilding|aerospace|industrial region|industrial corridor|se?zs?|cluster|agro-?based|mineral-?based|cottage|handloom|weaving)\b/],
  ['Transport & Communication', /\b(transport|railway|railways?|rail route|roadways?|national highway|expressway|golden quadrilateral|border road|ports?|harbou?r|airport|airline|inland waterway|waterways?|shipping|communication|telephone|post|postal|media|broadcasting)\b/],
  ['Population, Census & Settlement', /\b(population|census|demograph|density of population|literacy|sex ratio|child sex ratio|migration|urbanis|urbaniz|metropolitan|megalopolis|million city|towns?|settlement|tribe|scheduled tribe|scheduled caste|linguistic|language family|religious composition|growth rate of population)\b/],
  ['States, Boundaries & Regions', /\b(state|states? of india|union territor|new district|capital of|boundary of|neighbouring|bordering|reorganisation|states reorganisation|zonal|regional division|peninsular|coastal|island|andaman|nicobar|lakshadweep)\b/],
  ['Physical Features & Landforms', /\b(himalaya|great himalaya|lesser himalaya|shivalik|siwalik|purvanchal|aravalli|vindhya|satpura|western ghats|eastern ghats|deccan|plateau|plain|northern plain|bhabar|terai|bangar|khadar|deltaic plain|desert|thar|cold desert|ladakh|glacier|pass|valley|duns?|duars?|physiographic|landform|rock|geolog|earthquake|volcano|soil)\b/],
  ['Drainage? dup? no', /$^/],
];}

const TOPIC_EMOJI = {
  // test 1
  'Census & Population':'📊','Forests & Wildlife':'🦌','Schemes & Policies':'📜','Agriculture & Irrigation':'🌾','Transport':'🚉','Minerals':'⛏️','Rivers, Lakes & Waterfalls':'🌊','Art, Culture & Language':'🎭','Books, Authors & Press':'📚','Polity & Elections':'🏛️','Economy & Industry':'🏭','Modern Bihar & Freedom Struggle':'🇮🇳','Medieval Bihar':'🕌','Ancient Bihar':'🏺','Physical Geography':'⛰️','Current Affairs (Bihar)':'📰','General':'🔹',
  // world geo
  'Environment & Conservation':'🌿','Oceans & Currents':'🌊','Rivers & Lakes':'💧','Climate':'🌦️','Minerals & Resources':'⛏️','Population & Settlement':'🏙️','Agriculture & Economy':'🚜','Physical Landforms':'⛰️','Continents & Regions':'🗺️',
  // current affairs
  'Sports':'🏏','Awards & Honours':'🏅','Appointments & Persons in News':'👤','Obituaries':'🕯️','Summits, Conferences & Meetings':'🤝','Defence & Security':'🛡️','Space & Nuclear':'🚀','Science & Technology':'🔬','Economy, Banking & Finance':'💰','Reports, Indices & Data':'📈','Agreements & Appointments (Intl)':'🤝','Environment & Health':'🩺','States & Governance':'🏘️','Books, Days & Misc':'📖',
  // indian geography
  'Environment & Wildlife':'🐅','Rivers & Drainage':'🏞️','Climate & Monsoon':'🌧️','Soils & Natural Vegetation':'🌳','Agriculture':'🌾','Minerals & Energy':'⚡','Industry':'🏭','Transport & Communication':'🚛','Population, Census & Settlement':'📊','States, Boundaries & Regions':'🇮🇳','Physical Features & Landforms':'🏔️',
  // economy
  'International Institutions & Trade Bodies':'🌐','Banking & Finance':'🏦','Budget & Taxation':'🧾','External Sector & Trade':'🚢','Money & Capital Markets':'💱','Agriculture & Rural Economy':'🌾','Industry & Infrastructure':'🏗️','Poverty & Employment':'👥','Growth & National Income':'📈',
  // ancient history
  'Art & Architecture':'🛕','Literature':'📜','Buddhism & Jainism':'☸️','Science & Math':'🔢','Indus Valley':'🏺','Vedic Age':'🐄','Mauryan Empire':'🦁','Invasions (Persian & Greek)':'🏹','Post-Mauryan Period':'🏛️','Gupta & Post-Gupta':'👑','South India':'🌴','Mahajanapadas & Magadh':'⚔️','Prehistoric & Stone Age':'🪨','Philosophy & Religion':'🪔',
  // medieval
  'Bhakti & Sufi Movements':'🕌','Art, Culture & Literature':'🎨','Marathas & Sikhs':'⚔️','Vijayanagar & Regional Kingdoms':'🏰','Delhi Sultanate':'👑','Mughal Empire':'🕌','Arrival of Turks & Early Sultanate':'🏇','Administration, Economy & Society':'⚖️',
  // biology + sci-tech
  'Space & Defence Technology':'🚀','IT, Electronics & New Tech':'💻','Nuclear & Energy Technology':'⚛️','Biotechnology':'🧬','Cell & Biomolecules':'🔬','Genetics & Heredity':'🧪','Human Physiology':'🫀','Plant Biology':'🌱','Diseases & Health':'🦠','Nutrition & Vitamins':'🥗','Ecology & Environment':'🌍','Evolution & Taxonomy':'🐒','Microbiology':'🧫',
  // modern history
  'Revolt of 1857':'⚔️','Socio-Religious Reform':'🕉️','Press, Education & Literature':'📰','Peasant, Tribal & Civil Rebellions':'🔥','European Companies & Conquest':'⛵','Economic Policies & Exploitation':'💸','Governors-General & Administration':'🎩','Early Political Associations':'🏛️','Personalities & Miscellaneous':'👤','Partition & Independence':'🇮🇳','Constitutional Reforms (1892–1935)':'📜','Gandhi & Mass Movements':'🕊️','Revolutionary Nationalism':'💣','Congress & National Movement Phases':'🚩','Peasant, Worker & Tribal Movements':'👥','Princely States & Integration':'🏰','Post-Independence India':'🇮🇳','Personalities & Books':'📖','Bihar & the National Movement':'🌟',
  // physics + chemistry
  'Optics':'👁️','Electricity & Magnetism':'⚡','Modern & Nuclear Physics':'⚛️','Sound & Waves':'🔊','Heat & Thermodynamics':'🌡️','Motion, Forces & Mechanics':'⚽','Units, Measurement & Instruments':'📏','Everyday Physics & Scientists':'👨‍🔬','Atomic Structure & Periodic Table':'🧪','Chemical Bonding & Reactions':'🔗','Metals, Non-Metals & Metallurgy':'🪙','Organic & Everyday Chemistry':'🧫','States of Matter & Gas Laws':'🫧','Solutions & Electrochemistry':'🔋',
  // polity
  'Constitution & Preamble':'📖','Fundamental Rights, Duties & DPSP':'⚖️','Union Executive':'🏛️','Parliament':'🏛️','Judiciary':'⚖️','State Government':'🏢','Local Government':'🏘️','Elections & Representation':'🗳️','Constitutional & Statutory Bodies':'🏛️','Amendments & Special Provisions':'📜','Centre-State & Misc Provisions':'🤝',
};

module.exports = { RULES, TOPIC_EMOJI };
