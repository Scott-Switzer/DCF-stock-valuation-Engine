// Public symbol metadata. Eligibility must be verified before valuation.
const TICKER_DATA = [
  {
    "s": "A",
    "n": "Agilent Technologies, Inc. Common Stock"
  },
  {
    "s": "AA",
    "n": "Alcoa Corporation Common Stock "
  },
  {
    "s": "AAC",
    "n": "Ares Acquisition Corporation III Class A Ordinary Shares"
  },
  {
    "s": "AACG",
    "n": "ATA Creativity Global - American Depositary Shares, each representing two common shares"
  },
  {
    "s": "AACI",
    "n": "Armada Acquisition Corp. III - Class A Ordinary Share"
  },
  {
    "s": "AACIU",
    "n": "Armada Acquisition Corp. III - Units"
  },
  {
    "s": "AACO",
    "n": "Abony Acquisition Corp. I - Class A Ordinary Share"
  },
  {
    "s": "AACOU",
    "n": "Abony Acquisition Corp. I - Units"
  },
  {
    "s": "AACOW",
    "n": "Abony Acquisition Corp. I - Warrants"
  },
  {
    "s": "AACP",
    "n": "Apogee Acquisition Corp - Class A Ordinary Shares"
  },
  {
    "s": "AACPU",
    "n": "Apogee Acquisition Corp - Units"
  },
  {
    "s": "AADX",
    "n": "Applied Aerospace & Defense, Inc. Common Stock"
  },
  {
    "s": "AAL",
    "n": "American Airlines Group, Inc. - Common Stock"
  },
  {
    "s": "AAME",
    "n": "Atlantic American Corporation - Common Stock"
  },
  {
    "s": "AAMI",
    "n": "Acadian Asset Management Inc. Common Stock"
  },
  {
    "s": "AAOI",
    "n": "Applied Optoelectronics, Inc. - Common Stock"
  },
  {
    "s": "AAON",
    "n": "AAON, Inc. - Common Stock"
  },
  {
    "s": "AAP",
    "n": "Advance Auto Parts Inc."
  },
  {
    "s": "AAPG",
    "n": "Ascentage Pharma Group International - American Depository Shares"
  },
  {
    "s": "AAPL",
    "n": "Apple Inc. - Common Stock"
  },
  {
    "s": "AARD",
    "n": "Aardvark Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "AAT",
    "n": "American Assets Trust, Inc. Common Stock"
  },
  {
    "s": "AAUC",
    "n": "Allied Gold Corporation Common Shares"
  },
  {
    "s": "AB",
    "n": "AllianceBernstein Holding L.P.  Units"
  },
  {
    "s": "ABAT",
    "n": "American Battery Technology Company - Common Stock"
  },
  {
    "s": "ABBV",
    "n": "AbbVie Inc. Common Stock"
  },
  {
    "s": "ABCB",
    "n": "Ameris Bancorp Common Stock"
  },
  {
    "s": "ABCL",
    "n": "AbCellera Biologics Inc. - Common Shares"
  },
  {
    "s": "ABEO",
    "n": "Abeona Therapeutics Inc. - Common Stock"
  },
  {
    "s": "ABEV",
    "n": "Ambev S.A. American Depositary Shares (Each representing 1 Common Share)"
  },
  {
    "s": "ABG",
    "n": "Asbury Automotive Group Inc Common Stock"
  },
  {
    "s": "ABLV",
    "n": "Able View Global Inc. - Class B Ordinary Shares"
  },
  {
    "s": "ABM",
    "n": "ABM Industries Incorporated Common Stock"
  },
  {
    "s": "ABNB",
    "n": "Airbnb, Inc. - Class A Common Stock"
  },
  {
    "s": "ABOS",
    "n": "Acumen Pharmaceuticals, Inc. - Common Stock"
  },
  {
    "s": "ABR",
    "n": "Arbor Realty Trust Common Stock"
  },
  {
    "s": "ABSI",
    "n": "Absci Corporation - Common Stock"
  },
  {
    "s": "ABT",
    "n": "Abbott Laboratories Common Stock"
  },
  {
    "s": "ABTC",
    "n": "American Bitcoin Corp. - Class A Common Stock"
  },
  {
    "s": "ABTS",
    "n": "Abits Group Inc - Ordinary Shares"
  },
  {
    "s": "ABUS",
    "n": "Arbutus Biopharma Corporation - Common Stock"
  },
  {
    "s": "ABVC",
    "n": "ABVC BioPharma, Inc. - Common Stock"
  },
  {
    "s": "ABVX",
    "n": "Abivax SA - American Depositary Shares"
  },
  {
    "s": "ABX",
    "n": "Abacus Global Management, Inc. Class A Common Stock"
  },
  {
    "s": "ABXL",
    "n": "Abacus Global Management, Inc. 9.875% Fixed Rate Senior Notes due 2028"
  },
  {
    "s": "ACA",
    "n": "Arcosa, Inc. Common Stock "
  },
  {
    "s": "ACAA",
    "n": "Averin Capital Acquisition Corp. - Class A Ordinary Shares"
  },
  {
    "s": "ACAAU",
    "n": "Averin Capital Acquisition Corp. - Units"
  },
  {
    "s": "ACAAW",
    "n": "Averin Capital Acquisition Corp. - Warrants"
  },
  {
    "s": "ACAD",
    "n": "ACADIA Pharmaceuticals Inc. - Common Stock"
  },
  {
    "s": "ACB",
    "n": "Aurora Cannabis Inc. - Common Shares"
  },
  {
    "s": "ACCL",
    "n": "Acco Group Holdings Limited - Class A Ordinary Shares"
  },
  {
    "s": "ACCO",
    "n": "Acco Brands Corporation Common Stock"
  },
  {
    "s": "ACCS",
    "n": "ACCESS Newswire Inc. Common Stock"
  },
  {
    "s": "ACCV",
    "n": "Accelevation Holdings Corp. - Class A ordinary shares"
  },
  {
    "s": "ACDC",
    "n": "ProFrac Holding Corp. - Class A Common Stock"
  },
  {
    "s": "ACEL",
    "n": "Accel Entertainment, Inc. "
  },
  {
    "s": "ACET",
    "n": "Adicet Bio, Inc. - Common Stock"
  },
  {
    "s": "ACFN",
    "n": "Acorn Energy, Inc. - Common Stock"
  },
  {
    "s": "ACGC",
    "n": "ACP Holdings Acquisition Corp. - Class A Ordinary Shares"
  },
  {
    "s": "ACGCU",
    "n": "ACP Holdings Acquisition Corp. - Units"
  },
  {
    "s": "ACGCW",
    "n": "ACP Holdings Acquisition Corp. - Warrants"
  },
  {
    "s": "ACGL",
    "n": "Arch Capital Group Ltd. - Common Stock"
  },
  {
    "s": "ACH",
    "n": "Accendra Health, Inc. Common Stock"
  },
  {
    "s": "ACHC",
    "n": "Acadia Healthcare Company, Inc. - Common Stock"
  },
  {
    "s": "ACHR",
    "n": "Archer Aviation Inc. Class A Common Stock"
  },
  {
    "s": "ACHV",
    "n": "Achieve Life Sciences, Inc.  - Common Shares"
  },
  {
    "s": "ACI",
    "n": "Albertsons Companies, Inc. Class A Common Stock"
  },
  {
    "s": "ACIC",
    "n": "American Coastal Insurance Corporation - Common Stock"
  },
  {
    "s": "ACIU",
    "n": "AC Immune SA - Common Stock"
  },
  {
    "s": "ACIW",
    "n": "ACI Worldwide, Inc. - Common Stock"
  },
  {
    "s": "ACLS",
    "n": "Axcelis Technologies, Inc. - Common Stock"
  },
  {
    "s": "ACM",
    "n": "AECOM Common Stock"
  },
  {
    "s": "ACMR",
    "n": "ACM Research, Inc. - Class A Common Stock"
  },
  {
    "s": "ACN",
    "n": "Accenture plc Class A Ordinary Shares (Ireland)"
  },
  {
    "s": "ACNB",
    "n": "ACNB Corporation - Common Stock"
  },
  {
    "s": "ACNT",
    "n": "Ascent Industries Co. - Common Stock"
  },
  {
    "s": "ACOG",
    "n": "Alpha Cognition Inc. - Common Stock"
  },
  {
    "s": "ACON",
    "n": "Aclarion, Inc. - Common Stock"
  },
  {
    "s": "ACR",
    "n": "ACRES Commercial Realty Corp. Common Stock"
  },
  {
    "s": "ACRE",
    "n": "Ares Commercial Real Estate Corporation Common Stock"
  },
  {
    "s": "ACRS",
    "n": "Aclaris Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "ACRV",
    "n": "Acrivon Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "ACT",
    "n": "Enact Holdings, Inc. - Common Stock"
  },
  {
    "s": "ACTG",
    "n": "Acacia Research Corporation - Common Stock"
  },
  {
    "s": "ACTU",
    "n": "Actuate Therapeutics, Inc. - Common stock"
  },
  {
    "s": "ACU",
    "n": "Acme United Corporation. Common Stock"
  },
  {
    "s": "ACVA",
    "n": "ACV Auctions Inc. Class A Common Stock"
  },
  {
    "s": "ACXP",
    "n": "Acurx Pharmaceuticals, Inc. - Common Stock"
  },
  {
    "s": "AD",
    "n": "Array Digital Infrastructure, Inc. Common Shares"
  },
  {
    "s": "ADAC",
    "n": "American Drive Acquisition Company - Class A Ordinary Shares"
  },
  {
    "s": "ADACU",
    "n": "American Drive Acquisition Company - Units"
  },
  {
    "s": "ADAG",
    "n": "Adagene Inc. - ADS, each representing 1.25 ordinary shares"
  },
  {
    "s": "ADAM",
    "n": "Adamas Trust, Inc. - Common Stock"
  },
  {
    "s": "ADAMG",
    "n": "Adamas Trust, Inc. - 9.125% Senior Notes Due 2030"
  },
  {
    "s": "ADAMH",
    "n": "Adamas Trust, Inc. - 9.875% Senior Notes Due 2030"
  },
  {
    "s": "ADAMI",
    "n": "Adamas Trust, Inc. - 9.125% Senior Notes Due 2029"
  },
  {
    "s": "ADAMK",
    "n": "Adamas Trust, Inc. - 9.600% Senior Notes Due 2031"
  },
  {
    "s": "ADAMO",
    "n": "Adamas Trust, Inc. - 9.250% Senior Notes Due 2031"
  },
  {
    "s": "ADBE",
    "n": "Adobe Inc. - Common Stock"
  },
  {
    "s": "ADBT",
    "n": "Advasa Holdings, Inc. - Common stock"
  },
  {
    "s": "ADC",
    "n": "Agree Realty Corporation Common Stock"
  },
  {
    "s": "ADCT",
    "n": "ADC Therapeutics SA Common Shares"
  },
  {
    "s": "ADEA",
    "n": "Adeia Inc.  - Common Stock"
  },
  {
    "s": "ADGM",
    "n": "Adagio Medical Holdings, Inc - Common Stock"
  },
  {
    "s": "ADI",
    "n": "Analog Devices, Inc. - Common Stock"
  },
  {
    "s": "ADIG",
    "n": "ADI Global Distribution Inc. Common Stock"
  },
  {
    "s": "ADIL",
    "n": "Adial Pharmaceuticals, Inc - Common Stock"
  },
  {
    "s": "ADM",
    "n": "Archer-Daniels-Midland Company Common Stock"
  },
  {
    "s": "ADMA",
    "n": "ADMA Biologics Inc - Common Stock"
  },
  {
    "s": "ADNT",
    "n": "Adient plc Ordinary Shares "
  },
  {
    "s": "ADP",
    "n": "Automatic Data Processing, Inc. - Common Stock"
  },
  {
    "s": "ADPT",
    "n": "Adaptive Biotechnologies Corporation - Common Stock"
  },
  {
    "s": "ADRX",
    "n": "ADARx Pharmaceuticals, Inc. - Common stock"
  },
  {
    "s": "ADSE",
    "n": "ADS-TEC ENERGY PLC - Ordinary Shares"
  },
  {
    "s": "ADSK",
    "n": "Autodesk, Inc. - Common Stock"
  },
  {
    "s": "ADT",
    "n": "ADT Inc. Common Stock"
  },
  {
    "s": "ADTN",
    "n": "ADTRAN Holdings, Inc. - Common Stock"
  },
  {
    "s": "ADUR",
    "n": "Aduro Clean Technologies Inc. - Common Stock"
  },
  {
    "s": "ADUS",
    "n": "Addus HomeCare Corporation - Common Stock"
  },
  {
    "s": "ADV",
    "n": "Advantage Solutions Inc.  - Class A Common Stock"
  },
  {
    "s": "ADVB",
    "n": "Advanced Biomed Inc. - Common Stock"
  },
  {
    "s": "ADXN",
    "n": "Addex Therapeutics Ltd - American Depositary Shares"
  },
  {
    "s": "AEAQ",
    "n": "Activate Energy Acquisition Corp. - Class A Ordinary Share"
  },
  {
    "s": "AEAQU",
    "n": "Activate Energy Acquisition Corp. - Unit"
  },
  {
    "s": "AEBI",
    "n": "Aebi Schmidt Holding AG - Common Stock"
  },
  {
    "s": "AEC",
    "n": "Anfield Energy Inc. - Common Shares"
  },
  {
    "s": "AEE",
    "n": "Ameren Corporation Common Stock"
  },
  {
    "s": "AEFC",
    "n": "Aegon Funding Company LLC 5.10% Subordinated Notes due 2049"
  },
  {
    "s": "AEG",
    "n": "Aegon Ltd. New York Registry Shares"
  },
  {
    "s": "AEHL",
    "n": "Antelope Enterprise Holdings Limited - Class A Ordinary Shares"
  },
  {
    "s": "AEHR",
    "n": "Aehr Test Systems - Common Stock"
  },
  {
    "s": "AEI",
    "n": "Alset Inc. - Common Stock"
  },
  {
    "s": "AEIS",
    "n": "Advanced Energy Industries, Inc. - Common Stock"
  },
  {
    "s": "AEM",
    "n": "Agnico Eagle Mines Limited Common Stock"
  },
  {
    "s": "AEMD",
    "n": "Aethlon Medical, Inc. - Common Stock"
  },
  {
    "s": "AENT",
    "n": "Alliance Entertainment Holding Corporation - common stock"
  },
  {
    "s": "AENTW",
    "n": "Alliance Entertainment Holding Corporation - Warrants"
  },
  {
    "s": "AEO",
    "n": "American Eagle Outfitters, Inc. Common Stock"
  },
  {
    "s": "AEON",
    "n": "AEON Biopharma, Inc. Class A Common Stock"
  },
  {
    "s": "AEP",
    "n": "American Electric Power Company, Inc. - Common Stock"
  },
  {
    "s": "AER",
    "n": "AerCap Holdings N.V. Ordinary Shares"
  },
  {
    "s": "AERO",
    "n": "Grupo Aeromexico, S.A.B. de C.V. American Depositary Shares (each representing ten (10) Common Shares)"
  },
  {
    "s": "AERT",
    "n": "Aeries Technology, Inc. - Class A Ordinary Share"
  },
  {
    "s": "AES",
    "n": "The AES Corporation Common Stock"
  },
  {
    "s": "AESI",
    "n": "Atlas Energy Solutions Inc. Common Stock"
  },
  {
    "s": "AESP",
    "n": "Aeon Acquisition I Corp. - Class A Ordinary Shares"
  },
  {
    "s": "AESPU",
    "n": "Aeon Acquisition I Corp. - Units"
  },
  {
    "s": "AESPW",
    "n": "Aeon Acquisition I Corp. - Warrants"
  },
  {
    "s": "AEVA",
    "n": "Aeva Technologies, Inc. - Common Stock"
  },
  {
    "s": "AEXA",
    "n": "American Exceptionalism Acquisition Corp. A Class A Ordinary Shares"
  },
  {
    "s": "AEYE",
    "n": "AudioEye, Inc. - Common Stock"
  },
  {
    "s": "AFCG",
    "n": "Advanced Flower Capital Inc. - Common Stock"
  },
  {
    "s": "AFG",
    "n": "American Financial Group, Inc. Common Stock"
  },
  {
    "s": "AFGB",
    "n": "American Financial Group, Inc. 5.875% Subordinated Debentures due 2059"
  },
  {
    "s": "AFGC",
    "n": "American Financial Group, Inc. 5.125% Subordinated Debentures due 2059"
  },
  {
    "s": "AFGD",
    "n": "American Financial Group, Inc. 5.625% Subordinated Debentures due 2060"
  },
  {
    "s": "AFGE",
    "n": "American Financial Group, Inc. 4.500% Subordinated Debentures due 2060"
  },
  {
    "s": "AFJK",
    "n": "Aimei Health Technology Co., Ltd - Ordinary Share"
  },
  {
    "s": "AFJKR",
    "n": "Aimei Health Technology Co., Ltd - Right"
  },
  {
    "s": "AFJKU",
    "n": "Aimei Health Technology Co., Ltd - Unit"
  },
  {
    "s": "AFL",
    "n": "AFLAC Incorporated Common Stock"
  },
  {
    "s": "AFRI",
    "n": "Forafric Global PLC - Ordinary Shares"
  },
  {
    "s": "AFRIW",
    "n": "Forafric Global PLC - Warrants"
  },
  {
    "s": "AFRM",
    "n": "Affirm Holdings, Inc. - Class A Common Stock"
  },
  {
    "s": "AFYA",
    "n": "Afya Limited - Class A Common Shares"
  },
  {
    "s": "AG",
    "n": "First Majestic Silver Corp. Ordinary Shares (Canada)"
  },
  {
    "s": "AGBK",
    "n": "AGI Inc Class A Common Shares"
  },
  {
    "s": "AGCC",
    "n": "Agencia Comercial Spirits Ltd - Class A Ordinary Share"
  },
  {
    "s": "AGCO",
    "n": "AGCO Corporation Common Stock"
  },
  {
    "s": "AGEN",
    "n": "Agenus Inc. - Common Stock"
  },
  {
    "s": "AGI",
    "n": "Alamos Gold Inc. Class A Common Shares"
  },
  {
    "s": "AGIG",
    "n": "Abundia Global Impact Group Inc. Common stock"
  },
  {
    "s": "AGIO",
    "n": "Agios Pharmaceuticals, Inc. - Common Stock"
  },
  {
    "s": "AGL",
    "n": "agilon health, inc. Common Stock"
  },
  {
    "s": "AGM",
    "n": "Federal Agricultural Mortgage Corporation Common Stock"
  },
  {
    "s": "AGM-A",
    "n": "Federal Agricultural Mortgage Corporation Common Stock"
  },
  {
    "s": "AGMB",
    "n": "AgomAb Therapeutics NV - ADRs representing one common share."
  },
  {
    "s": "AGMH",
    "n": "AGM Group Holdings Inc. - Class A Ordinary Shares"
  },
  {
    "s": "AGNC",
    "n": "AGNC Investment Corp. - Common Stock"
  },
  {
    "s": "AGNT",
    "n": "AGNT, Inc. - Common Stock"
  },
  {
    "s": "AGO",
    "n": "Assured Guaranty Ltd. Common Stock"
  },
  {
    "s": "AGPU",
    "n": "Axe Compute Inc. - Common Stock"
  },
  {
    "s": "AGRO",
    "n": "Adecoagro S.A. Common Shares"
  },
  {
    "s": "AGRZ",
    "n": "Agroz Inc. - Class A Ordinary Shares"
  },
  {
    "s": "AGX",
    "n": "Argan, Inc. Common Stock"
  },
  {
    "s": "AGYS",
    "n": "Agilysys, Inc. - Common Stock"
  },
  {
    "s": "AHCO",
    "n": "AdaptHealth Corp.  - Common Stock"
  },
  {
    "s": "AHG",
    "n": "Akso Health Group - American Depositary Shares"
  },
  {
    "s": "AHMA",
    "n": "Ambitions Enterprise Management Co. L.L.C - Class A Ordinary Shares"
  },
  {
    "s": "AHRT",
    "n": "AH Realty Trust, Inc. Common Stock"
  },
  {
    "s": "AHT",
    "n": "Ashford Hospitality Trust Inc Common Stock"
  },
  {
    "s": "AI",
    "n": "C3.ai, Inc. Class A Common Stock"
  },
  {
    "s": "AIAI",
    "n": "AIAI Holdings Corporation - Class A common stock"
  },
  {
    "s": "AIB",
    "n": "AIB Data Centers Inc. Common Stock"
  },
  {
    "s": "AIBZ",
    "n": "Bitzero Holdings Inc. - Common Shares"
  },
  {
    "s": "AIDX",
    "n": "20/20 Biolabs, Inc. - Common Stock"
  },
  {
    "s": "AIFA",
    "n": "All In FutureTech Alliance, Inc. - Common Stock"
  },
  {
    "s": "AIFC",
    "n": "AI Financial Corporation - Common Stock"
  },
  {
    "s": "AIFF",
    "n": "Firefly Neuroscience, Inc.  - Common Stock"
  },
  {
    "s": "AIFU",
    "n": "AIFU Inc. - Class A Ordinary Share"
  },
  {
    "s": "AIG",
    "n": "American International Group, Inc. New Common Stock"
  },
  {
    "s": "AII",
    "n": "American Integrity Insurance Group, Inc. Common Stock"
  },
  {
    "s": "AIIA",
    "n": "AI Infrastructure Acquisition Corp. Class A Ordinary Shares"
  },
  {
    "s": "AIIA-U",
    "n": "AI Infrastructure Acquisition Corp. Units, each consisting of one Class A Ordinary Share and one Right"
  },
  {
    "s": "AIIO",
    "n": "Robo.ai Inc. - Class B Ordinary Shares"
  },
  {
    "s": "AIIR",
    "n": "Air Global PLC - Ordinary shares"
  },
  {
    "s": "AIM",
    "n": "AIM ImmunoTech Inc. Common Stock"
  },
  {
    "s": "AIMD",
    "n": "Ainos, Inc. - Common Stock"
  },
  {
    "s": "AIMDW",
    "n": "Ainos, Inc. - warrants"
  },
  {
    "s": "AIN",
    "n": "Albany International Corporation Common Stock"
  },
  {
    "s": "AIOK",
    "n": "AI OKTO CORP. - Common Stock"
  },
  {
    "s": "AIOS",
    "n": "AIOS Tech Inc. - Class A Common Shares"
  },
  {
    "s": "AIOT",
    "n": "PowerFleet, Inc. - Common Stock"
  },
  {
    "s": "AIP",
    "n": "Arteris, Inc.  - Common Stock"
  },
  {
    "s": "AIR",
    "n": "AAR Corp. Common Stock"
  },
  {
    "s": "AIRE",
    "n": "reAlpha Tech Corp. - Common Stock"
  },
  {
    "s": "AIRG",
    "n": "Airgain, Inc. - Common Stock"
  },
  {
    "s": "AIRI",
    "n": "Air Industries Group Common Stock"
  },
  {
    "s": "AIRJ",
    "n": "AirJoule Technologies Corporation - Class A Common Stock"
  },
  {
    "s": "AIRO",
    "n": "AIRO Group Holdings, Inc. - Common Stock"
  },
  {
    "s": "AIRS",
    "n": "AirSculpt Technologies, Inc. - Common Stock"
  },
  {
    "s": "AIRT",
    "n": "Air T, Inc. - Common Stock"
  },
  {
    "s": "AISP",
    "n": "Airship AI Holdings, Inc - Class A Common Stock"
  },
  {
    "s": "AISPW",
    "n": "Airship AI Holdings, Inc - Warrants"
  },
  {
    "s": "AIT",
    "n": "Applied Industrial Technologies, Inc. Common Stock"
  },
  {
    "s": "AIV",
    "n": "Apartment Investment and Management Company Common Stock"
  },
  {
    "s": "AIXI",
    "n": "XIAO-I Corporation - American Depositary Shares"
  },
  {
    "s": "AIZ",
    "n": "Assurant, Inc. Common Stock"
  },
  {
    "s": "AIZN",
    "n": "Assurant, Inc. 5.25% Subordinated Notes due 2061"
  },
  {
    "s": "AJG",
    "n": "Arthur J. Gallagher & Co. Common Stock"
  },
  {
    "s": "AKA",
    "n": "a.k.a. Brands Holding Corp. Common Stock"
  },
  {
    "s": "AKAM",
    "n": "Akamai Technologies, Inc. - Common Stock"
  },
  {
    "s": "AKAN",
    "n": "Akanda Corp. - Common Shares"
  },
  {
    "s": "AKBA",
    "n": "Akebia Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "AKO-A",
    "n": "Embotelladora Andina S.A. Common Stock"
  },
  {
    "s": "AKO-B",
    "n": "Embotelladora Andina S.A. Common Stock"
  },
  {
    "s": "AKR",
    "n": "Acadia Realty Trust Common Stock"
  },
  {
    "s": "AKTS",
    "n": "Aktis Oncology, Inc. - Common stock"
  },
  {
    "s": "AKTX",
    "n": "Akari Therapeutics Plc - American Depositary Shares"
  },
  {
    "s": "ALAB",
    "n": "Astera Labs, Inc. - Common Stock"
  },
  {
    "s": "ALAR",
    "n": "Alarum Technologies Ltd. - American Depositary Shares"
  },
  {
    "s": "ALB",
    "n": "Albemarle Corporation Common Stock"
  },
  {
    "s": "ALC",
    "n": "Alcon Inc. Ordinary Shares"
  },
  {
    "s": "ALCO",
    "n": "Alico, Inc. - Common Stock"
  },
  {
    "s": "ALDF",
    "n": "Aldel Financial II Inc. - Class A Ordinary Shares"
  },
  {
    "s": "ALDFU",
    "n": "Aldel Financial II Inc. - Units"
  },
  {
    "s": "ALDFW",
    "n": "Aldel Financial II Inc. - Warrants"
  },
  {
    "s": "ALDX",
    "n": "Aldeyra Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "ALEC",
    "n": "Alector, Inc. - Common Stock"
  },
  {
    "s": "ALF",
    "n": "Centurion Acquisition Corp. - Class A Ordinary Shares"
  },
  {
    "s": "ALFUU",
    "n": "Centurion Acquisition Corp. - Unit"
  },
  {
    "s": "ALG",
    "n": "Alamo Group, Inc. Common Stock"
  },
  {
    "s": "ALGM",
    "n": "Allegro MicroSystems, Inc. - Common Stock"
  },
  {
    "s": "ALGN",
    "n": "Align Technology, Inc. - Common Stock"
  },
  {
    "s": "ALGS",
    "n": "Aligos Therapeutics, Inc. - Common stock"
  },
  {
    "s": "ALGT",
    "n": "Allegiant Travel Company - Common Stock"
  },
  {
    "s": "ALH",
    "n": "Alliance Laundry Holdings Inc. Common Stock"
  },
  {
    "s": "ALHC",
    "n": "Alignment Healthcare, Inc. - Common Stock"
  },
  {
    "s": "ALIS",
    "n": "Calisa Acquisition Corp - Ordinary shares"
  },
  {
    "s": "ALISR",
    "n": "Calisa Acquisition Corp - Right"
  },
  {
    "s": "ALISU",
    "n": "Calisa Acquisition Corp - Units"
  },
  {
    "s": "ALIT",
    "n": "Alight, Inc. Class A Common Stock"
  },
  {
    "s": "ALK",
    "n": "Alaska Air Group, Inc. Common Stock"
  },
  {
    "s": "ALKS",
    "n": "Alkermes plc - Ordinary Shares"
  },
  {
    "s": "ALKT",
    "n": "Alkami Technology, Inc. - Common Stock"
  },
  {
    "s": "ALL",
    "n": "Allstate Corporation (The) Common Stock"
  },
  {
    "s": "ALLE",
    "n": "Allegion plc Ordinary Shares"
  },
  {
    "s": "ALLO",
    "n": "Allogene Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "ALLR",
    "n": "Allarity Therapeutics, Inc. - Common stock"
  },
  {
    "s": "ALLT",
    "n": "Allot Ltd. - Ordinary Shares"
  },
  {
    "s": "ALLY",
    "n": "Ally Financial Inc. Common Stock"
  },
  {
    "s": "ALM",
    "n": "Almonty Industries Inc. - Common Shares"
  },
  {
    "s": "ALMR",
    "n": "Alamar Biosciences, Inc. - Class A common stock"
  },
  {
    "s": "ALMS",
    "n": "Alumis Inc. - Common Stock"
  },
  {
    "s": "ALMU",
    "n": "Aeluma, Inc. - Common Stock"
  },
  {
    "s": "ALNT",
    "n": "Allient Inc. - Common Stock"
  },
  {
    "s": "ALNY",
    "n": "Alnylam Pharmaceuticals, Inc. - Common Stock"
  },
  {
    "s": "ALOV",
    "n": "Aldabra 4 Liquidity Opportunity Vehicle, Inc. - Class A Ordinary Shares"
  },
  {
    "s": "ALOVU",
    "n": "Aldabra 4 Liquidity Opportunity Vehicle, Inc. - Units"
  },
  {
    "s": "ALOVW",
    "n": "Aldabra 4 Liquidity Opportunity Vehicle, Inc. - Warrants"
  },
  {
    "s": "ALOY",
    "n": "REalloys Inc. - Common Stock"
  },
  {
    "s": "ALP",
    "n": "Alpha Compute Corp  - Ordinary Shares"
  },
  {
    "s": "ALPS",
    "n": "ALPS Group Inc - Ordinary Share"
  },
  {
    "s": "ALPX",
    "n": "Alpex Acquisition Corporation - Class A Ordinary Shares"
  },
  {
    "s": "ALPXU",
    "n": "Alpex Acquisition Corporation - Units"
  },
  {
    "s": "ALPXW",
    "n": "Alpex Acquisition Corporation - Warrants"
  },
  {
    "s": "ALRM",
    "n": "Alarm.com Holdings, Inc. - Common Stock"
  },
  {
    "s": "ALRS",
    "n": "Alerus Financial Corporation - Common Stock"
  },
  {
    "s": "ALSN",
    "n": "Allison Transmission Holdings, Inc. Common Stock"
  },
  {
    "s": "ALT",
    "n": "Altimmune, Inc. - Common Stock"
  },
  {
    "s": "ALTG",
    "n": "Alta Equipment Group Inc. Class A Common Stock"
  },
  {
    "s": "ALTI",
    "n": "AlTi Global, Inc. - Class A Common Stock"
  },
  {
    "s": "ALTO",
    "n": "Alto Ingredients, Inc. - Common Stock"
  },
  {
    "s": "ALUB",
    "n": "Alussa Energy Acquisition Corp. II Class A Ordinary Shares"
  },
  {
    "s": "ALV",
    "n": "Autoliv, Inc. Common Stock"
  },
  {
    "s": "ALVO",
    "n": "Alvotech - Ordinary Shares"
  },
  {
    "s": "ALX",
    "n": "Alexander's, Inc. Common Stock"
  },
  {
    "s": "ALXO",
    "n": "ALX Oncology Holdings Inc. - Common Stock"
  },
  {
    "s": "ALZN",
    "n": "Alzamend Neuro, Inc. - Common Stock"
  },
  {
    "s": "AM",
    "n": "Antero Midstream Corporation Common Stock"
  },
  {
    "s": "AMAC",
    "n": "AMR Resources Acquisition Corp - Class A Ordinary Shares"
  },
  {
    "s": "AMACU",
    "n": "AMR Resources Acquisition Corp - Units"
  },
  {
    "s": "AMACW",
    "n": "AMR Resources Acquisition Corp - Warrants"
  },
  {
    "s": "AMAL",
    "n": "Amalgamated Financial Corp. - Common Stock"
  },
  {
    "s": "AMAN",
    "n": "Amanat Acquisition Corp - Class A Ordinary Shares"
  },
  {
    "s": "AMAT",
    "n": "Applied Materials, Inc. - Common Stock"
  },
  {
    "s": "AMBA",
    "n": "Ambarella, Inc. - Ordinary Shares"
  },
  {
    "s": "AMBO",
    "n": "Ambow Education Holding Ltd. American Depository Shares (each representing twenty (20) Class A Ordinary Shares)"
  },
  {
    "s": "AMBP",
    "n": "Ardagh Metal Packaging S.A. Ordinary Shares"
  },
  {
    "s": "AMBQ",
    "n": "Ambiq Micro, Inc. Common Stock"
  },
  {
    "s": "AMBR",
    "n": "Amber International Holding Limited - American Depositary Shares"
  },
  {
    "s": "AMC",
    "n": "AMC Entertainment Holdings, Inc. Class A Common Stock"
  },
  {
    "s": "AMCI",
    "n": "AMC Robotics Corporation - Common Stock"
  },
  {
    "s": "AMCR",
    "n": "Amcor plc Ordinary Shares"
  },
  {
    "s": "AMCX",
    "n": "AMC Global Media Inc. - Class A Common Stock"
  },
  {
    "s": "AMD",
    "n": "Advanced Micro Devices, Inc. - Common Stock"
  },
  {
    "s": "AME",
    "n": "AMETEK, Inc."
  },
  {
    "s": "AMG",
    "n": "Affiliated Managers Group, Inc. Common Stock"
  },
  {
    "s": "AMGN",
    "n": "Amgen Inc. - Common Stock"
  },
  {
    "s": "AMH",
    "n": "American Homes 4 Rent Common Shares of Beneficial Interest"
  },
  {
    "s": "AMIX",
    "n": "Autonomix Medical, Inc. - Common Stock"
  },
  {
    "s": "AMKR",
    "n": "Amkor Technology, Inc. - Common Stock"
  },
  {
    "s": "AMLX",
    "n": "Amylyx Pharmaceuticals, Inc. - Common Stock"
  },
  {
    "s": "AMN",
    "n": "AMN Healthcare Services Inc"
  },
  {
    "s": "AMOD",
    "n": "Alpha Modus Holdings, Inc. - Class A Common Stock"
  },
  {
    "s": "AMP",
    "n": "Ameriprise Financial, Inc. Common Stock"
  },
  {
    "s": "AMPG",
    "n": "Amplitech Group, Inc. - Common Stock"
  },
  {
    "s": "AMPGZ",
    "n": "Amplitech Group, Inc. - Series B Right"
  },
  {
    "s": "AMPH",
    "n": "Amphastar Pharmaceuticals, Inc. - Common Stock"
  },
  {
    "s": "AMPL",
    "n": "Amplitude, Inc. - Class A Common Stock"
  },
  {
    "s": "AMPX",
    "n": "Amprius Technologies, Inc. Common Stock"
  },
  {
    "s": "AMPX-W",
    "n": "Amprius Technologies, Inc. Warrants to purchase one share of Common Stock at an exercise price of $11.50 per share"
  },
  {
    "s": "AMPY",
    "n": "Amplify Energy Corp. Common Stock"
  },
  {
    "s": "AMR",
    "n": "Alpha Metallurgical Resources, Inc. Common Stock"
  },
  {
    "s": "AMRC",
    "n": "Ameresco, Inc. Class A Common Stock"
  },
  {
    "s": "AMRN",
    "n": "Amarin Corporation plc - American Depositary Shares"
  },
  {
    "s": "AMRX",
    "n": "Amneal Pharmaceuticals, Inc. - Class A Common Stock"
  },
  {
    "s": "AMRZ",
    "n": "Amrize Ltd Ordinary Shares"
  },
  {
    "s": "AMS",
    "n": "American Shared Hospital Services Common Stock"
  },
  {
    "s": "AMSC",
    "n": "American Superconductor Corporation - Common Stock"
  },
  {
    "s": "AMSF",
    "n": "AMERISAFE, Inc. - Common Stock"
  },
  {
    "s": "AMSS",
    "n": "AMASS Brands Inc. - Common Stock"
  },
  {
    "s": "AMST",
    "n": "Amesite Inc. - Common Stock"
  },
  {
    "s": "AMTB",
    "n": "Amerant Bancorp Inc. Class A Common Stock"
  },
  {
    "s": "AMTD",
    "n": "AMTD IDEA Group American Depositary Shares, each representing six (6) Class A Ordinary Shares"
  },
  {
    "s": "AMTM",
    "n": "Amentum Holdings, Inc. Common Stock"
  },
  {
    "s": "AMTX",
    "n": "Aemetis, Inc - Common Stock"
  },
  {
    "s": "AMWL",
    "n": "American Well Corporation Class A Common Stock"
  },
  {
    "s": "AMX",
    "n": "America Movil, S.A.B. de C.V. American Depositary Shares (each representing the right to receive twenty (20) Series B Shares"
  },
  {
    "s": "AMZN",
    "n": "Amazon.com, Inc. - Common Stock"
  },
  {
    "s": "AN",
    "n": "AutoNation, Inc. Common Stock"
  },
  {
    "s": "ANAB",
    "n": "AnaptysBio, Inc. - Common Stock"
  },
  {
    "s": "ANDE",
    "n": "The Andersons, Inc. - Common Stock"
  },
  {
    "s": "ANDG",
    "n": "Andersen Group Inc. Class A Common Stock"
  },
  {
    "s": "ANET",
    "n": "Arista Networks, Inc. Common Stock"
  },
  {
    "s": "ANF",
    "n": "Abercrombie & Fitch Company Common Stock"
  },
  {
    "s": "ANGH",
    "n": "Anghami Inc. - Ordinary Shares"
  },
  {
    "s": "ANGHW",
    "n": "Anghami Inc. - Warrants"
  },
  {
    "s": "ANGI",
    "n": "Angi Inc. - Class A Common Stock"
  },
  {
    "s": "ANGO",
    "n": "AngioDynamics, Inc. - Common Stock"
  },
  {
    "s": "ANGX",
    "n": "Angel Studios, Inc. Class A Common Stock"
  },
  {
    "s": "ANIK",
    "n": "Anika Therapeutics Inc. - Common Stock"
  },
  {
    "s": "ANIP",
    "n": "ANI Pharmaceuticals, Inc. - Common Stock"
  },
  {
    "s": "ANIX",
    "n": "Anixa Biosciences, Inc. - Common Stock"
  },
  {
    "s": "ANL",
    "n": "Adlai Nortye Group Ltd. - American Depositary Shares"
  },
  {
    "s": "ANNA",
    "n": "AleAnna, Inc. - Class A Common Stock"
  },
  {
    "s": "ANNX",
    "n": "Annexon, Inc. - common stock"
  },
  {
    "s": "ANPA",
    "n": "Rich Sparkle Holdings Limited - Ordinary Shares"
  },
  {
    "s": "ANRO",
    "n": "Alto Neuroscience, Inc. Common Stock"
  },
  {
    "s": "ANTA",
    "n": "Antalpha Platform Holding Company - Class A Ordinary Shares"
  },
  {
    "s": "ANTX",
    "n": "AN2 Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "ANVS",
    "n": "Annovis Bio, Inc. Common Stock"
  },
  {
    "s": "AON",
    "n": "Aon plc Class A Ordinary Shares (Ireland)"
  },
  {
    "s": "AORT",
    "n": "Artivion, Inc. Common Stock"
  },
  {
    "s": "AOS",
    "n": "A.O. Smith Corporation Common Stock"
  },
  {
    "s": "AOSL",
    "n": "Alpha and Omega Semiconductor Limited - Common Shares"
  },
  {
    "s": "AOUT",
    "n": "American Outdoor Brands, Inc. - Common Stock"
  },
  {
    "s": "AP",
    "n": "Ampco-Pittsburgh Corporation Common Stock"
  },
  {
    "s": "APA",
    "n": "APA Corporation - Common Stock"
  },
  {
    "s": "APAC",
    "n": "StoneBridge Acquisition II Corporation - Class A Ordinary Shares"
  },
  {
    "s": "APACU",
    "n": "StoneBridge Acquisition II Corporation - Units"
  },
  {
    "s": "APAM",
    "n": "Artisan Partners Asset Management Inc. Class A Common Stock"
  },
  {
    "s": "APC",
    "n": "ARKO Petroleum Corp. - Class A Common Stock"
  },
  {
    "s": "APD",
    "n": "Air Products and Chemicals, Inc. Common Stock"
  },
  {
    "s": "APEI",
    "n": "American Public Education, Inc. - Common Stock"
  },
  {
    "s": "APG",
    "n": "APi Group Corporation Common Stock"
  },
  {
    "s": "APH",
    "n": "Amphenol Corporation Common Stock"
  },
  {
    "s": "API",
    "n": "Agora, Inc. - ADS"
  },
  {
    "s": "APLD",
    "n": "Applied Digital Corporation - Common Stock"
  },
  {
    "s": "APLM",
    "n": "Apollomics Inc. - Class A Ordinary Shares"
  },
  {
    "s": "APMC",
    "n": "AmperCap Acquisition Company - Ordinary Shares"
  },
  {
    "s": "APMCR",
    "n": "AmperCap Acquisition Company - Right"
  },
  {
    "s": "APMCU",
    "n": "AmperCap Acquisition Company - Unit"
  },
  {
    "s": "APMD",
    "n": "Apnimed, Inc. - Common Stock"
  },
  {
    "s": "APO",
    "n": "Apollo Global Management, Inc. (New) Common Stock"
  },
  {
    "s": "APOG",
    "n": "Apogee Enterprises, Inc. - Common Stock"
  },
  {
    "s": "APOS",
    "n": "Apollo Global Management, Inc. 7.625% Fixed-Rate Resettable Junior Subordinated Notes due 2053"
  },
  {
    "s": "APP",
    "n": "Applovin Corporation - Class A Common Stock"
  },
  {
    "s": "APPF",
    "n": "AppFolio, Inc. - Class A Common Stock"
  },
  {
    "s": "APPN",
    "n": "Appian Corporation - Class A Common Stock"
  },
  {
    "s": "APPS",
    "n": "Digital Turbine, Inc. - Common Stock"
  },
  {
    "s": "APRE",
    "n": "Aprea Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "APT",
    "n": "Alpha Pro Tech, Ltd. Common Stock"
  },
  {
    "s": "APTV",
    "n": "Aptiv PLC Ordinary Shares"
  },
  {
    "s": "APUR",
    "n": "Aperture AC - Class A Ordinary Shares"
  },
  {
    "s": "APUS",
    "n": "Apimeds Pharmaceuticals US, Inc. Common Stock"
  },
  {
    "s": "APVO",
    "n": "Aptevo Therapeutics Inc. - Common Stock"
  },
  {
    "s": "APWC",
    "n": "Asia Pacific Wire & Cable Corporation Limited  - Common shares, Par value .01 per share"
  },
  {
    "s": "APXT",
    "n": "Apex Treasury Corporation - Class A Ordinary Share"
  },
  {
    "s": "APXTU",
    "n": "Apex Treasury Corporation - Units"
  },
  {
    "s": "APXTW",
    "n": "Apex Treasury Corporation - Warrants"
  },
  {
    "s": "APYX",
    "n": "Apyx Medical Corporation - Common Stock"
  },
  {
    "s": "AQB",
    "n": "AquaBounty Technologies, Inc. - Common Stock"
  },
  {
    "s": "AQMS",
    "n": "Aqua Metals, Inc. - Common Stock"
  },
  {
    "s": "AQN",
    "n": "Algonquin Power & Utilities Corp. Common Shares"
  },
  {
    "s": "AQNB",
    "n": "Algonquin Power & Utilities Corp. 6.20% Fixed-to-Floating Subordinated Notes Series 2019-A due July 1, 2079"
  },
  {
    "s": "AQST",
    "n": "Aquestive Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "AR",
    "n": "Antero Resources Corporation Common Stock"
  },
  {
    "s": "ARAI",
    "n": "Arrive AI Inc. - Common Stock"
  },
  {
    "s": "ARAY",
    "n": "Accuray Incorporated - Common Stock"
  },
  {
    "s": "ARBB",
    "n": "ARB IOT Group Limited - Ordinary Shares"
  },
  {
    "s": "ARBE",
    "n": "Arbe Robotics Ltd. - Ordinary Shares"
  },
  {
    "s": "ARBK",
    "n": "Argo Blockchain plc - American Depositary Shares"
  },
  {
    "s": "ARCB",
    "n": "ArcBest Corporation - Common Stock"
  },
  {
    "s": "ARCI",
    "n": "Archimedes Tech SPAC Partners III Co. - Ordinary Share"
  },
  {
    "s": "ARCIU",
    "n": "Archimedes Tech SPAC Partners III Co. - Unit"
  },
  {
    "s": "ARCL",
    "n": "ARC Group Acquisition I Corp - Class A Ordinary Shares"
  },
  {
    "s": "ARCLR",
    "n": "ARC Group Acquisition I Corp - Right"
  },
  {
    "s": "ARCLU",
    "n": "ARC Group Acquisition I Corp - Unit"
  },
  {
    "s": "ARCLW",
    "n": "ARC Group Acquisition I Corp - Warrants"
  },
  {
    "s": "ARCO",
    "n": "Arcos Dorados Holdings Inc. Class A Shares"
  },
  {
    "s": "ARCT",
    "n": "Arcturus Therapeutics Holdings Inc. - Common Stock"
  },
  {
    "s": "ARDT",
    "n": "Ardent Health, Inc. Common Stock"
  },
  {
    "s": "ARDX",
    "n": "Ardelyx, Inc. - Common Stock"
  },
  {
    "s": "ARE",
    "n": "Alexandria Real Estate Equities, Inc. Common Stock"
  },
  {
    "s": "AREC",
    "n": "American Resources Corporation - Class A Common Stock"
  },
  {
    "s": "ARES",
    "n": "Ares Management Corporation Class A Common Stock"
  },
  {
    "s": "ARGX",
    "n": "argenx SE - American Depositary Shares"
  },
  {
    "s": "ARHS",
    "n": "Arhaus, Inc. - Class A Common Stock"
  },
  {
    "s": "ARI",
    "n": "Apollo Commercial Real Estate Finance, Inc"
  },
  {
    "s": "ARIS",
    "n": "Aris Mining Corporation Common Shares"
  },
  {
    "s": "ARKO",
    "n": "ARKO Corp. - Common Stock"
  },
  {
    "s": "ARKR",
    "n": "Ark Restaurants Corp. - Common Stock"
  },
  {
    "s": "ARL",
    "n": "American Realty Investors, Inc. Common Stock"
  },
  {
    "s": "ARLO",
    "n": "Arlo Technologies, Inc. Common Stock"
  },
  {
    "s": "ARLP",
    "n": "Alliance Resource Partners, L.P. - Common Units Representing Limited Partnership Interests"
  },
  {
    "s": "ARM",
    "n": "Arm Holdings plc - American Depositary Shares"
  },
  {
    "s": "ARMK",
    "n": "Aramark Common Stock"
  },
  {
    "s": "ARMP",
    "n": "Armata Pharmaceuticals, Inc. Common Stock"
  },
  {
    "s": "AROC",
    "n": "Archrock, Inc. Common Stock"
  },
  {
    "s": "AROW",
    "n": "Arrow Financial Corporation - Common Stock"
  },
  {
    "s": "ARQ",
    "n": "Arq, Inc. - Common Stock"
  },
  {
    "s": "ARQQ",
    "n": "Arqit Quantum Inc. - Ordinary Shares"
  },
  {
    "s": "ARQT",
    "n": "Arcutis Biotherapeutics, Inc. - Common stock"
  },
  {
    "s": "ARRY",
    "n": "Array Technologies, Inc. - Common Stock"
  },
  {
    "s": "ARTC",
    "n": "Art Technology Acquisition Corp. - Class A Ordinary Shares"
  },
  {
    "s": "ARTCU",
    "n": "Art Technology Acquisition Corp. - Units"
  },
  {
    "s": "ARTCW",
    "n": "Art Technology Acquisition Corp. - Warrants"
  },
  {
    "s": "ARTL",
    "n": "Artelo Biosciences, Inc. - Common Stock"
  },
  {
    "s": "ARTNA",
    "n": "Artesian Resources Corporation - Class A Non-Voting Common Stock"
  },
  {
    "s": "ARTV",
    "n": "Artiva Biotherapeutics, Inc. - Common Stock"
  },
  {
    "s": "ARTW",
    "n": "Art's-Way Manufacturing Co., Inc. - Common Stock"
  },
  {
    "s": "ARVN",
    "n": "Arvinas, Inc. - Common Stock"
  },
  {
    "s": "ARW",
    "n": "Arrow Electronics, Inc. Common Stock"
  },
  {
    "s": "ARWR",
    "n": "Arrowhead Pharmaceuticals, Inc. - Common Stock"
  },
  {
    "s": "ARX",
    "n": "Accelerant Holdings Class A Common Shares"
  },
  {
    "s": "ARXS",
    "n": "Arxis, Inc. - Class A Common Stock"
  },
  {
    "s": "AS",
    "n": "Amer Sports, Inc. Ordinary Shares"
  },
  {
    "s": "ASA",
    "n": "ASA  Gold and Precious Metals Limited"
  },
  {
    "s": "ASAN",
    "n": "Asana, Inc. Class A Common Stock"
  },
  {
    "s": "ASB",
    "n": "Associated Banc-Corp Common Stock"
  },
  {
    "s": "ASBA",
    "n": "Associated Banc-Corp 6.625% Fixed-Rate Reset Subordinated Notes due 2033"
  },
  {
    "s": "ASBH",
    "n": "American Savings Bank, N.A. Common Stock"
  },
  {
    "s": "ASBP",
    "n": "Aspire-Lakewood Holdings, Inc. - Common Stock"
  },
  {
    "s": "ASC",
    "n": "Ardmore Shipping Corporation Common Stock"
  },
  {
    "s": "ASH",
    "n": "Ashland Inc. Common Stock"
  },
  {
    "s": "ASIC",
    "n": "Ategrity Specialty Insurance Company Holdings Common Stock"
  },
  {
    "s": "ASIX",
    "n": "AdvanSix Inc. Common Stock "
  },
  {
    "s": "ASLE",
    "n": "AerSale Corporation - Common Stock"
  },
  {
    "s": "ASM",
    "n": "Avino Silver & Gold Mines Ltd. Common Shares (Canada)"
  },
  {
    "s": "ASMB",
    "n": "Assembly Biosciences, Inc. - Common Stock"
  },
  {
    "s": "ASML",
    "n": "ASML Holding N.V. - New York Registry Shares"
  },
  {
    "s": "ASND",
    "n": "Ascendis Pharma A/S - Ordinary Share"
  },
  {
    "s": "ASO",
    "n": "Academy Sports and Outdoors, Inc. - Common Stock"
  },
  {
    "s": "ASPC",
    "n": "A SPAC III Acquisition Corp. - Class A Ordinary Shares"
  },
  {
    "s": "ASPCR",
    "n": "A SPAC III Acquisition Corp. - Right"
  },
  {
    "s": "ASPCU",
    "n": "A SPAC III Acquisition Corp. - Unit"
  },
  {
    "s": "ASPI",
    "n": "ASP Isotopes Inc. - Common Stock"
  },
  {
    "s": "ASPN",
    "n": "Aspen Aerogels, Inc. Common Stock"
  },
  {
    "s": "ASPS",
    "n": "Altisource Portfolio Solutions S.A. - Common Stock"
  },
  {
    "s": "ASPSW",
    "n": "Altisource Portfolio Solutions S.A. - Net Settle Stakeholder Warrants"
  },
  {
    "s": "ASPSZ",
    "n": "Altisource Portfolio Solutions S.A. - Cash Exercise Stakeholder Warrants"
  },
  {
    "s": "ASR",
    "n": "Grupo Aeroportuario del Sureste, S.A. de C.V. Common Stock"
  },
  {
    "s": "ASRV",
    "n": "AmeriServ Financial Inc. - Common Stock"
  },
  {
    "s": "ASST",
    "n": "Strive, Inc. - Class A Common Stock"
  },
  {
    "s": "ASTC",
    "n": "Astrotech Corporation - Common Stock"
  },
  {
    "s": "ASTE",
    "n": "Astec Industries, Inc. - Common Stock"
  },
  {
    "s": "ASTH",
    "n": "Astrana Health Inc. - Common Stock"
  },
  {
    "s": "ASTI",
    "n": "Ascent Solar Technologies, Inc - Common Stock"
  },
  {
    "s": "ASTL",
    "n": "Algoma Steel Group Inc. - Common Shares"
  },
  {
    "s": "ASTS",
    "n": "AST SpaceMobile, Inc. - Class A Common Stock"
  },
  {
    "s": "ASUR",
    "n": "Asure Software Inc - Common Stock"
  },
  {
    "s": "ASX",
    "n": "ASE Technology Holding Co., Ltd. American Depositary Shares (each representing Two Common Shares) "
  },
  {
    "s": "ASYS",
    "n": "Amtech Systems, Inc. - Common Stock"
  },
  {
    "s": "ATAT",
    "n": "Atour Lifestyle Holdings Limited - American Depositary Shares"
  },
  {
    "s": "ATCH",
    "n": "AtlasClear Holdings, Inc. Common Stock"
  },
  {
    "s": "ATCX",
    "n": "Atlas Critical Minerals Corporation - Common Stock"
  },
  {
    "s": "ATEC",
    "n": "Alphatec Holdings, Inc. - Common Stock"
  },
  {
    "s": "ATEN",
    "n": "A10 Networks, Inc. Common Stock"
  },
  {
    "s": "ATER",
    "n": "Aterian, Inc. - Common Stock"
  },
  {
    "s": "ATEX",
    "n": "Anterix Inc. - Common Stock"
  },
  {
    "s": "ATGL",
    "n": "Alpha Technology Group Limited - Class A Ordinary Shares"
  },
  {
    "s": "ATHE",
    "n": "Alterity Therapeutics Limited - American Depositary Shares"
  },
  {
    "s": "ATHM",
    "n": "Autohome Inc. American Depositary Shares, each representing four class A ordinary shares."
  },
  {
    "s": "ATHR",
    "n": "Aether Holdings, Inc. - Common Stock"
  },
  {
    "s": "ATHS",
    "n": "Athene Holding Ltd. 7.250% Fixed-Rate Reset Junior Subordinated Debentures due 2064"
  },
  {
    "s": "ATI",
    "n": "ATI Inc. Common Stock"
  },
  {
    "s": "ATII",
    "n": "Archimedes Tech SPAC Partners II Co. - Ordinary Shares"
  },
  {
    "s": "ATIIU",
    "n": "Archimedes Tech SPAC Partners II Co. - Unit"
  },
  {
    "s": "ATKR",
    "n": "Atkore Inc. Common Stock"
  },
  {
    "s": "ATLC",
    "n": "Atlanticus Holdings Corporation - Common Stock"
  },
  {
    "s": "ATLCL",
    "n": "Atlanticus Holdings Corporation - 6.125% Senior Notes due 2026"
  },
  {
    "s": "ATLCZ",
    "n": "Atlanticus Holdings Corporation - 9.25% Senior Notes due 2029"
  },
  {
    "s": "ATLO",
    "n": "Ames National Corporation - Common Stock"
  },
  {
    "s": "ATLQ",
    "n": "JAB Acquisition Corp I - Class A Ordinary Shares"
  },
  {
    "s": "ATLQU",
    "n": "JAB Acquisition Corp I - Units"
  },
  {
    "s": "ATLQW",
    "n": "JAB Acquisition Corp I - Warrants"
  },
  {
    "s": "ATLX",
    "n": "Atlas Lithium Corporation - Common Stock"
  },
  {
    "s": "ATMU",
    "n": "Atmus Filtration Technologies Inc. Common Stock"
  },
  {
    "s": "ATNI",
    "n": "ATN International, Inc. - Common Stock"
  },
  {
    "s": "ATNM",
    "n": "Actinium Pharmaceuticals, Inc. (Delaware) Common Stock"
  },
  {
    "s": "ATO",
    "n": "Atmos Energy Corporation Common Stock"
  },
  {
    "s": "ATOM",
    "n": "Atomera Incorporated - Common Stock"
  },
  {
    "s": "ATOS",
    "n": "Atossa Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "ATPC",
    "n": "Agape ATP Corporation - Common Stock"
  },
  {
    "s": "ATR",
    "n": "AptarGroup, Inc. Common Stock"
  },
  {
    "s": "ATRA",
    "n": "Atara Biotherapeutics, Inc. - Common Stock"
  },
  {
    "s": "ATRC",
    "n": "AtriCure, Inc. - Common Stock"
  },
  {
    "s": "ATRO",
    "n": "Astronics Corporation - Common Stock"
  },
  {
    "s": "ATS",
    "n": "ATS Corporation Common Shares"
  },
  {
    "s": "ATTO",
    "n": "Attovia Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "ATTT",
    "n": "Atlas Trinity Tech Limited - Ordinary Shares"
  },
  {
    "s": "ATXG",
    "n": "Addentax Group Corp. - Common Stock"
  },
  {
    "s": "ATYR",
    "n": "aTyr Pharma, Inc. - Common Stock"
  },
  {
    "s": "AU",
    "n": "AngloGold Ashanti PLC Ordinary Shares"
  },
  {
    "s": "AUB",
    "n": "Atlantic Union Bankshares Corporation Common Stock"
  },
  {
    "s": "AUBN",
    "n": "Auburn National Bancorporation, Inc. - Common Stock"
  },
  {
    "s": "AUC",
    "n": "ATIF Holdings Limited - Ordinary Shares"
  },
  {
    "s": "AUDC",
    "n": "AudioCodes Ltd. - Ordinary Shares"
  },
  {
    "s": "AUGO",
    "n": "Aura Minerals Inc. - Common Shares"
  },
  {
    "s": "AUID",
    "n": "authID Inc. - Common Stock"
  },
  {
    "s": "AUNA",
    "n": "Auna SA Class A Ordinary Shares"
  },
  {
    "s": "AUPH",
    "n": "Aurinia Pharmaceuticals Inc - Common Shares"
  },
  {
    "s": "AUR",
    "n": "Aurora Innovation, Inc.  - Class A Common Stock"
  },
  {
    "s": "AURA",
    "n": "Aura Biosciences, Inc. - Common Stock"
  },
  {
    "s": "AURE",
    "n": "Aurelion Inc.  - Class A Ordinary Shares"
  },
  {
    "s": "AUST",
    "n": "Austin Gold Corp. Common Shares"
  },
  {
    "s": "AUTL",
    "n": "Autolus Therapeutics plc - American Depositary Shares"
  },
  {
    "s": "AUUD",
    "n": "Auddia Inc. - Common Stock"
  },
  {
    "s": "AUXX",
    "n": "Gold X2 Mining Inc. Common Shares"
  },
  {
    "s": "AVA",
    "n": "Avista Corporation Common Stock"
  },
  {
    "s": "AVAH",
    "n": "Aveanna Healthcare Holdings Inc. - Common Stock"
  },
  {
    "s": "AVAT",
    "n": "Avalanche Treasury Corporation - Class A Common Stock"
  },
  {
    "s": "AVAV",
    "n": "AeroVironment, Inc. - Common Stock"
  },
  {
    "s": "AVBC",
    "n": "Avidia Bancorp, Inc. Common Stock"
  },
  {
    "s": "AVBH",
    "n": "Avidbank Holdings, Inc. - Common Stock"
  },
  {
    "s": "AVBP",
    "n": "ArriVent BioPharma, Inc. - Common Stock"
  },
  {
    "s": "AVD",
    "n": "American Vanguard Corporation Common Stock ($0.10 Par Value)"
  },
  {
    "s": "AVEX",
    "n": "AEVEX Corp. Class A Common Stock"
  },
  {
    "s": "AVGO",
    "n": "Broadcom Inc. - Common Stock"
  },
  {
    "s": "AVIR",
    "n": "Atea Pharmaceuticals, Inc. - common stock"
  },
  {
    "s": "AVLN",
    "n": "Avalyn Pharma Inc. - common stock"
  },
  {
    "s": "AVNT",
    "n": "Avient Corporation Common Stock"
  },
  {
    "s": "AVNW",
    "n": "Aviat Networks, Inc. - Common Stock"
  },
  {
    "s": "AVO",
    "n": "Mission Produce, Inc. - Common Stock"
  },
  {
    "s": "AVPT",
    "n": "AvePoint, Inc. - Class A Common Stock"
  },
  {
    "s": "AVR",
    "n": "Anteris Technologies Global Corp. - Common Stock"
  },
  {
    "s": "AVT",
    "n": "Avnet, Inc. - Common Stock"
  },
  {
    "s": "AVTR",
    "n": "Avantor, Inc. Common Stock"
  },
  {
    "s": "AVTX",
    "n": "Avalo Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "AVX",
    "n": "Avax One Technology Ltd. - Common Shares"
  },
  {
    "s": "AVXL",
    "n": "Anavex Life Sciences Corp. - Common Stock"
  },
  {
    "s": "AVY",
    "n": "Avery Dennison Corporation Common Stock"
  },
  {
    "s": "AWI",
    "n": "Armstrong World Industries Inc Common Stock"
  },
  {
    "s": "AWK",
    "n": "American Water Works Company, Inc. Common Stock"
  },
  {
    "s": "AWR",
    "n": "American States Water Company Common Stock"
  },
  {
    "s": "AWRE",
    "n": "Aware, Inc. - Common Stock"
  },
  {
    "s": "AWX",
    "n": "Avalon Holdings Corporation Common Stock"
  },
  {
    "s": "AX",
    "n": "Axos Financial, Inc. Common Stock"
  },
  {
    "s": "AXG",
    "n": "Solowin Holdings - Class A Ordinary Share"
  },
  {
    "s": "AXGN",
    "n": "Axogen, Inc. - Common Stock"
  },
  {
    "s": "AXIL",
    "n": "AXIL Brands, Inc. Common Stock"
  },
  {
    "s": "AXIN",
    "n": "Axiom Intelligence Acquisition Corp 1 - Class A Ordinary Shares"
  },
  {
    "s": "AXINR",
    "n": "Axiom Intelligence Acquisition Corp 1 - Right"
  },
  {
    "s": "AXINU",
    "n": "Axiom Intelligence Acquisition Corp 1 - Units"
  },
  {
    "s": "AXON",
    "n": "Axon Enterprise, Inc. - Common Stock"
  },
  {
    "s": "AXP",
    "n": "American Express Company Common Stock"
  },
  {
    "s": "AXR",
    "n": "AMREP Corporation Common Stock"
  },
  {
    "s": "AXS",
    "n": "Axis Capital Holdings Limited Common Stock"
  },
  {
    "s": "AXSM",
    "n": "Axsome Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "AXTA",
    "n": "Axalta Coating Systems Ltd. Common Shares"
  },
  {
    "s": "AXTI",
    "n": "AXT Inc - Common Stock"
  },
  {
    "s": "AYA",
    "n": "Aya Gold & Silver Inc. - Common Shares"
  },
  {
    "s": "AYI",
    "n": "Acuity Inc. Common Stock"
  },
  {
    "s": "AYTU",
    "n": "Aytu BioPharma, Inc.  - Common Stock"
  },
  {
    "s": "AZ",
    "n": "A2Z Cust2Mate Solutions Corp. - Common Shares"
  },
  {
    "s": "AZI",
    "n": "Autozi Internet Technology (Global) Ltd. - Class A Ordinary Shares"
  },
  {
    "s": "AZIO",
    "n": "Azio AI Holdings, Inc. - Common stock"
  },
  {
    "s": "AZN",
    "n": "AstraZeneca PLC Ordinary Shares"
  },
  {
    "s": "AZO",
    "n": "AutoZone, Inc. Common Stock"
  },
  {
    "s": "AZTA",
    "n": "Azenta, Inc. - Common Stock"
  },
  {
    "s": "AZTR",
    "n": "Azitra Inc Common Stock"
  },
  {
    "s": "AZUL",
    "n": "Azul S.A. American Depositary Shares, each representing two (2) Common Shares"
  },
  {
    "s": "AZZ",
    "n": "AZZ Inc."
  },
  {
    "s": "B",
    "n": "Barrick Mining Corporation Common Shares"
  },
  {
    "s": "BA",
    "n": "Boeing Company (The) Common Stock"
  },
  {
    "s": "BABA",
    "n": "Alibaba Group Holding Limited American Depositary Shares each representing eight Ordinary share"
  },
  {
    "s": "BAC",
    "n": "Bank of America Corporation Common Stock"
  },
  {
    "s": "BACC",
    "n": "Blue Acquisition Corp. - Class A Ordinary Shares"
  },
  {
    "s": "BACCR",
    "n": "Blue Acquisition Corp. - Right"
  },
  {
    "s": "BACCU",
    "n": "Blue Acquisition Corp. - Unit"
  },
  {
    "s": "BAER",
    "n": "Bridger Aerospace Group Holdings, Inc. - Common Stock"
  },
  {
    "s": "BAFN",
    "n": "BayFirst Financial Corp. - Common Stock"
  },
  {
    "s": "BAH",
    "n": "Booz Allen Hamilton Holding Corporation Common Stock"
  },
  {
    "s": "BAK",
    "n": "Braskem SA ADR"
  },
  {
    "s": "BALL",
    "n": "Ball Corporation Common Stock"
  },
  {
    "s": "BALY",
    "n": "Bally's Corporation Common Stock"
  },
  {
    "s": "BAM",
    "n": "Brookfield Asset Management Inc Class A Limited Voting Shares"
  },
  {
    "s": "BANC",
    "n": "Banc of California, Inc. Common Stock"
  },
  {
    "s": "BAND",
    "n": "Bandwidth Inc. - Class A Common Stock"
  },
  {
    "s": "BANF",
    "n": "BancFirst Corporation - Common Stock"
  },
  {
    "s": "BANL",
    "n": "CBL International Limited - Class B Ordinary Shares"
  },
  {
    "s": "BANR",
    "n": "Banner Corporation - Common Stock"
  },
  {
    "s": "BAOS",
    "n": "Baosheng Media Group Holdings Limited - Ordinary shares"
  },
  {
    "s": "BAP",
    "n": "Credicorp Ltd. Common Stock"
  },
  {
    "s": "BAR",
    "n": "GraniteShares Gold Trust Shares of Beneficial Interest"
  },
  {
    "s": "BARK",
    "n": "BARK, Inc. Class A Common Stock"
  },
  {
    "s": "BATL",
    "n": "Battalion Oil Corporation Common Stock"
  },
  {
    "s": "BATRA",
    "n": "Atlanta Braves Holdings, Inc. - Series A Common Stock"
  },
  {
    "s": "BATRK",
    "n": "Atlanta Braves Holdings, Inc. - Series C Common Stock"
  },
  {
    "s": "BAX",
    "n": "Baxter International Inc. Common Stock"
  },
  {
    "s": "BB",
    "n": "BlackBerry Limited Common Stock"
  },
  {
    "s": "BBAI",
    "n": "BigBear.ai, Inc. Common Stock"
  },
  {
    "s": "BBAI-W",
    "n": "BigBear.ai, Inc. Redeemable Warrants, each exercisable for one share of Common Stock at an exercise price of $11.50 per share"
  },
  {
    "s": "BBAR",
    "n": "Banco BBVA Argentina S.A. ADS"
  },
  {
    "s": "BBCI",
    "n": "Bradbury Capital Inc. - Ordinary Shares"
  },
  {
    "s": "BBCIW",
    "n": "Bradbury Capital Inc. - Warrants"
  },
  {
    "s": "BBCP",
    "n": "Concrete Pumping Holdings, Inc.  - Common Stock"
  },
  {
    "s": "BBD",
    "n": "Banco Bradesco Sa American Depositary Shares"
  },
  {
    "s": "BBDC",
    "n": "Barings BDC, Inc. Common Stock"
  },
  {
    "s": "BBDO",
    "n": "Banco Bradesco Sa American Depositary Shares (each representing one Common Share)"
  },
  {
    "s": "BBGI",
    "n": "Beasley Broadcast Group, Inc. - Class A Common Stock"
  },
  {
    "s": "BBIO",
    "n": "BridgeBio Pharma, Inc. - Common Stock"
  },
  {
    "s": "BBLG",
    "n": "Bone Biologics Corp - Common Stock"
  },
  {
    "s": "BBLGW",
    "n": "Bone Biologics Corp - warrants"
  },
  {
    "s": "BBN",
    "n": "BlackRock Taxable Municipal Bond Trust Common Shares of Beneficial Interest"
  },
  {
    "s": "BBNX",
    "n": "Beta Bionics, Inc. - Common Stock"
  },
  {
    "s": "BBOT",
    "n": "BridgeBio Oncology Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "BBSI",
    "n": "Barrett Business Services, Inc. - Common Stock"
  },
  {
    "s": "BBT",
    "n": "Beacon Financial Corporation Common stock"
  },
  {
    "s": "BBUC",
    "n": "Brookfield Business Corporation Class A Subordinate Voting Shares"
  },
  {
    "s": "BBVA",
    "n": "Banco Bilbao Vizcaya Argentaria S.A. Common Stock"
  },
  {
    "s": "BBW",
    "n": "Build-A-Bear Workshop, Inc. Common Stock"
  },
  {
    "s": "BBWI",
    "n": "Bath & Body Works, Inc."
  },
  {
    "s": "BBY",
    "n": "Best Buy Co., Inc. Common Stock"
  },
  {
    "s": "BC",
    "n": "Brunswick Corporation Common Stock"
  },
  {
    "s": "BCAL",
    "n": "California BanCorp - Common Stock"
  },
  {
    "s": "BCAT",
    "n": "BlackRock Capital Allocation Term Trust Common Shares of Beneficial Interest"
  },
  {
    "s": "BCAX",
    "n": "Bicara Therapeutics Inc. - Common Stock"
  },
  {
    "s": "BCBP",
    "n": "BCB Bancorp, Inc. (NJ) - Common Stock"
  },
  {
    "s": "BCC",
    "n": "Boise Cascade, L.L.C. Common Stock"
  },
  {
    "s": "BCCQ",
    "n": "Bleichroeder Acquisition Corp. III - Class A Ordinary Shares"
  },
  {
    "s": "BCCQU",
    "n": "Bleichroeder Acquisition Corp. III - Units"
  },
  {
    "s": "BCDA",
    "n": "BioCardia, Inc. - Common Stock"
  },
  {
    "s": "BCE",
    "n": "BCE, Inc. Common Stock"
  },
  {
    "s": "BCG",
    "n": "Binah Capital Group, Inc. - Common Stock"
  },
  {
    "s": "BCGWW",
    "n": "Binah Capital Group, Inc. - Warrants"
  },
  {
    "s": "BCH",
    "n": "Banco De Chile ADS"
  },
  {
    "s": "BCHT",
    "n": "Birchtech Corp. Common Stock"
  },
  {
    "s": "BCML",
    "n": "BayCom Corp - Common Stock"
  },
  {
    "s": "BCO",
    "n": "Brinks Company (The) Common Stock"
  },
  {
    "s": "BCPC",
    "n": "Balchem Corporation - Common Stock"
  },
  {
    "s": "BCRX",
    "n": "BioCryst Pharmaceuticals, Inc. - Common Stock"
  },
  {
    "s": "BCS",
    "n": "Barclays PLC Common Stock"
  },
  {
    "s": "BCSF",
    "n": "Bain Capital Specialty Finance, Inc. Common Stock"
  },
  {
    "s": "BCSS",
    "n": "Bain Capital GSS Investment Corp. Class A Ordinary Shares"
  },
  {
    "s": "BCTX",
    "n": "BriaCell Therapeutics Corp. - Common Shares"
  },
  {
    "s": "BCTXL",
    "n": "BriaCell Therapeutics Corp. - Warrants"
  },
  {
    "s": "BCX",
    "n": "BlackRock Resources Common Shares of Beneficial Interest"
  },
  {
    "s": "BCYC",
    "n": "Bicycle Therapeutics plc - American Depositary Shares"
  },
  {
    "s": "BDAI",
    "n": "Biddance AI Systems, Inc. - Class A Ordinary Share"
  },
  {
    "s": "BDC",
    "n": "Belden Inc Common Stock"
  },
  {
    "s": "BDCI",
    "n": "BTC Development Corp. - Class A Ordinary Shares"
  },
  {
    "s": "BDCIU",
    "n": "BTC Development Corp. - Unit"
  },
  {
    "s": "BDJ",
    "n": "Blackrock Enhanced Equity Dividend Trust"
  },
  {
    "s": "BDL",
    "n": "Flanigan's Enterprises, Inc. Common Stock"
  },
  {
    "s": "BDMD",
    "n": "Baird Medical Investment Holdings Ltd - Ordinary Share"
  },
  {
    "s": "BDN",
    "n": "Brandywine Realty Trust Common Stock"
  },
  {
    "s": "BDRX",
    "n": "Biodexa Pharmaceuticals plc - American Depositary Shares"
  },
  {
    "s": "BDSX",
    "n": "Biodesix, Inc. - Common Stock"
  },
  {
    "s": "BDTX",
    "n": "Black Diamond Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "BDX",
    "n": "Becton, Dickinson and Company Common Stock"
  },
  {
    "s": "BE",
    "n": "Bloom Energy Corporation Class A Common Stock"
  },
  {
    "s": "BEAG",
    "n": "Bold Eagle Acquisition Corp. - Class A Ordinary Shares"
  },
  {
    "s": "BEAGR",
    "n": "Bold Eagle Acquisition Corp. - Right"
  },
  {
    "s": "BEAGU",
    "n": "Bold Eagle Acquisition Corp. - Units"
  },
  {
    "s": "BEAM",
    "n": "Beam Therapeutics Inc. - Common Stock"
  },
  {
    "s": "BEAT",
    "n": "Heartbeam, Inc. - Common Stock"
  },
  {
    "s": "BEBE",
    "n": "TGE Value Creative Solutions Corp Class A Ordinary Shares"
  },
  {
    "s": "BEEM",
    "n": "Beam Global - Common Stock"
  },
  {
    "s": "BEEP",
    "n": "Mobile Infrastructure Corporation - Common Stock"
  },
  {
    "s": "BEKE",
    "n": "KE Holdings Inc American Depositary Shares (each representing three Class A Ordinary Shares)"
  },
  {
    "s": "BELFA",
    "n": "Bel Fuse Inc. - Class A Common Stock"
  },
  {
    "s": "BELFB",
    "n": "Bel Fuse Inc. - Class B Common Stock"
  },
  {
    "s": "BEN",
    "n": "Franklin Templeton, Inc. Common Stock"
  },
  {
    "s": "BENF",
    "n": "Beneficient - Class A Common Stock"
  },
  {
    "s": "BEP",
    "n": "Brookfield Renewable Partners L.P. Limited Partnership Units"
  },
  {
    "s": "BEPC",
    "n": "Brookfield Renewable Corporation Brookfield Renewable Corporation Class A Subordinate Voting Shares"
  },
  {
    "s": "BEPH",
    "n": "Brookfield BRP Holdings (Canada) Inc. 4.625% Perpetual Subordinated Notes"
  },
  {
    "s": "BEPI",
    "n": "Brookfield BRP Holdings (Canada) Inc. 4.875% Perpetual Subordinated Notes"
  },
  {
    "s": "BEPJ",
    "n": "Brookfield BRP Holdings (Canada) Inc. 7.250% Perpetual Subordinated Notes"
  },
  {
    "s": "BESS",
    "n": "Bimergen Energy Corporation Common Stock"
  },
  {
    "s": "BESS-W",
    "n": "Bimergen Energy Corporation Warrants, each share exercisable to purchase one share of Common Stock"
  },
  {
    "s": "BETA",
    "n": "Beta Technologies, Inc. Class A Common Stock"
  },
  {
    "s": "BETR",
    "n": "Better Home & Finance Holding Company - Class A Common Stock"
  },
  {
    "s": "BF-A",
    "n": "Brown Forman Inc Class A Common Stock"
  },
  {
    "s": "BF-B",
    "n": "Brown Forman Inc Class B Common Stock"
  },
  {
    "s": "BFAM",
    "n": "Bright Horizons Family Solutions Inc. Common Stock"
  },
  {
    "s": "BFC",
    "n": "Bank First Corporation - Common Stock"
  },
  {
    "s": "BFH",
    "n": "Bread Financial Holdings, Inc. Common Stock"
  },
  {
    "s": "BFLY",
    "n": "Butterfly Network, Inc. Class A Common Stock"
  },
  {
    "s": "BFRG",
    "n": "Bullfrog AI Holdings, Inc. - Common Stock"
  },
  {
    "s": "BFRGW",
    "n": "Bullfrog AI Holdings, Inc. - Warrants"
  },
  {
    "s": "BFRI",
    "n": "Biofrontera Inc. - Common Stock"
  },
  {
    "s": "BFRIW",
    "n": "Biofrontera Inc. - Warrants"
  },
  {
    "s": "BFS",
    "n": "Saul Centers, Inc. Common Stock"
  },
  {
    "s": "BFST",
    "n": "Business First Bancshares, Inc. - Common Stock"
  },
  {
    "s": "BG",
    "n": "Bunge Limited Common Shares"
  },
  {
    "s": "BGC",
    "n": "BGC Group, Inc. - Class A Common Stock"
  },
  {
    "s": "BGDE",
    "n": "Big Digital Energy, Inc. - Common Stock"
  },
  {
    "s": "BGIN",
    "n": "Bgin Blockchain Limited - Class A Ordinary Shares"
  },
  {
    "s": "BGL",
    "n": "Blue Gold Limited - Class A ordinary shares"
  },
  {
    "s": "BGLC",
    "n": "BioNexus Gene Lab Corp - Common stock"
  },
  {
    "s": "BGM",
    "n": "BGM Group Ltd. - Class A Ordinary Shares"
  },
  {
    "s": "BGMS",
    "n": "Bio Green Med Solution, Inc. - Common Stock"
  },
  {
    "s": "BGR",
    "n": "BlackRock Energy and Resources Trust"
  },
  {
    "s": "BGS",
    "n": "B&G Foods, Inc. Common Stock"
  },
  {
    "s": "BGSF",
    "n": "BGSF, Inc. Common Stock"
  },
  {
    "s": "BGSI",
    "n": "Boyd Group Services Inc. Common Shares"
  },
  {
    "s": "BGT",
    "n": "BlackRock Floating Rate Income Trust"
  },
  {
    "s": "BGY",
    "n": "Blackrock Enhanced International Dividend Trust"
  },
  {
    "s": "BH",
    "n": "Biglari Holdings Inc. Class B Common Stock"
  },
  {
    "s": "BH-A",
    "n": "Biglari Holdings Inc. Class A Common Stock"
  },
  {
    "s": "BHAV",
    "n": "BHAV Acquisition Corp - Class A Ordinary Shares"
  },
  {
    "s": "BHAVU",
    "n": "BHAV Acquisition Corp - Units"
  },
  {
    "s": "BHB",
    "n": "Bar Harbor Bankshares, Inc. Common Stock"
  },
  {
    "s": "BHC",
    "n": "Bausch Health Companies Inc. Common Stock"
  },
  {
    "s": "BHE",
    "n": "Benchmark Electronics, Inc. Common Stock"
  },
  {
    "s": "BHF",
    "n": "Brighthouse Financial, Inc. - Common Stock"
  },
  {
    "s": "BHFAL",
    "n": "Brighthouse Financial, Inc. - Junior Subordinated Debentures due 2058"
  },
  {
    "s": "BHK",
    "n": "Blackrock Core Bond Trust"
  },
  {
    "s": "BHM",
    "n": "Bluerock Homes Trust, Inc. Class A Common Stock"
  },
  {
    "s": "BHP",
    "n": "BHP Group Limited American Depositary Shares (Each representing two Ordinary Shares)"
  },
  {
    "s": "BHR",
    "n": "Braemar Hotels & Resorts Inc. Common Stock"
  },
  {
    "s": "BHRB",
    "n": "Burke & Herbert Financial Services Corp. - Common Stock"
  },
  {
    "s": "BHST",
    "n": "BioHarvest Sciences Inc. - Common Stock"
  },
  {
    "s": "BHV",
    "n": "BlackRock Virginia Municipal Bond Trust"
  },
  {
    "s": "BHVN",
    "n": "Biohaven Ltd. Common Shares "
  },
  {
    "s": "BIAF",
    "n": "bioAffinity Technologies, Inc. - Common Stock"
  },
  {
    "s": "BID",
    "n": "Tribeca Strategic Acquisition Corp. - Class A Ordinary Shares"
  },
  {
    "s": "BIDU",
    "n": "Baidu, Inc. - American Depositary Shares, each representing 8 ordinary share"
  },
  {
    "s": "BIDWU",
    "n": "Tribeca Strategic Acquisition Corp. - Unit"
  },
  {
    "s": "BIIB",
    "n": "Biogen Inc. - Common Stock"
  },
  {
    "s": "BIII",
    "n": "Black Spade Acquisition III Co Class A Ordinary Shares"
  },
  {
    "s": "BILI",
    "n": "Bilibili Inc. - American Depositary Shares"
  },
  {
    "s": "BILL",
    "n": "BILL Holdings, Inc. Common Stock"
  },
  {
    "s": "BIO",
    "n": "Bio-Rad Laboratories, Inc. Class A Common Stock"
  },
  {
    "s": "BIO-B",
    "n": "Bio-Rad Laboratories, Inc. Class B  Common Stock"
  },
  {
    "s": "BIOA",
    "n": "BioAge Labs, Inc. - Common Stock"
  },
  {
    "s": "BIOT",
    "n": "Instinct Bio Technical Company Holdings Inc. - Common stock"
  },
  {
    "s": "BIOTW",
    "n": "Instinct Bio Technical Company Holdings Inc. - Warrants"
  },
  {
    "s": "BIOX",
    "n": "Bioceres Crop Solutions Corp. - Ordinary Shares"
  },
  {
    "s": "BIPC",
    "n": "Brookfield Infrastructure Corporation Brookfield Infrastructure Corporation"
  },
  {
    "s": "BIPH",
    "n": "Brookfield Infrastructure Corporation 5.000% Subordinated Notes due 2081"
  },
  {
    "s": "BIPI",
    "n": "BIP Bermuda Holdings I Limited 5.125% Perpetual Subordinated Notes"
  },
  {
    "s": "BIPJ",
    "n": "Brookfield Infrastructure Corporation 7.250% Subordinated Notes due 2084"
  },
  {
    "s": "BIRD",
    "n": "Smartbird, Inc. - Class A Common Stock"
  },
  {
    "s": "BIRK",
    "n": "Birkenstock Holding plc Ordinary Shares"
  },
  {
    "s": "BIT",
    "n": "BlackRock Multi-Sector Income Trust Common Shares of Beneficial Interest"
  },
  {
    "s": "BIVI",
    "n": "BioVie Inc. - Common stock"
  },
  {
    "s": "BIXI",
    "n": "Bitcoin Infrastructure Acquisition Corp Ltd. - Class A Ordinary Shares"
  },
  {
    "s": "BIXIU",
    "n": "Bitcoin Infrastructure Acquisition Corp Ltd. - Units"
  },
  {
    "s": "BIXIW",
    "n": "Bitcoin Infrastructure Acquisition Corp Ltd. - Warrants"
  },
  {
    "s": "BIYA",
    "n": "Baiya International Group Inc.  - Ordinary Shares"
  },
  {
    "s": "BJ",
    "n": "BJ's Wholesale Club Holdings, Inc. Common Stock"
  },
  {
    "s": "BJDX",
    "n": "Bluejay Diagnostics, Inc. - Common Stock"
  },
  {
    "s": "BJRI",
    "n": "BJ's Restaurants, Inc. - Common Stock"
  },
  {
    "s": "BKD",
    "n": "Brookdale Senior Living Inc. Common Stock"
  },
  {
    "s": "BKE",
    "n": "Buckle, Inc. (The) Common Stock"
  },
  {
    "s": "BKH",
    "n": "Black Hills Corporation Common Stock"
  },
  {
    "s": "BKHA",
    "n": "Black Hawk Acquisition Corporation - Class A Ordinary Shares"
  },
  {
    "s": "BKHAU",
    "n": "Black Hawk Acquisition Corporation - Units"
  },
  {
    "s": "BKKT",
    "n": "Bakkt, Inc. Class A Common Stock"
  },
  {
    "s": "BKNG",
    "n": "Booking Holdings Inc. - Common Stock"
  },
  {
    "s": "BKR",
    "n": "Baker Hughes Company - Common Stock"
  },
  {
    "s": "BKSY",
    "n": "BlackSky Technology Inc. Class A Common Stock"
  },
  {
    "s": "BKT",
    "n": "BlackRock Income Trust Inc. (The)"
  },
  {
    "s": "BKTI",
    "n": "BK Technologies Corporation Common Stock"
  },
  {
    "s": "BKU",
    "n": "BankUnited, Inc. Common Stock"
  },
  {
    "s": "BKV",
    "n": "BKV Corporation Common Stock"
  },
  {
    "s": "BKYI",
    "n": "BIO-key International, Inc. - Common Stock"
  },
  {
    "s": "BL",
    "n": "BlackLine, Inc. - Common Stock"
  },
  {
    "s": "BLBD",
    "n": "Blue Bird Corporation - Common Stock"
  },
  {
    "s": "BLCO",
    "n": "Bausch + Lomb Corporation Common Shares"
  },
  {
    "s": "BLDP",
    "n": "Ballard Power Systems, Inc. - Common Shares"
  },
  {
    "s": "BLDR",
    "n": "Builders FirstSource, Inc. Common Stock"
  },
  {
    "s": "BLIN",
    "n": "Bridgeline Digital, Inc. - Common Stock"
  },
  {
    "s": "BLIV",
    "n": "BeLive Holdings - ordinary shares"
  },
  {
    "s": "BLK",
    "n": "BlackRock, Inc. Common Stock"
  },
  {
    "s": "BLKB",
    "n": "Blackbaud, Inc. - Common Stock"
  },
  {
    "s": "BLLN",
    "n": "BillionToOne, Inc. - Class A common stock"
  },
  {
    "s": "BLMN",
    "n": "Bloomin' Brands, Inc. - Common Stock"
  },
  {
    "s": "BLND",
    "n": "Blend Labs, Inc. Class A Common Stock"
  },
  {
    "s": "BLNE",
    "n": "Beeline Holdings, Inc. - Common Stock"
  },
  {
    "s": "BLNK",
    "n": "Blink Charging Co. - Common Stock"
  },
  {
    "s": "BLRK",
    "n": "Bluerock Acquisition Corp. - Class A Ordinary Shares"
  },
  {
    "s": "BLRKU",
    "n": "Bluerock Acquisition Corp. - Units"
  },
  {
    "s": "BLRKW",
    "n": "Bluerock Acquisition Corp. - Warrants"
  },
  {
    "s": "BLRX",
    "n": "BioLineRx Ltd. - American Depositary Shares"
  },
  {
    "s": "BLSH",
    "n": "Bullish Ordinary Shares"
  },
  {
    "s": "BLSM",
    "n": "BlossomHill Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "BLTE",
    "n": "Belite Bio, Inc - American Depositary Shares"
  },
  {
    "s": "BLUW",
    "n": "Blue Water Acquisition Corp. III - Class A Ordinary Shares"
  },
  {
    "s": "BLUWU",
    "n": "Blue Water Acquisition Corp. III - Unit."
  },
  {
    "s": "BLW",
    "n": "Blackrock Limited Duration Income Trust"
  },
  {
    "s": "BLX",
    "n": "Bladex, Inc. Class E Common Stock"
  },
  {
    "s": "BLZE",
    "n": "Backblaze, Inc. - Common Stock"
  },
  {
    "s": "BLZR",
    "n": "Trailblazer Acquisition Corp. - Class A Ordinary Shares"
  },
  {
    "s": "BLZRU",
    "n": "Trailblazer Acquisition Corp. - Unit"
  },
  {
    "s": "BMA",
    "n": "Banco Macro S.A.  ADR (representing Ten Class B Common Shares)"
  },
  {
    "s": "BMBL",
    "n": "Bumble Inc. - common stock"
  },
  {
    "s": "BME",
    "n": "Blackrock Health Sciences Trust"
  },
  {
    "s": "BMEA",
    "n": "Biomea Fusion, Inc. - Common Stock"
  },
  {
    "s": "BMEZ",
    "n": "BlackRock Health Sciences Term Trust Common Shares of Beneficial Interest"
  },
  {
    "s": "BMGL",
    "n": "Basel Medical Group Ltd - ordinary shares"
  },
  {
    "s": "BMHL",
    "n": "Bluemount Holdings Limited - Class B Ordinary Shares"
  },
  {
    "s": "BMI",
    "n": "Badger Meter, Inc. Common Stock"
  },
  {
    "s": "BMM",
    "n": "Blue Moon Metals Inc. - Common Shares"
  },
  {
    "s": "BMN",
    "n": "BlackRock 2037 Municipal Target Term Trust Common Shares of Beneficial Interest"
  },
  {
    "s": "BMNR",
    "n": "BitMine Immersion Technologies, Inc. Common Stock"
  },
  {
    "s": "BMO",
    "n": "Bank Of Montreal Common Stock"
  },
  {
    "s": "BMR",
    "n": "Beamr Imaging Ltd. - Ordinary Share"
  },
  {
    "s": "BMRA",
    "n": "Biomerica, Inc. - Common Stock"
  },
  {
    "s": "BMRC",
    "n": "Bank of Marin Bancorp - Common Stock"
  },
  {
    "s": "BMRN",
    "n": "BioMarin Pharmaceutical Inc. - Common Stock"
  },
  {
    "s": "BMY",
    "n": "Bristol-Myers Squibb Company Common Stock"
  },
  {
    "s": "BN",
    "n": "Brookfield Corporation Class A Limited Voting Shares"
  },
  {
    "s": "BNAI",
    "n": "Brand Engagement Network Inc. - Common Stock"
  },
  {
    "s": "BNC",
    "n": "BNB Standard Corporation - Common Stock"
  },
  {
    "s": "BNCWZ",
    "n": "BNB Standard Corporation - Warrants"
  },
  {
    "s": "BNED",
    "n": "Barnes & Noble Education, Inc Common Stock"
  },
  {
    "s": "BNGO",
    "n": "Bionano Genomics, Inc. - Common Stock"
  },
  {
    "s": "BNH",
    "n": "Brookfield Finance Inc. 4.625% Subordinated Notes due October 16, 2080"
  },
  {
    "s": "BNJ",
    "n": "Brookfield Finance Inc. 4.50% Perpetual Subordinated Notes"
  },
  {
    "s": "BNKK",
    "n": "Bonk, Inc. - Common Stock"
  },
  {
    "s": "BNL",
    "n": "Broadstone Net Lease, Inc. Common Stock"
  },
  {
    "s": "BNR",
    "n": "Burning Rock Biotech Limited - American Depositary Shares"
  },
  {
    "s": "BNS",
    "n": "Bank Nova Scotia Halifax Pfd 3 Ordinary Shares"
  },
  {
    "s": "BNT",
    "n": "Brookfield Wealth Solutions Ltd. Class A Exchangeable Limited Voting Shares"
  },
  {
    "s": "BNTC",
    "n": "Benitec Biopharma Inc. - Common Stock"
  },
  {
    "s": "BNTX",
    "n": "BioNTech SE - American Depositary Shares"
  },
  {
    "s": "BNY",
    "n": "The Bank of New York Mellon Corporation Common Stock"
  },
  {
    "s": "BOBS",
    "n": "Bob's Discount Furniture, Inc. Common Stock"
  },
  {
    "s": "BOC",
    "n": "Boston Omaha Corporation Class A Common Stock"
  },
  {
    "s": "BODI",
    "n": "The Beachbody Company, Inc. - Class A Common Stock"
  },
  {
    "s": "BOE",
    "n": "Blackrock Enhanced Global Dividend Trust Common Shares of Beneficial Interest"
  },
  {
    "s": "BOF",
    "n": "BranchOut Food Inc. - Common Stock"
  },
  {
    "s": "BOH",
    "n": "Bank of Hawaii Corporation Common Stock"
  },
  {
    "s": "BOKF",
    "n": "BOK Financial Corporation - Common Stock"
  },
  {
    "s": "BOLD",
    "n": "Boundless Bio, Inc. - Common Stock"
  },
  {
    "s": "BOLT",
    "n": "Bolt Biotherapeutics, Inc. - Common Stock"
  },
  {
    "s": "BON",
    "n": "Bon Natural Life Limited - Class A Ordinary Shares"
  },
  {
    "s": "BOOM",
    "n": "DMC Global Inc. - Common Stock"
  },
  {
    "s": "BOOT",
    "n": "Boot Barn Holdings, Inc. Common Stock"
  },
  {
    "s": "BORR",
    "n": "Borr Drilling Limited Common Shares"
  },
  {
    "s": "BOSC",
    "n": "B.O.S. Better Online Solutions - Ordinary Shares"
  },
  {
    "s": "BOT",
    "n": "RoboStrategy, Inc. - Common Stock"
  },
  {
    "s": "BOTJ",
    "n": "Bank of the James Financial Group, Inc. - Common Stock"
  },
  {
    "s": "BOW",
    "n": "Bowhead Specialty Holdings Inc. Common Stock"
  },
  {
    "s": "BOX",
    "n": "Box, Inc. Class A Common Stock"
  },
  {
    "s": "BOXL",
    "n": "Boxlight Corporation - Class A Common Stock"
  },
  {
    "s": "BP",
    "n": "BP p.l.c. Common Stock"
  },
  {
    "s": "BPAC",
    "n": "Blueport Acquisition Ltd - Class A Ordinary Shares"
  },
  {
    "s": "BPACU",
    "n": "Blueport Acquisition Ltd - Units"
  },
  {
    "s": "BPOP",
    "n": "Popular, Inc. - Common Stock"
  },
  {
    "s": "BPRN",
    "n": "Princeton Bancorp, Inc. - Common Stock"
  },
  {
    "s": "BQ",
    "n": "Boqii Holding Limited Class A Ordinary Shares"
  },
  {
    "s": "BR",
    "n": "Broadridge Financial Solutions, Inc. Common Stock"
  },
  {
    "s": "BRAG",
    "n": "Bragg Gaming Group Inc. - Common Shares"
  },
  {
    "s": "BRAI",
    "n": "Braiin Limited - Common Stock"
  },
  {
    "s": "BRBI",
    "n": "BRBI BR Partners S.A. - ADSs"
  },
  {
    "s": "BRBR",
    "n": "BellRing Brands, Inc. Common Stock "
  },
  {
    "s": "BRBS",
    "n": "Blue Ridge Bankshares, Inc. Common Stock"
  },
  {
    "s": "BRC",
    "n": "Brady Corporation Common Stock"
  },
  {
    "s": "BRCB",
    "n": "Black Rock Coffee Bar, Inc. - Class A Common Stock"
  },
  {
    "s": "BRCC",
    "n": "BRC Inc. Class A Common Stock"
  },
  {
    "s": "BREZ",
    "n": "Breeze Acquisition Corp. II - Ordinary Shares"
  },
  {
    "s": "BRFH",
    "n": "Barfresh Food Group Inc. - Common Stock"
  },
  {
    "s": "BRIA",
    "n": "BrilliA Inc Class A Ordinary Shares"
  },
  {
    "s": "BRID",
    "n": "Bridgford Foods Corporation - Common Stock"
  },
  {
    "s": "BRK-A",
    "n": "Berkshire Hathaway Inc. Common Stock"
  },
  {
    "s": "BRK-B",
    "n": "Berkshire Hathaway Inc. New Common Stock"
  },
  {
    "s": "BRKH",
    "n": "Burtech Acquisition Corp II - Class A Ordinary Shares"
  },
  {
    "s": "BRKHU",
    "n": "Burtech Acquisition Corp II - Units"
  },
  {
    "s": "BRKHW",
    "n": "Burtech Acquisition Corp II - Warrants"
  },
  {
    "s": "BRKR",
    "n": "Bruker Corporation - Common Stock"
  },
  {
    "s": "BRLS",
    "n": "Borealis Foods Inc. - Class A Common Shares"
  },
  {
    "s": "BRLT",
    "n": "Brilliant Earth Group, Inc. - Class A Common Stock"
  },
  {
    "s": "BRN",
    "n": "Barnwell Industries, Inc. Common Stock"
  },
  {
    "s": "BRNX",
    "n": "BrenX Ltd. - Ordinary Shares"
  },
  {
    "s": "BRO",
    "n": "Brown & Brown, Inc. Common Stock"
  },
  {
    "s": "BROS",
    "n": "Dutch Bros Inc. Class A Common Stock"
  },
  {
    "s": "BRRKU",
    "n": "Bluerock Acquisition Corp. II - Units"
  },
  {
    "s": "BRSL",
    "n": "Brightstar Lottery PLC Trading under the Legal Name to begin at the market open on July 21, 2025. Ordinary Shares"
  },
  {
    "s": "BRSP",
    "n": "BrightSpire Capital, Inc. Class A Common Stock"
  },
  {
    "s": "BRT",
    "n": "BRT Apartments Corp. (MD) Common Stock"
  },
  {
    "s": "BRTM",
    "n": "B&R Technology Merger Corp. - Class A Ordinary Shares"
  },
  {
    "s": "BRTMU",
    "n": "B&R Technology Merger Corp. - Units"
  },
  {
    "s": "BRTMW",
    "n": "B&R Technology Merger Corp. - Warrants"
  },
  {
    "s": "BRTX",
    "n": "BioRestorative Therapies, Inc. - Common Stock"
  },
  {
    "s": "BRUN",
    "n": "Boost Run Inc. - Class A Common Stock"
  },
  {
    "s": "BRVE",
    "n": "Braveheart Bio, Inc. - Common Stock"
  },
  {
    "s": "BRX",
    "n": "Brixmor Property Group Inc. Common Stock"
  },
  {
    "s": "BRZE",
    "n": "Braze, Inc. - Class A Common Stock"
  },
  {
    "s": "BSAA",
    "n": "BEST SPAC I Acquisition Corp. - Class A Ordinary Shares"
  },
  {
    "s": "BSAAU",
    "n": "BEST SPAC I Acquisition Corp. - Unit"
  },
  {
    "s": "BSAC",
    "n": "Banco Santander - Chile ADS"
  },
  {
    "s": "BSBK",
    "n": "Bogota Financial Corp. - Common Stock"
  },
  {
    "s": "BSBR",
    "n": "Banco Santander Brasil SA American Depositary Shares, each representing one unit"
  },
  {
    "s": "BSEM",
    "n": "BioStem Technologies, Inc. - Common Stock"
  },
  {
    "s": "BSET",
    "n": "Bassett Furniture Industries, Incorporated - Common Stock"
  },
  {
    "s": "BSIN",
    "n": "Big Sky Industrial Inc. - Common Stock"
  },
  {
    "s": "BSM",
    "n": "Black Stone Minerals, L.P. Common units representing limited partner interests"
  },
  {
    "s": "BSP",
    "n": "Bending Spoons S.p.A. - Ordinary Shares"
  },
  {
    "s": "BSRR",
    "n": "Sierra Bancorp - Common Stock"
  },
  {
    "s": "BST",
    "n": "BlackRock Science and Technology Trust Common Shares of Beneficial Interest"
  },
  {
    "s": "BSTZ",
    "n": "BlackRock Science and Technology Term Trust Common Shares of Beneficial Interest"
  },
  {
    "s": "BSVN",
    "n": "Bank7 Corp. - Common stock"
  },
  {
    "s": "BSX",
    "n": "Boston Scientific Corporation Common Stock"
  },
  {
    "s": "BSY",
    "n": "Bentley Systems, Incorporated - Class B Common Stock"
  },
  {
    "s": "BTBD",
    "n": "BT Brands, Inc. - Common Stock"
  },
  {
    "s": "BTBT",
    "n": "Bit Digital, Inc. - Ordinary Share"
  },
  {
    "s": "BTCS",
    "n": "BTCS Inc. - Common Stock"
  },
  {
    "s": "BTCT",
    "n": "BTC Digital Ltd. - Ordinary Shares"
  },
  {
    "s": "BTDR",
    "n": "Bitdeer Technologies Group - Ordinary Shares"
  },
  {
    "s": "BTE",
    "n": "Baytex Energy Corp Common Shares"
  },
  {
    "s": "BTG",
    "n": "B2Gold Corp Common shares (Canada)"
  },
  {
    "s": "BTGO",
    "n": "BitGo Holdings, Inc. Class A Common Stock"
  },
  {
    "s": "BTI",
    "n": "British American Tobacco  Industries, p.l.c. Common Stock ADR"
  },
  {
    "s": "BTLN",
    "n": "Brightline Interactive, Inc. - Common Stock"
  },
  {
    "s": "BTMD",
    "n": "Biote Corp. - Class A common stock"
  },
  {
    "s": "BTOC",
    "n": "Armlogi Holding Corp. - common stock"
  },
  {
    "s": "BTQ",
    "n": "BTQ Technologies Corp. - Common Stock"
  },
  {
    "s": "BTSG",
    "n": "BrightSpring Health Services, Inc. - Common Stock"
  },
  {
    "s": "BTSGU",
    "n": "BrightSpring Health Services, Inc. - Tangible Equity Unit"
  },
  {
    "s": "BTT",
    "n": "BlackRock Municipal 2030 Target Term Trust"
  },
  {
    "s": "BTTC",
    "n": "Black Titan Corp - Ordinary Shares"
  },
  {
    "s": "BTU",
    "n": "Peabody Energy Corporation Common Stock "
  },
  {
    "s": "BTX",
    "n": "BlackRock Technology and Private Equity Term Trust Common Shares of Beneficial Interest"
  },
  {
    "s": "BTZ",
    "n": "BlackRock Credit Allocation Income Trust"
  },
  {
    "s": "BUD",
    "n": "Anheuser-Busch Inbev SA Sponsored ADR (Belgium)"
  },
  {
    "s": "BUDA",
    "n": "Buda Juice, Inc. Common Stock"
  },
  {
    "s": "BUI",
    "n": "BlackRock Utility, Infrastructure & Power Opportunities Trust"
  },
  {
    "s": "BULL",
    "n": "Webull Corporation - Class A Ordinary Shares"
  },
  {
    "s": "BULLW",
    "n": "Webull Corporation - Warrants"
  },
  {
    "s": "BUR",
    "n": "Burford Capital Limited Ordinary Shares"
  },
  {
    "s": "BURL",
    "n": "Burlington Stores, Inc. Common Stock"
  },
  {
    "s": "BURU",
    "n": "Nuburu, Inc. Common Stock"
  },
  {
    "s": "BUSE",
    "n": "First Busey Corporation - Common Stock"
  },
  {
    "s": "BUUU",
    "n": "BUUU Group Limited - Class A Ordinary Share"
  },
  {
    "s": "BV",
    "n": "BrightView Holdings, Inc. Common Stock"
  },
  {
    "s": "BVC",
    "n": "BitVentures Limited - Ordinary Share"
  },
  {
    "s": "BVFL",
    "n": "BV Financial, Inc. - Common Stock"
  },
  {
    "s": "BVN",
    "n": "Buenaventura Mining Company Inc."
  },
  {
    "s": "BVS",
    "n": "Bioventus Inc. - Class A Common Stock"
  },
  {
    "s": "BW",
    "n": "Babcock & Wilcox Enterprises, Inc. Common Stock"
  },
  {
    "s": "BWA",
    "n": "BorgWarner Inc. Common Stock"
  },
  {
    "s": "BWAY",
    "n": "BrainsWay Ltd. - American Depositary Shares"
  },
  {
    "s": "BWB",
    "n": "Bridgewater Bancshares, Inc. - Common Stock"
  },
  {
    "s": "BWEN",
    "n": "Broadwind, Inc. - Common Stock"
  },
  {
    "s": "BWFG",
    "n": "Bankwell Financial Group, Inc. - Common Stock"
  },
  {
    "s": "BWIN",
    "n": "The Baldwin Insurance Group, Inc. - Class A Common Stock"
  },
  {
    "s": "BWIV",
    "n": "Blue Water Acquisition Corp. IV Class A Ordinary Shares"
  },
  {
    "s": "BWIV-W",
    "n": "Blue Water Acquisition Corp. IV Warrants entitling the holder to purchase one Class A ordinary share at a price of $11.50 per share"
  },
  {
    "s": "BWLP",
    "n": "BW LPG Limited Common Shares"
  },
  {
    "s": "BWMN",
    "n": "Bowman Consulting Group Ltd. - Common Stock"
  },
  {
    "s": "BWMX",
    "n": "Betterware de Mexico, S.A.P.I. de C.V. Ordinary Shares"
  },
  {
    "s": "BWXT",
    "n": "BWX Technologies, Inc. Common Stock"
  },
  {
    "s": "BX",
    "n": "Blackstone Inc. Common Stock"
  },
  {
    "s": "BXBL",
    "n": "BOXABL, Inc.  - Common stock"
  },
  {
    "s": "BXC",
    "n": "Bluelinx Holdings Inc. Common Stock"
  },
  {
    "s": "BXDC",
    "n": "Blackstone Digital Infrastructure Trust Inc. Common Stock"
  },
  {
    "s": "BXMT",
    "n": "Blackstone Mortgage Trust, Inc. Common Stock"
  },
  {
    "s": "BXP",
    "n": "BXP, Inc. Common Stock"
  },
  {
    "s": "BY",
    "n": "Byline Bancorp, Inc. Common Stock"
  },
  {
    "s": "BYAH",
    "n": "Park Ha Biological Technology Co., Ltd. - Class A Ordinary Shares"
  },
  {
    "s": "BYD",
    "n": "Boyd Gaming Corporation Common Stock"
  },
  {
    "s": "BYFC",
    "n": "Broadway Financial Corporation - Class A Common Stock"
  },
  {
    "s": "BYND",
    "n": "Beyond Meat, Inc. - Common stock"
  },
  {
    "s": "BYRN",
    "n": "Byrna Technologies, Inc. - Common Stock"
  },
  {
    "s": "BYSI",
    "n": "BeyondSpring, Inc. - Ordinary Shares"
  },
  {
    "s": "BZ",
    "n": "KANZHUN LIMITED - American Depository Shares"
  },
  {
    "s": "BZAI",
    "n": "Blaize Holdings, Inc. - Common Stock"
  },
  {
    "s": "BZFD",
    "n": "BuzzFeed, Inc. - Class A Common Stock"
  },
  {
    "s": "BZH",
    "n": "Beazer Homes USA, Inc. Common Stock"
  },
  {
    "s": "BZUN",
    "n": "Baozun Inc. - American Depositary Shares"
  },
  {
    "s": "C",
    "n": "Citigroup, Inc. Common Stock"
  },
  {
    "s": "CAAP",
    "n": "Corporacion America Airports SA Common Shares"
  },
  {
    "s": "CAAS",
    "n": "China Automotive Systems, Inc. - Ordinary Share"
  },
  {
    "s": "CABA",
    "n": "Cabaletta Bio, Inc. - Common Stock"
  },
  {
    "s": "CABO",
    "n": "Cable One, Inc. Common Stock"
  },
  {
    "s": "CABR",
    "n": "Caring Brands, Inc. - Common Stock"
  },
  {
    "s": "CAC",
    "n": "Camden National Corporation - Common Stock"
  },
  {
    "s": "CACC",
    "n": "Credit Acceptance Corporation - Common Stock"
  },
  {
    "s": "CACI",
    "n": "CACI International, Inc. Class A Common Stock"
  },
  {
    "s": "CADL",
    "n": "Candel Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "CAE",
    "n": "CAE Inc - Common Shares"
  },
  {
    "s": "CAES",
    "n": "Cantor Equity Partners VII, Inc. - Class A Ordinary Shares"
  },
  {
    "s": "CAG",
    "n": "ConAgra Brands, Inc. Common Stock"
  },
  {
    "s": "CAH",
    "n": "Cardinal Health, Inc. Common Stock"
  },
  {
    "s": "CAI",
    "n": "Caris Life Sciences, Inc. - Common Stock"
  },
  {
    "s": "CAII",
    "n": "Collective Acquisition Corp. II - Class A Ordinary Shares"
  },
  {
    "s": "CAIIU",
    "n": "Collective Acquisition Corp. II - Units"
  },
  {
    "s": "CAIIW",
    "n": "Collective Acquisition Corp. II - Warrants"
  },
  {
    "s": "CAKE",
    "n": "The Cheesecake Factory Incorporated - Common Stock"
  },
  {
    "s": "CAL",
    "n": "Caleres, Inc. Common Stock"
  },
  {
    "s": "CALC",
    "n": "CalciMedica, Inc. - Common Stock"
  },
  {
    "s": "CALM",
    "n": "Cal-Maine Foods, Inc. - Common Stock"
  },
  {
    "s": "CALX",
    "n": "Calix, Inc Common Stock"
  },
  {
    "s": "CALY",
    "n": "Callaway Golf Company Common Stock"
  },
  {
    "s": "CAMP",
    "n": "CAMP4 Therapeutics Corporation - Common Stock"
  },
  {
    "s": "CAMT",
    "n": "Camtek Ltd. - Ordinary Shares"
  },
  {
    "s": "CAN",
    "n": "Canaan Inc. - American Depositary Shares"
  },
  {
    "s": "CANF",
    "n": "Can-Fite Biopharma Ltd American Depositary Shares, each representing two (2) Ordinary Shares"
  },
  {
    "s": "CANG",
    "n": "Cango Inc. Class A Ordinary Shares"
  },
  {
    "s": "CAPN",
    "n": "Cayson Acquisition Corp - Ordinary Shares"
  },
  {
    "s": "CAPNR",
    "n": "Cayson Acquisition Corp - Right"
  },
  {
    "s": "CAPNU",
    "n": "Cayson Acquisition Corp - Units"
  },
  {
    "s": "CAPR",
    "n": "Capricor Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "CAPS",
    "n": "Capstone Holding Corp. - Common Stock"
  },
  {
    "s": "CAQ",
    "n": "Cambridge Acquisition Corp. - Class A Ordinary Shares"
  },
  {
    "s": "CAQUU",
    "n": "Cambridge Acquisition Corp. - Unit"
  },
  {
    "s": "CAQUW",
    "n": "Cambridge Acquisition Corp. - Warrants"
  },
  {
    "s": "CAR",
    "n": "Avis Budget Group, Inc. - Common Stock"
  },
  {
    "s": "CARE",
    "n": "Carter Bankshares, Inc. - Common Stock"
  },
  {
    "s": "CARG",
    "n": "CarGurus, Inc. - Class A Common Stock"
  },
  {
    "s": "CARL",
    "n": "Carlsmed, Inc. - Common Stock"
  },
  {
    "s": "CARR",
    "n": "Carrier Global Corporation Common Stock "
  },
  {
    "s": "CARS",
    "n": "Cars.com Inc. Common Stock "
  },
  {
    "s": "CART",
    "n": "Maplebear Inc. - Common Stock"
  },
  {
    "s": "CASH",
    "n": "Pathward Financial, Inc. - Common Stock"
  },
  {
    "s": "CASS",
    "n": "Cass Information Systems, Inc - Common Stock"
  },
  {
    "s": "CAST",
    "n": "FreeCast, Inc. - Class A common stock"
  },
  {
    "s": "CASY",
    "n": "Caseys General Stores, Inc. - Common Stock"
  },
  {
    "s": "CAT",
    "n": "Caterpillar, Inc. Common Stock"
  },
  {
    "s": "CATL",
    "n": "Catalyst Acquisition Corp. - Class A Ordinary Share"
  },
  {
    "s": "CATLU",
    "n": "Catalyst Acquisition Corp. - Units"
  },
  {
    "s": "CATO",
    "n": "Cato Corporation (The) Class A Common Stock"
  },
  {
    "s": "CATX",
    "n": "Perspective Therapeutics, Inc. Common Stock"
  },
  {
    "s": "CATY",
    "n": "Cathay General Bancorp - Common Stock"
  },
  {
    "s": "CAVA",
    "n": "CAVA Group, Inc. Common Stock"
  },
  {
    "s": "CB",
    "n": "Chubb Limited  Common Stock"
  },
  {
    "s": "CBAN",
    "n": "Colony Bankcorp, Inc. Common Stock"
  },
  {
    "s": "CBAT",
    "n": "CBAK Energy Technology Limited - Ordinary Shares"
  },
  {
    "s": "CBC",
    "n": "Central Bancompany, Inc. - Class A Common Stock"
  },
  {
    "s": "CBFV",
    "n": "CB Financial Services, Inc. - Common Stock"
  },
  {
    "s": "CBIO",
    "n": "Crescent Biopharma, Inc. - Common Stock"
  },
  {
    "s": "CBK",
    "n": "Commercial Bancgroup, Inc. - Common Stock"
  },
  {
    "s": "CBL",
    "n": "CBL & Associates Properties, Inc. Common Stock"
  },
  {
    "s": "CBLL",
    "n": "CeriBell, Inc. - Common Stock"
  },
  {
    "s": "CBNA",
    "n": "Chain Bridge Bancorp, Inc. Class A Common Stock"
  },
  {
    "s": "CBNK",
    "n": "Capital Bancorp, Inc. - Common Stock"
  },
  {
    "s": "CBOE",
    "n": "Cboe Global Markets, Inc. Common Stock"
  },
  {
    "s": "CBRE",
    "n": "CBRE Group Inc Common Stock Class A"
  },
  {
    "s": "CBRL",
    "n": "Cracker Barrel Old Country Store, Inc. - Common Stock"
  },
  {
    "s": "CBRS",
    "n": "Cerebras Systems Inc. - Class A Common Stock"
  },
  {
    "s": "CBSH",
    "n": "Commerce Bancshares, Inc. - Common Stock"
  },
  {
    "s": "CBT",
    "n": "Cabot Corporation Common Stock"
  },
  {
    "s": "CBU",
    "n": "Community Financial System, Inc. Common Stock"
  },
  {
    "s": "CBUS",
    "n": "Cibus, Inc. - Class A Common Stock"
  },
  {
    "s": "CBZ",
    "n": "CBIZ, Inc. Common Stock"
  },
  {
    "s": "CC",
    "n": "Chemours Company (The) Common Stock"
  },
  {
    "s": "CCAP",
    "n": "Crescent Capital BDC, Inc. - Common Stock"
  },
  {
    "s": "CCAQ",
    "n": "Collective Acquisition Corp. - Class A ordinary shares"
  },
  {
    "s": "CCAQU",
    "n": "Collective Acquisition Corp. - Units"
  },
  {
    "s": "CCAQW",
    "n": "Collective Acquisition Corp. - Warrants"
  },
  {
    "s": "CCB",
    "n": "Coastal Financial Corporation - Common Stock"
  },
  {
    "s": "CCBG",
    "n": "Capital City Bank Group - Common Stock"
  },
  {
    "s": "CCC",
    "n": "CCC Intelligent Solutions Holdings Inc. - Common Stock"
  },
  {
    "s": "CCCC",
    "n": "C4 Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "CCCT",
    "n": "Columbus Circle Capital Corp III - Class A Ordinary Shares"
  },
  {
    "s": "CCCTU",
    "n": "Columbus Circle Capital Corp III - Units"
  },
  {
    "s": "CCCTW",
    "n": "Columbus Circle Capital Corp III - Warrants"
  },
  {
    "s": "CCEC",
    "n": "Capital Clean Energy Carriers Corp. - Common Share"
  },
  {
    "s": "CCEL",
    "n": "Cryo-Cell International, Inc. Common Stock"
  },
  {
    "s": "CCEP",
    "n": "Coca-Cola Europacific Partners plc - Ordinary Shares"
  },
  {
    "s": "CCG",
    "n": "Cheche Group Inc. - Class A Ordinary Shares"
  },
  {
    "s": "CCHH",
    "n": "CCH Holdings Ltd - Class A Ordinary Shares"
  },
  {
    "s": "CCI",
    "n": "Crown Castle Inc. Common Stock"
  },
  {
    "s": "CCII",
    "n": "Cohen Circle Acquisition Corp. II - Class A Ordinary Shares"
  },
  {
    "s": "CCIIU",
    "n": "Cohen Circle Acquisition Corp. II - Unit"
  },
  {
    "s": "CCJ",
    "n": "Cameco Corporation Common Stock"
  },
  {
    "s": "CCK",
    "n": "Crown Holdings, Inc."
  },
  {
    "s": "CCL",
    "n": "Carnival Corporation Ltd. Common Shares"
  },
  {
    "s": "CCLD",
    "n": "CareCloud, Inc. - Common Stock"
  },
  {
    "s": "CCM",
    "n": "Concord Medical Services Holdings Limited American Depositary Shares (Each represents thirty (30) Class A ordinary shares)"
  },
  {
    "s": "CCNE",
    "n": "CNB Financial Corporation - Common Stock"
  },
  {
    "s": "CCO",
    "n": "Clear Channel Outdoor Holdings, Inc. Common Stock"
  },
  {
    "s": "CCOI",
    "n": "Cogent Communications Holdings, Inc. - Common Stock"
  },
  {
    "s": "CCS",
    "n": "Century Communities, Inc. Common Stock"
  },
  {
    "s": "CCSI",
    "n": "Consensus Cloud Solutions, Inc. - Common Stock"
  },
  {
    "s": "CCTG",
    "n": "CCSC Technology International Holdings Limited - Class A Ordinary Shares"
  },
  {
    "s": "CCU",
    "n": "Compania Cervecerias Unidas, S.A. Common Stock"
  },
  {
    "s": "CCXI",
    "n": "Churchill Capital Corp XI - Class A Ordinary Shares"
  },
  {
    "s": "CCXIU",
    "n": "Churchill Capital Corp XI - Units"
  },
  {
    "s": "CCXIW",
    "n": "Churchill Capital Corp XI - Warrants"
  },
  {
    "s": "CCZ",
    "n": "Comcast Holdings ZONES"
  },
  {
    "s": "CD",
    "n": "Chaince Digital Holdings Inc. - American Ordinary Shares"
  },
  {
    "s": "CDE",
    "n": "Coeur Mining, Inc. Common Stock"
  },
  {
    "s": "CDIO",
    "n": "Cardio Diagnostics Holdings Inc. - Common stock"
  },
  {
    "s": "CDLR",
    "n": "Cadeler A/S American Depositary Share (each representing four (4) Ordinary Shares)"
  },
  {
    "s": "CDLX",
    "n": "Cardlytics, Inc. - Common Stock"
  },
  {
    "s": "CDNA",
    "n": "CareDx, Inc. - Common Stock"
  },
  {
    "s": "CDNL",
    "n": "Cardinal Infrastructure Group Inc. - Class A Common Stock"
  },
  {
    "s": "CDNS",
    "n": "Cadence Design Systems, Inc. - Common Stock"
  },
  {
    "s": "CDP",
    "n": "COPT Defense Properties Common Shares of Beneficial Interest"
  },
  {
    "s": "CDRE",
    "n": "Cadre Holdings, Inc. Common Stock"
  },
  {
    "s": "CDRO",
    "n": "Codere Online Luxembourg, S.A. - Ordinary Shares"
  },
  {
    "s": "CDROW",
    "n": "Codere Online Luxembourg, S.A. - Warrants"
  },
  {
    "s": "CDT",
    "n": "CDT Equity Inc. - Common Stock"
  },
  {
    "s": "CDTG",
    "n": "CDT Environmental Technology Investment Holdings Limited - ordinary shares"
  },
  {
    "s": "CDW",
    "n": "CDW Corporation - Common Stock"
  },
  {
    "s": "CDXS",
    "n": "Codexis, Inc. - Common Stock"
  },
  {
    "s": "CDZI",
    "n": "Cadiz, Inc. - Common Stock"
  },
  {
    "s": "CDZIP",
    "n": "Cadiz, Inc. - Depositary Shares"
  },
  {
    "s": "CE",
    "n": "Celanese Corporation Common Stock"
  },
  {
    "s": "CECO",
    "n": "CECO Environmental Corp. - Common Stock"
  },
  {
    "s": "CEG",
    "n": "Constellation Energy Corporation - Common Stock When-Issued"
  },
  {
    "s": "CELC",
    "n": "Celcuity Inc. - Common Stock"
  },
  {
    "s": "CELH",
    "n": "Celsius Holdings, Inc. - Common Stock"
  },
  {
    "s": "CELU",
    "n": "Celularity Inc. - Class A Common Stock"
  },
  {
    "s": "CELZ",
    "n": "Creative Medical Technology Holdings, Inc. - Common Stock"
  },
  {
    "s": "CENN",
    "n": "Cenntro Inc. - Common Stock"
  },
  {
    "s": "CENT",
    "n": "Central Garden & Pet Company - Common Stock"
  },
  {
    "s": "CENTA",
    "n": "Central Garden & Pet Company - Class A Common Stock Nonvoting"
  },
  {
    "s": "CENX",
    "n": "Century Aluminum Company - Common Stock"
  },
  {
    "s": "CEPF",
    "n": "Cantor Equity Partners IV, Inc. - Class A Ordinary Shares"
  },
  {
    "s": "CEPL",
    "n": "Capstone Energy Plus, Inc. - Common Stock"
  },
  {
    "s": "CEPO",
    "n": "Cantor Equity Partners I, Inc. - Class A Ordinary Shares"
  },
  {
    "s": "CEPS",
    "n": "Cantor Equity Partners VI, Inc. - Class A Ordinary Shares"
  },
  {
    "s": "CEPU",
    "n": "Central Puerto S.A. American Depositary Shares (each represents ten Common Shares)"
  },
  {
    "s": "CEPV",
    "n": "Cantor Equity Partners V, Inc. - Class A Ordinary Shares"
  },
  {
    "s": "CERS",
    "n": "Cerus Corporation - Common Stock"
  },
  {
    "s": "CERT",
    "n": "Certara, Inc. - Common Stock"
  },
  {
    "s": "CET",
    "n": "Central Securities Corporation Common Stock"
  },
  {
    "s": "CETX",
    "n": "Cemtrex Inc. - Common Stock"
  },
  {
    "s": "CETY",
    "n": "Clean Energy Technologies, Inc. - Common Stock"
  },
  {
    "s": "CEV",
    "n": "Eaton Vance California Municipal Income Trust Shares of Beneficial Interest"
  },
  {
    "s": "CEVA",
    "n": "CEVA, Inc. - Common Stock"
  },
  {
    "s": "CF",
    "n": "CF Industries Holdings, Inc. Common Stock"
  },
  {
    "s": "CFBK",
    "n": "CF Bankshares Inc. - Common Stock"
  },
  {
    "s": "CFFI",
    "n": "C&F Financial Corporation - Common Stock"
  },
  {
    "s": "CFFN",
    "n": "Capitol Federal Financial, Inc. - Common Stock"
  },
  {
    "s": "CFG",
    "n": "Citizens Financial Group, Inc. Common Stock"
  },
  {
    "s": "CFR",
    "n": "Cullen/Frost Bankers, Inc. Common Stock"
  },
  {
    "s": "CG",
    "n": "The Carlyle Group Inc. - Common Stock"
  },
  {
    "s": "CGABL",
    "n": "The Carlyle Group Inc. - 4.625% Subordinated Notes due 2061"
  },
  {
    "s": "CGAU",
    "n": "Centerra Gold Inc. Common Shares"
  },
  {
    "s": "CGC",
    "n": "Canopy Growth Corporation - Common Shares"
  },
  {
    "s": "CGCF",
    "n": "Cartesian Growth Corporation IV - Class A Ordinary Shares"
  },
  {
    "s": "CGCFU",
    "n": "Cartesian Growth Corporation IV - Units"
  },
  {
    "s": "CGCFW",
    "n": "Cartesian Growth Corporation IV - Warrants"
  },
  {
    "s": "CGEM",
    "n": "Cullinan Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "CGEN",
    "n": "Compugen Ltd. - Ordinary Shares"
  },
  {
    "s": "CGNT",
    "n": "Cognyte Software Ltd. - Ordinary Shares"
  },
  {
    "s": "CGNX",
    "n": "Cognex Corporation - Common Stock"
  },
  {
    "s": "CGON",
    "n": "CG Oncology, Inc. - Common stock"
  },
  {
    "s": "CGTL",
    "n": "Creative Global Technology Holdings Limited - Class A Ordinary Shares"
  },
  {
    "s": "CGTX",
    "n": "Cognition Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "CHA",
    "n": "Chagee Holdings Limited - American Depositary Shares, each representing 1 Class A ordinary share"
  },
  {
    "s": "CHAI",
    "n": "Core AI Holdings, Inc. - Common Shares"
  },
  {
    "s": "CHAR",
    "n": "Charlton Aria Acquisition Corporation - Class A Ordinary Shares"
  },
  {
    "s": "CHARU",
    "n": "Charlton Aria Acquisition Corporation - Units"
  },
  {
    "s": "CHCI",
    "n": "Comstock Holding Companies, Inc. - Class A Common Stock"
  },
  {
    "s": "CHCO",
    "n": "City Holding Company - Common Stock"
  },
  {
    "s": "CHCT",
    "n": "Community Healthcare Trust Incorporated Common Stock"
  },
  {
    "s": "CHD",
    "n": "Church & Dwight Company, Inc. Common Stock"
  },
  {
    "s": "CHDN",
    "n": "Churchill Downs, Incorporated - Common Stock"
  },
  {
    "s": "CHE",
    "n": "Chemed Corp"
  },
  {
    "s": "CHEC",
    "n": "Chenghe Acquisition III Co. - Class A Ordinary Shares"
  },
  {
    "s": "CHECU",
    "n": "Chenghe Acquisition III Co. - Units"
  },
  {
    "s": "CHECW",
    "n": "Chenghe Acquisition III Co. - Warrants"
  },
  {
    "s": "CHEF",
    "n": "The Chefs' Warehouse, Inc. - Common Stock"
  },
  {
    "s": "CHGA",
    "n": "Change Agents Corporation  - Common Stock"
  },
  {
    "s": "CHGG",
    "n": "Chegg, Inc. Common Stock"
  },
  {
    "s": "CHH",
    "n": "Choice Hotels International, Inc. Common Stock"
  },
  {
    "s": "CHKP",
    "n": "Check Point Software Technologies Ltd. - Ordinary Shares"
  },
  {
    "s": "CHMG",
    "n": "Chemung Financial Corp  - Common Stock"
  },
  {
    "s": "CHMI",
    "n": "Cherry Hill Mortgage Investment Corporation Common Stock"
  },
  {
    "s": "CHNR",
    "n": "China Natural Resources, Inc. - Common Shares"
  },
  {
    "s": "CHOW",
    "n": "ChowChow Cloud International Holdings Limited Ordinary Shares"
  },
  {
    "s": "CHPG",
    "n": "ChampionsGate Acquisition Corporation - Class A Ordinary Share"
  },
  {
    "s": "CHPGU",
    "n": "ChampionsGate Acquisition Corporation - Unit"
  },
  {
    "s": "CHPT",
    "n": "ChargePoint Holdings, Inc. Common Stock"
  },
  {
    "s": "CHR",
    "n": "Cheer Holding, Inc.  - Class A Ordinary Share"
  },
  {
    "s": "CHRD",
    "n": "Chord Energy Corporation - Common Stock"
  },
  {
    "s": "CHRN",
    "n": "ChronoScale Holdings Corporation - Common Stock"
  },
  {
    "s": "CHRS",
    "n": "Coherus Oncology, Inc. - Common Stock"
  },
  {
    "s": "CHRW",
    "n": "C.H. Robinson Worldwide, Inc. - Common Stock"
  },
  {
    "s": "CHSN",
    "n": "Chanson International Holding - Class A Ordinary Shares"
  },
  {
    "s": "CHT",
    "n": "Chunghwa Telecom Co., Ltd."
  },
  {
    "s": "CHTR",
    "n": "Charter Communications, Inc. - Class A Common Stock"
  },
  {
    "s": "CHWM",
    "n": "Chilwa Minerals Limited - American Depository Shares"
  },
  {
    "s": "CHWY",
    "n": "Chewy, Inc. Class A Common Stock"
  },
  {
    "s": "CHYM",
    "n": "Chime Financial, Inc. - Class A Common Stock"
  },
  {
    "s": "CI",
    "n": "The Cigna Group Common Stock"
  },
  {
    "s": "CIA",
    "n": "Citizens, Inc. Class A Common Stock ($1.00 Par)"
  },
  {
    "s": "CICB",
    "n": "CION Investment Corporation 7.50% Notes due 2029"
  },
  {
    "s": "CICC",
    "n": "CION Investment Corporation 7.50% Notes due 2031"
  },
  {
    "s": "CIEN",
    "n": "Ciena Corporation Common Stock"
  },
  {
    "s": "CIFR",
    "n": "Cipher Digital Inc. - Common Stock"
  },
  {
    "s": "CIG",
    "n": "Comp En De Mn Cemig ADS American Depositary Shares"
  },
  {
    "s": "CIG-C",
    "n": "Comp En De Mn Cemig ADS American Depositary Receipts"
  },
  {
    "s": "CIGI",
    "n": "Colliers International Group Inc.  - Subordinate Voting Shares"
  },
  {
    "s": "CIGL",
    "n": "Concorde International Group Ltd - Class A Ordinary Shares"
  },
  {
    "s": "CIIT",
    "n": "Tianci International, Inc. - Common Stock"
  },
  {
    "s": "CIM",
    "n": "Chimera Investment Corporation Common Stock"
  },
  {
    "s": "CIMN",
    "n": "Chimera Investment Corporation 9.000% Senior Notes due 2029"
  },
  {
    "s": "CIMO",
    "n": "Chimera Investment Corporation 9.250% Senior Notes due 2029"
  },
  {
    "s": "CIMP",
    "n": "Chimera Investment Corporation 8.875% Senior Notes due 2030"
  },
  {
    "s": "CINF",
    "n": "Cincinnati Financial Corporation - Common Stock"
  },
  {
    "s": "CING",
    "n": "Cingulate Inc. - Common Stock"
  },
  {
    "s": "CINGW",
    "n": "Cingulate Inc. - Warrants"
  },
  {
    "s": "CINT",
    "n": "CI&T Inc Class A Common Shares"
  },
  {
    "s": "CION",
    "n": "CION Investment Corporation Common Stock"
  },
  {
    "s": "CIRC",
    "n": "Circle8 Group, Inc. - Common Stock"
  },
  {
    "s": "CISO",
    "n": "CISO Global, Inc. - Common Stock"
  },
  {
    "s": "CISS",
    "n": "C3is Inc. - Common Stock"
  },
  {
    "s": "CITR",
    "n": "CitroTech Inc. Common Stock"
  },
  {
    "s": "CIVB",
    "n": "Civista Bancshares, Inc.  - Common Stock"
  },
  {
    "s": "CIX",
    "n": "CompX International Inc. Common Stock"
  },
  {
    "s": "CJMB",
    "n": "Callan JMB Inc. - Common Stock"
  },
  {
    "s": "CKX",
    "n": "CKX Lands, Inc. Common Stock"
  },
  {
    "s": "CL",
    "n": "Colgate-Palmolive Company Common Stock"
  },
  {
    "s": "CLAR",
    "n": "Clarus Corporation - Common Stock"
  },
  {
    "s": "CLB",
    "n": "Core Laboratories Inc. Common Stock"
  },
  {
    "s": "CLBK",
    "n": "Columbia Financial, Inc. - Common Stock"
  },
  {
    "s": "CLBR",
    "n": "Colombier Acquisition Corp. III Class A Ordinary Shares"
  },
  {
    "s": "CLBT",
    "n": "Cellebrite DI Ltd. - Ordinary Shares"
  },
  {
    "s": "CLDI",
    "n": "Calidi Biotherapeutics, Inc. Common Stock"
  },
  {
    "s": "CLDX",
    "n": "Celldex Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "CLF",
    "n": "Cleveland-Cliffs Inc. Common Stock"
  },
  {
    "s": "CLFD",
    "n": "Clearfield, Inc. - Common Stock"
  },
  {
    "s": "CLGN",
    "n": "CollPlant Biotechnologies Ltd. - Ordinary Shares"
  },
  {
    "s": "CLH",
    "n": "Clean Harbors, Inc. Common Stock"
  },
  {
    "s": "CLIK",
    "n": "Click Holdings Limited - Ordinary Share"
  },
  {
    "s": "CLIR",
    "n": "ClearSign Technologies Corporation - Common Stock"
  },
  {
    "s": "CLLS",
    "n": "Cellectis S.A. - American Depositary Shares"
  },
  {
    "s": "CLMB",
    "n": "Climb Global Solutions, Inc. - Common Stock"
  },
  {
    "s": "CLMT",
    "n": "Calumet, Inc - Common Stock"
  },
  {
    "s": "CLNE",
    "n": "Clean Energy Fuels Corp. - Common Stock"
  },
  {
    "s": "CLNN",
    "n": "Clene Inc. - Common Stock"
  },
  {
    "s": "CLOV",
    "n": "Clover Health Investments, Corp.  - Class A Common stock"
  },
  {
    "s": "CLPR",
    "n": "Clipper Realty Inc. Common Stock"
  },
  {
    "s": "CLPS",
    "n": "CLPS Incorporation - Common Stock"
  },
  {
    "s": "CLPT",
    "n": "ClearPoint Neuro Inc. - Common Stock"
  },
  {
    "s": "CLRB",
    "n": "Cellectar Biosciences, Inc. - Common Stock"
  },
  {
    "s": "CLRO",
    "n": "ClearOne, Inc. - Common Stock"
  },
  {
    "s": "CLS",
    "n": "Celestica, Inc. Common Stock"
  },
  {
    "s": "CLSK",
    "n": "CleanSpark, Inc. - Common Stock"
  },
  {
    "s": "CLST",
    "n": "Catalyst Bancorp, Inc. - common stock"
  },
  {
    "s": "CLVT",
    "n": "Clarivate Plc Ordinary Shares"
  },
  {
    "s": "CLW",
    "n": "Clearwater Paper Corporation Common Stock"
  },
  {
    "s": "CLWT",
    "n": "Euro Tech Holdings Company Limited - Ordinary Shares"
  },
  {
    "s": "CLX",
    "n": "Clorox Company (The) Common Stock"
  },
  {
    "s": "CLYM",
    "n": "Climb Bio, Inc. - Common Stock"
  },
  {
    "s": "CM",
    "n": "Canadian Imperial Bank of Commerce Common Stock"
  },
  {
    "s": "CMBT",
    "n": "CMB.TECH NV Ordinary Shares"
  },
  {
    "s": "CMC",
    "n": "Commercial Metals Company Common Stock"
  },
  {
    "s": "CMCL",
    "n": "Caledonia Mining Corporation Plc Common Shares"
  },
  {
    "s": "CMCM",
    "n": "Cheetah Mobile Inc. American Depositary Shares, each representing fifty (50) Class A Ordinary Shares"
  },
  {
    "s": "CMCO",
    "n": "Columbus McKinnon Corporation - Common Stock"
  },
  {
    "s": "CMCSA",
    "n": "Comcast Corporation - Class A Common Stock"
  },
  {
    "s": "CMCT",
    "n": "Creative Media  - Common Stock"
  },
  {
    "s": "CMDB",
    "n": "Costamare Bulkers Holdings Limited Common Stock"
  },
  {
    "s": "CME",
    "n": "CME Group Inc. - Class A Common Stock"
  },
  {
    "s": "CMG",
    "n": "Chipotle Mexican Grill, Inc. Common Stock"
  },
  {
    "s": "CMI",
    "n": "Cummins Inc. Common Stock"
  },
  {
    "s": "CMMB",
    "n": "Chemomab Therapeutics Ltd.  - American Depositary Shares"
  },
  {
    "s": "CMND",
    "n": "Clearmind Medicine Inc. - Common Shares"
  },
  {
    "s": "CMP",
    "n": "Compass Minerals Intl Inc Common Stock"
  },
  {
    "s": "CMPR",
    "n": "Cimpress plc - Ordinary Shares"
  },
  {
    "s": "CMPS",
    "n": "COMPASS Pathways Plc - American Depository Shares"
  },
  {
    "s": "CMPX",
    "n": "Compass Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "CMRC",
    "n": "Commerce.com, Inc. - Series 1 Common Stock"
  },
  {
    "s": "CMRE",
    "n": "Costamare Inc. Common Stock $0.0001 par value"
  },
  {
    "s": "CMS",
    "n": "CMS Energy Corporation Common Stock"
  },
  {
    "s": "CMSA",
    "n": "CMS Energy Corporation 5.625% Junior Subordinated Notes due 2078"
  },
  {
    "s": "CMSC",
    "n": "CMS Energy Corporation 5.875% Junior Subordinated Notes due 2078"
  },
  {
    "s": "CMSD",
    "n": "CMS Energy Corporation 5.875% Junior Subordinated Notes due 2079"
  },
  {
    "s": "CMT",
    "n": "Core Molding Technologies Inc Common Stock"
  },
  {
    "s": "CMTG",
    "n": "Claros Mortgage Trust, Inc. Common Stock"
  },
  {
    "s": "CMTL",
    "n": "Comtech Telecommunications Corp. - Common Stock"
  },
  {
    "s": "CMTV",
    "n": "Community Bancorp.  - Common stock"
  },
  {
    "s": "CNA",
    "n": "CNA Financial Corporation Common Stock"
  },
  {
    "s": "CNC",
    "n": "Centene Corporation Common Stock"
  },
  {
    "s": "CNCK",
    "n": "Coincheck Group N.V. - Ordinary Shares"
  },
  {
    "s": "CNCKW",
    "n": "Coincheck Group N.V. - Warrants"
  },
  {
    "s": "CNDT",
    "n": "Conduent Incorporated - Common Stock"
  },
  {
    "s": "CNET",
    "n": "ZW Data Action Technologies Inc. - Common Stock"
  },
  {
    "s": "CNEY",
    "n": "CN Energy Group Inc. - Class A Ordinary Shares"
  },
  {
    "s": "CNF",
    "n": "CNFinance Holdings Limited American Depositary Shares, each representing two hundred (200) Ordinary Shares"
  },
  {
    "s": "CNH",
    "n": "CNH Industrial N.V. Common Shares"
  },
  {
    "s": "CNI",
    "n": "Canadian National Railway Company Common Stock"
  },
  {
    "s": "CNK",
    "n": "Cinemark Holdings Inc Cinemark Holdings, Inc. Common Stock"
  },
  {
    "s": "CNL",
    "n": "Collective Mining Ltd. - Common Stock"
  },
  {
    "s": "CNM",
    "n": "Core & Main, Inc. Class A Common Stock"
  },
  {
    "s": "CNMD",
    "n": "CONMED Corporation Common Stock"
  },
  {
    "s": "CNNE",
    "n": "Cannae Holdings, Inc. Common Stock"
  },
  {
    "s": "CNO",
    "n": "CNO Financial Group, Inc. Common Stock"
  },
  {
    "s": "CNOB",
    "n": "ConnectOne Bancorp, Inc. - Common Stock"
  },
  {
    "s": "CNP",
    "n": "CenterPoint Energy, Inc (Holding Co) Common Stock"
  },
  {
    "s": "CNQ",
    "n": "Canadian Natural Resources Limited Common Stock"
  },
  {
    "s": "CNR",
    "n": "Core Natural Resources, Inc. Common Stock"
  },
  {
    "s": "CNS",
    "n": "Cohen & Steers Inc Common Stock"
  },
  {
    "s": "CNSP",
    "n": "CNS Pharmaceuticals, Inc. - Common Stock"
  },
  {
    "s": "CNSY",
    "n": "Cerenome, Inc. - Common Stock"
  },
  {
    "s": "CNTB",
    "n": "Connect Biopharma Holdings Limited - Ordinary Shares"
  },
  {
    "s": "CNTN",
    "n": "Canton Strategic Holdings, Inc. - Common Stock"
  },
  {
    "s": "CNTX",
    "n": "Context Therapeutics Inc. - Common Stock"
  },
  {
    "s": "CNTY",
    "n": "Century Casinos, Inc. - Common Stock"
  },
  {
    "s": "CNVS",
    "n": "Cineverse Corp. - Class A Common Stock"
  },
  {
    "s": "CNX",
    "n": "CNX Resources Corporation Common Stock"
  },
  {
    "s": "CNXC",
    "n": "Concentrix Corporation - Common Stock"
  },
  {
    "s": "CNXN",
    "n": "PC Connection, Inc. - Common Stock"
  },
  {
    "s": "CNXU",
    "n": "Conexeu Sciences Inc. - Common Stock"
  },
  {
    "s": "COAG",
    "n": "Hemab Therapeutics Holdings, Inc. - Common Stock"
  },
  {
    "s": "COCH",
    "n": "Envoy Medical, Inc. - Class A Common Stock"
  },
  {
    "s": "COCO",
    "n": "The Vita Coco Company, Inc. - Common Stock"
  },
  {
    "s": "COCP",
    "n": "Cocrystal Pharma, Inc. - Common Stock"
  },
  {
    "s": "CODA",
    "n": "Coda Octopus Group, Inc. - Common stock"
  },
  {
    "s": "CODI",
    "n": "D/B/A Compass Diversified Holdings Shares of Beneficial Interest"
  },
  {
    "s": "CODX",
    "n": "Co-Diagnostics, Inc. - Common Stock"
  },
  {
    "s": "COE",
    "n": "51Talk Online Education Group American depositary shares, each representing 60 Class A ordinary shares"
  },
  {
    "s": "COF",
    "n": "Capital One Financial Corporation Common Stock"
  },
  {
    "s": "COFS",
    "n": "ChoiceOne Financial Services, Inc. - Common Stock"
  },
  {
    "s": "COGT",
    "n": "Cogent Biosciences, Inc. - Common Stock"
  },
  {
    "s": "COHN",
    "n": "Cohen & Company Inc."
  },
  {
    "s": "COHR",
    "n": "Coherent Corp. Common Stock"
  },
  {
    "s": "COHU",
    "n": "Cohu, Inc. - Common Stock"
  },
  {
    "s": "COIN",
    "n": "Coinbase Global, Inc. - Class A Common Stock"
  },
  {
    "s": "COKE",
    "n": "Coca-Cola Consolidated, Inc. - Common Stock"
  },
  {
    "s": "COLB",
    "n": "Columbia Banking System, Inc. - Common Stock"
  },
  {
    "s": "COLD",
    "n": "Americold Realty Trust, Inc. Common Stock"
  },
  {
    "s": "COLL",
    "n": "Collegium Pharmaceutical, Inc. - Common Stock"
  },
  {
    "s": "COLM",
    "n": "Columbia Sportswear Company - Common Stock"
  },
  {
    "s": "COMP",
    "n": "Compass, Inc. Class A Common Stock"
  },
  {
    "s": "CON",
    "n": "Concentra Group Holdings Parent, Inc. Common Stock"
  },
  {
    "s": "COO",
    "n": "The Cooper Companies, Inc.  - Common Stock"
  },
  {
    "s": "COOK",
    "n": "Traeger, Inc. Common Stock"
  },
  {
    "s": "COOT",
    "n": "Australian Oilseeds Holdings Limited - Ordinary Shares"
  },
  {
    "s": "COP",
    "n": "ConocoPhillips Common Stock"
  },
  {
    "s": "COPL",
    "n": "Copley Acquisition Corp Ordinary Shares"
  },
  {
    "s": "COPR",
    "n": "Idaho Copper Corporation Common Stock"
  },
  {
    "s": "COR",
    "n": "Cencora, Inc. Common Stock"
  },
  {
    "s": "CORT",
    "n": "Corcept Therapeutics Incorporated - Common Stock"
  },
  {
    "s": "CORZ",
    "n": "Core Scientific, Inc. - Common Stock"
  },
  {
    "s": "CORZW",
    "n": "Core Scientific, Inc. - Tranche 1 Warrants"
  },
  {
    "s": "CORZZ",
    "n": "Core Scientific, Inc. - Tranche 2 Warrants"
  },
  {
    "s": "COSM",
    "n": "Cosmos Health Inc. - Common Stock"
  },
  {
    "s": "COSO",
    "n": "CoastalSouth Bancshares, Inc. Common Stock"
  },
  {
    "s": "COST",
    "n": "Costco Wholesale Corporation - Common Stock"
  },
  {
    "s": "COTY",
    "n": "Coty Inc. Class A Common Stock"
  },
  {
    "s": "COUR",
    "n": "Coursera, Inc. Common Stock"
  },
  {
    "s": "COYA",
    "n": "Coya Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "CP",
    "n": "Canadian Pacific Kansas City Limited Common Shares"
  },
  {
    "s": "CPA",
    "n": "Copa Holdings, S.A. Class A Common Stock"
  },
  {
    "s": "CPAC",
    "n": "Cementos Pacasmayo S.A.A. American Depositary Shares (Each representing five Common Shares)"
  },
  {
    "s": "CPAY",
    "n": "Corpay, Inc. Common Stock"
  },
  {
    "s": "CPB",
    "n": "The Campbell's Company - Common Stock"
  },
  {
    "s": "CPBI",
    "n": "Central Plains Bancshares, Inc. - Common Stock"
  },
  {
    "s": "CPF",
    "n": "Central Pacific Financial Corp New"
  },
  {
    "s": "CPHC",
    "n": "Canterbury Park Holding Corporation - Common Stock"
  },
  {
    "s": "CPHI",
    "n": "China Pharma Holdings, Inc. Common Stock"
  },
  {
    "s": "CPIX",
    "n": "Cumberland Pharmaceuticals Inc. - Common Stock"
  },
  {
    "s": "CPK",
    "n": "Chesapeake Utilities Corporation Common Stock"
  },
  {
    "s": "CPNG",
    "n": "Coupang, Inc. Class A Common Stock"
  },
  {
    "s": "CPOP",
    "n": "Pop Culture Group Co., Ltd - Class A Ordinary Shares"
  },
  {
    "s": "CPRI",
    "n": "Capri Holdings Limited Ordinary Shares"
  },
  {
    "s": "CPRT",
    "n": "Copart, Inc. - Common Stock"
  },
  {
    "s": "CPS",
    "n": "Cooper-Standard Holdings Inc. Common Stock"
  },
  {
    "s": "CPSH",
    "n": "CPS Technologies Corp. - Common Stock"
  },
  {
    "s": "CPSS",
    "n": "Consumer Portfolio Services, Inc. - Common Stock"
  },
  {
    "s": "CPT",
    "n": "Camden Property Trust Common Stock"
  },
  {
    "s": "CR",
    "n": "Crane Company Common Stock"
  },
  {
    "s": "CRAC",
    "n": "Crown Reserve Acquisition Corp. I - Class A Ordinary Shares"
  },
  {
    "s": "CRACU",
    "n": "Crown Reserve Acquisition Corp. I - Unit"
  },
  {
    "s": "CRAI",
    "n": "CRA International,Inc. - Common Stock"
  },
  {
    "s": "CRAN",
    "n": "Crane Harbor Acquisition Corp. II - Class A Ordinary Shares"
  },
  {
    "s": "CRANU",
    "n": "Crane Harbor Acquisition Corp. II - Units"
  },
  {
    "s": "CRAQ",
    "n": "Cal Redwood Acquisition Corp. - Class A Ordinary Shares"
  },
  {
    "s": "CRAQR",
    "n": "Cal Redwood Acquisition Corp. - Right"
  },
  {
    "s": "CRAQU",
    "n": "Cal Redwood Acquisition Corp. - Units"
  },
  {
    "s": "CRBD",
    "n": "Corebridge Financial Inc. 6.375% Junior Subordinated Notes due 2064"
  },
  {
    "s": "CRBG",
    "n": "Corebridge Financial Inc. Common Stock"
  },
  {
    "s": "CRBP",
    "n": "Corbus Pharmaceuticals Holdings, Inc. - Common Stock"
  },
  {
    "s": "CRBU",
    "n": "Caribou Biosciences, Inc. - Common Stock"
  },
  {
    "s": "CRC",
    "n": "California Resources Corporation Common Stock"
  },
  {
    "s": "CRCL",
    "n": "Circle Internet Group, Inc. Class A Common Stock"
  },
  {
    "s": "CRCT",
    "n": "Cricut, Inc. - Class A common stock"
  },
  {
    "s": "CRD-A",
    "n": "Crawford & Company Common Stock"
  },
  {
    "s": "CRD-B",
    "n": "Crawford & Company Common Stock"
  },
  {
    "s": "CRDF",
    "n": "Cardiff Oncology, Inc. - Common Stock"
  },
  {
    "s": "CRDL",
    "n": "Cardiol Therapeutics Inc. - Class A Common Shares"
  },
  {
    "s": "CRDO",
    "n": "Credo Technology Group Holding Ltd - Ordinary Shares"
  },
  {
    "s": "CRE",
    "n": "Cre8 Enterprise Limited - Class A Ordinary Shares"
  },
  {
    "s": "CRESY",
    "n": "Cresud S.A.C.I.F. y A. - American Depositary Shares, each representing ten shares of Common Stock"
  },
  {
    "s": "CREX",
    "n": "Creative Realities, Inc. - Common Stock"
  },
  {
    "s": "CRGO",
    "n": "Freightos Limited - Ordinary shares"
  },
  {
    "s": "CRGOW",
    "n": "Freightos Limited - Warrants"
  },
  {
    "s": "CRGY",
    "n": "Crescent Energy Company Class A Common Stock"
  },
  {
    "s": "CRH",
    "n": "CRH PLC Ordinary Shares"
  },
  {
    "s": "CRI",
    "n": "Carter's, Inc. Common Stock"
  },
  {
    "s": "CRIS",
    "n": "Curis, Inc. - Common Stock"
  },
  {
    "s": "CRK",
    "n": "Comstock Resources, Inc. Common Stock"
  },
  {
    "s": "CRL",
    "n": "Charles River Laboratories International, Inc. Common Stock"
  },
  {
    "s": "CRM",
    "n": "Salesforce, Inc. Common Stock"
  },
  {
    "s": "CRMD",
    "n": "CorMedix Inc. - Common Stock"
  },
  {
    "s": "CRML",
    "n": "Critical Metals Corp. - Ordinary Shares"
  },
  {
    "s": "CRMLW",
    "n": "Critical Metals Corp. - Warrants"
  },
  {
    "s": "CRMT",
    "n": "America's Car-Mart, Inc. - Common Stock"
  },
  {
    "s": "CRNC",
    "n": "Cerence Inc. - Common Stock"
  },
  {
    "s": "CRNT",
    "n": "Ceragon Networks Ltd. - Ordinary Shares"
  },
  {
    "s": "CRON",
    "n": "Cronos Group Inc. - Common Share"
  },
  {
    "s": "CROX",
    "n": "Crocs, Inc. - Common Stock"
  },
  {
    "s": "CRS",
    "n": "Carpenter Technology Corporation Common Stock"
  },
  {
    "s": "CRSP",
    "n": "CRISPR Therapeutics AG - Common Shares"
  },
  {
    "s": "CRSR",
    "n": "Corsair Gaming, Inc. - Common Stock"
  },
  {
    "s": "CRT",
    "n": "Cross Timbers Royalty Trust Common Stock"
  },
  {
    "s": "CRTO",
    "n": "Criteo S.A. - Ordinary Shares"
  },
  {
    "s": "CRUS",
    "n": "Cirrus Logic, Inc. - Common Stock"
  },
  {
    "s": "CRVL",
    "n": "CorVel Corp. - Common Stock"
  },
  {
    "s": "CRVO",
    "n": "CervoMed Inc. - Common Stock"
  },
  {
    "s": "CRVS",
    "n": "Corvus Pharmaceuticals, Inc. - Common Stock"
  },
  {
    "s": "CRWD",
    "n": "CrowdStrike Holdings, Inc. - Class A Common Stock"
  },
  {
    "s": "CRWS",
    "n": "Crown Crafts, Inc. - Common Stock"
  },
  {
    "s": "CRWV",
    "n": "CoreWeave, Inc. - Class A Common Stock"
  },
  {
    "s": "CSAI",
    "n": "Cloudastructure, Inc. - Class A Common Stock"
  },
  {
    "s": "CSBR",
    "n": "Champions Oncology, Inc. - Common Stock"
  },
  {
    "s": "CSCO",
    "n": "Cisco Systems, Inc. - Common Stock"
  },
  {
    "s": "CSGP",
    "n": "CoStar Group, Inc. - Common Stock"
  },
  {
    "s": "CSHR",
    "n": "CoinShares PLC - Ordinary Shares"
  },
  {
    "s": "CSHRW",
    "n": "CoinShares PLC - Warrants"
  },
  {
    "s": "CSIQ",
    "n": "Canadian Solar Inc. - Common Shares"
  },
  {
    "s": "CSL",
    "n": "Carlisle Companies Incorporated Common Stock"
  },
  {
    "s": "CSPI",
    "n": "CSP Inc. - Common Stock"
  },
  {
    "s": "CSQR",
    "n": "Csquare, Inc. Common Stock"
  },
  {
    "s": "CSR",
    "n": "D/B/A Centerspace Common Stock"
  },
  {
    "s": "CSTE",
    "n": "Caesarstone Ltd. - Ordinary Shares"
  },
  {
    "s": "CSTL",
    "n": "Castle Biosciences, Inc. - Common stock"
  },
  {
    "s": "CSTM",
    "n": "Constellium SE Ordinary Shares (France)"
  },
  {
    "s": "CSV",
    "n": "Carriage Services, Inc. Common Stock"
  },
  {
    "s": "CSW",
    "n": "CSW Industrials, Inc. Common Stock"
  },
  {
    "s": "CSWC",
    "n": "Capital Southwest Corporation - Common Stock"
  },
  {
    "s": "CSX",
    "n": "CSX Corporation - Common Stock"
  },
  {
    "s": "CTAA",
    "n": "ClearThink 1 Acquisition Corp. - Class A Ordinary Shares"
  },
  {
    "s": "CTAAU",
    "n": "ClearThink 1 Acquisition Corp. - Units"
  },
  {
    "s": "CTAS",
    "n": "Cintas Corporation - Common Stock"
  },
  {
    "s": "CTBI",
    "n": "Community Trust Bancorp, Inc. - Common Stock"
  },
  {
    "s": "CTEV",
    "n": "Claritev Corporation Class A Common Stock"
  },
  {
    "s": "CTGG",
    "n": "Qwest Corporation - 6.500% Notes due 2051"
  },
  {
    "s": "CTGO",
    "n": "Contango Silver & Gold Inc. Common Stock"
  },
  {
    "s": "CTHH",
    "n": "Qwest Corporation - 6.750% Notes due 2052"
  },
  {
    "s": "CTKB",
    "n": "Cytek Biosciences, Inc. - Common Stock"
  },
  {
    "s": "CTM",
    "n": "Castellum, Inc. Common Stock"
  },
  {
    "s": "CTMX",
    "n": "CytomX Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "CTNM",
    "n": "Contineum Therapeutics, Inc. - Common stock"
  },
  {
    "s": "CTNT",
    "n": "Cheetah Net Supply Chain Service Inc. - Class A Common Stock"
  },
  {
    "s": "CTO",
    "n": "CTO Realty Growth, Inc. Common Stock"
  },
  {
    "s": "CTOR",
    "n": "Citius Oncology, Inc.  - Common Stock"
  },
  {
    "s": "CTOS",
    "n": "Custom Truck One Source, Inc. Common Stock"
  },
  {
    "s": "CTRI",
    "n": "Centuri Holdings, Inc. Common Stock"
  },
  {
    "s": "CTRM",
    "n": "Castor Maritime Inc. - Common Shares"
  },
  {
    "s": "CTRN",
    "n": "Citi Trends, Inc. - Common Stock"
  },
  {
    "s": "CTS",
    "n": "CTS Corporation Common Stock"
  },
  {
    "s": "CTSH",
    "n": "Cognizant Technology Solutions Corporation - Class A Common Stock"
  },
  {
    "s": "CTSO",
    "n": "Cytosorbents Corporation - Common Stock"
  },
  {
    "s": "CTVA",
    "n": "Corteva, Inc. Common Stock "
  },
  {
    "s": "CTW",
    "n": "CTW - Class A Ordinary Shares"
  },
  {
    "s": "CTXR",
    "n": "Citius Pharmaceuticals, Inc. - Common Stock"
  },
  {
    "s": "CUB",
    "n": "Lionheart Holdings - Class A Ordinary Shares"
  },
  {
    "s": "CUBB",
    "n": "Customers Bancorp, Inc 5.375% Subordinated Notes Due 2034"
  },
  {
    "s": "CUBE",
    "n": "CubeSmart Common Shares"
  },
  {
    "s": "CUBI",
    "n": "Customers Bancorp, Inc Common Stock"
  },
  {
    "s": "CUBWU",
    "n": "Lionheart Holdings - Unit"
  },
  {
    "s": "CUE",
    "n": "Cue Biopharma, Inc. - Common Stock"
  },
  {
    "s": "CULP",
    "n": "Culp, Inc. - Common Shares"
  },
  {
    "s": "CUPR",
    "n": "Cuprina Holdings (Cayman) Limited - Class A Ordinary shares"
  },
  {
    "s": "CURB",
    "n": "Curbline Properties Corp. Common Stock"
  },
  {
    "s": "CURI",
    "n": "CuriosityStream Inc.  - Class A Common Stock"
  },
  {
    "s": "CURR",
    "n": "Currenc Group Inc. - Ordinary Shares"
  },
  {
    "s": "CURV",
    "n": "Torrid Holdings Inc. Common Stock"
  },
  {
    "s": "CURX",
    "n": "Curanex Pharmaceuticals Inc - Common Stock"
  },
  {
    "s": "CUVL",
    "n": "Clinuvel Pharmaceuticals Limited - American Depositary Shares"
  },
  {
    "s": "CUZ",
    "n": "Cousins Properties Incorporated Common Stock"
  },
  {
    "s": "CV",
    "n": "CapsoVision, Inc. - Common Stock"
  },
  {
    "s": "CVBF",
    "n": "CVB Financial Corporation - Common Stock"
  },
  {
    "s": "CVCO",
    "n": "Cavco Industries, Inc. - Common Stock"
  },
  {
    "s": "CVE",
    "n": "Cenovus Energy Inc Common Stock"
  },
  {
    "s": "CVEO",
    "n": "Civeo Corporation (Canada) Common Shares"
  },
  {
    "s": "CVGI",
    "n": "Commercial Vehicle Group, Inc. - Common Stock"
  },
  {
    "s": "CVI",
    "n": "CVR Energy Inc. Common Stock"
  },
  {
    "s": "CVKD",
    "n": "Cadrenal Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "CVLG",
    "n": "Covenant Logistics Group, Inc. Class A Common Stock"
  },
  {
    "s": "CVLT",
    "n": "Commvault Systems, Inc. - Common Stock"
  },
  {
    "s": "CVM",
    "n": "Cel-Sci Corporation Common Stock"
  },
  {
    "s": "CVNA",
    "n": "Carvana Co. Class A Common Stock"
  },
  {
    "s": "CVR",
    "n": "Chicago Rivet & Machine Co. Common Stock"
  },
  {
    "s": "CVRX",
    "n": "CVRx, Inc. - Common Stock"
  },
  {
    "s": "CVS",
    "n": "CVS Health Corporation Common Stock"
  },
  {
    "s": "CVSA",
    "n": "Covista Inc. Common Shares"
  },
  {
    "s": "CVU",
    "n": "CPI Aerostructures, Inc. Common Stock"
  },
  {
    "s": "CVV",
    "n": "CVD Equipment Corporation - Common Stock"
  },
  {
    "s": "CVX",
    "n": "Chevron Corporation Common Stock"
  },
  {
    "s": "CW",
    "n": "Curtiss-Wright Corporation Common Stock"
  },
  {
    "s": "CWBC",
    "n": "Community West Bancshares - Common Stock"
  },
  {
    "s": "CWCO",
    "n": "Consolidated Water Co. Ltd. - Ordinary Shares"
  },
  {
    "s": "CWD",
    "n": "CaliberCos Inc. - Class A Common Stock"
  },
  {
    "s": "CWEN",
    "n": "Clearway Energy, Inc. Class C Common Stock"
  },
  {
    "s": "CWH",
    "n": "Camping World Holdings, Inc. Class A Common Stock"
  },
  {
    "s": "CWK",
    "n": "Cushman & Wakefield Ltd. Common Shares"
  },
  {
    "s": "CWST",
    "n": "Casella Waste Systems, Inc. - Class A Common Stock"
  },
  {
    "s": "CWT",
    "n": "California Water Service Group Common Stock"
  },
  {
    "s": "CX",
    "n": "Cemex, S.A.B. de C.V. Sponsored ADR"
  },
  {
    "s": "CXAI",
    "n": "CXApp Inc. - Class A Common Stock"
  },
  {
    "s": "CXDO",
    "n": "Crexendo, Inc. - Common Stock"
  },
  {
    "s": "CXII",
    "n": "Churchill Capital Corp XII - Class A Ordinary Shares"
  },
  {
    "s": "CXIIU",
    "n": "Churchill Capital Corp XII - Units"
  },
  {
    "s": "CXIIW",
    "n": "Churchill Capital Corp XII - Warrants"
  },
  {
    "s": "CXM",
    "n": "Sprinklr, Inc. Class A Common Stock"
  },
  {
    "s": "CXT",
    "n": "Crane NXT, Co. Common Stock"
  },
  {
    "s": "CXW",
    "n": "CoreCivic, Inc. Common Stock"
  },
  {
    "s": "CYAB",
    "n": "Cyabra, Inc. - Common Stock"
  },
  {
    "s": "CYCU",
    "n": "Cycurion, Inc. - Common Stock"
  },
  {
    "s": "CYCUW",
    "n": "Cycurion, Inc. - Warrants"
  },
  {
    "s": "CYD",
    "n": "China Yuchai International Limited Common Stock"
  },
  {
    "s": "CYH",
    "n": "Community Health Systems, Inc. Common Stock"
  },
  {
    "s": "CYN",
    "n": "Cyngn Inc. - Common stock"
  },
  {
    "s": "CYPH",
    "n": "Cypherpunk Technologies Inc. - Common Stock"
  },
  {
    "s": "CYRX",
    "n": "CryoPort, Inc. - Common Stock"
  },
  {
    "s": "CYTK",
    "n": "Cytokinetics, Incorporated - Common Stock"
  },
  {
    "s": "CZFS",
    "n": "Citizens Financial Services, Inc. - Common Stock"
  },
  {
    "s": "CZNC",
    "n": "Citizens & Northern Corp - Common Stock"
  },
  {
    "s": "CZR",
    "n": "Caesars Entertainment, Inc. - Common Stock"
  },
  {
    "s": "CZWI",
    "n": "Citizens Community Bancorp, Inc. - Common Stock"
  },
  {
    "s": "D",
    "n": "Dominion Energy, Inc. Common Stock"
  },
  {
    "s": "DAAQ",
    "n": "Digital Asset Acquisition Corp. - Class A Ordinary shares"
  },
  {
    "s": "DAAQU",
    "n": "Digital Asset Acquisition Corp. - Units"
  },
  {
    "s": "DAC",
    "n": "Danaos Corporation Common Stock"
  },
  {
    "s": "DAIC",
    "n": "CID HoldCo, Inc. - Common Stock"
  },
  {
    "s": "DAICW",
    "n": "CID HoldCo, Inc. - Warrants"
  },
  {
    "s": "DAIO",
    "n": "Data I/O Corporation - Common Stock"
  },
  {
    "s": "DAKT",
    "n": "Daktronics, Inc. - Common Stock"
  },
  {
    "s": "DAL",
    "n": "Delta Air Lines, Inc. Common Stock"
  },
  {
    "s": "DAN",
    "n": "Dana Incorporated Common Stock "
  },
  {
    "s": "DAO",
    "n": "Youdao, Inc. American Depositary Shares, each representing one Class A Ordinary Share"
  },
  {
    "s": "DAR",
    "n": "Darling Ingredients Inc. Common Stock"
  },
  {
    "s": "DARE",
    "n": "Dare Bioscience, Inc. - Common Stock"
  },
  {
    "s": "DASH",
    "n": "DoorDash, Inc. - Common Stock"
  },
  {
    "s": "DAVA",
    "n": "Endava plc American Depositary Shares (each representing one Class A Ordinary Share)"
  },
  {
    "s": "DAVE",
    "n": "Dave Inc.  - Class A Common Stock"
  },
  {
    "s": "DAVEW",
    "n": "Dave Inc.  - Warrants"
  },
  {
    "s": "DB",
    "n": "Deutsche Bank AG Common Stock"
  },
  {
    "s": "DBCA",
    "n": "D. Boral Acquisition I Corp. - Class A Ordinary Shares"
  },
  {
    "s": "DBCAU",
    "n": "D. Boral Acquisition I Corp. - Unit"
  },
  {
    "s": "DBCAW",
    "n": "D. Boral Acquisition I Corp. - Warrants"
  },
  {
    "s": "DBD",
    "n": "Diebold Nixdorf Incorporated Common stock"
  },
  {
    "s": "DBGI",
    "n": "Digital Brands Group, Inc. - Common Stock"
  },
  {
    "s": "DBI",
    "n": "Designer Brands Inc. Class A Common Stock"
  },
  {
    "s": "DBVT",
    "n": "DBV Technologies S.A. - American Depositary Shares"
  },
  {
    "s": "DBX",
    "n": "Dropbox, Inc. - Class A Common Stock"
  },
  {
    "s": "DC",
    "n": "Dakota Gold Corp. Common Stock"
  },
  {
    "s": "DCBG",
    "n": "Dime Commercial Bancshares, Inc. 9.000% Junior Subordinated Notes"
  },
  {
    "s": "DCBO",
    "n": "Docebo Inc. - Common Shares"
  },
  {
    "s": "DCGO",
    "n": "DocGo Inc. - Common Stock"
  },
  {
    "s": "DCH",
    "n": "Dauch Corporation Common Stock"
  },
  {
    "s": "DCI",
    "n": "Donaldson Company, Inc. Common Stock"
  },
  {
    "s": "DCO",
    "n": "Ducommun Incorporated Common Stock"
  },
  {
    "s": "DCOM",
    "n": "Dime Commercial Bancshares, Inc. Common Stock"
  },
  {
    "s": "DCOY",
    "n": "Decoy Therapeutics Inc. - Common Stock"
  },
  {
    "s": "DCTH",
    "n": "Delcath Systems, Inc. - Common Stock"
  },
  {
    "s": "DCX",
    "n": "Digital Currency X Technology Inc. - Class A Ordinary Shares"
  },
  {
    "s": "DD",
    "n": "DuPont de Nemours, Inc. Common Stock"
  },
  {
    "s": "DDC",
    "n": "DDC Enterprise Limited Class A Ordinary Shares"
  },
  {
    "s": "DDD",
    "n": "3D Systems Corporation Common Stock"
  },
  {
    "s": "DDI",
    "n": "DoubleDown Interactive Co., Ltd. - American Depository Shares"
  },
  {
    "s": "DDL",
    "n": "Dingdong (Cayman) Limited American Depositary Shares (each two representing three Ordinary Shares)"
  },
  {
    "s": "DDOG",
    "n": "Datadog, Inc. - Class A Common Stock"
  },
  {
    "s": "DDS",
    "n": "Dillard's, Inc. Common Stock"
  },
  {
    "s": "DDT",
    "n": "Dillard's Capital Trust I"
  },
  {
    "s": "DE",
    "n": "Deere & Company Common Stock"
  },
  {
    "s": "DEA",
    "n": "Easterly Government Properties, Inc. Common Stock"
  },
  {
    "s": "DEC",
    "n": "Diversified Energy Company Common Stock"
  },
  {
    "s": "DECK",
    "n": "Deckers Outdoor Corporation Common Stock"
  },
  {
    "s": "DEFT",
    "n": "Defi Technologies, Inc. - Common Stock"
  },
  {
    "s": "DEI",
    "n": "Douglas Emmett, Inc. Common Stock"
  },
  {
    "s": "DELL",
    "n": "Dell Technologies Inc. Class C Common Stock "
  },
  {
    "s": "DEO",
    "n": "Diageo plc Common Stock"
  },
  {
    "s": "DERM",
    "n": "Journey Medical Corporation - Common Stock"
  },
  {
    "s": "DETX",
    "n": "Liberty Defense Holdings, Ltd. - Common Shares"
  },
  {
    "s": "DFDV",
    "n": "DeFi Development Corp. - Common Stock"
  },
  {
    "s": "DFH",
    "n": "Dream Finders Homes, Inc. Class A Common Stock"
  },
  {
    "s": "DFIN",
    "n": "Donnelley Financial Solutions, Inc. Common Stock "
  },
  {
    "s": "DFLI",
    "n": "Dragonfly Energy Holdings Corp - Common Stock"
  },
  {
    "s": "DFNS",
    "n": "T3 Defense Inc. - Common Stock"
  },
  {
    "s": "DFNSW",
    "n": "T3 Defense Inc. - Warrants"
  },
  {
    "s": "DFSC",
    "n": "DEFSEC Technologies Inc. - common stock, no R/S concurrent with offering"
  },
  {
    "s": "DFTX",
    "n": "Definium Therapeutics, Inc.  - Common Shares"
  },
  {
    "s": "DG",
    "n": "Dollar General Corporation Common Stock"
  },
  {
    "s": "DGAC",
    "n": "Disciplined Growth Acquisition Corporation Class A Ordinary Shares"
  },
  {
    "s": "DGAC-U",
    "n": "Disciplined Growth Acquisition Corporation Units, each consisting of one Class A Ordinary Share and one Right"
  },
  {
    "s": "DGICA",
    "n": "Donegal Group, Inc. - Class A Common Stock"
  },
  {
    "s": "DGICB",
    "n": "Donegal Group, Inc. - Class B Common Stock"
  },
  {
    "s": "DGII",
    "n": "Digi International Inc. - Common Stock"
  },
  {
    "s": "DGNX",
    "n": "Diginex Limited - Ordinary Shares"
  },
  {
    "s": "DGX",
    "n": "Quest Diagnostics Incorporated Common Stock"
  },
  {
    "s": "DGXX",
    "n": "Digi Power X Inc. - Common Subordinate Voting Shares"
  },
  {
    "s": "DH",
    "n": "Definitive Healthcare Corp. - Class A Common Stock"
  },
  {
    "s": "DHC",
    "n": "Diversified Healthcare Trust  - Common Shares of Beneficial Interest"
  },
  {
    "s": "DHCNI",
    "n": "Diversified Healthcare Trust  - 5.625% Senior Notes due 2042"
  },
  {
    "s": "DHCNL",
    "n": "Diversified Healthcare Trust  - 6.25% Senior Notes Due 2046"
  },
  {
    "s": "DHI",
    "n": "D.R. Horton, Inc. Common Stock"
  },
  {
    "s": "DHR",
    "n": "Danaher Corporation Common Stock"
  },
  {
    "s": "DHT",
    "n": "DHT Holdings, Inc."
  },
  {
    "s": "DHX",
    "n": "DHI Group, Inc. Common Stock"
  },
  {
    "s": "DIBS",
    "n": "1stdibs.com, Inc. - Common Stock"
  },
  {
    "s": "DIN",
    "n": "Dine Brands Global, Inc. Common Stock"
  },
  {
    "s": "DINO",
    "n": "HF Sinclair Corporation Common Stock"
  },
  {
    "s": "DIOD",
    "n": "Diodes Incorporated - Common Stock"
  },
  {
    "s": "DIS",
    "n": "Walt Disney Company (The) Common Stock"
  },
  {
    "s": "DIT",
    "n": "AMCON Distributing Company Common Stock"
  },
  {
    "s": "DJCO",
    "n": "Daily Journal Corp. (S.C.) - Common Stock"
  },
  {
    "s": "DJT",
    "n": "Trump Media & Technology Group Corp. - Common Stock"
  },
  {
    "s": "DJTWW",
    "n": "Trump Media & Technology Group Corp. - Warrants"
  },
  {
    "s": "DK",
    "n": "Delek US Holdings, Inc. Common Stock"
  },
  {
    "s": "DKI",
    "n": "DarkIris Inc. - Class A Ordinary Shares"
  },
  {
    "s": "DKL",
    "n": "Delek Logistics Partners, L.P. Common Units representing Limited Partner Interests"
  },
  {
    "s": "DKNG",
    "n": "DraftKings Inc. - Class A Common Stock"
  },
  {
    "s": "DKS",
    "n": "Dick's Sporting Goods Inc Common Stock"
  },
  {
    "s": "DLB",
    "n": "Dolby Laboratories Common Stock"
  },
  {
    "s": "DLHC",
    "n": "DLH Holdings Corp. - Common Stock"
  },
  {
    "s": "DLO",
    "n": "DLocal Limited - Class A Common Shares"
  },
  {
    "s": "DLPN",
    "n": "Dolphin Entertainment, Inc. - Common Stock"
  },
  {
    "s": "DLR",
    "n": "Digital Realty Trust, Inc. Common Stock"
  },
  {
    "s": "DLTH",
    "n": "Duluth Holdings Inc. - Class B Common Stock"
  },
  {
    "s": "DLTR",
    "n": "Dollar Tree, Inc. - Common Stock"
  },
  {
    "s": "DLX",
    "n": "Deluxe Corporation Common Stock"
  },
  {
    "s": "DLXY",
    "n": "Delixy Holdings Limited - Class A Ordinary Shares"
  },
  {
    "s": "DMAA",
    "n": "Drugs Made In America Acquisition Corp. - Ordinary Shares"
  },
  {
    "s": "DMAAU",
    "n": "Drugs Made In America Acquisition Corp. - Units"
  },
  {
    "s": "DMAC",
    "n": "DiaMedica Therapeutics Inc. - Common Stock"
  },
  {
    "s": "DMC",
    "n": "Del Monte Corporation Ordinary Shares"
  },
  {
    "s": "DMII",
    "n": "Drugs Made In America Acquisition II Corp. - Ordinary Shares"
  },
  {
    "s": "DMIIR",
    "n": "Drugs Made In America Acquisition II Corp. - Right"
  },
  {
    "s": "DMIIU",
    "n": "Drugs Made In America Acquisition II Corp. - Unit"
  },
  {
    "s": "DMLP",
    "n": "Dorchester Minerals, L.P. - Common Units Representing Limited Partnership Interests"
  },
  {
    "s": "DMRA",
    "n": "Damora Therapeutics, Inc. - Ordinary Shares"
  },
  {
    "s": "DMRC",
    "n": "Digimarc Corporation - Common Stock"
  },
  {
    "s": "DNA",
    "n": "Ginkgo Bioworks Holdings, Inc. Class A Common Stock"
  },
  {
    "s": "DNLI",
    "n": "Denali Therapeutics Inc. - Common Stock"
  },
  {
    "s": "DNMX",
    "n": "Dynamix Corporation III - Class A Ordinary Shares"
  },
  {
    "s": "DNMXU",
    "n": "Dynamix Corporation III - Unit"
  },
  {
    "s": "DNMXW",
    "n": "Dynamix Corporation III - Warrants"
  },
  {
    "s": "DNN",
    "n": "Denison Mines Corp Ordinary Shares (Canada)"
  },
  {
    "s": "DNOW",
    "n": "DNOW Inc. Common Stock"
  },
  {
    "s": "DNTH",
    "n": "Dianthus Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "DNUT",
    "n": "Krispy Kreme, Inc. - Common Stock"
  },
  {
    "s": "DOC",
    "n": "Healthpeak Properties, Inc. Common Stock"
  },
  {
    "s": "DOCN",
    "n": "DigitalOcean Holdings, Inc. Common Stock"
  },
  {
    "s": "DOCS",
    "n": "Doximity, Inc. Class A Common Stock"
  },
  {
    "s": "DOCU",
    "n": "DocuSign, Inc. - Common Stock"
  },
  {
    "s": "DOGZ",
    "n": "Dogness (International) Corporation - Class A Common Stock"
  },
  {
    "s": "DOLE",
    "n": "Dole plc Ordinary Shares"
  },
  {
    "s": "DOMH",
    "n": "Dominari Holdings Inc. - Common Stock"
  },
  {
    "s": "DOO",
    "n": "BRP Inc. - Common Subordinate Voting Shares"
  },
  {
    "s": "DORM",
    "n": "Dorman Products, Inc. - Common Stock"
  },
  {
    "s": "DOUG",
    "n": "Douglas Elliman Inc. Common Stock"
  },
  {
    "s": "DOV",
    "n": "Dover Corporation Common Stock"
  },
  {
    "s": "DOW",
    "n": "Dow Inc. Common Stock "
  },
  {
    "s": "DOX",
    "n": "Amdocs Limited - Ordinary Shares"
  },
  {
    "s": "DOYU",
    "n": "DouYu International Holdings Limited - American Depositary Shares"
  },
  {
    "s": "DPC",
    "n": "DPC Holdings PLC Ordinary Shares"
  },
  {
    "s": "DPRO",
    "n": "Draganfly Inc. - Common Shares"
  },
  {
    "s": "DPU",
    "n": "Nexpu Ltd. - Class A Ordinary Shares"
  },
  {
    "s": "DPZ",
    "n": "Domino's Pizza Inc - Common Stock"
  },
  {
    "s": "DQ",
    "n": "DAQO New Energy Corp. American Depositary Shares, each representing five ordinary shares"
  },
  {
    "s": "DRD",
    "n": "DRDGOLD Limited American Depositary Shares"
  },
  {
    "s": "DRDB",
    "n": "Roman DBDR Acquisition Corp. II - Ordinary shares"
  },
  {
    "s": "DRDBU",
    "n": "Roman DBDR Acquisition Corp. II - Unit"
  },
  {
    "s": "DRDBW",
    "n": "Roman DBDR Acquisition Corp. II - Warrants"
  },
  {
    "s": "DRH",
    "n": "Diamondrock Hospitality Company - Common Stock"
  },
  {
    "s": "DRI",
    "n": "Darden Restaurants, Inc. Common Stock"
  },
  {
    "s": "DRIO",
    "n": "DarioHealth Corp. - Common Stock"
  },
  {
    "s": "DRK",
    "n": "DarkHorse Technologies Inc. - Common Shares"
  },
  {
    "s": "DRMA",
    "n": "Dermata Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "DRS",
    "n": "Leonardo DRS, Inc. - Common Stock"
  },
  {
    "s": "DRTS",
    "n": "Alpha Tau Medical Ltd. - Ordinary Shares"
  },
  {
    "s": "DRUG",
    "n": "Bright Minds Biosciences Inc. - common stock"
  },
  {
    "s": "DRVN",
    "n": "Driven Brands Holdings Inc. - Common Stock"
  },
  {
    "s": "DSAC",
    "n": "Daedalus Special Acquisition Corp. - Class A Ordinary Shares"
  },
  {
    "s": "DSACU",
    "n": "Daedalus Special Acquisition Corp. - Unit"
  },
  {
    "s": "DSC",
    "n": "DSC Holdings Ltd. - American Depositary Shares"
  },
  {
    "s": "DSGN",
    "n": "Design Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "DSGR",
    "n": "Distribution Solutions Group, Inc. - Common Stock"
  },
  {
    "s": "DSGX",
    "n": "The Descartes Systems Group Inc. - Common Stock"
  },
  {
    "s": "DSP",
    "n": "Viant Technology Inc. - common stock"
  },
  {
    "s": "DSS",
    "n": "DSS, Inc. Common Stock"
  },
  {
    "s": "DSWL",
    "n": "Deswell Industries, Inc. - Common Shares"
  },
  {
    "s": "DSX",
    "n": "Diana Shipping inc. common stock"
  },
  {
    "s": "DSX-W",
    "n": "Diana Shipping inc. Warrants"
  },
  {
    "s": "DSY",
    "n": "Big Tree Cloud Holdings Limited - Class A Ordinary Shares"
  },
  {
    "s": "DSYWW",
    "n": "Big Tree Cloud Holdings Limited - Warrants"
  },
  {
    "s": "DT",
    "n": "Dynatrace, Inc. Common Stock"
  },
  {
    "s": "DTB",
    "n": "DTE Energy Company 2020 Series G 4.375% Junior Subordinated Debentures due 2080"
  },
  {
    "s": "DTCX",
    "n": "Datacentrex, Inc. - Common Stock"
  },
  {
    "s": "DTE",
    "n": "DTE Energy Company Common Stock"
  },
  {
    "s": "DTG",
    "n": "DTE Energy Company 2021 Series E 4.375% Junior Subordinated Debentures"
  },
  {
    "s": "DTI",
    "n": "Drilling Tools International Corporation  - Common Stock"
  },
  {
    "s": "DTIL",
    "n": "Precision BioSciences, Inc. - Common Stock"
  },
  {
    "s": "DTK",
    "n": "DTE Energy Company 2025 Series H 6.25% Junior Subordinated Debentures due 2085"
  },
  {
    "s": "DTM",
    "n": "DT Midstream, Inc. Common Stock "
  },
  {
    "s": "DTSQ",
    "n": "DT Cloud Star Acquisition Corporation - Ordinary Shares"
  },
  {
    "s": "DTSQR",
    "n": "DT Cloud Star Acquisition Corporation - Right"
  },
  {
    "s": "DTSQU",
    "n": "DT Cloud Star Acquisition Corporation - Units"
  },
  {
    "s": "DTSS",
    "n": "Datasea Intelligent Technology Ltd. - Class A Ordinary Shares"
  },
  {
    "s": "DTST",
    "n": "Data Storage Corporation - Common Stock"
  },
  {
    "s": "DTW",
    "n": "DTE Energy Company 2017 Series E 5.25% Junior Subordinated Debentures due 2077"
  },
  {
    "s": "DUK",
    "n": "Duke Energy Corporation (Holding Company) Common Stock"
  },
  {
    "s": "DUKB",
    "n": "Duke Energy Corporation 5.625% Junior Subordinated Debentures due 2078"
  },
  {
    "s": "DUKR",
    "n": "DUKE Robotics Corp. - Common Stock"
  },
  {
    "s": "DUKU",
    "n": "Duke Energy Corporation Corporate Units"
  },
  {
    "s": "DUO",
    "n": "Fangdd Network Group Ltd. - Class A Ordinary Shares"
  },
  {
    "s": "DUOL",
    "n": "Duolingo, Inc. - Class A Common Stock"
  },
  {
    "s": "DUOT",
    "n": "Duos Technologies Group, Inc. - Common Stock"
  },
  {
    "s": "DV",
    "n": "DoubleVerify Holdings, Inc. Common Stock"
  },
  {
    "s": "DVA",
    "n": "DaVita Inc. Common Stock"
  },
  {
    "s": "DVLT",
    "n": "Datavault AI Inc. - Common Stock"
  },
  {
    "s": "DVN",
    "n": "Devon Energy Corporation Common Stock"
  },
  {
    "s": "DWSN",
    "n": "Dawson Geophysical Company - Common Stock"
  },
  {
    "s": "DWTX",
    "n": "Dogwood Therapeutics, Inc.  - Common Stock"
  },
  {
    "s": "DX",
    "n": "Dynex Capital, Inc. Common Stock"
  },
  {
    "s": "DXC",
    "n": "DXC Technology Company Common Stock "
  },
  {
    "s": "DXCM",
    "n": "DexCom, Inc. - Common Stock"
  },
  {
    "s": "DXF",
    "n": "Eason Technology Limited American Depositary Shares (each representing sixty-thousand (60,000) Ordinary Shares)"
  },
  {
    "s": "DXLG",
    "n": "Destination XL Group, Inc. - Common Stock"
  },
  {
    "s": "DXPE",
    "n": "DXP Enterprises, Inc. - Common Stock"
  },
  {
    "s": "DXST",
    "n": "Decent Holding Inc. - Class A Ordinary Shares"
  },
  {
    "s": "DXYZ",
    "n": "Destiny Tech100 Inc. Common Stock"
  },
  {
    "s": "DY",
    "n": "Dycom Industries, Inc. Common Stock"
  },
  {
    "s": "DYAI",
    "n": "Dyadic International, Inc. - Common Stock"
  },
  {
    "s": "DYN",
    "n": "Dyne Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "DYNC",
    "n": "Dynamix Corporation - Class A Ordinary Share"
  },
  {
    "s": "DYNCU",
    "n": "Dynamix Corporation - Unit"
  },
  {
    "s": "DYOR",
    "n": "Insight Digital Partners II - Class A Ordinary Shares"
  },
  {
    "s": "DYORU",
    "n": "Insight Digital Partners II - Units"
  },
  {
    "s": "DYORW",
    "n": "Insight Digital Partners II - Warrants"
  },
  {
    "s": "E",
    "n": "ENI S.p.A. Common Stock"
  },
  {
    "s": "EAF",
    "n": "GrafTech International Ltd. Common Stock"
  },
  {
    "s": "EAI",
    "n": "Entergy Arkansas, LLC First Mortgage Bonds, 4.875% Series Due September 1, 2066"
  },
  {
    "s": "EARN",
    "n": "Ellington Credit Company Common Shares of Beneficial Interest"
  },
  {
    "s": "EAT",
    "n": "Brinker International, Inc. Common Stock"
  },
  {
    "s": "EBAY",
    "n": "eBay Inc. - Common Stock"
  },
  {
    "s": "EBC",
    "n": "Eastern Bankshares, Inc. - Common Stock"
  },
  {
    "s": "EBF",
    "n": "Ennis, Inc. Common Stock"
  },
  {
    "s": "EBMT",
    "n": "Eagle Bancorp Montana, Inc. - Common Stock"
  },
  {
    "s": "EBON",
    "n": "Ebang International Holdings Inc. - Class A Ordinary Shares"
  },
  {
    "s": "EBS",
    "n": "Emergent BioSolutions Inc. Common Stock"
  },
  {
    "s": "EC",
    "n": "Ecopetrol S.A. American Depositary Shares"
  },
  {
    "s": "ECAT",
    "n": "BlackRock ESG Capital Allocation Term Trust Common Shares of Beneficial Interest"
  },
  {
    "s": "ECBK",
    "n": "ECB Bancorp, Inc. - Common Stock"
  },
  {
    "s": "ECC",
    "n": "Eagle Point Credit Company Common Share of Beneficial Interest"
  },
  {
    "s": "ECCU",
    "n": "Eagle Point Credit Company 7.75% Notes due 2030"
  },
  {
    "s": "ECCV",
    "n": "Eagle Point Credit Company 5.375% Notes due 2029"
  },
  {
    "s": "ECG",
    "n": "Everus Construction Group, Inc. Common Stock"
  },
  {
    "s": "ECHO",
    "n": "EchoStar Corporation - Common stock"
  },
  {
    "s": "ECL",
    "n": "Ecolab Inc. Common Stock"
  },
  {
    "s": "ECO",
    "n": "Okeanis Eco Tankers Corp. Common Stock"
  },
  {
    "s": "ECOR",
    "n": "electroCore, Inc. - Common Stock"
  },
  {
    "s": "ECPG",
    "n": "Encore Capital Group Inc - Common Stock"
  },
  {
    "s": "ECVT",
    "n": "Ecovyst Inc. Common Stock"
  },
  {
    "s": "ECX",
    "n": "ECARX Holdings Inc. - Class A Ordinary shares"
  },
  {
    "s": "ECXWW",
    "n": "ECARX Holdings Inc. - Warrants"
  },
  {
    "s": "ED",
    "n": "Consolidated Edison, Inc. Common Stock"
  },
  {
    "s": "EDBL",
    "n": "Edible Garden AG Incorporated - Common Stock"
  },
  {
    "s": "EDHL",
    "n": "Everbright Digital Holding Limited - Ordinary Shares"
  },
  {
    "s": "EDIT",
    "n": "Editas Medicine, Inc. - Common Stock"
  },
  {
    "s": "EDN",
    "n": "Empresa Distribuidora Y Comercializadora Norte S.A. (Edenor) American Depositary Shares"
  },
  {
    "s": "EDRY",
    "n": "EuroDry Ltd. - Common Shares"
  },
  {
    "s": "EDSA",
    "n": "Edesa Biotech, Inc. - Common Shares"
  },
  {
    "s": "EDTK",
    "n": "Skillful Craftsman Education Technology Limited - Ordinary Share"
  },
  {
    "s": "EDU",
    "n": "New Oriental Education & Technology Group, Inc. Sponsored ADR representing 10 Ordinary Share (Cayman Islands)"
  },
  {
    "s": "EDUC",
    "n": "Educational Development Corporation - Common Stock"
  },
  {
    "s": "EDVA",
    "n": "Endovia Health Sciences, Inc. Common Stock"
  },
  {
    "s": "EE",
    "n": "Excelerate Energy, Inc. Class A Common Stock"
  },
  {
    "s": "EEFT",
    "n": "Euronet Worldwide, Inc. - Common Stock"
  },
  {
    "s": "EEIQ",
    "n": "EpicQuest Education Group International Limited - Common Stock"
  },
  {
    "s": "EFC",
    "n": "Ellington Financial Inc. Common Stock "
  },
  {
    "s": "EFOI",
    "n": "Energy Focus, Inc. - Common Stock"
  },
  {
    "s": "EFOR",
    "n": "Everforth, Inc. Common Stock"
  },
  {
    "s": "EFSC",
    "n": "Enterprise Financial Services Corporation - Common Stock"
  },
  {
    "s": "EFSI",
    "n": "Eagle Financial Services Inc - Common Stock"
  },
  {
    "s": "EFT",
    "n": "Eaton Vance Floating Rate Income Trust Common Shares of Beneficial Interest"
  },
  {
    "s": "EFTY",
    "n": "Etoiles Capital Group Co., Ltd. - Class A Ordinary Shares"
  },
  {
    "s": "EFX",
    "n": "Equifax, Inc. Common Stock"
  },
  {
    "s": "EFXT",
    "n": "Enerflex Ltd Common Shares"
  },
  {
    "s": "EG",
    "n": "Everest Group, Ltd. Common Stock"
  },
  {
    "s": "EGAN",
    "n": "eGain Corporation - Common Stock"
  },
  {
    "s": "EGBN",
    "n": "Eagle Bancorp, Inc. - Common Stock"
  },
  {
    "s": "EGG",
    "n": "Enigmatig Limited Class A Ordinary Shares"
  },
  {
    "s": "EGHA",
    "n": "EGH Acquisition Corp. - Class A ordinary shares"
  },
  {
    "s": "EGHAU",
    "n": "EGH Acquisition Corp. - Unit"
  },
  {
    "s": "EGHT",
    "n": "8x8 Inc - Common stock"
  },
  {
    "s": "EGO",
    "n": "Eldorado Gold Corporation Ordinary Shares"
  },
  {
    "s": "EGP",
    "n": "EastGroup Properties, Inc. Common Stock"
  },
  {
    "s": "EGY",
    "n": "VAALCO Energy, Inc.  Common Stock"
  },
  {
    "s": "EH",
    "n": "EHang Holdings Limited - ADS"
  },
  {
    "s": "EHC",
    "n": "Encompass Health Corporation Common Stock"
  },
  {
    "s": "EHGO",
    "n": "Eshallgo Inc. - Class A Ordinary Shares"
  },
  {
    "s": "EHLD",
    "n": "Euroholdings Ltd. - Common Stock"
  },
  {
    "s": "EHTH",
    "n": "eHealth, Inc. - Common Stock"
  },
  {
    "s": "EIC",
    "n": "Eagle Point Income Company Common Shares of Beneficial Interest"
  },
  {
    "s": "EIG",
    "n": "Employers Holdings Inc Common Stock"
  },
  {
    "s": "EIKN",
    "n": "Eikon Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "EIX",
    "n": "Edison International Common Stock"
  },
  {
    "s": "EJH",
    "n": "E-Home Household Service Holdings Limited - Ordinary shares"
  },
  {
    "s": "EL",
    "n": "Estee Lauder Companies, Inc. (The) Common Stock"
  },
  {
    "s": "ELA",
    "n": "Envela Corporation Common Stock"
  },
  {
    "s": "ELAB",
    "n": "PMGC Holdings Inc. - Common Stock"
  },
  {
    "s": "ELAN",
    "n": "Elanco Animal Health Incorporated Common Stock"
  },
  {
    "s": "ELBM",
    "n": "Electra Battery Materials Corporation - Common Stock"
  },
  {
    "s": "ELC",
    "n": "Entergy Louisiana, Inc. Collateral Trust Mortgage Bonds, 4.875 % Series due September 1, 2066"
  },
  {
    "s": "ELDN",
    "n": "Eledon Pharmaceuticals, Inc. - Common Stock"
  },
  {
    "s": "ELE",
    "n": "Elemental Royalty Corporation - Common Stock"
  },
  {
    "s": "ELF",
    "n": "e.l.f. Beauty, Inc. Common Stock"
  },
  {
    "s": "ELLA",
    "n": "Ellington Credit Company 8.50% Notes due 2031"
  },
  {
    "s": "ELLO",
    "n": "Ellomay Capital Ltd Ordinary Shares (Israel)"
  },
  {
    "s": "ELMD",
    "n": "Electromed, Inc. Common Stock"
  },
  {
    "s": "ELME",
    "n": "Elme Communities Common Stock"
  },
  {
    "s": "ELMT",
    "n": "The Elmet Group Co. - Common Stock"
  },
  {
    "s": "ELOG",
    "n": "Eastern International Ltd. - Ordinary Shares"
  },
  {
    "s": "ELOX",
    "n": "Eloxx Pharmaceuticals, Inc. - Common Stock"
  },
  {
    "s": "ELPC",
    "n": "Companhia Paranaense de Energia (COPEL) American Depositary Shares (each representing four (4) Common Shares)"
  },
  {
    "s": "ELPW",
    "n": "Elong Power Holding Limited - Class A Ordinary Shares"
  },
  {
    "s": "ELS",
    "n": "Equity Lifestyle Properties, Inc. Common Stock"
  },
  {
    "s": "ELTK",
    "n": "Eltek Ltd. - Ordinary Shares"
  },
  {
    "s": "ELTX",
    "n": "Elicio Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "ELUT",
    "n": "Elutia, Inc. - Class A Common Stock"
  },
  {
    "s": "ELV",
    "n": "Elevance Health, Inc. Common Stock"
  },
  {
    "s": "ELVA",
    "n": "Electrovaya Inc. - Common Shares"
  },
  {
    "s": "ELVN",
    "n": "Enliven Therapeutics, Inc.  - Common Stock"
  },
  {
    "s": "ELVR",
    "n": "Elevra Lithium Limited - American Depository Shares"
  },
  {
    "s": "ELWT",
    "n": "Elauwit Connection, Inc. - Common Stock"
  },
  {
    "s": "EMA",
    "n": "Emera Incorporated Common Shares"
  },
  {
    "s": "EMAT",
    "n": "Evolution Metals & Technologies Corp. - Common Stock"
  },
  {
    "s": "EMBC",
    "n": "Embecta Corp. - Common Stock"
  },
  {
    "s": "EMBJ",
    "n": "Embraer S.A. Common Stock"
  },
  {
    "s": "EME",
    "n": "EMCOR Group, Inc. Common Stock"
  },
  {
    "s": "EMIS",
    "n": "Emmis Acquisition Corp. - Class A Ordinary Share"
  },
  {
    "s": "EML",
    "n": "Eastern Company (The) - Common Stock"
  },
  {
    "s": "EMN",
    "n": "Eastman Chemical Company Common Stock"
  },
  {
    "s": "EMP",
    "n": "Entergy Mississippi, LLC First Mortgage Bonds, 4.90% Series Due October 1, 2066"
  },
  {
    "s": "EMPD",
    "n": "Empery Digital Inc. - Common stock"
  },
  {
    "s": "EMR",
    "n": "Emerson Electric Company Common Stock"
  },
  {
    "s": "ENB",
    "n": "Enbridge Inc Common Stock"
  },
  {
    "s": "ENGN",
    "n": "enGene Therapeutics Inc. - Common Stock"
  },
  {
    "s": "ENGNW",
    "n": "enGene Therapeutics Inc. - Warrants"
  },
  {
    "s": "ENGS",
    "n": "Energys Group Limited - Ordinary Shares"
  },
  {
    "s": "ENHA",
    "n": "Enhanced Group Inc. Class A Common Stock"
  },
  {
    "s": "ENIC",
    "n": "Enel Chile S.A. American Depositary Shares (Each representing 50 shares of Common Stock)"
  },
  {
    "s": "ENJ",
    "n": "Entergy New Orleans, LLC First Mortgage Bonds, 5.0% Series due December 1, 2052"
  },
  {
    "s": "ENLT",
    "n": "Enlight Renewable Energy Ltd. - Ordinary Shares"
  },
  {
    "s": "ENLV",
    "n": "Enlivex Ltd. - Ordinary Shares"
  },
  {
    "s": "ENO",
    "n": "Entergy New Orleans, LLC First Mortgage Bonds, 5.50% Series due April 1, 2066"
  },
  {
    "s": "ENOV",
    "n": "Enovis Corporation Common Stock"
  },
  {
    "s": "ENPH",
    "n": "Enphase Energy, Inc. - Common Stock"
  },
  {
    "s": "ENR",
    "n": "Energizer Holdings, Inc. Common Stock"
  },
  {
    "s": "ENRD",
    "n": "Einride AB - American Depositary Shares"
  },
  {
    "s": "ENRDW",
    "n": "Einride AB - Warrants"
  },
  {
    "s": "ENS",
    "n": "EnerSys Common Stock"
  },
  {
    "s": "ENSC",
    "n": "Ensysce Biosciences, Inc. - Common Stock"
  },
  {
    "s": "ENSG",
    "n": "The Ensign Group, Inc. - Common Stock"
  },
  {
    "s": "ENTA",
    "n": "Enanta Pharmaceuticals, Inc. - Common Stock"
  },
  {
    "s": "ENTG",
    "n": "Entegris, Inc. - Common Stock"
  },
  {
    "s": "ENTX",
    "n": "Entera Bio Ltd. - Ordinary Shares"
  },
  {
    "s": "ENVA",
    "n": "Enova International, Inc. Common Stock"
  },
  {
    "s": "ENVB",
    "n": "Enveric Biosciences, Inc.  - Common Stock"
  },
  {
    "s": "ENVX",
    "n": "Enovix Corporation - Common Stock"
  },
  {
    "s": "EOCN",
    "n": "Eocene Ltd. - Ordinary Shares"
  },
  {
    "s": "EOG",
    "n": "EOG Resources, Inc. Common Stock"
  },
  {
    "s": "EOLS",
    "n": "Evolus, Inc. - Common Stock"
  },
  {
    "s": "EONR",
    "n": "EON Resources Inc. Class A Common Stock"
  },
  {
    "s": "EOSE",
    "n": "Eos Energy Enterprises, Inc. - Common Stock"
  },
  {
    "s": "EOT",
    "n": "Eaton Vance Municipal Income Trust EATON VANCE NATIONAL MUNICIPAL OPPORTUNITIES TRUST"
  },
  {
    "s": "EP",
    "n": "Empire Petroleum Corporation Common Stock"
  },
  {
    "s": "EPAC",
    "n": "Enerpac Tool Group Corp. Common Stock"
  },
  {
    "s": "EPAM",
    "n": "EPAM Systems, Inc. Common Stock"
  },
  {
    "s": "EPC",
    "n": "Edgewell Personal Care Company Common Stock"
  },
  {
    "s": "EPD",
    "n": "Enterprise Products Partners L.P. Common Stock"
  },
  {
    "s": "EPM",
    "n": "Evolution Petroleum Corporation, Inc. Common Stock"
  },
  {
    "s": "EPOW",
    "n": "E-Power Inc. - Class A Ordinary Shares"
  },
  {
    "s": "EPR",
    "n": "EPR Properties Common Stock"
  },
  {
    "s": "EPRT",
    "n": "Essential Properties Realty Trust, Inc. Common Stock"
  },
  {
    "s": "EPRX",
    "n": "Eupraxia Pharmaceuticals Inc. - Common Stock"
  },
  {
    "s": "EPSM",
    "n": "Epsium Enterprise Limited - Class A Ordinary Shares"
  },
  {
    "s": "EPSN",
    "n": "Epsilon Energy Ltd. - Common Shares"
  },
  {
    "s": "EQ",
    "n": "Equillium, Inc. - Common Stock"
  },
  {
    "s": "EQBK",
    "n": "Equity Bancshares, Inc. Class A Common Stock"
  },
  {
    "s": "EQH",
    "n": "Equitable Holdings, Inc. Common Stock"
  },
  {
    "s": "EQIX",
    "n": "Equinix, Inc. - Common Stock"
  },
  {
    "s": "EQNR",
    "n": "Equinor ASA"
  },
  {
    "s": "EQPT",
    "n": "EquipmentShare.com Inc - Class A Common Stock"
  },
  {
    "s": "EQS",
    "n": "Equus Total Return, Inc. Common Stock"
  },
  {
    "s": "EQT",
    "n": "EQT Corporation Common Stock"
  },
  {
    "s": "EQX",
    "n": "Equinox Gold Corp. Common Shares"
  },
  {
    "s": "ERAS",
    "n": "Erasca, Inc. - Common Stock"
  },
  {
    "s": "ERIC",
    "n": "Ericsson - American Depositary Shares each representing 1 underlying Class B share"
  },
  {
    "s": "ERIE",
    "n": "Erie Indemnity Company - Class A Common Stock"
  },
  {
    "s": "ERII",
    "n": "Energy Recovery, Inc. - Common Stock"
  },
  {
    "s": "ERNA",
    "n": "Ernexa Therapeutics Inc. - Common Stock"
  },
  {
    "s": "ERNAW",
    "n": "Ernexa Therapeutics Inc. - Warrants"
  },
  {
    "s": "ERO",
    "n": "Ero Copper Corp. Common Shares"
  },
  {
    "s": "EROC",
    "n": "ERock, Inc. Class A Common Stock"
  },
  {
    "s": "EROK",
    "n": "EagleRock Land, LLC Class A shares representing limited liability company interests"
  },
  {
    "s": "ES",
    "n": "Eversource Energy (D/B/A) Common Stock"
  },
  {
    "s": "ESAB",
    "n": "ESAB Corporation Common Stock"
  },
  {
    "s": "ESBA",
    "n": "Empire State Realty OP, L.P. Series ES Operating Partnership Units Representing Limited Partnership Interests"
  },
  {
    "s": "ESCA",
    "n": "Escalade, Incorporated - Common Stock"
  },
  {
    "s": "ESE",
    "n": "ESCO Technologies Inc. Common Stock"
  },
  {
    "s": "ESEA",
    "n": "Euroseas Ltd. - Common Stock"
  },
  {
    "s": "ESI",
    "n": "Element Solutions Inc. Common Stock"
  },
  {
    "s": "ESLA",
    "n": "Estrella Immunopharma, Inc. - Common Stock"
  },
  {
    "s": "ESLT",
    "n": "Elbit Systems Ltd. - Ordinary Shares"
  },
  {
    "s": "ESNT",
    "n": "Essent Group Ltd. Common Shares"
  },
  {
    "s": "ESOA",
    "n": "Energy Services of America Corporation - Common Stock"
  },
  {
    "s": "ESP",
    "n": "Espey Mfg. & Electronics Corp. Common Stock"
  },
  {
    "s": "ESQ",
    "n": "Esquire Financial Holdings, Inc. - Common Stock"
  },
  {
    "s": "ESRT",
    "n": "Empire State Realty Trust, Inc. Class A Common Stock"
  },
  {
    "s": "ESS",
    "n": "Essex Property Trust, Inc. Common Stock"
  },
  {
    "s": "ESTA",
    "n": "Establishment Labs Holdings Inc. - Common Shares"
  },
  {
    "s": "ESTC",
    "n": "Elastic N.V. Ordinary Shares"
  },
  {
    "s": "ESYN",
    "n": "EnerSyn Global Inc. - Common Stock"
  },
  {
    "s": "ETD",
    "n": "Ethan Allen Interiors Inc. Common Stock"
  },
  {
    "s": "ETN",
    "n": "Eaton Corporation, PLC Ordinary Shares"
  },
  {
    "s": "ETO",
    "n": "Eaton Vance Tax-Advantage Global Dividend Opp Common Stock"
  },
  {
    "s": "ETON",
    "n": "Eton Pharmaceuticals, Inc. - Common Stock"
  },
  {
    "s": "ETOR",
    "n": "eToro Group Ltd. - Class A Common Shares"
  },
  {
    "s": "ETR",
    "n": "Entergy Corporation Common Stock"
  },
  {
    "s": "ETRA",
    "n": "Electra Therapeutics, Inc. - Common stock"
  },
  {
    "s": "ETS",
    "n": "Elite Express Holding Inc. - Class A Common Stock"
  },
  {
    "s": "ETSS",
    "n": "Energy Transition Special Opportunities Class A Ordinary Shares"
  },
  {
    "s": "ETSY",
    "n": "Etsy, Inc. Common Stock"
  },
  {
    "s": "ETX",
    "n": "Eaton Vance Municipal Income 2028 Term Trust Common Shares of Beneficial Interest"
  },
  {
    "s": "EU",
    "n": "enCore Energy Corp. - Common Stock"
  },
  {
    "s": "EUDA",
    "n": "Euda Health Holdings Limited - Ordinary Shares"
  },
  {
    "s": "EURK",
    "n": "Eureka Acquisition Corp - Class A Ordinary Share"
  },
  {
    "s": "EURKR",
    "n": "Eureka Acquisition Corp - Right"
  },
  {
    "s": "EURKU",
    "n": "Eureka Acquisition Corp - Unit"
  },
  {
    "s": "EVAC",
    "n": "EQV Ventures Acquisition Corp. II Class A Ordinary Shares"
  },
  {
    "s": "EVAX",
    "n": "Evaxion A/S - American Depositary Share"
  },
  {
    "s": "EVC",
    "n": "Entravision Communications Corporation Common Stock"
  },
  {
    "s": "EVCM",
    "n": "EverCommerce Inc. - Common Stock"
  },
  {
    "s": "EVER",
    "n": "EverQuote, Inc. - Class A Common Stock"
  },
  {
    "s": "EVEX",
    "n": "Eve Holding, Inc. Common Stock"
  },
  {
    "s": "EVEX-W",
    "n": "Eve Holding, Inc. Warrants, each exercisable for one share of Common Stock at an exercise price of $11.50 per share"
  },
  {
    "s": "EVF",
    "n": "Eaton Vance Senior Income Trust Common Stock"
  },
  {
    "s": "EVGN",
    "n": "Evogene Ltd. - Ordinary Shares"
  },
  {
    "s": "EVGO",
    "n": "EVgo Inc. - Common Stock"
  },
  {
    "s": "EVH",
    "n": "Evolent Health, Inc Class A Common Stock"
  },
  {
    "s": "EVI",
    "n": "EVI Industries, Inc.  Common Stock"
  },
  {
    "s": "EVLV",
    "n": "Evolv Technologies Holdings, Inc. - Class A Common Stock"
  },
  {
    "s": "EVMN",
    "n": "Evommune, Inc. Common Stock"
  },
  {
    "s": "EVN",
    "n": "Eaton Vance Municipal Income Trust Common Stock"
  },
  {
    "s": "EVO",
    "n": "Evotec SE - American Depositary Shares each representing 1/2 of one ordinary share"
  },
  {
    "s": "EVOX",
    "n": "Evolution Global Acquisition Corp - Class A Ordinary Shares"
  },
  {
    "s": "EVOXU",
    "n": "Evolution Global Acquisition Corp - Units"
  },
  {
    "s": "EVOXW",
    "n": "Evolution Global Acquisition Corp - Warrants"
  },
  {
    "s": "EVR",
    "n": "Evercore Inc. Class A Common Stock"
  },
  {
    "s": "EVRG",
    "n": "Evergy, Inc. - Common Stock"
  },
  {
    "s": "EVTC",
    "n": "Evertec, Inc. Common Stock"
  },
  {
    "s": "EVTL",
    "n": "Vertical Aerospace Ltd. Ordinary Shares"
  },
  {
    "s": "EW",
    "n": "Edwards Lifesciences Corporation Common Stock"
  },
  {
    "s": "EWAV",
    "n": "East West Ave Acquisition Corp. - Common Stock"
  },
  {
    "s": "EWAVU",
    "n": "East West Ave Acquisition Corp. - Units"
  },
  {
    "s": "EWBC",
    "n": "East West Bancorp, Inc. - Common Stock"
  },
  {
    "s": "EWTX",
    "n": "Edgewise Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "EXC",
    "n": "Exelon Corporation - Common Stock"
  },
  {
    "s": "EXE",
    "n": "Expand Energy Corporation - Common Stock"
  },
  {
    "s": "EXEL",
    "n": "Exelixis, Inc. - Common Stock"
  },
  {
    "s": "EXFY",
    "n": "Expensify, Inc. - Class A Common Stock"
  },
  {
    "s": "EXK",
    "n": "Endeavour Silver Corporation Ordinary Shares (Canada)"
  },
  {
    "s": "EXLS",
    "n": "ExlService Holdings, Inc. - Common Stock"
  },
  {
    "s": "EXOD",
    "n": "Exodus Movement, Inc. Class A Common Stock"
  },
  {
    "s": "EXOZ",
    "n": "eXoZymes Inc. - Common Stock"
  },
  {
    "s": "EXP",
    "n": "Eagle Materials Inc Common Stock"
  },
  {
    "s": "EXPD",
    "n": "Expeditors International of Washington, Inc. Common Stock"
  },
  {
    "s": "EXPE",
    "n": "Expedia Group, Inc. - Common Stock"
  },
  {
    "s": "EXPO",
    "n": "Exponent, Inc. - Common Stock"
  },
  {
    "s": "EXR",
    "n": "Extra Space Storage Inc Common Stock"
  },
  {
    "s": "EXTR",
    "n": "Extreme Networks, Inc. - Common Stock"
  },
  {
    "s": "EXYN",
    "n": "Exyn Technologies, Inc. - Common Stock"
  },
  {
    "s": "EYE",
    "n": "National Vision Holdings, Inc. - Common Stock"
  },
  {
    "s": "EYPT",
    "n": "EyePoint, Inc. - Common Stock"
  },
  {
    "s": "EZGO",
    "n": "EZGO Technologies Ltd. - Ordinary Shares"
  },
  {
    "s": "EZPW",
    "n": "EZCORP, Inc. - Class A Non-Voting Common Stock"
  },
  {
    "s": "EZRA",
    "n": "Reliance Global Group, Inc. - Common Stock"
  },
  {
    "s": "F",
    "n": "Ford Motor Company Common Stock"
  },
  {
    "s": "FA",
    "n": "First Advantage Corporation - Common Stock"
  },
  {
    "s": "FABC",
    "n": "Fabric.AI, Inc. - Common Stock"
  },
  {
    "s": "FAC",
    "n": "Factorial Energy Inc. - Class A Common Stock"
  },
  {
    "s": "FACT",
    "n": "FACT II Acquisition Corp. - Class A Ordinary Shares"
  },
  {
    "s": "FACTU",
    "n": "FACT II Acquisition Corp. - Unit"
  },
  {
    "s": "FAF",
    "n": "First American Corporation (New) Common Stock"
  },
  {
    "s": "FAMI",
    "n": "Farmmi, Inc. - Class A Ordinary Shares"
  },
  {
    "s": "FANG",
    "n": "Diamondback Energy, Inc. - Common Stock"
  },
  {
    "s": "FAST",
    "n": "Fastenal Company - Common Stock"
  },
  {
    "s": "FATE",
    "n": "Fate Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "FATN",
    "n": "FatPipe, Inc. - common stock"
  },
  {
    "s": "FBDT",
    "n": "First Breach Inc. - Common Stock"
  },
  {
    "s": "FBGL",
    "n": "FBS Global Limited - Ordinary Shares"
  },
  {
    "s": "FBIN",
    "n": "Fortune Brands Innovations, Inc. Common Stock"
  },
  {
    "s": "FBIO",
    "n": "Fortress Biotech, Inc. - Common Stock"
  },
  {
    "s": "FBIZ",
    "n": "First Business Financial Services, Inc. - Common Stock"
  },
  {
    "s": "FBK",
    "n": "FB Financial Corporation Common Stock"
  },
  {
    "s": "FBLA",
    "n": "FB Bancorp, Inc. - Common Stock"
  },
  {
    "s": "FBLG",
    "n": "FibroBiologics, Inc. - Common Stock"
  },
  {
    "s": "FBNC",
    "n": "First Bancorp - Common Stock"
  },
  {
    "s": "FBP",
    "n": "First BanCorp. New Common Stock"
  },
  {
    "s": "FBRT",
    "n": "Franklin BSP Realty Trust, Inc. Common Stock"
  },
  {
    "s": "FBYD",
    "n": "Falcon's Beyond Global, Inc. - Class A Common Stock"
  },
  {
    "s": "FBYDW",
    "n": "Falcon's Beyond Global, Inc. - Warrants"
  },
  {
    "s": "FC",
    "n": "Franklin Covey Company Common Stock"
  },
  {
    "s": "FCAP",
    "n": "First Capital, Inc. - Common Stock"
  },
  {
    "s": "FCBC",
    "n": "First Community Bankshares, Inc. - Common Stock"
  },
  {
    "s": "FCBM",
    "n": "First Carolina Financial Services, Inc. Common Stock"
  },
  {
    "s": "FCCO",
    "n": "First Community Corporation - Common Stock"
  },
  {
    "s": "FCEL",
    "n": "FuelCell Energy, Inc. - Common Stock"
  },
  {
    "s": "FCF",
    "n": "First Commonwealth Financial Corporation Common Stock"
  },
  {
    "s": "FCFS",
    "n": "FirstCash Holdings, Inc. - Common Stock"
  },
  {
    "s": "FCHL",
    "n": "Fitness Champs Holdings Limited - Ordinary Shares"
  },
  {
    "s": "FCN",
    "n": "FTI Consulting, Inc. Common Stock"
  },
  {
    "s": "FCNCA",
    "n": "First Citizens BancShares, Inc. - Class A Common Stock"
  },
  {
    "s": "FCPT",
    "n": "Four Corners Property Trust, Inc. Common Stock"
  },
  {
    "s": "FCRS",
    "n": "FutureCrest Acquisition Corp. Class A Ordinary Shares"
  },
  {
    "s": "FCUV",
    "n": "Focus Universal Inc. - Common Stock"
  },
  {
    "s": "FCX",
    "n": "Freeport-McMoRan, Inc. Common Stock"
  },
  {
    "s": "FDBC",
    "n": "Fidelity D & D Bancorp, Inc. - Common Stock"
  },
  {
    "s": "FDMM",
    "n": "Freedom Metals Acquisition Corp. - Class A Ordinary Shares"
  },
  {
    "s": "FDMMU",
    "n": "Freedom Metals Acquisition Corp. - Units"
  },
  {
    "s": "FDMMW",
    "n": "Freedom Metals Acquisition Corp. - Warrants"
  },
  {
    "s": "FDMT",
    "n": "4D Molecular Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "FDS",
    "n": "FactSet Research Systems Inc. Common Stock"
  },
  {
    "s": "FDSB",
    "n": "Fifth District Bancorp, Inc. - Common Stock"
  },
  {
    "s": "FDX",
    "n": "FedEx Corporation Common Stock"
  },
  {
    "s": "FDXF",
    "n": "FedEx Freight Holding Company, Inc. Common Stock"
  },
  {
    "s": "FE",
    "n": "FirstEnergy Corp. Common Stock"
  },
  {
    "s": "FEAM",
    "n": "5E Advanced Materials, Inc. - Common Stock"
  },
  {
    "s": "FEBO",
    "n": "Fenbo Holdings Limited - Class A Ordinary Shares"
  },
  {
    "s": "FEDU",
    "n": "Four Seasons Education (Cayman) Inc. American Depositary Shares, each ADS representing 10 ordinary shares"
  },
  {
    "s": "FEIM",
    "n": "Frequency Electronics, Inc. - Common Stock"
  },
  {
    "s": "FELE",
    "n": "Franklin Electric Co., Inc. - Common Stock"
  },
  {
    "s": "FEMY",
    "n": "Femasys Inc. - Common Stock"
  },
  {
    "s": "FENC",
    "n": "Fennec Pharmaceuticals Inc. - Common Stock"
  },
  {
    "s": "FENG",
    "n": "Phoenix New Media Limited American Depositary Shares, each representing 48 Class A ordinary shares."
  },
  {
    "s": "FER",
    "n": "Ferrovial N.V. - Ordinary Shares"
  },
  {
    "s": "FERA",
    "n": "Fifth Era Acquisition Corp I - Class A Ordinary Shares"
  },
  {
    "s": "FERAU",
    "n": "Fifth Era Acquisition Corp I - Units"
  },
  {
    "s": "FERG",
    "n": "Ferguson Enterprises Inc. Common Stock"
  },
  {
    "s": "FET",
    "n": "Forum Energy Technologies, Inc. Common Stock"
  },
  {
    "s": "FF",
    "n": "FutureFuel Corp.  Common shares"
  },
  {
    "s": "FFAI",
    "n": "Faraday Future Intelligent Electric Inc. - Class A Common Stock"
  },
  {
    "s": "FFBC",
    "n": "First Financial Bancorp. - Common Stock"
  },
  {
    "s": "FFIN",
    "n": "First Financial Bankshares, Inc. - Common Stock"
  },
  {
    "s": "FFIV",
    "n": "F5, Inc. - Common Stock"
  },
  {
    "s": "FFR",
    "n": "FF EAI Robotics Ecosystem Inc. - Common Stock"
  },
  {
    "s": "FG",
    "n": "F&G Annuities & Life, Inc. Common Stock"
  },
  {
    "s": "FGBI",
    "n": "First Guaranty Bancshares, Inc. - Common Stock"
  },
  {
    "s": "FGC",
    "n": "FG Communities Holdings Inc. - Common Stock"
  },
  {
    "s": "FGI",
    "n": "FGI Industries Ltd. - Ordinary Shares"
  },
  {
    "s": "FGII",
    "n": "FG Imperii Acquisition Corp. - Class A Ordinary Shares"
  },
  {
    "s": "FGIIU",
    "n": "FG Imperii Acquisition Corp. - Units"
  },
  {
    "s": "FGIIW",
    "n": "FG Imperii Acquisition Corp. - Warrants"
  },
  {
    "s": "FGL",
    "n": "Founder Group Limited - Class A Ordinary Shares"
  },
  {
    "s": "FGN",
    "n": "F&G Annuities & Life, Inc. 7.950% Senior Notes due 2053"
  },
  {
    "s": "FGSN",
    "n": "F&G Annuities & Life, Inc. 7.300% Junior Subordinated Notes due 2065"
  },
  {
    "s": "FHB",
    "n": "First Hawaiian, Inc. - Common Stock"
  },
  {
    "s": "FHI",
    "n": "Federated Hermes, Inc. Common Stock"
  },
  {
    "s": "FHN",
    "n": "First Horizon Corporation Common Stock"
  },
  {
    "s": "FHTX",
    "n": "Foghorn Therapeutics Inc. - Common Stock"
  },
  {
    "s": "FIBK",
    "n": "First Interstate BancSystem, Inc. - Common Stock"
  },
  {
    "s": "FICO",
    "n": "Fair Isaac Corporation Common Stock"
  },
  {
    "s": "FIEE",
    "n": "FiEE, Inc - Common Stock"
  },
  {
    "s": "FIG",
    "n": "Figma, Inc. Class A Common Stock"
  },
  {
    "s": "FIGR",
    "n": "Figure Technology Solutions, Inc. - Class A Common Stock"
  },
  {
    "s": "FIGS",
    "n": "FIGS, Inc. Class A Common Stock"
  },
  {
    "s": "FIGX",
    "n": "FIGX Capital Acquisition Corp. - Class A ordinary share"
  },
  {
    "s": "FIGXU",
    "n": "FIGX Capital Acquisition Corp. - Units"
  },
  {
    "s": "FINS",
    "n": "Angel Oak Financial Strategies Income Term Trust Common Shares of Beneficial Interest"
  },
  {
    "s": "FINV",
    "n": "FinVolution Group American Depositary Shares"
  },
  {
    "s": "FINW",
    "n": "FinWise Bancorp - Common Stock"
  },
  {
    "s": "FIP",
    "n": "FTAI Infrastructure Inc. - Common Stock"
  },
  {
    "s": "FIRY",
    "n": "Firy Inc. Class A Common Stock"
  },
  {
    "s": "FIS",
    "n": "Fidelity National Information Services, Inc. Common Stock"
  },
  {
    "s": "FISI",
    "n": "Financial Institutions, Inc. - Common Stock"
  },
  {
    "s": "FISK",
    "n": "Empire State Realty OP, L.P. Series 250 Operating Partnership Units Representing Limited Partnership Interests"
  },
  {
    "s": "FISN",
    "n": "Deep Fission, Inc. - Common Stock"
  },
  {
    "s": "FISV",
    "n": "Fiserv, Inc. - Common Stock"
  },
  {
    "s": "FITB",
    "n": "Fifth Third Bancorp Common Stock"
  },
  {
    "s": "FIVE",
    "n": "Five Below, Inc. - Common Stock"
  },
  {
    "s": "FIVN",
    "n": "Five9, Inc. - Common Stock"
  },
  {
    "s": "FIX",
    "n": "Comfort Systems USA, Inc. Common Stock"
  },
  {
    "s": "FIZZ",
    "n": "National Beverage Corp. - Common Stock"
  },
  {
    "s": "FJDI",
    "n": "ARC Group Securities Acquisition I - Class A Ordinary Shares"
  },
  {
    "s": "FJDIU",
    "n": "ARC Group Securities Acquisition I - Units"
  },
  {
    "s": "FJDIW",
    "n": "ARC Group Securities Acquisition I - Warrants"
  },
  {
    "s": "FJET",
    "n": "Starfighters Space, Inc. Common Stock"
  },
  {
    "s": "FKWL",
    "n": "Franklin Wireless Corp. - common stock"
  },
  {
    "s": "FLD",
    "n": "Fold Holdings, Inc. - Class A Common Stock"
  },
  {
    "s": "FLEX",
    "n": "Flex Ltd. - Ordinary Shares"
  },
  {
    "s": "FLG",
    "n": "Flagstar Bank, N.A. Common Stock"
  },
  {
    "s": "FLGT",
    "n": "Fulgent Genetics, Inc. - Common Stock"
  },
  {
    "s": "FLL",
    "n": "Full House Resorts, Inc. - Common Stock"
  },
  {
    "s": "FLNA",
    "n": "Filana Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "FLNC",
    "n": "Fluence Energy, Inc. - Class A Common Stock"
  },
  {
    "s": "FLNG",
    "n": "FLEX LNG Ltd. Ordinary Shares"
  },
  {
    "s": "FLNT",
    "n": "Fluent, Inc. - Common Stock"
  },
  {
    "s": "FLO",
    "n": "Flowers Foods, Inc. Common Stock"
  },
  {
    "s": "FLOC",
    "n": "Flowco Holdings Inc. Class A Common Stock"
  },
  {
    "s": "FLR",
    "n": "Fluor Corporation Common Stock"
  },
  {
    "s": "FLS",
    "n": "Flowserve Corporation Common Stock"
  },
  {
    "s": "FLUT",
    "n": "Flutter Entertainment plc Ordinary Shares"
  },
  {
    "s": "FLUX",
    "n": "Flux Power Holdings, Inc. - Common Stock"
  },
  {
    "s": "FLWS",
    "n": "1-800-FLOWERS.COM, Inc. - Class A Common Stock"
  },
  {
    "s": "FLX",
    "n": "BingEx Limited - American Depositary Shares"
  },
  {
    "s": "FLXS",
    "n": "Flexsteel Industries, Inc. - Common Stock"
  },
  {
    "s": "FLY",
    "n": "Firefly Aerospace Inc. - Common Stock"
  },
  {
    "s": "FLYE",
    "n": "Fly-E Group, Inc. - Common Stock"
  },
  {
    "s": "FLYW",
    "n": "Flywire Corporation - Voting Common Stock"
  },
  {
    "s": "FLYX",
    "n": "flyExclusive, Inc. Class A Common Stock"
  },
  {
    "s": "FMAC",
    "n": "Future Money Acquisition Corporation - Ordinary Shares"
  },
  {
    "s": "FMACU",
    "n": "Future Money Acquisition Corporation - Units"
  },
  {
    "s": "FMAO",
    "n": "Farmers & Merchants Bancorp, Inc. - Common Stock"
  },
  {
    "s": "FMBH",
    "n": "First Mid Bancshares, Inc. - Common Stock"
  },
  {
    "s": "FMC",
    "n": "FMC Corporation Common Stock"
  },
  {
    "s": "FMFC",
    "n": "Kandal M Venture Limited - Class A ordinary Shares"
  },
  {
    "s": "FMNB",
    "n": "Farmers National Banc Corp. - Common Stock"
  },
  {
    "s": "FMS",
    "n": "Fresenius Medical Care AG American Depositary Shares (Each representing 1/2 of an Ordinary Share)"
  },
  {
    "s": "FMST",
    "n": "Foremost Clean Energy Ltd. - Common Shares"
  },
  {
    "s": "FMX",
    "n": "Fomento Economico Mexicano S.A.B. de C.V. Common Stock"
  },
  {
    "s": "FN",
    "n": "Fabrinet Ordinary Shares"
  },
  {
    "s": "FNB",
    "n": "F.N.B. Corporation Common Stock"
  },
  {
    "s": "FND",
    "n": "Floor & Decor Holdings, Inc. Common Stock"
  },
  {
    "s": "FNF",
    "n": "Fidelity National Financial, Inc. Common Stock"
  },
  {
    "s": "FNGD",
    "n": "MicroSectors FANG  Index -3X Inverse Leveraged ETNs due January 8, 2038"
  },
  {
    "s": "FNGO",
    "n": "MicroSectors FANG  Index 2X Leveraged ETNs due January 8, 2038"
  },
  {
    "s": "FNGR",
    "n": "FingerMotion, Inc. - common stock"
  },
  {
    "s": "FNKO",
    "n": "Funko, Inc. - Class A Common Stock"
  },
  {
    "s": "FNLC",
    "n": "First Bancorp, Inc (ME) - Common Stock"
  },
  {
    "s": "FNRN",
    "n": "First Northern Community Bancorp - Common stock"
  },
  {
    "s": "FNUC",
    "n": "Frontier Nuclear and Minerals Inc. - Common Shares"
  },
  {
    "s": "FNV",
    "n": "Franco-Nevada Corporation"
  },
  {
    "s": "FNWB",
    "n": "First Northwest Bancorp - Common Stock"
  },
  {
    "s": "FNWD",
    "n": "Finward Bancorp - common stock"
  },
  {
    "s": "FOA",
    "n": "Finance of America Companies Inc. Class A Common Stock"
  },
  {
    "s": "FOCL",
    "n": "EDAP TMS S.A. - American Depositary Shares, each representing One Ordinary Share"
  },
  {
    "s": "FOFO",
    "n": "Hang Feng Technology Innovation Co., Ltd. - Ordinary Shares"
  },
  {
    "s": "FOIL",
    "n": "Londian Wason New Energy Tech Inc. American Depositary Shares, each representing five Ordinary Shares"
  },
  {
    "s": "FOR",
    "n": "Forestar Group Inc Common Stock "
  },
  {
    "s": "FORM",
    "n": "FormFactor, Inc. - Common Stock"
  },
  {
    "s": "FORR",
    "n": "Forrester Research, Inc. - Common Stock"
  },
  {
    "s": "FORTY",
    "n": "Formula Systems (1985) Ltd. - American Depositary Shares"
  },
  {
    "s": "FOSL",
    "n": "Fossil Group, Inc. - Common Stock"
  },
  {
    "s": "FOUR",
    "n": "Shift4 Payments, Inc. Class A Common Stock"
  },
  {
    "s": "FOX",
    "n": "Fox Corporation - Class B Common Stock"
  },
  {
    "s": "FOXA",
    "n": "Fox Corporation - Class A Common Stock"
  },
  {
    "s": "FOXF",
    "n": "Fox Factory Holding Corp. - Common Stock"
  },
  {
    "s": "FOXX",
    "n": "Foxx Development Holdings Inc. - Common Stock"
  },
  {
    "s": "FPH",
    "n": "Five Point Holdings, LLC Class A Common Shares"
  },
  {
    "s": "FPI",
    "n": "Farmland Partners Inc. Common Stock"
  },
  {
    "s": "FPS",
    "n": "Forgent Power Solutions, Inc. Class A Common Stock"
  },
  {
    "s": "FR",
    "n": "First Industrial Realty Trust, Inc. Common Stock"
  },
  {
    "s": "FRAF",
    "n": "Franklin Financial Services Corporation - Common Stock"
  },
  {
    "s": "FRBA",
    "n": "First Bank  - Common Stock"
  },
  {
    "s": "FRBT",
    "n": "Forbright, Inc. - Class A Common Stock"
  },
  {
    "s": "FRD",
    "n": "Friedman Industries Inc. - Common Stock"
  },
  {
    "s": "FRGT",
    "n": "Freight Technologies, Inc. - Ordinary Shares"
  },
  {
    "s": "FRHC",
    "n": "Freedom Holding Corp. - Common Stock"
  },
  {
    "s": "FRME",
    "n": "First Merchants Corporation - Common Stock"
  },
  {
    "s": "FRMI",
    "n": "Fermi Inc. - Common Stock"
  },
  {
    "s": "FRMM",
    "n": "Forum Markets, Incorporated - Common Stock"
  },
  {
    "s": "FRNM",
    "n": "Freenome, Inc. - Common stock"
  },
  {
    "s": "FRO",
    "n": "Frontline Plc Ordinary Shares"
  },
  {
    "s": "FROG",
    "n": "JFrog Ltd. - Ordinary shares"
  },
  {
    "s": "FRPH",
    "n": "FRP Holdings, Inc. - Common Stock"
  },
  {
    "s": "FRPT",
    "n": "Freshpet, Inc. - Common Stock"
  },
  {
    "s": "FRSH",
    "n": "Freshworks Inc. - Class A Common Stock"
  },
  {
    "s": "FRST",
    "n": "Primis Financial Corp. - Common Stock"
  },
  {
    "s": "FRSX",
    "n": "Foresight Autonomous Holdings Ltd. - American Depositary Shares"
  },
  {
    "s": "FRT",
    "n": "Federal Realty Investment Trust Common Stock"
  },
  {
    "s": "FRTT",
    "n": "Fort Technology Inc. - Common Shares"
  },
  {
    "s": "FRVO",
    "n": "Fervo Energy Company - Class A common stock"
  },
  {
    "s": "FSBC",
    "n": "Five Star Bancorp - Common Stock"
  },
  {
    "s": "FSBW",
    "n": "FS Bancorp, Inc. - Common Stock"
  },
  {
    "s": "FSCO",
    "n": "FS Credit Opportunities Corp. Common Stock"
  },
  {
    "s": "FSHP",
    "n": "Flag Ship Acquisition Corp. - Ordinary Shares"
  },
  {
    "s": "FSHPR",
    "n": "Flag Ship Acquisition Corp. - Right"
  },
  {
    "s": "FSHPU",
    "n": "Flag Ship Acquisition Corp. - Unit"
  },
  {
    "s": "FSI",
    "n": "Flexible Solutions International Inc. Common Stock (CDA)"
  },
  {
    "s": "FSK",
    "n": "FS KKR Capital Corp. Common Stock"
  },
  {
    "s": "FSLR",
    "n": "First Solar, Inc. - Common Stock"
  },
  {
    "s": "FSLY",
    "n": "Fastly, Inc. - Class A Common Stock"
  },
  {
    "s": "FSM",
    "n": "Fortuna Mining Corp. Common Shares"
  },
  {
    "s": "FSP",
    "n": "Franklin Street Properties Corp. Common Stock"
  },
  {
    "s": "FSS",
    "n": "Federal Signal Corporation Common Stock"
  },
  {
    "s": "FSTR",
    "n": "L.B. Foster Company - Common Stock"
  },
  {
    "s": "FSUN",
    "n": "FirstSun Capital Bancorp - Common Stock"
  },
  {
    "s": "FSV",
    "n": "FirstService Corporation - Common Shares"
  },
  {
    "s": "FT",
    "n": "Franklin Universal Trust Common Stock"
  },
  {
    "s": "FTAI",
    "n": "FTAI Aviation Ltd. - Common Stock"
  },
  {
    "s": "FTCI",
    "n": "FTC Solar, Inc. - Common Stock"
  },
  {
    "s": "FTDR",
    "n": "Frontdoor, Inc. - Common Stock"
  },
  {
    "s": "FTEK",
    "n": "Fuel Tech, Inc. - Common Stock"
  },
  {
    "s": "FTF",
    "n": "Franklin Limited Duration Income Trust Common Shares of Beneficial Interest"
  },
  {
    "s": "FTFT",
    "n": "Future FinTech Group Inc. - Common Stock"
  },
  {
    "s": "FTH",
    "n": "Faeth Therapeutics, Inc.  - Common Stock"
  },
  {
    "s": "FTHA",
    "n": "Forefront Tech Holdings Acquisition Corp - Class A Ordinary Shares"
  },
  {
    "s": "FTHAU",
    "n": "Forefront Tech Holdings Acquisition Corp - Unit"
  },
  {
    "s": "FTHM",
    "n": "Fathom Holdings Inc. - Common Stock"
  },
  {
    "s": "FTI",
    "n": "TechnipFMC plc Ordinary Share"
  },
  {
    "s": "FTK",
    "n": "Flotek Industries, Inc. Common Stock"
  },
  {
    "s": "FTLF",
    "n": "FitLife Brands, Inc. - Common Stock"
  },
  {
    "s": "FTNT",
    "n": "Fortinet, Inc. - Common Stock"
  },
  {
    "s": "FTRA",
    "n": "FutureCorp Space Acquisition 1 Class A Ordinary Shares"
  },
  {
    "s": "FTRE",
    "n": "Fortrea Holdings Inc. - Common Stock"
  },
  {
    "s": "FTS",
    "n": "Fortis Inc. Common Shares"
  },
  {
    "s": "FTV",
    "n": "Fortive Corporation Common Stock "
  },
  {
    "s": "FTW",
    "n": "Presidio Production Company Class A Common Stock"
  },
  {
    "s": "FUBO",
    "n": "FuboTV Inc. Class A Common Stock"
  },
  {
    "s": "FUFU",
    "n": "BitFuFu Inc. - Class A Ordinary Shares"
  },
  {
    "s": "FUL",
    "n": "H. B. Fuller Company Common Stock"
  },
  {
    "s": "FULC",
    "n": "Fulcrum Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "FULT",
    "n": "Fulton Financial Corporation - Common Stock"
  },
  {
    "s": "FUN",
    "n": "Six Flags Entertainment Corporation Common Stock New"
  },
  {
    "s": "FUNC",
    "n": "First United Corporation - Common Stock"
  },
  {
    "s": "FURY",
    "n": "Fury Gold Mines Limited Common Shares"
  },
  {
    "s": "FUSB",
    "n": "First US Bancshares, Inc. - Common Stock"
  },
  {
    "s": "FUSE",
    "n": "Fusemachines Inc. - Common stock"
  },
  {
    "s": "FUSEW",
    "n": "Fusemachines Inc. - Warrants"
  },
  {
    "s": "FUTU",
    "n": "Futu Holdings Limited - American Depositary Shares"
  },
  {
    "s": "FVAV",
    "n": "Fortress Value Acquisition Corp. V - Class A Ordinary Shares"
  },
  {
    "s": "FVCB",
    "n": "FVCBankcorp, Inc. - Common Stock"
  },
  {
    "s": "FVN",
    "n": "Future Vision II Acquisition Corporation - Ordinary Shares"
  },
  {
    "s": "FVNNR",
    "n": "Future Vision II Acquisition Corporation - Right"
  },
  {
    "s": "FVNNU",
    "n": "Future Vision II Acquisition Corporation - Units"
  },
  {
    "s": "FVRR",
    "n": "Fiverr International Ltd. Ordinary Shares, no par value"
  },
  {
    "s": "FWAC",
    "n": "Futurewave Acquisition Corporation - Ordinary Shares"
  },
  {
    "s": "FWACU",
    "n": "Futurewave Acquisition Corporation - Units"
  },
  {
    "s": "FWACW",
    "n": "Futurewave Acquisition Corporation - Warrants"
  },
  {
    "s": "FWDI",
    "n": "Forward Industries, Inc. - Common Stock"
  },
  {
    "s": "FWONA",
    "n": "Liberty Media Corporation - Series A Common Stock"
  },
  {
    "s": "FWONK",
    "n": "Liberty Media Corporation - Series C Common Stock"
  },
  {
    "s": "FWRD",
    "n": "Forward Air Corporation - Common Stock"
  },
  {
    "s": "FWRG",
    "n": "First Watch Restaurant Group, Inc. - Common Stock"
  },
  {
    "s": "FXAC",
    "n": "FortuneX Acquisition Corporation - Ordinary shares"
  },
  {
    "s": "FXACU",
    "n": "FortuneX Acquisition Corporation - Units"
  },
  {
    "s": "FXHO",
    "n": "UTime Limited - Class A Ordinary Shares"
  },
  {
    "s": "FXNC",
    "n": "First National Corporation - Common Stock"
  },
  {
    "s": "G",
    "n": "Genpact Limited Common Stock"
  },
  {
    "s": "GAB",
    "n": "Gabelli Equity Trust, Inc. (The) Common Stock"
  },
  {
    "s": "GABC",
    "n": "German American Bancorp, Inc. - Common Stock"
  },
  {
    "s": "GAIA",
    "n": "Gaia, Inc. - Class A Common Stock"
  },
  {
    "s": "GAIN",
    "n": "Gladstone Investment Corporation - Business Development Company"
  },
  {
    "s": "GAING",
    "n": "Gladstone Investment Corporation - 7.125% Notes due 2031"
  },
  {
    "s": "GAINI",
    "n": "Gladstone Investment Corporation - 7.875% Notes due 2030"
  },
  {
    "s": "GAINZ",
    "n": "Gladstone Investment Corporation - 4.875% Notes due 2028"
  },
  {
    "s": "GALT",
    "n": "Galectin Therapeutics Inc. - Common Stock"
  },
  {
    "s": "GAM",
    "n": "General American Investors, Inc. Common Stock"
  },
  {
    "s": "GAME",
    "n": "GameSquare Holdings, Inc. - Common stock"
  },
  {
    "s": "GANX",
    "n": "Gain Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "GAP",
    "n": "Gap, Inc. (The) Common Stock"
  },
  {
    "s": "GASS",
    "n": "StealthGas, Inc. - common stock"
  },
  {
    "s": "GATX",
    "n": "GATX Corporation Common Stock"
  },
  {
    "s": "GAU",
    "n": "Galiano Gold Inc."
  },
  {
    "s": "GAUZ",
    "n": "Gauzy Ltd. - Ordinary Shares"
  },
  {
    "s": "GBAB",
    "n": "Guggenheim Taxable Municipal Bond & Investment Grade Debt Trust Common Shares of Beneficial Interest"
  },
  {
    "s": "GBCI",
    "n": "Glacier Bancorp, Inc. Common Stock"
  },
  {
    "s": "GBFH",
    "n": "GBank Financial Holdings Inc. - Common Stock"
  },
  {
    "s": "GBLI",
    "n": "Global Indemnity Group, LLC - Class A Common Shares"
  },
  {
    "s": "GBR",
    "n": "New Concept Energy, Inc Common Stock"
  },
  {
    "s": "GBX",
    "n": "Greenbrier Companies, Inc. (The) Common Stock"
  },
  {
    "s": "GCBC",
    "n": "Greene County Bancorp, Inc. - Common Stock"
  },
  {
    "s": "GCDT",
    "n": "Green Circle Decarbonize Technology Limited Class A Ordinary Shares"
  },
  {
    "s": "GCGR",
    "n": "General Catalyst Global Resilience Merger Corp. - Class A Ordinary Shares"
  },
  {
    "s": "GCGRU",
    "n": "General Catalyst Global Resilience Merger Corp. - Units"
  },
  {
    "s": "GCGRW",
    "n": "General Catalyst Global Resilience Merger Corp. - Warrants"
  },
  {
    "s": "GCL",
    "n": "GCL Global Holdings Ltd - Ordinary Shares"
  },
  {
    "s": "GCLWW",
    "n": "GCL Global Holdings Ltd - Warrants"
  },
  {
    "s": "GCMG",
    "n": "GCM Grosvenor Inc. - Class A Common Stock"
  },
  {
    "s": "GCO",
    "n": "Genesco Inc. Common Stock"
  },
  {
    "s": "GCT",
    "n": "GigaCloud Technology Inc - Class A Ordinary Shares"
  },
  {
    "s": "GCTK",
    "n": "GlucoTrack, Inc. - Common Stock"
  },
  {
    "s": "GCTS",
    "n": "GCT Semiconductor Holding, Inc. Common Stock"
  },
  {
    "s": "GD",
    "n": "General Dynamics Corporation Common Stock"
  },
  {
    "s": "GDC",
    "n": "GD Culture Group Limited - Common Stock"
  },
  {
    "s": "GDDY",
    "n": "GoDaddy Inc. Class A Common Stock"
  },
  {
    "s": "GDEV",
    "n": "GDEV Inc. - Ordinary Shares"
  },
  {
    "s": "GDHG",
    "n": "Golden Heaven Group Holdings Ltd.  - Class A Ordinary Shares"
  },
  {
    "s": "GDOT",
    "n": "Green Dot Corporation Class A Common Stock, $0.001 par value"
  },
  {
    "s": "GDRX",
    "n": "GoodRx Holdings, Inc. - Class A Common Stock"
  },
  {
    "s": "GDS",
    "n": "GDS Holdings Limited - American Depositary Shares"
  },
  {
    "s": "GDTC",
    "n": "CytoMed Therapeutics Limited - Ordinary Shares"
  },
  {
    "s": "GDV",
    "n": "Gabelli Dividend & Income Trust Common Shares of Beneficial Interest"
  },
  {
    "s": "GDYN",
    "n": "Grid Dynamics Holdings, Inc. - Class A Common Stock"
  },
  {
    "s": "GE",
    "n": "GE Aerospace Common Stock"
  },
  {
    "s": "GECCG",
    "n": "Great Elm Capital Corp. - 7.75% Notes Due 2030"
  },
  {
    "s": "GECCH",
    "n": "Great Elm Capital Corp. - 8.125% Notes Due 2029"
  },
  {
    "s": "GECCI",
    "n": "Great Elm Capital Corp. - 8.50% NOTES DUE 2029"
  },
  {
    "s": "GEF",
    "n": "Greif Inc. Class A Common Stock"
  },
  {
    "s": "GEF-B",
    "n": "Greif, Inc. Corporation Class B Common Stock"
  },
  {
    "s": "GEG",
    "n": "Great Elm Group, Inc.  - Common Stock"
  },
  {
    "s": "GEGGL",
    "n": "Great Elm Group, Inc.  - 7.25% Notes due 2027"
  },
  {
    "s": "GEHC",
    "n": "GE HealthCare Technologies Inc. - Common Stock"
  },
  {
    "s": "GEL",
    "n": "Genesis Energy, L.P. Common Units"
  },
  {
    "s": "GELS",
    "n": "Gelteq Limited - Ordinary Shares"
  },
  {
    "s": "GEMI",
    "n": "Gemini Space Station, Inc. - Class A Common Stock"
  },
  {
    "s": "GEN",
    "n": "Gen Digital Inc. - Common Stock"
  },
  {
    "s": "GENB",
    "n": "Generate Biomedicines, Inc. - Common Stock"
  },
  {
    "s": "GENC",
    "n": "Gencor Industries, Inc. Common Stock"
  },
  {
    "s": "GENI",
    "n": "Genius Sports Limited Ordinary Shares"
  },
  {
    "s": "GENK",
    "n": "GEN Restaurant Group, Inc. - Class A Common Stock"
  },
  {
    "s": "GEOS",
    "n": "Geospace Technologies Corporation - Common Stock"
  },
  {
    "s": "GERN",
    "n": "Geron Corporation - Common Stock"
  },
  {
    "s": "GEV",
    "n": "GE Vernova Inc. Common Stock"
  },
  {
    "s": "GEVO",
    "n": "Gevo, Inc. - Common Stock"
  },
  {
    "s": "GFAI",
    "n": "Guardforce AI Co., Limited - Ordinary Shares"
  },
  {
    "s": "GFF",
    "n": "Griffon Corporation Common Stock"
  },
  {
    "s": "GFI",
    "n": "Gold Fields Limited American Depositary Shares"
  },
  {
    "s": "GFL",
    "n": "GFL Environmental Inc. Subordinate voting shares, no par value"
  },
  {
    "s": "GFR",
    "n": "Greenfire Resources Ltd. Common Shares"
  },
  {
    "s": "GFS",
    "n": "GlobalFoundries Inc. - Ordinary Share"
  },
  {
    "s": "GFUZ",
    "n": "General Fusion Group Ltd. - Common Shares"
  },
  {
    "s": "GGAL",
    "n": "Grupo Financiero Galicia S.A. - American Depositary Shares, Class B Shares underlying"
  },
  {
    "s": "GGB",
    "n": "Gerdau S.A. Common Stock"
  },
  {
    "s": "GGG",
    "n": "Graco Inc. Common Stock"
  },
  {
    "s": "GGN",
    "n": "GAMCO Global Gold, Natural Resources & Income Trust"
  },
  {
    "s": "GGR",
    "n": "Gogoro Inc. - Ordinary Shares"
  },
  {
    "s": "GGT",
    "n": "Gabelli Multi-Media Trust, Inc. (The) Common Stock"
  },
  {
    "s": "GGZ",
    "n": "Gabelli Global Small and Mid Cap Value Trust (The) Common Shares of Beneficial Interest"
  },
  {
    "s": "GH",
    "n": "Guardant Health, Inc. - Common Stock"
  },
  {
    "s": "GHC",
    "n": "Graham Holdings Company Common Stock"
  },
  {
    "s": "GHG",
    "n": "GreenTree Hospitality Group Ltd. American depositary shares, each representing one Class A ordinary share"
  },
  {
    "s": "GHM",
    "n": "Graham Corporation Common Stock"
  },
  {
    "s": "GHRS",
    "n": "GH Research PLC - Ordinary Shares"
  },
  {
    "s": "GHXI",
    "n": "Gores Holdings XI, Inc. - Class A Ordinary Shares"
  },
  {
    "s": "GHXIU",
    "n": "Gores Holdings XI, Inc. - Units"
  },
  {
    "s": "GIB",
    "n": "CGI Inc. Common Stock"
  },
  {
    "s": "GIBO",
    "n": "GIBO Holdings Limited - Class A Ordinary Shares"
  },
  {
    "s": "GIBOW",
    "n": "GIBO Holdings Limited - Warrants"
  },
  {
    "s": "GIC",
    "n": "Global Industrial Company Common Stock"
  },
  {
    "s": "GIFT",
    "n": "Giftify, Inc. - Common Stock"
  },
  {
    "s": "GIGM",
    "n": "GigaMedia Limited - Ordinary Shares"
  },
  {
    "s": "GIII",
    "n": "G-III Apparel Group, LTD. - Common Stock"
  },
  {
    "s": "GIL",
    "n": "Gildan Activewear, Inc. Class A Sub. Vot. Common Stock"
  },
  {
    "s": "GILD",
    "n": "Gilead Sciences, Inc. - Common Stock"
  },
  {
    "s": "GILT",
    "n": "Gilat Satellite Networks Ltd. - Ordinary Shares"
  },
  {
    "s": "GIPR",
    "n": "Generation Income Properties Inc. - Common stock"
  },
  {
    "s": "GIS",
    "n": "General Mills, Inc. Common Stock"
  },
  {
    "s": "GITS",
    "n": "Global Interactive Technologies, Inc. Common Stock - Common Stock"
  },
  {
    "s": "GIW",
    "n": "GigCapital8 Corp. - Class A Ordinary Shares"
  },
  {
    "s": "GIWWU",
    "n": "GigCapital8 Corp. - Units"
  },
  {
    "s": "GIX",
    "n": "GigCapital9 Corp. - Class A Ordinary Share"
  },
  {
    "s": "GIXI",
    "n": "Gix Internet Ltd. - Ordinary Shares"
  },
  {
    "s": "GIXXU",
    "n": "GigCapital9 Corp. - Units"
  },
  {
    "s": "GJH",
    "n": "Synthetic Fixed-Income Securities Inc 6.375% (STRATS) Cl A-1"
  },
  {
    "s": "GJO",
    "n": "Synthetic Fixed-Income Securities, Inc. on behalf of STRATS(SM) Trust for Wal-Mart Stores, Inc. Securities, Series 2004-5"
  },
  {
    "s": "GJP",
    "n": "Synthetic Fixed-Income Securities, Inc. on behalf of STRATS (SM) Trust for Dominion Resources, Inc. Securities, Series 2005-6, Floating Rate Structured Repackaged Asset-Backed Trust Securities (STRATS) Certificates"
  },
  {
    "s": "GJR",
    "n": "Synthetic Fixed-Income Securities, Inc. STRATS Trust for Procter&Gamble Securities, Series 2006-1"
  },
  {
    "s": "GJS",
    "n": "Goldman Sachs Group Securities STRATS Trust for Goldman Sachs Group Securities, Series 2006-2"
  },
  {
    "s": "GJT",
    "n": "Synthetic Fixed-Income Securities, Inc. Floating Rate Structured Repackaged Asset-Backed Trust Securities Certificates, Series 2006-3"
  },
  {
    "s": "GKOS",
    "n": "Glaukos Corporation Common Stock"
  },
  {
    "s": "GL",
    "n": "Globe Life Inc. Common Stock"
  },
  {
    "s": "GLAS",
    "n": "Glass House Brands Inc. Subordinate Voting Shares"
  },
  {
    "s": "GLBE",
    "n": "Global-E Online Ltd. - ordinary shares"
  },
  {
    "s": "GLBS",
    "n": "Globus Maritime Limited - Common Stock"
  },
  {
    "s": "GLDG",
    "n": "GoldMining Inc. Common Shares"
  },
  {
    "s": "GLE",
    "n": "Global Engine Group Holding Limited - Class A Ordinary Shares"
  },
  {
    "s": "GLED",
    "n": "GalaxyEdge Acquisition Corporation Ordinary Shares"
  },
  {
    "s": "GLED-U",
    "n": "GalaxyEdge Acquisition Corporation Units, each consisting of one Ordinary Share and one Right entitling the holder to receive 1/4th of one ordinary share"
  },
  {
    "s": "GLIBA",
    "n": "Liberty Capital Corporation - Series A GCI Group Common Stock"
  },
  {
    "s": "GLIBK",
    "n": "Liberty Capital Corporation - Series C GCI Group Common Stock"
  },
  {
    "s": "GLND",
    "n": "Greenland Energy Company - Common Stock"
  },
  {
    "s": "GLNG",
    "n": "Golar LNG Limited - Common Shares"
  },
  {
    "s": "GLOB",
    "n": "Globant S.A. Common Shares"
  },
  {
    "s": "GLOO",
    "n": "Gloo Holdings, Inc. - Common Stock"
  },
  {
    "s": "GLPI",
    "n": "Gaming and Leisure Properties, Inc. - Common Stock"
  },
  {
    "s": "GLRE",
    "n": "Greenlight Reinsurance, Ltd. - Class A Ordinary Shares"
  },
  {
    "s": "GLSI",
    "n": "Greenwich LifeSciences, Inc. - Common stock"
  },
  {
    "s": "GLU",
    "n": "Gabelli Global Utility Common Shares of Beneficial Ownership"
  },
  {
    "s": "GLUE",
    "n": "Monte Rosa Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "GLW",
    "n": "Corning Incorporated Common Stock"
  },
  {
    "s": "GLXG",
    "n": "Galaxy Payroll Group Limited - Class A Ordinary Shares"
  },
  {
    "s": "GLXY",
    "n": "Galaxy Digital Inc. - Class A common stock"
  },
  {
    "s": "GM",
    "n": "General Motors Company Common Stock"
  },
  {
    "s": "GMAB",
    "n": "Genmab A/S - American Depositary Shares"
  },
  {
    "s": "GME",
    "n": "GameStop Corporation Common Stock"
  },
  {
    "s": "GME-W",
    "n": "GameStop Corporation Warrants to Purchase Common Stock"
  },
  {
    "s": "GMED",
    "n": "Globus Medical, Inc. Class A Common Stock"
  },
  {
    "s": "GMEX",
    "n": "GMEX ROBOTICS CORPORATION - Class A Ordinary Shares"
  },
  {
    "s": "GMHS",
    "n": "Gamehaus Holdings Inc. - Class A Ordinary Shares"
  },
  {
    "s": "GMM",
    "n": "Global Mofy AI Limited  - Class A Ordinary Shares"
  },
  {
    "s": "GMRS",
    "n": "GMR Solutions Inc. Class A Common Stock"
  },
  {
    "s": "GMTL",
    "n": "Guardian Metal Resources PLC ADS"
  },
  {
    "s": "GNE",
    "n": "Genie Energy Ltd. Class B Common Stock Stock"
  },
  {
    "s": "GNK",
    "n": "Genco Shipping & Trading Limited Ordinary Shares New (Marshall Islands)"
  },
  {
    "s": "GNL",
    "n": "Global Net Lease, Inc. Common Stock"
  },
  {
    "s": "GNLN",
    "n": "Greenlane Holdings, Inc. - Class A Common Stock"
  },
  {
    "s": "GNLX",
    "n": "Genelux Corporation - Common Stock"
  },
  {
    "s": "GNPX",
    "n": "Genprex, Inc. - Common Stock"
  },
  {
    "s": "GNRC",
    "n": "Generac Holdlings Inc. Common Stock"
  },
  {
    "s": "GNS",
    "n": "Genius Group Limited Ordinary Shares"
  },
  {
    "s": "GNSS",
    "n": "Genasys Inc. - Common Stock"
  },
  {
    "s": "GNT",
    "n": "GAMCO Natural Resources, Gold & Income Trust"
  },
  {
    "s": "GNTA",
    "n": "Genenta Science S.p.A. - American Depositary Shares"
  },
  {
    "s": "GNTX",
    "n": "Gentex Corporation - Common Stock"
  },
  {
    "s": "GNW",
    "n": "Genworth Financial Inc Common Stock"
  },
  {
    "s": "GO",
    "n": "Grocery Outlet Holding Corp. - Common Stock"
  },
  {
    "s": "GOAI",
    "n": "Eva Live Inc. - Common Stock"
  },
  {
    "s": "GOGO",
    "n": "Gogo Inc. - Common Stock"
  },
  {
    "s": "GOLD",
    "n": "Gold.com, Inc. Common Stock"
  },
  {
    "s": "GOLF",
    "n": "Acushnet Holdings Corp. Common Stock"
  },
  {
    "s": "GOOD",
    "n": "Gladstone Commercial Corporation - Real Estate Investment Trust"
  },
  {
    "s": "GOOG",
    "n": "Alphabet Inc. - Class C Capital Stock"
  },
  {
    "s": "GOOGL",
    "n": "Alphabet Inc. - Class A Common Stock"
  },
  {
    "s": "GOOS",
    "n": "Canada Goose Holdings Inc. Subordinate Voting Shares"
  },
  {
    "s": "GORO",
    "n": "Goldgroup Mining Inc. Common Shares"
  },
  {
    "s": "GOSS",
    "n": "Gossamer Bio, Inc. - Common Stock"
  },
  {
    "s": "GOTU",
    "n": "Gaotu Techedu Inc. American Depositary Shares"
  },
  {
    "s": "GOVX",
    "n": "GeoVax Labs, Inc. - Common Stock"
  },
  {
    "s": "GOW",
    "n": "GOWell Energy Technology - Ordinary shares"
  },
  {
    "s": "GP",
    "n": "GreenPower Motor Company Inc. - Common Shares"
  },
  {
    "s": "GPAC",
    "n": "General Purpose Acquisition Corp. - Class A Ordinary Shares"
  },
  {
    "s": "GPACU",
    "n": "General Purpose Acquisition Corp. - Units"
  },
  {
    "s": "GPAT",
    "n": "GP-Act III Acquisition Corp. - Class A Ordinary Share"
  },
  {
    "s": "GPATU",
    "n": "GP-Act III Acquisition Corp. - Units"
  },
  {
    "s": "GPATW",
    "n": "GP-Act III Acquisition Corp. - Warrants"
  },
  {
    "s": "GPC",
    "n": "Genuine Parts Company Common Stock"
  },
  {
    "s": "GPCR",
    "n": "Structure Therapeutics Inc. - American Depositary Shares"
  },
  {
    "s": "GPGI",
    "n": "GPGI, Inc. Class A Common Stock"
  },
  {
    "s": "GPI",
    "n": "Group 1 Automotive, Inc. Common Stock"
  },
  {
    "s": "GPJA",
    "n": "Georgia Power Company Series 2017A 5.00% Junior Subordinated Notes due October 1, 2077"
  },
  {
    "s": "GPK",
    "n": "Graphic Packaging Holding Company"
  },
  {
    "s": "GPMT",
    "n": "Granite Point Mortgage Trust Inc. Common Stock"
  },
  {
    "s": "GPN",
    "n": "Global Payments Inc. Common Stock"
  },
  {
    "s": "GPOR",
    "n": "Gulfport Energy Corporation Common Shares"
  },
  {
    "s": "GPRE",
    "n": "Green Plains, Inc. - Common Stock"
  },
  {
    "s": "GPRK",
    "n": "Geopark Ltd Common Shares"
  },
  {
    "s": "GPRO",
    "n": "GoPro, Inc. - Class A Common Stock"
  },
  {
    "s": "GPUS",
    "n": "Hyperscale Data, Inc. Common Stock"
  },
  {
    "s": "GRAB",
    "n": "Grab Holdings Limited - Class A Ordinary Shares"
  },
  {
    "s": "GRAL",
    "n": "GRAIL, Inc. - Common Stock"
  },
  {
    "s": "GRAN",
    "n": "Grande Group Limited - Class A Ordinary Shares"
  },
  {
    "s": "GRBK",
    "n": "Green Brick Partners, Inc. Common Stock"
  },
  {
    "s": "GRC",
    "n": "Gorman-Rupp Company (The) Common Stock"
  },
  {
    "s": "GRCE",
    "n": "Grace Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "GRDN",
    "n": "Guardian Pharmacy Services, Inc. Class A Common Stock"
  },
  {
    "s": "GRDX",
    "n": "GridAI Technologies Corp.  - Common Stock"
  },
  {
    "s": "GREEL",
    "n": "Vulcan Infrastructure and Power Inc. - 8.50% Senior Notes due 2026"
  },
  {
    "s": "GRFS",
    "n": "Grifols, S.A. - American Depositary Shares"
  },
  {
    "s": "GRI",
    "n": "GRI Bio, Inc. - Common Stock"
  },
  {
    "s": "GRML",
    "n": "Greenland Mines Ltd - Common Stock"
  },
  {
    "s": "GRMLW",
    "n": "Greenland Mines Ltd - Warrants"
  },
  {
    "s": "GRMN",
    "n": "Garmin Ltd. Common Stock (Switzerland)"
  },
  {
    "s": "GRN",
    "n": "iPath Series B Carbon Exchange-Traded Notes"
  },
  {
    "s": "GRND",
    "n": "Grindr Inc. Common Stock"
  },
  {
    "s": "GRNQ",
    "n": "Greenpro Capital Corp. - Common Stock"
  },
  {
    "s": "GRNT",
    "n": "Granite Ridge Resources, Inc. Common Stock"
  },
  {
    "s": "GRO",
    "n": "Brazil Potash Corp. Common Shares"
  },
  {
    "s": "GROV",
    "n": "Grove Collaborative Holdings, Inc. Class A Common Stock"
  },
  {
    "s": "GROW",
    "n": "U.S. Global Investors, Inc. - Class A Common Stock"
  },
  {
    "s": "GROY",
    "n": "Gold Royalty Corp. Common Shares"
  },
  {
    "s": "GROY-W",
    "n": "Gold Royalty Corp. Warrants"
  },
  {
    "s": "GRPN",
    "n": "Groupon, Inc. - Common Stock"
  },
  {
    "s": "GRRR",
    "n": "Gorilla Technology Group Inc. - Ordinary shares"
  },
  {
    "s": "GRSD",
    "n": "Grandstand Limited - Ordinary Shares"
  },
  {
    "s": "GRVY",
    "n": "GRAVITY Co., Ltd. - American depositary shares, each representing one common share."
  },
  {
    "s": "GRWG",
    "n": "GrowGeneration Corp. - Common Stock"
  },
  {
    "s": "GRX",
    "n": "The Gabelli Healthcare & Wellness Trust Common Shares of Beneficial Interest"
  },
  {
    "s": "GS",
    "n": "Goldman Sachs Group, Inc. (The) Common Stock"
  },
  {
    "s": "GSAT",
    "n": "Globalstar, Inc. - Common Stock"
  },
  {
    "s": "GSBC",
    "n": "Great Southern Bancorp, Inc. - Common Stock"
  },
  {
    "s": "GSBD",
    "n": "Goldman Sachs BDC, Inc. Common Stock"
  },
  {
    "s": "GSHD",
    "n": "Goosehead Insurance, Inc. - Class A Common Stock"
  },
  {
    "s": "GSHR",
    "n": "Gesher Acquisition Corp. II - Class A Ordinary Shares"
  },
  {
    "s": "GSHRU",
    "n": "Gesher Acquisition Corp. II - Units"
  },
  {
    "s": "GSHRW",
    "n": "Gesher Acquisition Corp. II - Warrants"
  },
  {
    "s": "GSIT",
    "n": "GSI Technology, Inc. - Common Stock"
  },
  {
    "s": "GSIW",
    "n": "Garden Stage Limited - Class A Ordinary Shares"
  },
  {
    "s": "GSK",
    "n": "GSK plc American Depositary Shares (Each representing two Ordinary Shares)"
  },
  {
    "s": "GSL",
    "n": "Global Ship Lease Inc New Class A Common Shares"
  },
  {
    "s": "GSM",
    "n": "Ferroglobe PLC - Ordinary Shares"
  },
  {
    "s": "GSRF",
    "n": "GSR IV Acquisition Corp. - Class A ordinary share"
  },
  {
    "s": "GSRFU",
    "n": "GSR IV Acquisition Corp. - Units"
  },
  {
    "s": "GSRV",
    "n": "GSR V Acquisition Corp. - Class A ordinary shares"
  },
  {
    "s": "GSRVU",
    "n": "GSR V Acquisition Corp. - Units"
  },
  {
    "s": "GSUN",
    "n": "Golden Sun Technology Group Limited - Class A Ordinary Shares"
  },
  {
    "s": "GT",
    "n": "The Goodyear Tire & Rubber Company - Common Stock"
  },
  {
    "s": "GTBP",
    "n": "GT Biopharma, Inc. - Common Stock"
  },
  {
    "s": "GTE",
    "n": "Gran Tierra Energy Inc. Common Stock"
  },
  {
    "s": "GTEC",
    "n": "Greenland Technologies Holding Corporation - Class A Ordinary Shares"
  },
  {
    "s": "GTEN",
    "n": "Gores Holdings X, Inc. - Class A ordinary shares"
  },
  {
    "s": "GTENU",
    "n": "Gores Holdings X, Inc. - Units"
  },
  {
    "s": "GTENW",
    "n": "Gores Holdings X, Inc. - Warrants"
  },
  {
    "s": "GTERA",
    "n": "Globa Terra Acquisition Corporation - Class A Ordinary Shares"
  },
  {
    "s": "GTERU",
    "n": "Globa Terra Acquisition Corporation - Units"
  },
  {
    "s": "GTERW",
    "n": "Globa Terra Acquisition Corporation - Warrants"
  },
  {
    "s": "GTES",
    "n": "Gates Industrial Corporation Ltd. Common Shares"
  },
  {
    "s": "GTIM",
    "n": "Good Times Restaurants Inc. - Common Stock"
  },
  {
    "s": "GTLB",
    "n": "GitLab Inc. - Class A Common Stock"
  },
  {
    "s": "GTM",
    "n": "ZoomInfo Technologies Inc. - Common Stock"
  },
  {
    "s": "GTN",
    "n": "Gray Media, Inc. Common Stock"
  },
  {
    "s": "GTN-A",
    "n": "Gray Media, Inc. Class A Common Stock"
  },
  {
    "s": "GTX",
    "n": "Garrett Motion Inc. - Common Stock"
  },
  {
    "s": "GTY",
    "n": "Getty Realty Corporation Common Stock"
  },
  {
    "s": "GUAC",
    "n": "Berto Acquisition Corp. II - Ordinary Shares"
  },
  {
    "s": "GUACU",
    "n": "Berto Acquisition Corp. II - Units"
  },
  {
    "s": "GUACW",
    "n": "Berto Acquisition Corp. II - Warrants"
  },
  {
    "s": "GURE",
    "n": "Gulf Resources, Inc. - Common Stock"
  },
  {
    "s": "GUT",
    "n": "Gabelli Utility Trust (The) Common Stock"
  },
  {
    "s": "GUTS",
    "n": "Fractyl Health, Inc. - Common Stock"
  },
  {
    "s": "GVA",
    "n": "Granite Construction Incorporated Common Stock"
  },
  {
    "s": "GVH",
    "n": "Globavend Holdings Limited - Ord Shares"
  },
  {
    "s": "GWAV",
    "n": "Greenwave Technology Solutions, Inc. - Common Stock"
  },
  {
    "s": "GWRE",
    "n": "Guidewire Software, Inc. Common Stock"
  },
  {
    "s": "GWRS",
    "n": "Global Water Resources, Inc. - common stock"
  },
  {
    "s": "GWW",
    "n": "W.W. Grainger, Inc. Common Stock"
  },
  {
    "s": "GXAI",
    "n": "Gaxos.ai Inc. - Common Stock"
  },
  {
    "s": "GXO",
    "n": "GXO Logistics, Inc. Common Stock "
  },
  {
    "s": "GYGY",
    "n": "Game Your Game, Inc. - Common Stock"
  },
  {
    "s": "GYRE",
    "n": "Gyre Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "GYRO",
    "n": "Gyrodyne , LLC - Common Stock"
  },
  {
    "s": "H",
    "n": "Hyatt Hotels Corporation Class A Common Stock"
  },
  {
    "s": "HACQ",
    "n": "HCM IV Acquisition Corp. - Class A Ordinary Share"
  },
  {
    "s": "HACQU",
    "n": "HCM IV Acquisition Corp. - Unit"
  },
  {
    "s": "HACQW",
    "n": "HCM IV Acquisition Corp. - Warrants"
  },
  {
    "s": "HAE",
    "n": "Haemonetics Corporation Common Stock"
  },
  {
    "s": "HAFC",
    "n": "Hanmi Financial Corporation - Common Stock"
  },
  {
    "s": "HAFN",
    "n": "Hafnia Limited Common Shares"
  },
  {
    "s": "HAIN",
    "n": "The Hain Celestial Group, Inc. - Common Stock"
  },
  {
    "s": "HAL",
    "n": "Halliburton Company Common Stock"
  },
  {
    "s": "HALO",
    "n": "Halozyme Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "HAO",
    "n": "Haoxi Health Technology Limited - Class A Ord Share"
  },
  {
    "s": "HAPN",
    "n": "Happen, Inc. - Common Stock"
  },
  {
    "s": "HAS",
    "n": "Hasbro, Inc. - Common Stock"
  },
  {
    "s": "HASI",
    "n": "HA Sustainable Infrastructure Capital, Inc. Common Stock"
  },
  {
    "s": "HAVA",
    "n": "Harvard Ave Acquisition Corporation - Class A Ordinary Share"
  },
  {
    "s": "HAVAU",
    "n": "Harvard Ave Acquisition Corporation - Unit"
  },
  {
    "s": "HAWK",
    "n": "HawkEye 360, Inc. Common Stock"
  },
  {
    "s": "HAYW",
    "n": "Hayward Holdings, Inc. Common Stock"
  },
  {
    "s": "HBAN",
    "n": "Huntington Bancshares Incorporated - Common Stock"
  },
  {
    "s": "HBB",
    "n": "Hamilton Beach Brands Holding Company Class A Common Stock "
  },
  {
    "s": "HBCP",
    "n": "Home Bancorp, Inc. - Common Stock"
  },
  {
    "s": "HBIO",
    "n": "Harvard Bioscience, Inc. - Common Stock"
  },
  {
    "s": "HBM",
    "n": "Hudbay Minerals Inc. Ordinary Shares (Canada)"
  },
  {
    "s": "HBNB",
    "n": "Hotel101 Global Holdings Corp. - Class A Ordinary Shares"
  },
  {
    "s": "HBNC",
    "n": "Horizon Bancorp, Inc. - Common Stock"
  },
  {
    "s": "HBT",
    "n": "HBT Financial, Inc. - Common Stock"
  },
  {
    "s": "HCA",
    "n": "HCA Healthcare, Inc. Common Stock"
  },
  {
    "s": "HCAC",
    "n": "Hall Chadwick Acquisition Corp. - Class A Ordinary Shares"
  },
  {
    "s": "HCACU",
    "n": "Hall Chadwick Acquisition Corp. - Unit"
  },
  {
    "s": "HCAI",
    "n": "Huachen AI Parking Management Technology Holding Co., Ltd. - Class A Ordinary Shares"
  },
  {
    "s": "HCAT",
    "n": "Health Catalyst, Inc - Common stock"
  },
  {
    "s": "HCC",
    "n": "Warrior Met Coal, Inc. Common Stock"
  },
  {
    "s": "HCHL",
    "n": "Happy City Holdings Limited - Class A Ordinary shares"
  },
  {
    "s": "HCI",
    "n": "HCI Group, Inc. Common Stock"
  },
  {
    "s": "HCIC",
    "n": "Hennessy Capital Investment Corp. VIII - Class A Ordinary Shares"
  },
  {
    "s": "HCICU",
    "n": "Hennessy Capital Investment Corp. VIII - Units"
  },
  {
    "s": "HCKT",
    "n": "The Hackett Group, Inc. - Common Stock"
  },
  {
    "s": "HCM",
    "n": "HUTCHMED (China) Limited - American Depositary Shares"
  },
  {
    "s": "HCMA",
    "n": "HCM III Acquisition Corp. - Class A Ordinary Share"
  },
  {
    "s": "HCMAU",
    "n": "HCM III Acquisition Corp. - Units"
  },
  {
    "s": "HCMAW",
    "n": "HCM III Acquisition Corp. - Warrants"
  },
  {
    "s": "HCSG",
    "n": "Healthcare Services Group, Inc. - Common Stock"
  },
  {
    "s": "HCTI",
    "n": "Healthcare Triangle, Inc. - Common Stock"
  },
  {
    "s": "HCWB",
    "n": "HCW Biologics Inc. - Common Stock"
  },
  {
    "s": "HCXY",
    "n": "Hercules Capital, Inc. 6.25% Notes due 2033"
  },
  {
    "s": "HD",
    "n": "Home Depot, Inc. (The) Common Stock"
  },
  {
    "s": "HDB",
    "n": "HDFC Bank Limited Common Stock"
  },
  {
    "s": "HDL",
    "n": "SUPER HI INTERNATIONAL HOLDING LTD. - American Depositary Shares"
  },
  {
    "s": "HDRN",
    "n": "Hadron Energy, Inc. - Common Stock"
  },
  {
    "s": "HDSN",
    "n": "Hudson Technologies, Inc. - Common Stock"
  },
  {
    "s": "HE",
    "n": "Hawaiian Electric Industries, Inc. Common Stock"
  },
  {
    "s": "HEI",
    "n": "Heico Corporation Common Stock"
  },
  {
    "s": "HEI-A",
    "n": "Heico Corporation Common Stock"
  },
  {
    "s": "HELE",
    "n": "Helen of Troy Limited - Common Stock"
  },
  {
    "s": "HELP",
    "n": "Helus Pharma Inc.  - Common Stock"
  },
  {
    "s": "HEPS",
    "n": "D-Market Electronic Services & Trading - American Depositary Shares"
  },
  {
    "s": "HERE",
    "n": "Here Group Limited - American Depositary Shares"
  },
  {
    "s": "HFBL",
    "n": "Home Federal Bancorp, Inc. of Louisiana - Common Stock"
  },
  {
    "s": "HFFG",
    "n": "HF Foods Group Inc. - Common Stock"
  },
  {
    "s": "HFWA",
    "n": "Heritage Financial Corporation - Common Stock"
  },
  {
    "s": "HG",
    "n": "Hamilton Insurance Group, Ltd. Class B Common Shares"
  },
  {
    "s": "HGBL",
    "n": "Heritage Global Inc. - Common Stock"
  },
  {
    "s": "HGTY",
    "n": "Hagerty, Inc. Class A Common Stock"
  },
  {
    "s": "HGV",
    "n": "Hilton Grand Vacations Inc. Common Stock "
  },
  {
    "s": "HHH",
    "n": "Howard Hughes Holdings Inc. Common Stock"
  },
  {
    "s": "HHS",
    "n": "Harte Hanks, Inc. - Common Stock"
  },
  {
    "s": "HIFS",
    "n": "Hingham Institution for Savings - Common Stock"
  },
  {
    "s": "HIG",
    "n": "The Hartford Insurance Group, Inc. Common Stock"
  },
  {
    "s": "HIHO",
    "n": "Highway Holdings Limited - Common Stock"
  },
  {
    "s": "HII",
    "n": "Huntington Ingalls Industries, Inc. Common Stock"
  },
  {
    "s": "HIMS",
    "n": "Hims & Hers Health, Inc. Class A Common Stock"
  },
  {
    "s": "HIMX",
    "n": "Himax Technologies, Inc. - American depositary shares, each of which represents two ordinary shares."
  },
  {
    "s": "HIND",
    "n": "Vyome Holdings, Inc. - Common Stock"
  },
  {
    "s": "HIPO",
    "n": "Hippo Holdings Inc. Common Stock"
  },
  {
    "s": "HIT",
    "n": "Health In Tech, Inc. - Class A Common Stock"
  },
  {
    "s": "HITI",
    "n": "High Tide Inc. - Common Shares"
  },
  {
    "s": "HIVE",
    "n": "HIVE Digital Technologies Ltd - Common Shares"
  },
  {
    "s": "HIW",
    "n": "Highwoods Properties, Inc. Common Stock"
  },
  {
    "s": "HKD",
    "n": "AMTD Digital Inc. American Depositary Shares (every five of which represent two Class A Ordinary Shares)"
  },
  {
    "s": "HKPD",
    "n": "Cellyan Biotechnology Co., Ltd  - Class A Ordinary Shares"
  },
  {
    "s": "HL",
    "n": "Hecla Mining Company Common Stock"
  },
  {
    "s": "HLF",
    "n": "Herbalife Ltd. Common Shares"
  },
  {
    "s": "HLI",
    "n": "Houlihan Lokey, Inc. Class A Common Stock"
  },
  {
    "s": "HLIO",
    "n": "Helios Technologies, Inc. Common Stock"
  },
  {
    "s": "HLIT",
    "n": "Harmonic Inc. - Common Stock"
  },
  {
    "s": "HLLY",
    "n": "Holley Inc. Common Stock"
  },
  {
    "s": "HLMN",
    "n": "Hillman Solutions Corp. - Common Stock"
  },
  {
    "s": "HLN",
    "n": "Haleon plc American Depositary Shares (Each representing two Ordinary Shares)"
  },
  {
    "s": "HLNE",
    "n": "Hamilton Lane Incorporated - Class A Common Stock"
  },
  {
    "s": "HLP",
    "n": "Hongli Group Inc. - Class A Ordinary Shares"
  },
  {
    "s": "HLSQ",
    "n": "Tessera Defense and Homeland Security Inc. Common Stock"
  },
  {
    "s": "HLT",
    "n": "Hilton Worldwide Holdings Inc. Common Stock "
  },
  {
    "s": "HLXC",
    "n": "Helix Acquisition Corp. III - Class A Ordinary Shares"
  },
  {
    "s": "HMC",
    "n": "Honda Motor Company, Ltd. Common Stock"
  },
  {
    "s": "HMH",
    "n": "HMH Holding Inc. - Common Stock"
  },
  {
    "s": "HMN",
    "n": "Horace Mann Educators Corporation Common Stock"
  },
  {
    "s": "HMR",
    "n": "Heidmar Maritime Holdings Corp. - Common Stock"
  },
  {
    "s": "HMY",
    "n": "Harmony Gold Mining Company Limited"
  },
  {
    "s": "HNGE",
    "n": "Hinge Health, Inc. Class A Common Stock"
  },
  {
    "s": "HNI",
    "n": "HNI Corporation Common Stock"
  },
  {
    "s": "HNNA",
    "n": "Hennessy Advisors, Inc. - Common Stock"
  },
  {
    "s": "HNRG",
    "n": "Hallador Energy Company - Common Stock"
  },
  {
    "s": "HNST",
    "n": "The Honest Company, Inc. - Common Stock"
  },
  {
    "s": "HNVR",
    "n": "Hanover Bancorp, Inc. - Common Stock"
  },
  {
    "s": "HODO",
    "n": "House of Doge Inc. - Common Stock"
  },
  {
    "s": "HOFT",
    "n": "Hooker Furnishings Corporation - Common Stock"
  },
  {
    "s": "HOG",
    "n": "Harley-Davidson, Inc. Common Stock"
  },
  {
    "s": "HOLO",
    "n": "MicroCloud Hologram Inc. - Ordinary Shares"
  },
  {
    "s": "HOMB",
    "n": "Home BancShares, Inc. Common Stock"
  },
  {
    "s": "HON",
    "n": "Honeywell International Inc. - Common Stock"
  },
  {
    "s": "HONA",
    "n": "Honeywell Aerospace Inc. - Common Stock"
  },
  {
    "s": "HOOD",
    "n": "Robinhood Markets, Inc. - Class A Common Stock"
  },
  {
    "s": "HOPE",
    "n": "Hope Bancorp, Inc. - Common Stock"
  },
  {
    "s": "HOS",
    "n": "Hornbeck Offshore Services, Inc. Common Stock"
  },
  {
    "s": "HOST",
    "n": "Host Digital Inc. Class A Common Stock"
  },
  {
    "s": "HOUR",
    "n": "Hour Loop, Inc. - common stock"
  },
  {
    "s": "HOV",
    "n": "Hovnanian Enterprises, Inc. Class A Common Stock"
  },
  {
    "s": "HOVR",
    "n": "New Horizon Aircraft Ltd. - Class A Ordinary Shares"
  },
  {
    "s": "HOWL",
    "n": "Werewolf Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "HP",
    "n": "Helmerich & Payne, Inc. Common Stock"
  },
  {
    "s": "HPAI",
    "n": "Helport AI Limited - Ordinary Shares"
  },
  {
    "s": "HPAIW",
    "n": "Helport AI Limited - Warrants"
  },
  {
    "s": "HPE",
    "n": "Hewlett Packard Enterprise Company Common Stock"
  },
  {
    "s": "HPK",
    "n": "HighPeak Energy, Inc. - Common Stock"
  },
  {
    "s": "HPP",
    "n": "Hudson Pacific Properties, Inc. Common Stock"
  },
  {
    "s": "HPQ",
    "n": "HP Inc. Common Stock"
  },
  {
    "s": "HQ",
    "n": "Horizon Quantum Holdings Ltd. - Class A Ordinary Shares"
  },
  {
    "s": "HQH",
    "n": "abrdn Healthcare Investors Shares of Beneficial Interest"
  },
  {
    "s": "HQI",
    "n": "HireQuest, Inc. - Common Stock"
  },
  {
    "s": "HQL",
    "n": "abrdn Life Sciences Investors Shares of Beneficial Interest"
  },
  {
    "s": "HQY",
    "n": "HealthEquity, Inc. - Common Stock"
  },
  {
    "s": "HR",
    "n": "Healthcare Realty Trust Incorporated Common Stock"
  },
  {
    "s": "HRB",
    "n": "H&R Block, Inc. Common Stock"
  },
  {
    "s": "HRI",
    "n": "Herc Holdings Inc. Common Stock "
  },
  {
    "s": "HRL",
    "n": "Hormel Foods Corporation Common Stock"
  },
  {
    "s": "HRMY",
    "n": "Harmony Biosciences Holdings, Inc. - Common Stock"
  },
  {
    "s": "HROW",
    "n": "Harrow, Inc. - Common Stock"
  },
  {
    "s": "HRTG",
    "n": "Heritage Insurance Holdings, Inc. Common Stock"
  },
  {
    "s": "HRTX",
    "n": "Heron Therapeutics, Inc.   - Common Stock"
  },
  {
    "s": "HRZN",
    "n": "Horizon Technology Finance Corporation - Common Stock"
  },
  {
    "s": "HSAI",
    "n": "Hesai Group - American Depositary Share"
  },
  {
    "s": "HSBC",
    "n": "HSBC Holdings, plc. Common Stock"
  },
  {
    "s": "HSCS",
    "n": "HeartSciences Inc. - Common Stock"
  },
  {
    "s": "HSDT",
    "n": "Solana Company - Class A Common Stock"
  },
  {
    "s": "HSHP",
    "n": "Himalaya Shipping Ltd. Common Shares"
  },
  {
    "s": "HSIC",
    "n": "Henry Schein, Inc. - Common Stock"
  },
  {
    "s": "HSLV",
    "n": "Highlander Silver Corp. Common Shares"
  },
  {
    "s": "HST",
    "n": "Host Hotels & Resorts, Inc. - Common Stock"
  },
  {
    "s": "HSTM",
    "n": "HealthStream, Inc. - Common Stock"
  },
  {
    "s": "HSY",
    "n": "The Hershey Company Common Stock"
  },
  {
    "s": "HTB",
    "n": "HomeTrust Bancshares, Inc. Common Stock"
  },
  {
    "s": "HTCO",
    "n": "High-Trend International Group - Class A Ordinary Shares"
  },
  {
    "s": "HTCR",
    "n": "Heartcore Enterprises, Inc. - Common Stock"
  },
  {
    "s": "HTFC",
    "n": "Horizon Technology Finance Corporation 6.25% Notes due 2027"
  },
  {
    "s": "HTFL",
    "n": "Heartflow, Inc. - Common Stock"
  },
  {
    "s": "HTGC",
    "n": "Hercules Capital, Inc. Common Stock"
  },
  {
    "s": "HTH",
    "n": "Hilltop Holdings Inc."
  },
  {
    "s": "HTHT",
    "n": "H World Group Limited - American Depositary Shares"
  },
  {
    "s": "HTLD",
    "n": "Heartland Express, Inc. - Common Stock"
  },
  {
    "s": "HTLM",
    "n": "HomesToLife Ltd - Ordinary Shares"
  },
  {
    "s": "HTO",
    "n": "H2O America  - Common Stock"
  },
  {
    "s": "HTOO",
    "n": "Fusion Fuel Green PLC - Ordinary Shares"
  },
  {
    "s": "HTT",
    "n": "High Templar Tech Limited American depositary shares, each representing one Class A ordinary share"
  },
  {
    "s": "HTZ",
    "n": "Hertz Global Holdings, Inc - Common Stock"
  },
  {
    "s": "HUBB",
    "n": "Hubbell Inc Common Stock"
  },
  {
    "s": "HUBC",
    "n": "Hub Cyber Security Ltd. - Ordinary Shares"
  },
  {
    "s": "HUBG",
    "n": "Hub Group, Inc. - Class A Common Stock"
  },
  {
    "s": "HUBS",
    "n": "HubSpot, Inc. Common Stock"
  },
  {
    "s": "HUCK",
    "n": "Huckleberry.ai, Inc. - Class B Common Stock"
  },
  {
    "s": "HUDI",
    "n": "Huadi International Group Co., Ltd. - Ordinary Shares"
  },
  {
    "s": "HUHU",
    "n": "HUHUTECH International Group Inc. - Ordinary Shares"
  },
  {
    "s": "HUIZ",
    "n": "Huize Holding Limited - American Depositary Shares"
  },
  {
    "s": "HUM",
    "n": "Humana Inc. Common Stock"
  },
  {
    "s": "HUMA",
    "n": "Humacyte, Inc. - Common Stock"
  },
  {
    "s": "HUN",
    "n": "Huntsman Corporation Common Stock"
  },
  {
    "s": "HURA",
    "n": "TuHURA Biosciences, Inc. - Common Stock"
  },
  {
    "s": "HURC",
    "n": "Hurco Companies, Inc. - Common Stock"
  },
  {
    "s": "HURN",
    "n": "Huron Consulting Group Inc. - Common Stock"
  },
  {
    "s": "HUT",
    "n": "Hut 8 Corp. - Common Stock"
  },
  {
    "s": "HUYA",
    "n": "HUYA Inc. American depositary shares, each  representing one Class A ordinary share"
  },
  {
    "s": "HVMC",
    "n": "Highview Merger Corp. - Class A Ordinary Share"
  },
  {
    "s": "HVMCU",
    "n": "Highview Merger Corp. - Units"
  },
  {
    "s": "HVMCW",
    "n": "Highview Merger Corp. - Warrants"
  },
  {
    "s": "HVT",
    "n": "Haverty Furniture Companies, Inc. Common Stock"
  },
  {
    "s": "HVT-A",
    "n": "Haverty Furniture Companies, Inc. Common Stock"
  },
  {
    "s": "HWBK",
    "n": "Hawthorn Bancshares, Inc. - Common Stock"
  },
  {
    "s": "HWC",
    "n": "Hancock Whitney Corporation - Common Stock"
  },
  {
    "s": "HWCPZ",
    "n": "Hancock Whitney Corporation - 6.25% Subordinated Notes due 2060"
  },
  {
    "s": "HWKN",
    "n": "Hawkins, Inc. - Common Stock"
  },
  {
    "s": "HWM",
    "n": "Howmet Aerospace Inc. Common Stock"
  },
  {
    "s": "HXHX",
    "n": "Haoxin Holdings Limited - Class A Ordinary Shares"
  },
  {
    "s": "HXL",
    "n": "Hexcel Corporation Common Stock"
  },
  {
    "s": "HY",
    "n": "Hyster-Yale, Inc. Class A common stock"
  },
  {
    "s": "HYFM",
    "n": "Hydrofarm Holdings Group, Inc. - Common Stock"
  },
  {
    "s": "HYFT",
    "n": "MindWalk Holdings Corp. - Common Stock"
  },
  {
    "s": "HYLN",
    "n": "Hyliion Holdings Corp. Class A Common Stock"
  },
  {
    "s": "HYMC",
    "n": "Hycroft Mining Holding Corporation - Class A Common Stock"
  },
  {
    "s": "HYNE",
    "n": "Hoyne Bancorp, Inc. - Common Stock"
  },
  {
    "s": "HYPD",
    "n": "Hyperion DeFi, Inc. - Common Stock"
  },
  {
    "s": "HYPR",
    "n": "Hyperfine, Inc.  - Class A Common Stock"
  },
  {
    "s": "HZO",
    "n": "MarineMax, Inc.  (FL) Common Stock"
  },
  {
    "s": "IA",
    "n": "Innovative Solutions and Support, Inc. - Common Stock"
  },
  {
    "s": "IACO",
    "n": "Idea Acquisition Corp. - Class A Ordinary Shares"
  },
  {
    "s": "IACOU",
    "n": "Idea Acquisition Corp. - Units"
  },
  {
    "s": "IACOW",
    "n": "Idea Acquisition Corp. - Warrants"
  },
  {
    "s": "IACQ",
    "n": "Irenic Acquisition Corp. - Class A Ordinary Shares"
  },
  {
    "s": "IACQU",
    "n": "Irenic Acquisition Corp. - Unit"
  },
  {
    "s": "IACQW",
    "n": "Irenic Acquisition Corp. - Warrants"
  },
  {
    "s": "IAG",
    "n": "Iamgold Corporation Ordinary Shares"
  },
  {
    "s": "IART",
    "n": "Integra LifeSciences Holdings Corporation - Common Stock"
  },
  {
    "s": "IAUX",
    "n": "i-80 Gold Corp. Common Shares"
  },
  {
    "s": "IBAC",
    "n": "IB Acquisition Corp. - Common Stock"
  },
  {
    "s": "IBACR",
    "n": "IB Acquisition Corp. - Right"
  },
  {
    "s": "IBCP",
    "n": "Independent Bank Corporation - Common Stock"
  },
  {
    "s": "IBEX",
    "n": "IBEX Limited - Common Share"
  },
  {
    "s": "IBG",
    "n": "Innovation Beverage Group Limited - Ordinary Shares"
  },
  {
    "s": "IBIO",
    "n": "iBio, Inc. - Common Stock"
  },
  {
    "s": "IBKR",
    "n": "Interactive Brokers Group, Inc. - Class A Common Stock"
  },
  {
    "s": "IBM",
    "n": "International Business Machines Corporation Common Stock"
  },
  {
    "s": "IBN",
    "n": "ICICI Bank Limited Common Stock"
  },
  {
    "s": "IBO",
    "n": "Impact BioMedical, Inc. Common Stock"
  },
  {
    "s": "IBOC",
    "n": "International Bancshares Corporation - Common Stock"
  },
  {
    "s": "IBP",
    "n": "Installed Building Products, Inc. Common Stock"
  },
  {
    "s": "IBRX",
    "n": "ImmunityBio, Inc. - Common Stock"
  },
  {
    "s": "IBTA",
    "n": "Ibotta, Inc. Class A Common Stock"
  },
  {
    "s": "ICCC",
    "n": "ImmuCell Corporation - Common Stock"
  },
  {
    "s": "ICCM",
    "n": "IceCure Medical Ltd. - Ordinary Shares"
  },
  {
    "s": "ICE",
    "n": "Intercontinental Exchange Inc. Common Stock"
  },
  {
    "s": "ICFI",
    "n": "ICF International, Inc. - Common Stock"
  },
  {
    "s": "ICG",
    "n": "Intchains Group Limited - American Depositary Shares"
  },
  {
    "s": "ICHR",
    "n": "Ichor Holdings - Ordinary Shares"
  },
  {
    "s": "ICL",
    "n": "ICL Group Ltd. Ordinary Shares"
  },
  {
    "s": "ICLR",
    "n": "ICON plc - Ordinary Shares"
  },
  {
    "s": "ICMB",
    "n": "Investcorp Credit Management BDC, Inc. - Common Stock"
  },
  {
    "s": "ICON",
    "n": "Icon Energy Corp. - Common stock"
  },
  {
    "s": "ICU",
    "n": "SeaStar Medical Holding Corporation - Common Stock"
  },
  {
    "s": "ICUI",
    "n": "ICU Medical, Inc. - Common Stock"
  },
  {
    "s": "IDA",
    "n": "IDACORP, Inc. Common Stock"
  },
  {
    "s": "IDAC",
    "n": "Iron Dome Acquisition I Corp. - Class A Ordinary Shares"
  },
  {
    "s": "IDACU",
    "n": "Iron Dome Acquisition I Corp. - Units"
  },
  {
    "s": "IDAI",
    "n": "T Stamp Inc. - Class A Common Stock"
  },
  {
    "s": "IDCC",
    "n": "InterDigital, Inc. - Common Stock"
  },
  {
    "s": "IDN",
    "n": "Intellicheck, Inc. - Common Stock"
  },
  {
    "s": "IDR",
    "n": "Idaho Strategic Resources, Inc. Common Stock"
  },
  {
    "s": "IDT",
    "n": "IDT Corporation Class B Common Stock"
  },
  {
    "s": "IDXX",
    "n": "IDEXX Laboratories, Inc. - Common Stock"
  },
  {
    "s": "IDYA",
    "n": "IDEAYA Biosciences, Inc. - Common Stock"
  },
  {
    "s": "IE",
    "n": "Ivanhoe Electric Inc. Common Stock"
  },
  {
    "s": "IEAG",
    "n": "Infinite Eagle Acquisition Corp. - Class A Ordinary Shares"
  },
  {
    "s": "IEAGU",
    "n": "Infinite Eagle Acquisition Corp. - Unit"
  },
  {
    "s": "IEP",
    "n": "Icahn Enterprises L.P. - Depositary Units representing Limited Partner Interests"
  },
  {
    "s": "IESC",
    "n": "IES Holdings, Inc. - Common Stock"
  },
  {
    "s": "IEX",
    "n": "IDEX Corporation Common Stock"
  },
  {
    "s": "IFBD",
    "n": "Infobird Co., Ltd - Ordinary Shares"
  },
  {
    "s": "IFF",
    "n": "International Flavors & Fragrances, Inc. Common Stock"
  },
  {
    "s": "IFRX",
    "n": "InflaRx N.V. - Common Stock"
  },
  {
    "s": "IFS",
    "n": "Intercorp Financial Services Inc. Common Shares"
  },
  {
    "s": "IGAC",
    "n": "Invest Green Acquisition Corporation - Class A Ordinary Shares"
  },
  {
    "s": "IGACU",
    "n": "Invest Green Acquisition Corporation - Units"
  },
  {
    "s": "IGC",
    "n": "IGC Pharma, Inc. Common Stock"
  },
  {
    "s": "IGI",
    "n": "Western Asset Investment Grade Opportunity Trust Inc. Common Stock"
  },
  {
    "s": "IGIC",
    "n": "International General Insurance Holdings Ltd. - Ordinary Shares"
  },
  {
    "s": "IH",
    "n": "iHuman Inc. American depositary shares, each representing five Class A ordinary shares"
  },
  {
    "s": "IHG",
    "n": "Intercontinental Hotels Group American Depositary Shares (Each representing one Ordinary Share)"
  },
  {
    "s": "IHRT",
    "n": "iHeartMedia, Inc. - Class A Common Stock"
  },
  {
    "s": "IHS",
    "n": "IHS Holding Limited Ordinary Shares"
  },
  {
    "s": "IHT",
    "n": "InnSuites Hospitality Trust Shares of Beneficial Interest"
  },
  {
    "s": "III",
    "n": "Information Services Group, Inc. - Common Stock"
  },
  {
    "s": "IIIN",
    "n": "Insteel Industries, Inc. Common Stock"
  },
  {
    "s": "IIIV",
    "n": "i3 Verticals, Inc. - Common Stock"
  },
  {
    "s": "IIM",
    "n": "Invesco Value Municipal Income Trust Common Stock"
  },
  {
    "s": "IIPR",
    "n": "Innovative Industrial Properties, Inc. Common Stock"
  },
  {
    "s": "IKT",
    "n": "Inhibikase Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "ILAG",
    "n": "Intelligent Living Application Group Inc. - Ordinary Shares"
  },
  {
    "s": "ILLU",
    "n": "Illumination Acquisition Corp I - Class A Ordinary Shares"
  },
  {
    "s": "ILLUU",
    "n": "Illumination Acquisition Corp I - Units"
  },
  {
    "s": "ILMN",
    "n": "Illumina, Inc. - Common Stock"
  },
  {
    "s": "ILPT",
    "n": "Industrial Logistics Properties Trust - Common Shares of Beneficial Interest"
  },
  {
    "s": "IMA",
    "n": "ImageneBio, Inc. - Common Stock"
  },
  {
    "s": "IMAX",
    "n": "Imax Corporation Common Stock"
  },
  {
    "s": "IMC",
    "n": "IMC Rare Earths Ltd Ordinary Shares"
  },
  {
    "s": "IMCC",
    "n": "IM Cannabis Corp. - Common Shares"
  },
  {
    "s": "IMCR",
    "n": "Immunocore Holdings plc - American Depositary Shares"
  },
  {
    "s": "IMDX",
    "n": "Insight Molecular Diagnostics Inc. - Common Stock"
  },
  {
    "s": "IMKTA",
    "n": "Ingles Markets, Incorporated - Class A Common Stock"
  },
  {
    "s": "IMMP",
    "n": "Immutep Limited - American Depositary Shares"
  },
  {
    "s": "IMMR",
    "n": "Immersion Corporation - Common Stock"
  },
  {
    "s": "IMMX",
    "n": "Immix Biopharma, Inc. - Common Stock"
  },
  {
    "s": "IMNM",
    "n": "Immunome, Inc. - Common Stock"
  },
  {
    "s": "IMNN",
    "n": "Imunon, Inc. - Common Stock"
  },
  {
    "s": "IMO",
    "n": "Imperial Oil Limited Common Stock"
  },
  {
    "s": "IMOS",
    "n": "ChipMOS TECHNOLOGIES INC. - American Depositary Shares"
  },
  {
    "s": "IMPP",
    "n": "Imperial Petroleum Inc. - Common Shares"
  },
  {
    "s": "IMRN",
    "n": "Immuron Limited - American Depositary Shares"
  },
  {
    "s": "IMRX",
    "n": "Immuneering Corporation - Class A Common Stock"
  },
  {
    "s": "IMSR",
    "n": "Terrestrial Energy Inc. - Common Stock"
  },
  {
    "s": "IMTE",
    "n": "Integrated Media Technology Limited - Ordinary Shares"
  },
  {
    "s": "IMTX",
    "n": "Immatics N.V. - Ordinary Shares"
  },
  {
    "s": "IMUX",
    "n": "Immunic, Inc.  - Common Stock"
  },
  {
    "s": "IMVT",
    "n": "Immunovant, Inc.  - Common Stock"
  },
  {
    "s": "IMXI",
    "n": "International Money Express, Inc. - Common Stock"
  },
  {
    "s": "INAB",
    "n": "IN8bio, Inc. - Common Stock"
  },
  {
    "s": "INAC",
    "n": "Indigo Acquisition Corp. - Ordinary Shares"
  },
  {
    "s": "INACR",
    "n": "Indigo Acquisition Corp. - Right"
  },
  {
    "s": "INACU",
    "n": "Indigo Acquisition Corp. - Unit"
  },
  {
    "s": "INBK",
    "n": "First Internet Bancorp - Common Stock"
  },
  {
    "s": "INBKZ",
    "n": "First Internet Bancorp - Fixed-to-Floating Rate Subordinated Notes Due 2029"
  },
  {
    "s": "INBS",
    "n": "Intelligent Bio Solutions Inc.  - Common Stock"
  },
  {
    "s": "INBX",
    "n": "Inhibrx Biosciences, Inc. - Common Stock"
  },
  {
    "s": "INCR",
    "n": "Intercure Ltd. - ordinary shares"
  },
  {
    "s": "INCY",
    "n": "Incyte Corporation - Common Stock"
  },
  {
    "s": "INDB",
    "n": "Independent Bank Corp. - Common Stock"
  },
  {
    "s": "INDI",
    "n": "indie Semiconductor, Inc. - Class A Common Stock"
  },
  {
    "s": "INDO",
    "n": "Indonesia Energy Corporation Limited Ordinary Shares"
  },
  {
    "s": "INDP",
    "n": "Indaptus Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "INDV",
    "n": "Indivior Pharmaceuticals, Inc.  - Common Stock"
  },
  {
    "s": "INEO",
    "n": "INNEOVA Holdings Limited - Class A Ordinary Shares"
  },
  {
    "s": "INFQ",
    "n": "Infleqtion, Inc. Common Stock"
  },
  {
    "s": "INFU",
    "n": "InfuSystems Holdings, Inc. Common Stock"
  },
  {
    "s": "INFY",
    "n": "Infosys Limited American Depositary Shares"
  },
  {
    "s": "ING",
    "n": "ING Group, N.V. Common Stock"
  },
  {
    "s": "INGM",
    "n": "Ingram Micro Holding Corporation Common Stock"
  },
  {
    "s": "INGN",
    "n": "Inogen, Inc - Common Stock"
  },
  {
    "s": "INGR",
    "n": "Ingredion Incorporated Common Stock"
  },
  {
    "s": "INHD",
    "n": "Inno Holdings Inc. - Common Stock"
  },
  {
    "s": "INIO",
    "n": "INNIO N.V. - Ordinary Shares"
  },
  {
    "s": "INKT",
    "n": "MiNK Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "INLF",
    "n": "INLIF LIMITED - Class A Ordinary shares"
  },
  {
    "s": "INLX",
    "n": "Intellinetics, Inc. Common Stock"
  },
  {
    "s": "INM",
    "n": "InMed Pharmaceuticals Inc. - Common Shares"
  },
  {
    "s": "INMB",
    "n": "INmune Bio Inc. - Common stock"
  },
  {
    "s": "INMD",
    "n": "InMode Ltd.  - Ordinary Shares"
  },
  {
    "s": "INN",
    "n": "Summit Hotel Properties, Inc. Common Stock"
  },
  {
    "s": "INNV",
    "n": "InnovAge Holding Corp. - Common Stock"
  },
  {
    "s": "INO",
    "n": "Inovio Pharmaceuticals, Inc. - Common Stock"
  },
  {
    "s": "INOD",
    "n": "Innodata Inc. - Common Stock"
  },
  {
    "s": "INR",
    "n": "Infinity Natural Resources, Inc. Class A Common Stock"
  },
  {
    "s": "INSE",
    "n": "Inspired Entertainment, Inc. - Common Stock"
  },
  {
    "s": "INSG",
    "n": "Inseego Corp. - Common Stock"
  },
  {
    "s": "INSM",
    "n": "Insmed Incorporated - Common Stock"
  },
  {
    "s": "INSP",
    "n": "Inspire Medical Systems, Inc. Common Stock"
  },
  {
    "s": "INSW",
    "n": "International Seaways, Inc. Common Stock "
  },
  {
    "s": "INTA",
    "n": "Intapp, Inc. - Common Stock"
  },
  {
    "s": "INTC",
    "n": "Intel Corporation - Common Stock"
  },
  {
    "s": "INTG",
    "n": "The Intergroup Corporation - Common Stock"
  },
  {
    "s": "INTJ",
    "n": "Intelligent Group Limited - Class A Ordinary Shares"
  },
  {
    "s": "INTR",
    "n": "Inter & Co. Inc. - Class A Common Shares"
  },
  {
    "s": "INTS",
    "n": "Intensity Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "INTT",
    "n": "inTest Corporation Common Stock"
  },
  {
    "s": "INTU",
    "n": "Intuit Inc. - Common Stock"
  },
  {
    "s": "INTZ",
    "n": "Intrusion Inc. - Common Stock"
  },
  {
    "s": "INUV",
    "n": "Inuvo, Inc."
  },
  {
    "s": "INV",
    "n": "Innventure, Inc. - Common Stock"
  },
  {
    "s": "INVA",
    "n": "Innoviva, Inc. - Common Stock"
  },
  {
    "s": "INVE",
    "n": "INVE Technologies, Inc. - Common Stock"
  },
  {
    "s": "INVH",
    "n": "Invitation Homes Inc. Common Stock"
  },
  {
    "s": "INVX",
    "n": "Innovex International, Inc. Common Stock"
  },
  {
    "s": "INVZ",
    "n": "Innoviz Technologies Ltd. - Ordinary shares"
  },
  {
    "s": "IOND",
    "n": "Ionic Digital Inc. - Class A Common Stock"
  },
  {
    "s": "IONQ",
    "n": "IonQ, Inc. Common Stock"
  },
  {
    "s": "IONR",
    "n": "ioneer Ltd - American Depositary Shares"
  },
  {
    "s": "IONS",
    "n": "Ionis Pharmaceuticals, Inc. - Common Stock"
  },
  {
    "s": "IOR",
    "n": "Income Opportunity Realty Investors, Inc. Common Stock"
  },
  {
    "s": "IOSP",
    "n": "Innospec Inc. - Common Stock"
  },
  {
    "s": "IOT",
    "n": "Samsara Inc. Class A Common Stock"
  },
  {
    "s": "IOTR",
    "n": "iOThree Limited - Ordinary Shares"
  },
  {
    "s": "IOVA",
    "n": "Iovance Biotherapeutics, Inc. - Common Stock"
  },
  {
    "s": "IP",
    "n": "International Paper Company Common Stock"
  },
  {
    "s": "IPAR",
    "n": "Interparfums, Inc. - Common Stock"
  },
  {
    "s": "IPDN",
    "n": "Professional Diversity Network, Inc. - Common Stock"
  },
  {
    "s": "IPFX",
    "n": "Inflection Point Acquisition Corp. VI - Class A Ordinary Shares"
  },
  {
    "s": "IPFXU",
    "n": "Inflection Point Acquisition Corp. VI - Units"
  },
  {
    "s": "IPGP",
    "n": "IPG Photonics Corporation - Common Stock"
  },
  {
    "s": "IPHA",
    "n": "Innate Pharma S.A. - American Depositary Shares"
  },
  {
    "s": "IPHX",
    "n": "Inflection Point Acquisition Corp. VIII - Class A Ordinary Shares"
  },
  {
    "s": "IPHXU",
    "n": "Inflection Point Acquisition Corp. VIII - Unit"
  },
  {
    "s": "IPI",
    "n": "Intrepid Potash, Inc Common Stock"
  },
  {
    "s": "IPM",
    "n": "Intelligent Protection Management Corp.  - Common Stock"
  },
  {
    "s": "IPSC",
    "n": "Century Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "IPST",
    "n": "IP Strategy Holdings, Inc. - Common Stock"
  },
  {
    "s": "IPVV",
    "n": "InterPrivate Investment Partners V, Inc. - Class A Ordinary Shares"
  },
  {
    "s": "IPVVU",
    "n": "InterPrivate Investment Partners V, Inc. - Units"
  },
  {
    "s": "IPVVW",
    "n": "InterPrivate Investment Partners V, Inc. - Warrants"
  },
  {
    "s": "IPW",
    "n": "iPower Inc. - Common Stock"
  },
  {
    "s": "IPWR",
    "n": "Ideal Power Inc. - Common Stock"
  },
  {
    "s": "IPX",
    "n": "IperionX Limited - American Depositary Share"
  },
  {
    "s": "IPXG",
    "n": "Inection Point Acquisition Corp. VII  - Class A Ordinary Shares"
  },
  {
    "s": "IPXGU",
    "n": "Inection Point Acquisition Corp. VII  - Unit"
  },
  {
    "s": "IQ",
    "n": "iQIYI, Inc. - American Depositary Shares"
  },
  {
    "s": "IQI",
    "n": "Invesco Quality Municipal Income Trust Common Stock"
  },
  {
    "s": "IQMX",
    "n": "IQM Quantum Computers Oyj - American Depositary Shares"
  },
  {
    "s": "IQMXW",
    "n": "IQM Quantum Computers Oyj - Warrants to purchase American Depositary Shares"
  },
  {
    "s": "IQST",
    "n": "iQSTEL Inc. - Common Stock"
  },
  {
    "s": "IQV",
    "n": "IQVIA Holdings, Inc. Common Stock"
  },
  {
    "s": "IR",
    "n": "Ingersoll Rand Inc. Common Stock"
  },
  {
    "s": "IRAB",
    "n": "Iris Acquisition Corp II Class A Ordinary Shares"
  },
  {
    "s": "IRD",
    "n": "Opus Genetics, Inc. - Common Stock"
  },
  {
    "s": "IRDM",
    "n": "Iridium Communications Inc - Common Stock"
  },
  {
    "s": "IREN",
    "n": "IREN Limited - Ordinary Shares"
  },
  {
    "s": "IRHO",
    "n": "Iron Horse Acquisitions II Corp. - Common Stock"
  },
  {
    "s": "IRHOU",
    "n": "Iron Horse Acquisitions II Corp. - Units"
  },
  {
    "s": "IRIX",
    "n": "IRIDEX Corporation - Common Stock"
  },
  {
    "s": "IRMD",
    "n": "iRadimed Corporation - Common Stock"
  },
  {
    "s": "IRON",
    "n": "Disc Medicine, Inc. - Common Stock"
  },
  {
    "s": "IRS",
    "n": "IRSA Inversiones Y Representaciones S.A. Global Depositary Shares (Each representing ten shares of Common Stock)"
  },
  {
    "s": "IRT",
    "n": "Independence Realty Trust, Inc. Common Stock"
  },
  {
    "s": "IRTC",
    "n": "iRhythm Holdings, Inc.  - Common Stock"
  },
  {
    "s": "IRWD",
    "n": "Ironwood Pharmaceuticals, Inc. - Class A Common Stock"
  },
  {
    "s": "ISBA",
    "n": "Isabella Bank Corporation - Common stock"
  },
  {
    "s": "ISNR",
    "n": "Snow Rothschild Acquisition Corp. - Class A Ordinary Shares"
  },
  {
    "s": "ISNRU",
    "n": "Snow Rothschild Acquisition Corp. - Units"
  },
  {
    "s": "ISNRW",
    "n": "Snow Rothschild Acquisition Corp. - Warrants"
  },
  {
    "s": "ISOU",
    "n": "IsoEnergy Ltd. Common Shares"
  },
  {
    "s": "ISPC",
    "n": "iSpecimen Inc. - Common Stock"
  },
  {
    "s": "ISPR",
    "n": "Ispire Technology Inc. - Common Stock"
  },
  {
    "s": "ISRG",
    "n": "Intuitive Surgical, Inc. - Common Stock"
  },
  {
    "s": "ISTR",
    "n": "Investar Holding Corporation - Common Stock"
  },
  {
    "s": "IT",
    "n": "Gartner, Inc. Common Stock"
  },
  {
    "s": "ITG",
    "n": "ITG, Inc. - Class A Common Stock"
  },
  {
    "s": "ITGR",
    "n": "Integer Holdings Corporation Common Stock"
  },
  {
    "s": "ITHA",
    "n": "ITHAX Acquisition Corp III - Class A Ordinary Shares"
  },
  {
    "s": "ITHAU",
    "n": "ITHAX Acquisition Corp III - Units"
  },
  {
    "s": "ITHAW",
    "n": "ITHAX Acquisition Corp III - Warrants"
  },
  {
    "s": "ITIC",
    "n": "Investors Title Company - Common Stock"
  },
  {
    "s": "ITOC",
    "n": "iTonic Holdings Ltd - Class A Ordinary Shares"
  },
  {
    "s": "ITP",
    "n": "IT Tech Packaging, Inc. Common Stock"
  },
  {
    "s": "ITRG",
    "n": "Integra Resources Corp. Common Shares"
  },
  {
    "s": "ITRI",
    "n": "Itron, Inc. - Common Stock"
  },
  {
    "s": "ITRN",
    "n": "Ituran Location and Control Ltd. - Ordinary Shares"
  },
  {
    "s": "ITT",
    "n": "ITT Inc. Common Stock "
  },
  {
    "s": "ITW",
    "n": "Illinois Tool Works Inc. Common Stock"
  },
  {
    "s": "IVA",
    "n": "Inventiva S.A. - American Depository Shares"
  },
  {
    "s": "IVAI",
    "n": "Ives Ultra AI Opportunities Inc. Common Stock"
  },
  {
    "s": "IVDA",
    "n": "Iveda Solutions, Inc. - Common Stock"
  },
  {
    "s": "IVF",
    "n": "INVO Fertility, Inc. - Common Stock"
  },
  {
    "s": "IVR",
    "n": "INVESCO MORTGAGE CAPITAL INC Common Stock"
  },
  {
    "s": "IVT",
    "n": "InvenTrust Properties Corp. Common Stock"
  },
  {
    "s": "IVVD",
    "n": "Invivyd, Inc. - Common Stock"
  },
  {
    "s": "IVZ",
    "n": "Invesco Ltd Common Stock"
  },
  {
    "s": "IX",
    "n": "ORIX Corporation American Depositary Shares"
  },
  {
    "s": "IXHL",
    "n": "Incannex Healthcare Inc. - Common Stock"
  },
  {
    "s": "IZEA",
    "n": "IZEA Worldwide, Inc. - Common Stock"
  },
  {
    "s": "IZM",
    "n": "ICZOOM Group Inc. - Class A Ordinary Shares"
  },
  {
    "s": "J",
    "n": "Jacobs Solutions Inc. Common Stock"
  },
  {
    "s": "JACK",
    "n": "Jack In The Box Inc. - Common Stock"
  },
  {
    "s": "JACS",
    "n": "Jackson Acquisition Company II Class A Ordinary Shares"
  },
  {
    "s": "JACS-U",
    "n": "Jackson Acquisition Company II Units, each consisting of one Class A ordinary share and one right to acquire one-tenth (1/10) of one Class A ordinary share"
  },
  {
    "s": "JAGU",
    "n": "Jaguar Uranium Corp. Class A Common Shares"
  },
  {
    "s": "JAGX",
    "n": "Jaguar Health, Inc. - Common Stock"
  },
  {
    "s": "JAKK",
    "n": "JAKKS Pacific, Inc. - Common Stock"
  },
  {
    "s": "JAN",
    "n": "Janus Living, Inc. Class A-1 Common Stock"
  },
  {
    "s": "JANX",
    "n": "Janux Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "JATT",
    "n": "JATT II Acquisition Corp - Ordinary Shares"
  },
  {
    "s": "JAZZ",
    "n": "Jazz Pharmaceuticals plc - Ordinary Shares"
  },
  {
    "s": "JBDI",
    "n": "JBDI Holdings Limited - Ordinary Shares"
  },
  {
    "s": "JBGS",
    "n": "JBG SMITH Properties Common Shares "
  },
  {
    "s": "JBHT",
    "n": "J.B. Hunt Transport Services, Inc. - Common Stock"
  },
  {
    "s": "JBI",
    "n": "Janus International Group, Inc. Common Stock"
  },
  {
    "s": "JBIO",
    "n": "Jade Biosciences, Inc. - Common Stock"
  },
  {
    "s": "JBK",
    "n": "Lehman ABS 3.50 3.50% Adjustable Corp Backed Tr Certs GS Cap I"
  },
  {
    "s": "JBL",
    "n": "Jabil Inc. Common Stock"
  },
  {
    "s": "JBLU",
    "n": "JetBlue Airways Corporation - Common Stock"
  },
  {
    "s": "JBS",
    "n": "JBS N.V. Class A Common Shares"
  },
  {
    "s": "JBSS",
    "n": "John B. Sanfilippo & Son, Inc. - Common Stock"
  },
  {
    "s": "JBTM",
    "n": "JBT Marel Corporation Common Stock"
  },
  {
    "s": "JCAP",
    "n": "Jefferson Capital, Inc. - Common Stock"
  },
  {
    "s": "JCI",
    "n": "Johnson Controls International plc Ordinary Share"
  },
  {
    "s": "JCSE",
    "n": "JE Cleantech Holdings Limited - Ordinary Shares"
  },
  {
    "s": "JCTC",
    "n": "Jewett-Cameron Trading Company - Common Shares"
  },
  {
    "s": "JD",
    "n": "JD.com, Inc. - American Depositary Shares"
  },
  {
    "s": "JDZG",
    "n": "JIADE LIMITED - Class A Ordinary Shares"
  },
  {
    "s": "JEF",
    "n": "Jefferies Financial Group Inc. Common Stock"
  },
  {
    "s": "JELD",
    "n": "JELD-WEN Holding, Inc. Common Stock"
  },
  {
    "s": "JEM",
    "n": "707 Cayman Holdings Limited - Ordinary Shares"
  },
  {
    "s": "JENA",
    "n": "Jena Acquisition Corporation II Class A Ordinary Shares"
  },
  {
    "s": "JENA-U",
    "n": "Jena Acquisition Corporation II Units, each consisting of one Class A ordinary share and one right"
  },
  {
    "s": "JF",
    "n": "J and Friends Holdings Limited - American Depositary Shares"
  },
  {
    "s": "JFIN",
    "n": "Jiayin Group Inc. - American Depositary Shares"
  },
  {
    "s": "JFU",
    "n": "9F Inc. - American Depositary Shares"
  },
  {
    "s": "JG",
    "n": "Aurora Mobile Limited - American Depositary Shares"
  },
  {
    "s": "JHI",
    "n": "John Hancock Investors Trust Common Stock"
  },
  {
    "s": "JHS",
    "n": "John Hancock Income Securities Trust Common Stock"
  },
  {
    "s": "JHX",
    "n": "James Hardie Industries plc. Ordinary Shares"
  },
  {
    "s": "JILL",
    "n": "J. Jill, Inc. Common Stock"
  },
  {
    "s": "JJSF",
    "n": "J & J Snack Foods Corp. - Common Stock"
  },
  {
    "s": "JKHY",
    "n": "Jack Henry & Associates, Inc. - Common Stock"
  },
  {
    "s": "JKS",
    "n": "JinkoSolar Holding Company Limited American Depositary Shares (each representing 4 Common Shares)"
  },
  {
    "s": "JL",
    "n": "J-Long Group Limited - Class A Ordinary Shares"
  },
  {
    "s": "JLHL",
    "n": "Julong Holding Limited - Class A Ordinary Shares"
  },
  {
    "s": "JLL",
    "n": "Jones Lang LaSalle Incorporated Common Stock"
  },
  {
    "s": "JMIA",
    "n": "Jumia Technologies AG American Depositary Shares, each representing two Ordinary Shares"
  },
  {
    "s": "JMKE",
    "n": "Jersey Mike's Subs Inc. Class A Common Stock"
  },
  {
    "s": "JMSB",
    "n": "John Marshall Bancorp, Inc. - Common Stock"
  },
  {
    "s": "JNJ",
    "n": "Johnson & Johnson Common Stock"
  },
  {
    "s": "JOB",
    "n": "GEE Group Inc. Common Stock"
  },
  {
    "s": "JOBY",
    "n": "Joby Aviation, Inc. Common Stock"
  },
  {
    "s": "JOE",
    "n": "St. Joe Company (The) Common Stock"
  },
  {
    "s": "JONE",
    "n": "Jones Ventures INTL Acquisition1 Corp - Class A Ordinary Shares"
  },
  {
    "s": "JONEU",
    "n": "Jones Ventures INTL Acquisition1 Corp - Units"
  },
  {
    "s": "JOUT",
    "n": "Johnson Outdoors Inc. - Class A Common Stock"
  },
  {
    "s": "JOYY",
    "n": "JOYY Inc. - American Depositary Shares"
  },
  {
    "s": "JPM",
    "n": "JP Morgan Chase & Co. Common Stock"
  },
  {
    "s": "JRSH",
    "n": "Jerash Holdings (US), Inc. - Common Stock"
  },
  {
    "s": "JRVR",
    "n": "James River Group Holdings, Inc. - Common Stock"
  },
  {
    "s": "JSM",
    "n": "Navient Corporation - 6% Senior Notes due December 15, 2043"
  },
  {
    "s": "JSPR",
    "n": "Jasper Therapeutics, Inc. - Class A Common Stock"
  },
  {
    "s": "JTAI",
    "n": "Jet.AI Inc. - Common Stock"
  },
  {
    "s": "JTTT",
    "n": "JATT III Acquisition Corp - Ordinary Shares"
  },
  {
    "s": "JUNS",
    "n": "Jupiter Neurosciences, Inc. - Common Stock"
  },
  {
    "s": "JVA",
    "n": "Coffee Holding Co., Inc. - Common Stock"
  },
  {
    "s": "JWEL",
    "n": "Jowell Global Ltd. - Ordinary Shares"
  },
  {
    "s": "JXG",
    "n": "JX Luxventure Group Inc. - Common Stock"
  },
  {
    "s": "JXN",
    "n": "Jackson Financial Inc. Class A Common Stock "
  },
  {
    "s": "JYD",
    "n": "Jayud Global Logistics Limited - Class A Ordinary Shares"
  },
  {
    "s": "JYNT",
    "n": "The Joint Corp. - Common Stock"
  },
  {
    "s": "JZ",
    "n": "Jianzhi Education Technology Group Company Limited - American Depositary Shares"
  },
  {
    "s": "JZXN",
    "n": "Jiuzi Holdings, Inc. - Ordinary Shares"
  },
  {
    "s": "KAI",
    "n": "Kadant Inc Common Stock"
  },
  {
    "s": "KALA",
    "n": "KALA BIO, Inc. - Common Stock"
  },
  {
    "s": "KALU",
    "n": "Kaiser Aluminum Corporation - Common Stock"
  },
  {
    "s": "KAPA",
    "n": "Kairos Pharma, Ltd. Common Stock"
  },
  {
    "s": "KARD",
    "n": "Kardigan, Inc. - Common Stock"
  },
  {
    "s": "KARO",
    "n": "Karooooo Ltd. - Ordinary shares"
  },
  {
    "s": "KAZR",
    "n": "Skyline Builders Group Holding Limited - Class A Ordinary Shares"
  },
  {
    "s": "KB",
    "n": "KB Financial Group Inc"
  },
  {
    "s": "KBDC",
    "n": "Kayne Anderson BDC, Inc. Common Stock"
  },
  {
    "s": "KBH",
    "n": "KB Home Common Stock"
  },
  {
    "s": "KBON",
    "n": "Karbon Capital Partners Corp. - Class A Ordinary Shares"
  },
  {
    "s": "KBONU",
    "n": "Karbon Capital Partners Corp. - Units"
  },
  {
    "s": "KBR",
    "n": "KBR, Inc. Common Stock"
  },
  {
    "s": "KBSX",
    "n": "FST Corp. - Ordinary Shares"
  },
  {
    "s": "KC",
    "n": "Kingsoft Cloud Holdings Limited - American Depositary Shares"
  },
  {
    "s": "KCAC-W",
    "n": "Kensington Capital Acquisition Corp. VI Class 1 redeemable warrants, each exercisable for one Class A ordinary share at an exercise price of $11.50"
  },
  {
    "s": "KCHV",
    "n": "Kochav Defense Acquisition Corp. - Class A Ordinary Shares"
  },
  {
    "s": "KCHVR",
    "n": "Kochav Defense Acquisition Corp. - Right"
  },
  {
    "s": "KCHVU",
    "n": "Kochav Defense Acquisition Corp. - Units"
  },
  {
    "s": "KD",
    "n": "Kyndryl Holdings, Inc. Common Stock"
  },
  {
    "s": "KDK",
    "n": "Kodiak AI, Inc. - Common Stock"
  },
  {
    "s": "KDP",
    "n": "Keurig Dr Pepper Inc. - Common Stock"
  },
  {
    "s": "KE",
    "n": "Kimball Electronics, Inc. - Common Stock"
  },
  {
    "s": "KEEL",
    "n": "Keel Infrastructure Corp. - Common Stock"
  },
  {
    "s": "KELYA",
    "n": "Kelly Services, Inc. - Class A Common Stock"
  },
  {
    "s": "KELYB",
    "n": "Kelly Services, Inc. - Class B Common Stock"
  },
  {
    "s": "KEN",
    "n": "Kenon Holdings Ltd. Ordinary Shares"
  },
  {
    "s": "KEP",
    "n": "Korea Electric Power Corporation Common Stock"
  },
  {
    "s": "KEQU",
    "n": "Kewaunee Scientific Corporation - Common Stock"
  },
  {
    "s": "KEX",
    "n": "Kirby Corporation Common Stock"
  },
  {
    "s": "KEY",
    "n": "KeyCorp Common Stock"
  },
  {
    "s": "KEYS",
    "n": "Keysight Technologies Inc. Common Stock"
  },
  {
    "s": "KEYY",
    "n": "Keystone Acquisition Corp. - Class A Ordinary Shares"
  },
  {
    "s": "KEYYU",
    "n": "Keystone Acquisition Corp. - Unit"
  },
  {
    "s": "KEYYW",
    "n": "Keystone Acquisition Corp. - Warrants"
  },
  {
    "s": "KFFB",
    "n": "Kentucky First Federal Bancorp - Common Stock"
  },
  {
    "s": "KFII",
    "n": "K&F Growth Acquisition Corp. II - Class A Ordinary shares"
  },
  {
    "s": "KFIIU",
    "n": "K&F Growth Acquisition Corp. II - Unit"
  },
  {
    "s": "KFRC",
    "n": "Kforce, Inc. Common Stock"
  },
  {
    "s": "KFY",
    "n": "Korn Ferry Common Stock"
  },
  {
    "s": "KG",
    "n": "Kestrel Group, Ltd. - Common Stock"
  },
  {
    "s": "KGC",
    "n": "Kinross Gold Corporation Common Stock"
  },
  {
    "s": "KGEI",
    "n": "Kolibri Global Energy Inc. - Common stock"
  },
  {
    "s": "KGS",
    "n": "Kodiak Gas Services, Inc. Common Stock"
  },
  {
    "s": "KHC",
    "n": "The Kraft Heinz Company Common Stock"
  },
  {
    "s": "KIDS",
    "n": "OrthoPediatrics Corp. - Common Stock"
  },
  {
    "s": "KIDZ",
    "n": "KIDZ AI Inc. - Class B Common Stock"
  },
  {
    "s": "KIDZW",
    "n": "KIDZ AI Inc. - Warrants"
  },
  {
    "s": "KIM",
    "n": "Kimco Realty Corporation (HC) Common Stock"
  },
  {
    "s": "KINS",
    "n": "Kingstone Companies, Inc - Common Stock"
  },
  {
    "s": "KITT",
    "n": "Nauticus Robotics, Inc. - Common stock"
  },
  {
    "s": "KKR",
    "n": "KKR & Co. Inc. Common Stock"
  },
  {
    "s": "KKRS",
    "n": "KKR Group Finance Co. IX LLC 4.625% Subordinated Notes due 2061"
  },
  {
    "s": "KKRT",
    "n": "KKR & Co. Inc. 6.875% Subordinated Notes due 2065"
  },
  {
    "s": "KLAC",
    "n": "KLA Corporation  - Common Stock"
  },
  {
    "s": "KLAR",
    "n": "Klarna Group plc Ordinary Shares"
  },
  {
    "s": "KLC",
    "n": "KinderCare Learning Companies, Inc. Common Stock"
  },
  {
    "s": "KLIC",
    "n": "Kulicke and Soffa Industries, Inc. - Common Stock"
  },
  {
    "s": "KLRA",
    "n": "Kailera Therapeutics, Inc. - Common stock"
  },
  {
    "s": "KLRS",
    "n": "Kalaris Therapeutics, Inc.  - Common Stock"
  },
  {
    "s": "KLTR",
    "n": "Kaltura, Inc. - Common Stock"
  },
  {
    "s": "KLXE",
    "n": "KLX Energy Services Holdings, Inc.  - Common Stock"
  },
  {
    "s": "KMB",
    "n": "Kimberly-Clark Corporation - Common Stock"
  },
  {
    "s": "KMDA",
    "n": "Kamada Ltd. - Ordinary Shares"
  },
  {
    "s": "KMI",
    "n": "Kinder Morgan, Inc. Common Stock"
  },
  {
    "s": "KMPB",
    "n": "Kemper Corporation 5.875% Fixed-Rate Reset Junior Subordinated Debentures due 2062"
  },
  {
    "s": "KMPR",
    "n": "Kemper Corporation"
  },
  {
    "s": "KMRK",
    "n": "K-Tech Solutions Company Limited - Class A Ordinary Shares"
  },
  {
    "s": "KMT",
    "n": "Kennametal Inc. Common Stock"
  },
  {
    "s": "KMTS",
    "n": "Kestra Medical Technologies, Ltd. - Common Stock"
  },
  {
    "s": "KMX",
    "n": "CarMax Inc"
  },
  {
    "s": "KN",
    "n": "Knowles Corporation Common Stock"
  },
  {
    "s": "KNDI",
    "n": "Kandi Technologies Group, Inc. - Ordinary Shares"
  },
  {
    "s": "KNF",
    "n": "Knife Riv Holding Co. Common Stock"
  },
  {
    "s": "KNRX",
    "n": "KNOREX LTD. Class A Ordinary Shares"
  },
  {
    "s": "KNSA",
    "n": "Kiniksa Pharmaceuticals International, plc - Class A Ordinary Shares"
  },
  {
    "s": "KNSL",
    "n": "Kinsale Capital Group, Inc. Common Stock"
  },
  {
    "s": "KNTK",
    "n": "Kinetik Holdings Inc. Class A Common Stock"
  },
  {
    "s": "KNX",
    "n": "Knight-Swift Transportation Holdings Inc."
  },
  {
    "s": "KO",
    "n": "Coca-Cola Company (The) Common Stock"
  },
  {
    "s": "KOD",
    "n": "Kodiak Sciences Inc - Common Stock"
  },
  {
    "s": "KODK",
    "n": "Eastman Kodak Company Common New"
  },
  {
    "s": "KOF",
    "n": "Coca Cola Femsa S.A.B. de C.V.  American Depositary Shares, each representing 10 Units (each Unit consists of 3 Series B Shares and 5 Series L Shares)"
  },
  {
    "s": "KOP",
    "n": "Koppers Holdings Inc. Common Stock"
  },
  {
    "s": "KOPN",
    "n": "Kopin Corporation - Common Stock"
  },
  {
    "s": "KOS",
    "n": "Kosmos Energy Ltd. Common Shares (DE)"
  },
  {
    "s": "KOSS",
    "n": "Koss Corporation - Common Stock"
  },
  {
    "s": "KOYN",
    "n": "CSLM Digital Asset Acquisition Corp III - Class A Ordinary Shares"
  },
  {
    "s": "KOYNU",
    "n": "CSLM Digital Asset Acquisition Corp III - Units"
  },
  {
    "s": "KOYNW",
    "n": "CSLM Digital Asset Acquisition Corp III - Warrants"
  },
  {
    "s": "KPET",
    "n": "KPET Ultra Paceline Corporation Class A Ordinary Shares"
  },
  {
    "s": "KPLT",
    "n": "Katapult Holdings, Inc. - Common Stock"
  },
  {
    "s": "KPRX",
    "n": "Kiora Pharmaceuticals, Inc.  - Common Stock"
  },
  {
    "s": "KPTI",
    "n": "Karyopharm Therapeutics Inc. - Common Stock"
  },
  {
    "s": "KR",
    "n": "Kroger Company (The) Common Stock"
  },
  {
    "s": "KRAQ",
    "n": "KRAKacquisition Corp - Class A Ordinary Shares"
  },
  {
    "s": "KRAQU",
    "n": "KRAKacquisition Corp - Unit"
  },
  {
    "s": "KRAQW",
    "n": "KRAKacquisition Corp - Warrants"
  },
  {
    "s": "KRC",
    "n": "Kilroy Realty Corporation Common Stock"
  },
  {
    "s": "KREF",
    "n": "KKR Real Estate Finance Trust Inc. Common Stock"
  },
  {
    "s": "KRG",
    "n": "Kite Realty Group Trust Common Stock"
  },
  {
    "s": "KRKR",
    "n": "36Kr Holdings Inc. - American Depositary Shares"
  },
  {
    "s": "KRMD",
    "n": "KORU Medical Systems, Inc. - Common Stock"
  },
  {
    "s": "KRMN",
    "n": "Karman Holdings Inc. Common Stock"
  },
  {
    "s": "KRNT",
    "n": "Kornit Digital Ltd. - Ordinary Shares"
  },
  {
    "s": "KRNY",
    "n": "Kearny Financial - Common Stock"
  },
  {
    "s": "KRO",
    "n": "Kronos Worldwide Inc Common Stock"
  },
  {
    "s": "KROS",
    "n": "Keros Therapeutics, Inc. - common stock"
  },
  {
    "s": "KRP",
    "n": "Kimbell Royalty Partners Common Units Representing Limited Partner Interests"
  },
  {
    "s": "KRRO",
    "n": "Korro Bio, Inc. - Common Stock"
  },
  {
    "s": "KRSA",
    "n": "Korsana Biosciences, Inc. - Common Stock"
  },
  {
    "s": "KRSP",
    "n": "Rice Acquisition Corporation 3 Class A Ordinary Shares"
  },
  {
    "s": "KRT",
    "n": "Karat Packaging Inc. - Common Stock"
  },
  {
    "s": "KRUS",
    "n": "Kura Sushi USA, Inc. - Class A Common Stock"
  },
  {
    "s": "KRYS",
    "n": "Krystal Biotech, Inc. - Common Stock"
  },
  {
    "s": "KSCP",
    "n": "Knightscope, Inc. - Class A Common Stock"
  },
  {
    "s": "KSPI",
    "n": "Joint Stock Company Kaspi.kz - American Depository Shares"
  },
  {
    "s": "KSS",
    "n": "Kohl's Corporation Common Stock"
  },
  {
    "s": "KT",
    "n": "KT Corporation Common Stock"
  },
  {
    "s": "KTB",
    "n": "Kontoor Brands, Inc. Common Stock "
  },
  {
    "s": "KTCC",
    "n": "Key Tronic Corporation - Common Stock"
  },
  {
    "s": "KTF",
    "n": "DWS Municipal Income Trust"
  },
  {
    "s": "KTN",
    "n": "Structured Products Corp 8.205% CorTS 8.205% Corporate Backed Trust Securities (CorTS)"
  },
  {
    "s": "KTOS",
    "n": "Kratos Defense & Security Solutions, Inc. - Common Stock"
  },
  {
    "s": "KTTA",
    "n": "Pasithea Therapeutics Corp. - Common Stock"
  },
  {
    "s": "KTWO",
    "n": "K2 Capital Acquisition Corporation - Class A Ordinary Share"
  },
  {
    "s": "KTWOU",
    "n": "K2 Capital Acquisition Corporation - Units"
  },
  {
    "s": "KULR",
    "n": "KULR Technology Group, Inc. Common Stock"
  },
  {
    "s": "KURA",
    "n": "Kura Oncology, Inc. - Common Stock"
  },
  {
    "s": "KUST",
    "n": "Kustom Entertainment, Inc. - Common Stock"
  },
  {
    "s": "KVHI",
    "n": "KVH Industries, Inc. - Common Stock"
  },
  {
    "s": "KVUE",
    "n": "Kenvue Inc. Common Stock"
  },
  {
    "s": "KVYO",
    "n": "Klaviyo, Inc. Series A Common Stock"
  },
  {
    "s": "KWR",
    "n": "Quaker Houghton Common Stock"
  },
  {
    "s": "KWY",
    "n": "Kingsway Corporation Common Stock"
  },
  {
    "s": "KXIN",
    "n": "Kaixin Holdings - Ordinary Shares"
  },
  {
    "s": "KYIV",
    "n": "Kyivstar Group Ltd. - Common Shares"
  },
  {
    "s": "KYMR",
    "n": "Kymera Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "KYNB",
    "n": "Kyntra Bio, Inc. - Common Stock"
  },
  {
    "s": "KYTX",
    "n": "Kyverna Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "KZIA",
    "n": "Kazia Therapeutics Limited - American Depositary Shares"
  },
  {
    "s": "L",
    "n": "Loews Corporation Common Stock"
  },
  {
    "s": "LAB",
    "n": "Standard BioTools Inc. - Common Stock"
  },
  {
    "s": "LABT",
    "n": "Lakewood-Amedex Biotherapeutics Inc. - Common Stock"
  },
  {
    "s": "LAC",
    "n": "Lithium Americas Corp. Common Shares"
  },
  {
    "s": "LAD",
    "n": "Lithia Motors, Inc. Common Stock"
  },
  {
    "s": "LADR",
    "n": "Ladder Capital Corp Class A Common Stock"
  },
  {
    "s": "LAES",
    "n": "SEALSQ Corp - Ordinary Shares"
  },
  {
    "s": "LAFA",
    "n": "LaFayette Acquisition Corp. - Ordinary Share"
  },
  {
    "s": "LAFAU",
    "n": "LaFayette Acquisition Corp. - Unit"
  },
  {
    "s": "LAKE",
    "n": "Lakeland Industries, Inc. - Common Stock"
  },
  {
    "s": "LAMR",
    "n": "Lamar Advertising Company - Class A Common Stock"
  },
  {
    "s": "LAND",
    "n": "Gladstone Land Corporation - Common Stock"
  },
  {
    "s": "LANV",
    "n": "Lanvin Group Holdings Limited Ordinary Shares"
  },
  {
    "s": "LAR",
    "n": "Lithium Argentina AG Common Shares"
  },
  {
    "s": "LARK",
    "n": "Landmark Bancorp Inc. - Common Stock"
  },
  {
    "s": "LASE",
    "n": "Laser Photonics Corporation - Common Stock"
  },
  {
    "s": "LASR",
    "n": "nLIGHT, Inc. - Common Stock"
  },
  {
    "s": "LATA",
    "n": "Galata Acquisition Corp. II - Class A Ordinary Shares"
  },
  {
    "s": "LATAU",
    "n": "Galata Acquisition Corp. II - Units"
  },
  {
    "s": "LAUR",
    "n": "Laureate Education, Inc. - Common Stock"
  },
  {
    "s": "LAW",
    "n": "CS Disco, Inc. Common Stock"
  },
  {
    "s": "LAWR",
    "n": "Robot Consulting Co., Ltd. - ADS"
  },
  {
    "s": "LAZ",
    "n": "Lazard, Inc. Common Stock"
  },
  {
    "s": "LB",
    "n": "LandBridge Company LLC Class A Shares Representing Limited Liability Company Interests"
  },
  {
    "s": "LBGJ",
    "n": "Li Bang International Corporation Inc. - Class A Ordinary Shares"
  },
  {
    "s": "LBRT",
    "n": "Liberty Energy Inc. Class A common stock"
  },
  {
    "s": "LBRX",
    "n": "LB Pharmaceuticals Inc - Common Stock"
  },
  {
    "s": "LBTYA",
    "n": "Liberty Global Ltd. - Class A Common Shares"
  },
  {
    "s": "LBTYB",
    "n": "Liberty Global Ltd. - Class B Common Shares"
  },
  {
    "s": "LBTYK",
    "n": "Liberty Global Ltd. - Class C Common Shares"
  },
  {
    "s": "LCCC",
    "n": "Lakeshore Acquisition III Corp. - Ordinary Shares"
  },
  {
    "s": "LCCCU",
    "n": "Lakeshore Acquisition III Corp. - Unit"
  },
  {
    "s": "LCFY",
    "n": "Locafy Limited - Ordinary Share"
  },
  {
    "s": "LCID",
    "n": "Lucid Group, Inc. - Common Stock"
  },
  {
    "s": "LCII",
    "n": "LCI Industries"
  },
  {
    "s": "LCLN",
    "n": "Lincoln International, Inc. Class A Common Stock"
  },
  {
    "s": "LCNB",
    "n": "LCNB Corporation - Common Stock"
  },
  {
    "s": "LCTX",
    "n": "Lineage Cell Therapeutics, Inc. Common Stock"
  },
  {
    "s": "LCUT",
    "n": "Lifetime Brands, Inc. - Common Stock"
  },
  {
    "s": "LDI",
    "n": "loanDepot, Inc. Class A Common Stock"
  },
  {
    "s": "LDOS",
    "n": "Leidos Holdings, Inc. Common Stock"
  },
  {
    "s": "LE",
    "n": "Lands' End, Inc. - Common Stock"
  },
  {
    "s": "LEA",
    "n": "Lear Corporation Common Stock"
  },
  {
    "s": "LECO",
    "n": "Lincoln Electric Holdings, Inc. - Common Shares"
  },
  {
    "s": "LEDRU",
    "n": "Leader's Advantage Acquisition Corp. - Units"
  },
  {
    "s": "LEDS",
    "n": "SemiLEDS Corporation - Common Stock"
  },
  {
    "s": "LEE",
    "n": "Lee Enterprises, Incorporated - Common Stock"
  },
  {
    "s": "LEGH",
    "n": "Legacy Housing Corporation - Common Stock"
  },
  {
    "s": "LEGN",
    "n": "Legend Biotech Corporation - American Depositary Shares"
  },
  {
    "s": "LEGO",
    "n": "Legato Merger Corp. IV Ordinary Shares"
  },
  {
    "s": "LEN",
    "n": "Lennar Corporation Class A Common Stock"
  },
  {
    "s": "LEN-B",
    "n": "Lennar Corporation Class B"
  },
  {
    "s": "LENZ",
    "n": "LENZ Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "LEO",
    "n": "BNY Mellon Strategic Municipals, Inc. Common Stock"
  },
  {
    "s": "LEU",
    "n": "Centrus Energy Corp. Class A Common Stock"
  },
  {
    "s": "LEVI",
    "n": "Levi Strauss & Co Class A Common Stock"
  },
  {
    "s": "LEXX",
    "n": "Lexaria Bioscience Corp. - Common Stock"
  },
  {
    "s": "LFAC",
    "n": "Leapfrog Acquisition Corporation - Class A Ordinary Shares"
  },
  {
    "s": "LFACU",
    "n": "Leapfrog Acquisition Corporation - Units"
  },
  {
    "s": "LFACW",
    "n": "Leapfrog Acquisition Corporation - Warrants"
  },
  {
    "s": "LFCR",
    "n": "Lifecore Biomedical, Inc. - Common Stock"
  },
  {
    "s": "LFMD",
    "n": "LifeMD, Inc. - Common Stock"
  },
  {
    "s": "LFS",
    "n": "LEIFRAS Co., Ltd. - American Depositary Shares"
  },
  {
    "s": "LFST",
    "n": "LifeStance Health Group, Inc. - Common Stock"
  },
  {
    "s": "LFT",
    "n": "Lument Finance Trust, Inc. Common Stock"
  },
  {
    "s": "LFTO",
    "n": "Liftoff Mobile, Inc. - Common Stock"
  },
  {
    "s": "LFUS",
    "n": "Littelfuse, Inc. - Common Stock"
  },
  {
    "s": "LFVN",
    "n": "Lifevantage Corporation - Common Stock"
  },
  {
    "s": "LFWD",
    "n": "Lifeward Ltd. - Ordinary Shares"
  },
  {
    "s": "LGCL",
    "n": "Lucas GC Limited - Class A Ordinary Shares"
  },
  {
    "s": "LGCY",
    "n": "Legacy Education Inc. Common Stock"
  },
  {
    "s": "LGHL",
    "n": "Lion Group Holding Ltd. - American Depositary Share"
  },
  {
    "s": "LGIH",
    "n": "LGI Homes, Inc. - Common Stock"
  },
  {
    "s": "LGL",
    "n": "LGL Group, Inc. (The) Common Stock"
  },
  {
    "s": "LGN",
    "n": "Legence Corp. - Class A Common stock"
  },
  {
    "s": "LGND",
    "n": "Ligand Pharmaceuticals Incorporated - Common Stock"
  },
  {
    "s": "LGO",
    "n": "Largo Inc. - Common Shares"
  },
  {
    "s": "LGPS",
    "n": "LogProstyle Inc. Common Shares"
  },
  {
    "s": "LGVN",
    "n": "Longeveron Inc. - Class A Common stock"
  },
  {
    "s": "LH",
    "n": "Labcorp Holdings Inc. Common Stock"
  },
  {
    "s": "LHAI",
    "n": "Linkhome Holdings Inc. - Common stock"
  },
  {
    "s": "LHSW",
    "n": "Lianhe Sowell International Group Ltd - Class A Ordinary Shares"
  },
  {
    "s": "LHX",
    "n": "L3Harris Technologies, Inc. Common Stock"
  },
  {
    "s": "LI",
    "n": "Li Auto Inc. - American Depositary Shares"
  },
  {
    "s": "LICN",
    "n": "Lichen International Limited - Class A Ordinary Shares"
  },
  {
    "s": "LIDR",
    "n": "AEye, Inc. - Class A Common Stock"
  },
  {
    "s": "LIEN",
    "n": "Chicago Atlantic BDC, Inc. - Common Stock"
  },
  {
    "s": "LIF",
    "n": "Life360, Inc. - Common Stock"
  },
  {
    "s": "LIFE",
    "n": "Ethos Technologies Inc. - Class A Common Stock"
  },
  {
    "s": "LII",
    "n": "Lennox International, Inc. Common Stock"
  },
  {
    "s": "LILA",
    "n": "Liberty Latin America Ltd. - Class A Common Stock"
  },
  {
    "s": "LILAK",
    "n": "Liberty Latin America Ltd. - Class C Common Stock"
  },
  {
    "s": "LILAP",
    "n": "Liberty Latin America Ltd. - 9.0% Fixed Rate Cumulative Perpetual Redeemable Series A Preference Shares"
  },
  {
    "s": "LIME",
    "n": "Neutron Holdings, Inc. - Common Stock"
  },
  {
    "s": "LIMN",
    "n": "Liminatus Pharma, Inc. - Class A Common Stock"
  },
  {
    "s": "LIMNW",
    "n": "Liminatus Pharma, Inc. - Warrants"
  },
  {
    "s": "LIN",
    "n": "Linde plc - Ordinary Shares"
  },
  {
    "s": "LINC",
    "n": "Lincoln Educational Services Corporation - Common Stock"
  },
  {
    "s": "LIND",
    "n": "Lindblad Expeditions Holdings Inc.  - Common Stock"
  },
  {
    "s": "LINE",
    "n": "Lineage, Inc. - Common Stock"
  },
  {
    "s": "LINK",
    "n": "Interlink Electronics, Inc. - Common Stock"
  },
  {
    "s": "LION",
    "n": "Lionsgate Studios Corp Common Shares"
  },
  {
    "s": "LIQT",
    "n": "LiqTech International, Inc. - Common Stock"
  },
  {
    "s": "LITB",
    "n": "LightInTheBox Holding Co., Ltd. American Depositary Shares, each representing twelve ordinary shares"
  },
  {
    "s": "LITE",
    "n": "Lumentum Holdings Inc. - Common Stock"
  },
  {
    "s": "LITS",
    "n": "Lite Strategy, Inc. - Common Stock"
  },
  {
    "s": "LIVE",
    "n": "Live Ventures Incorporated - Common Stock"
  },
  {
    "s": "LIVN",
    "n": "LivaNova PLC - Ordinary Shares"
  },
  {
    "s": "LKFN",
    "n": "Lakeland Financial Corporation - Common Stock"
  },
  {
    "s": "LKFT",
    "n": "Lakefront Biotherapeutics - American Depositary Shares"
  },
  {
    "s": "LKQ",
    "n": "LKQ Corporation - Common Stock"
  },
  {
    "s": "LKSP",
    "n": "Lake Superior Acquisition Corp. - Class A Ordinary Shares"
  },
  {
    "s": "LKSPU",
    "n": "Lake Superior Acquisition Corp. - Units"
  },
  {
    "s": "LLY",
    "n": "Eli Lilly and Company Common Stock"
  },
  {
    "s": "LLYVA",
    "n": "Liberty Live Holdings, Inc. - Series A Liberty Live Group Common Stock"
  },
  {
    "s": "LLYVK",
    "n": "Liberty Live Holdings, Inc. - Series C Liberty Live Group Common Stock"
  },
  {
    "s": "LMAT",
    "n": "LeMaitre Vascular, Inc. - Common Stock"
  },
  {
    "s": "LMB",
    "n": "Limbach Holdings, Inc. - Common Stock"
  },
  {
    "s": "LMND",
    "n": "Lemonade, Inc. Common Stock"
  },
  {
    "s": "LMNR",
    "n": "Limoneira Co - Common Stock"
  },
  {
    "s": "LMRI",
    "n": "Lumexa Imaging Holdings, Inc. - Common Stock"
  },
  {
    "s": "LMT",
    "n": "Lockheed Martin Corporation Common Stock"
  },
  {
    "s": "LNAI",
    "n": "Lunai Bioworks Inc. - Common Stock"
  },
  {
    "s": "LNC",
    "n": "Lincoln National Corporation Common Stock"
  },
  {
    "s": "LND",
    "n": "Brasilagro Brazilian Agric Real Estate Co Sponsored ADR (Brazil)"
  },
  {
    "s": "LNG",
    "n": "Cheniere Energy, Inc. Common Stock"
  },
  {
    "s": "LNKS",
    "n": "Linkers Industries Limited - Class A Ordinary Shares"
  },
  {
    "s": "LNN",
    "n": "Lindsay Corporation Common Stock"
  },
  {
    "s": "LNSR",
    "n": "LENSAR, Inc. - Common Stock"
  },
  {
    "s": "LNT",
    "n": "Alliant Energy Corporation - Common Stock"
  },
  {
    "s": "LNTH",
    "n": "Lantheus Holdings, Inc. - Common Stock"
  },
  {
    "s": "LNZA",
    "n": "LanzaTech Global, Inc. - Common Stock"
  },
  {
    "s": "LOAN",
    "n": "Manhattan Bridge Capital, Inc - Common Stock"
  },
  {
    "s": "LOAR",
    "n": "Loar Holdings Inc. Common Stock"
  },
  {
    "s": "LOB",
    "n": "Live Oak Bancshares, Inc. Common Stock"
  },
  {
    "s": "LOBO",
    "n": "LOBO TECHNOLOGIES LTD. - Class A Ordinary Shares"
  },
  {
    "s": "LOCL",
    "n": "Local Bounti Corporation Common Stock"
  },
  {
    "s": "LOCO",
    "n": "El Pollo Loco Holdings, Inc. - Common Stock"
  },
  {
    "s": "LODE",
    "n": "Comstock Inc. Common Stock"
  },
  {
    "s": "LOGI",
    "n": "Logitech International S.A. - Registered Shares"
  },
  {
    "s": "LOMA",
    "n": "Loma Negra Compania Industrial Argentina Sociedad Anonima ADS"
  },
  {
    "s": "LONA",
    "n": "LeonaBio, Inc. - Common Stock"
  },
  {
    "s": "LOOP",
    "n": "Loop Industries, Inc. - Common Stock"
  },
  {
    "s": "LOPE",
    "n": "Grand Canyon Education, Inc. - Common Stock"
  },
  {
    "s": "LOT",
    "n": "Lotus Technology Inc. - American Depositary Shares"
  },
  {
    "s": "LOTWW",
    "n": "Lotus Technology Inc. - Warrants"
  },
  {
    "s": "LOVE",
    "n": "The Lovesac Company - Common Stock"
  },
  {
    "s": "LOVIU",
    "n": "Live Oak Acquisition Corp. VI - Units"
  },
  {
    "s": "LOW",
    "n": "Lowe's Companies, Inc. Common Stock"
  },
  {
    "s": "LPA",
    "n": "Logistic Properties of the Americas Ordinary Shares"
  },
  {
    "s": "LPAA",
    "n": "Launch One Acquisition Corp. - Class A Ordinary Shares"
  },
  {
    "s": "LPAAU",
    "n": "Launch One Acquisition Corp. - Unit"
  },
  {
    "s": "LPBB",
    "n": "Launch Two Acquisition Corp. - Class A Ordinary Shares"
  },
  {
    "s": "LPBBU",
    "n": "Launch Two Acquisition Corp. - Unit"
  },
  {
    "s": "LPCN",
    "n": "Lipocine Inc. - Common Stock"
  },
  {
    "s": "LPCV",
    "n": "Launchpad Cadenza Acquisition Corp I - Class A Ordinary Share"
  },
  {
    "s": "LPCVU",
    "n": "Launchpad Cadenza Acquisition Corp I - Unit"
  },
  {
    "s": "LPG",
    "n": "Dorian LPG Ltd. Common Stock"
  },
  {
    "s": "LPL",
    "n": "LG Display Co, Ltd AMERICAN DEPOSITORY SHARES"
  },
  {
    "s": "LPLA",
    "n": "LPL Financial Holdings Inc. - Common Stock"
  },
  {
    "s": "LPTH",
    "n": "LightPath Technologies, Inc. - Class A Common Stock"
  },
  {
    "s": "LPX",
    "n": "Louisiana-Pacific Corporation Common Stock"
  },
  {
    "s": "LQDA",
    "n": "Liquidia Corporation - Common Stock"
  },
  {
    "s": "LQDT",
    "n": "Liquidity Services, Inc. - Common Stock"
  },
  {
    "s": "LRCX",
    "n": "Lam Research Corporation - Common Stock"
  },
  {
    "s": "LRE",
    "n": "Lead Real Estate Co., Ltd - American Depositary Shares"
  },
  {
    "s": "LRHC",
    "n": "La Rosa Holdings Corp. - Common Stock"
  },
  {
    "s": "LRMR",
    "n": "Larimar Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "LRN",
    "n": "Stride, Inc. Common Stock"
  },
  {
    "s": "LSAK",
    "n": "Lesaka Technologies, Inc. - Common Stock"
  },
  {
    "s": "LSBK",
    "n": "Lake Shore Bancorp, Inc. - Common Stock"
  },
  {
    "s": "LSCC",
    "n": "Lattice Semiconductor Corporation - Common Stock"
  },
  {
    "s": "LSE",
    "n": "Leishen Energy Holding Co., Ltd. - Class A Ordinary Shares"
  },
  {
    "s": "LSF",
    "n": "Laird Superfood, Inc. Common Stock"
  },
  {
    "s": "LSPD",
    "n": "Lightspeed Commerce Inc. Subordinate Voting Shares"
  },
  {
    "s": "LSTA",
    "n": "Lisata Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "LSTR",
    "n": "Landstar System, Inc. - Common Stock"
  },
  {
    "s": "LTBR",
    "n": "Lightbridge Corporation - Common Stock"
  },
  {
    "s": "LTC",
    "n": "LTC Properties, Inc. Common Stock"
  },
  {
    "s": "LTGO",
    "n": "Latigo Biotherapeutics, Inc. - Common Stock"
  },
  {
    "s": "LTGR",
    "n": "Long Table Growth Corp. - Class A Ordinary Shares"
  },
  {
    "s": "LTGRU",
    "n": "Long Table Growth Corp. - Units"
  },
  {
    "s": "LTGRW",
    "n": "Long Table Growth Corp. - Warrants"
  },
  {
    "s": "LTH",
    "n": "Life Time Group Holdings, Inc. Common Stock"
  },
  {
    "s": "LTM",
    "n": "LATAM Airlines Group S.A. American Depositary Shares (each representing two thousand (2,000) shares of Common Stock)"
  },
  {
    "s": "LTRN",
    "n": "Lantern Pharma Inc. - Common Stock"
  },
  {
    "s": "LTRX",
    "n": "Lantronix, Inc. - Common Stock"
  },
  {
    "s": "LU",
    "n": "Lufax Holding Ltd American Depositary Shares, each representing two (2) Ordinary Shares"
  },
  {
    "s": "LUCD",
    "n": "Lucid Diagnostics Inc. - Common Stock"
  },
  {
    "s": "LUCK",
    "n": "Lucky Strike Entertainment Corporation Class A Common Stock"
  },
  {
    "s": "LUCY",
    "n": "Innovative Eyewear, Inc. - Common Stock"
  },
  {
    "s": "LUCYW",
    "n": "Innovative Eyewear, Inc. - Warrants"
  },
  {
    "s": "LUD",
    "n": "Luda Technology Group Limited Ordinary Shares"
  },
  {
    "s": "LULU",
    "n": "lululemon athletica inc. - Common Stock"
  },
  {
    "s": "LUMN",
    "n": "Lumen Technologies, Inc.  - Common Stock"
  },
  {
    "s": "LUNG",
    "n": "Pulmonx Corporation - Common Stock"
  },
  {
    "s": "LUNR",
    "n": "Intuitive Machines, Inc. - Class A Common Stock"
  },
  {
    "s": "LUV",
    "n": "Southwest Airlines Company Common Stock"
  },
  {
    "s": "LUXE",
    "n": "LuxExperience B.V. American Depositary Shares, each representing one Ordinary Share"
  },
  {
    "s": "LVLU",
    "n": "Lulu's Fashion Lounge Holdings, Inc. - Common Stock"
  },
  {
    "s": "LVO",
    "n": "LiveOne, Inc. - Common Stock"
  },
  {
    "s": "LVS",
    "n": "Las Vegas Sands Corp. Common Stock"
  },
  {
    "s": "LVWR",
    "n": "LiveWire Group, Inc. Common Stock"
  },
  {
    "s": "LVWR-W",
    "n": "LiveWire Group, Inc. Warrants, each exercisable for one share of Common Stock at an exercise price of $11.50 per share"
  },
  {
    "s": "LW",
    "n": "Lamb Weston Holdings, Inc. Common Stock "
  },
  {
    "s": "LWAC",
    "n": "LightWave Acquisition Corp. - Class A Ordinary Shares"
  },
  {
    "s": "LWACU",
    "n": "LightWave Acquisition Corp. - Units"
  },
  {
    "s": "LWACW",
    "n": "LightWave Acquisition Corp. - Warrants"
  },
  {
    "s": "LWAY",
    "n": "Lifeway Foods, Inc. - Common Stock"
  },
  {
    "s": "LWLG",
    "n": "Lightwave Logic, Inc. - Common Stock"
  },
  {
    "s": "LX",
    "n": "LexinFintech Holdings Ltd. - American Depositary Shares"
  },
  {
    "s": "LXEH",
    "n": "Lixiang Education Holding Co., Ltd. - American Depositary Shares"
  },
  {
    "s": "LXEO",
    "n": "Lexeo Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "LXFR",
    "n": "Luxfer Holdings PLC Ordinary Shares"
  },
  {
    "s": "LXRX",
    "n": "Lexicon Pharmaceuticals, Inc. - Common Stock"
  },
  {
    "s": "LXU",
    "n": "LSB Industries, Inc. Common Stock"
  },
  {
    "s": "LYB",
    "n": "LyondellBasell Industries NV Ordinary Shares Class A (Netherlands)"
  },
  {
    "s": "LYEL",
    "n": "Lyell Immunopharma, Inc. - Common Stock"
  },
  {
    "s": "LYFT",
    "n": "Lyft, Inc. - Class A Common Stock"
  },
  {
    "s": "LYG",
    "n": "Lloyds Banking Group Plc American Depositary Shares"
  },
  {
    "s": "LYNX",
    "n": "Lyntris Inc. Common Stock"
  },
  {
    "s": "LYTS",
    "n": "LSI Industries Inc. - Common Stock"
  },
  {
    "s": "LYV",
    "n": "Live Nation Entertainment, Inc. Common Stock"
  },
  {
    "s": "LZ",
    "n": "LegalZoom.com, Inc. - Common Stock"
  },
  {
    "s": "LZB",
    "n": "La-Z-Boy Incorporated Common Stock"
  },
  {
    "s": "LZM",
    "n": "Lifezone Metals Limited Ordinary Shares"
  },
  {
    "s": "LZM-W",
    "n": "Lifezone Metals Limited Warrants"
  },
  {
    "s": "LZMH",
    "n": "LZ Technology Holdings Limited - Class B Ordinary Shares"
  },
  {
    "s": "M",
    "n": "Macy's Inc Common Stock"
  },
  {
    "s": "MA",
    "n": "Mastercard Incorporated Common Stock"
  },
  {
    "s": "MAA",
    "n": "Mid-America Apartment Communities, Inc. Common Stock"
  },
  {
    "s": "MAAS",
    "n": "Maase Inc. - Class A Ordinary Shares"
  },
  {
    "s": "MAC",
    "n": "Macerich Company (The) Common Stock"
  },
  {
    "s": "MACI",
    "n": "Melar Acquisition Corp. I - Class A Ordinary Shares"
  },
  {
    "s": "MACIU",
    "n": "Melar Acquisition Corp. I - Unit"
  },
  {
    "s": "MAGH",
    "n": "Magnitude International Ltd - Ordinary Shares"
  },
  {
    "s": "MAGN",
    "n": "Magnera Corporation Common Stock"
  },
  {
    "s": "MAIA",
    "n": "MAIA Biotechnology, Inc. Common Stock"
  },
  {
    "s": "MAIN",
    "n": "Main Street Capital Corporation Common Stock"
  },
  {
    "s": "MAIR",
    "n": "Madison Air Solutions Corporation Class A Common Stock"
  },
  {
    "s": "MAKO",
    "n": "Mako Mining Corp - Common Stock"
  },
  {
    "s": "MAMA",
    "n": "Mama's Creations, Inc. - Common Stock"
  },
  {
    "s": "MAMO",
    "n": "Massimo Group - Common Stock"
  },
  {
    "s": "MAN",
    "n": "ManpowerGroup Common Stock"
  },
  {
    "s": "MANE",
    "n": "Veradermics, Incorporated Common Stock"
  },
  {
    "s": "MANH",
    "n": "Manhattan Associates, Inc. - Common Stock"
  },
  {
    "s": "MANU",
    "n": "Manchester United Ltd. Class A Ordinary Shares"
  },
  {
    "s": "MAR",
    "n": "Marriott International - Class A Common Stock"
  },
  {
    "s": "MARA",
    "n": "MARA Holdings, Inc. - Common Stock"
  },
  {
    "s": "MARPS",
    "n": "Marine Petroleum Trust - Units of Beneficial Interest"
  },
  {
    "s": "MAS",
    "n": "Masco Corporation Common Stock"
  },
  {
    "s": "MASK",
    "n": "3 E Network Technology Group Ltd - Class A Ordinary Shares"
  },
  {
    "s": "MASS",
    "n": "908 Devices Inc. - Common Stock"
  },
  {
    "s": "MAT",
    "n": "Mattel, Inc. - Common Stock"
  },
  {
    "s": "MATH",
    "n": "Metalpha Technology Holding Limited - Ordinary Shares"
  },
  {
    "s": "MATV",
    "n": "Mativ Holdings, Inc. Common Stock"
  },
  {
    "s": "MATW",
    "n": "Matthews International Corporation - Class A Common Stock"
  },
  {
    "s": "MATX",
    "n": "Matson, Inc. Common Stock"
  },
  {
    "s": "MAX",
    "n": "MediaAlpha, Inc. Class A Common Stock"
  },
  {
    "s": "MAYS",
    "n": "J. W. Mays, Inc. - Common Stock"
  },
  {
    "s": "MAZE",
    "n": "Maze Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "MB",
    "n": "MasterBeef Group - Ordinary Shares"
  },
  {
    "s": "MBAI",
    "n": "MBody AI Ltd. - Ordinary Share"
  },
  {
    "s": "MBBC",
    "n": "Marathon Bancorp, Inc. - Common Stock"
  },
  {
    "s": "MBC",
    "n": "MasterBrand, Inc. Common Stock"
  },
  {
    "s": "MBGL",
    "n": "Mobility Global Inc. Common Stock"
  },
  {
    "s": "MBI",
    "n": "MBIA Inc. Common Stock"
  },
  {
    "s": "MBIN",
    "n": "Merchants Bancorp - Common Stock"
  },
  {
    "s": "MBIO",
    "n": "Mustang Bio, Inc. - Common Stock"
  },
  {
    "s": "MBLY",
    "n": "Mobileye Global Inc. - Class A Common Stock"
  },
  {
    "s": "MBOT",
    "n": "Microbot Medical Inc.  - Common Stock"
  },
  {
    "s": "MBRX",
    "n": "Moleculin Biotech, Inc. - Common Stock"
  },
  {
    "s": "MBUU",
    "n": "Malibu Boats, Inc. - Common Stock"
  },
  {
    "s": "MBVI",
    "n": "M3-Brigade Acquisition VI Corp. - Class A Ordinary Shares"
  },
  {
    "s": "MBVIU",
    "n": "M3-Brigade Acquisition VI Corp. - Units"
  },
  {
    "s": "MBWM",
    "n": "Mercantile Bank Corporation - Common Stock"
  },
  {
    "s": "MBX",
    "n": "MBX Biosciences, Inc. - Common Stock"
  },
  {
    "s": "MC",
    "n": "Moelis & Company Class A Common Stock"
  },
  {
    "s": "MCAH",
    "n": "Mountain Crest Acquisition 6 Corp. - Ordinary Shares"
  },
  {
    "s": "MCAHU",
    "n": "Mountain Crest Acquisition 6 Corp. - Units"
  },
  {
    "s": "MCB",
    "n": "Metropolitan Bank Holding Corp. Common Stock"
  },
  {
    "s": "MCBS",
    "n": "MetroCity Bankshares, Inc. - Common Stock"
  },
  {
    "s": "MCD",
    "n": "McDonald's Corporation Common Stock"
  },
  {
    "s": "MCFT",
    "n": "MasterCraft Boat Holdings, Inc. - Common Stock"
  },
  {
    "s": "MCGA",
    "n": "Yorkville Acquisition Corp. - Class A Ordinary Share"
  },
  {
    "s": "MCGAU",
    "n": "Yorkville Acquisition Corp. - Unit"
  },
  {
    "s": "MCHB",
    "n": "Mechanics Bancorp - Class A Common Stock"
  },
  {
    "s": "MCHP",
    "n": "Microchip Technology Incorporated - Common Stock"
  },
  {
    "s": "MCHX",
    "n": "Marchex, Inc. - Class B Common Stock"
  },
  {
    "s": "MCI",
    "n": "Barings Corporate Investors Common Stock"
  },
  {
    "s": "MCK",
    "n": "McKesson Corporation Common Stock"
  },
  {
    "s": "MCO",
    "n": "Moody's Corporation Common Stock"
  },
  {
    "s": "MCRB",
    "n": "Seres Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "MCRI",
    "n": "Monarch Casino & Resort, Inc. - Common Stock"
  },
  {
    "s": "MCRP",
    "n": "Micropolis AI Robotics Ordinary Shares"
  },
  {
    "s": "MCS",
    "n": "Marcus Corporation (The) Common Stock"
  },
  {
    "s": "MCTA",
    "n": "Charming Medical Limited - Class A Ordinary Shares"
  },
  {
    "s": "MCY",
    "n": "Mercury General Corporation Common Stock"
  },
  {
    "s": "MD",
    "n": "Pediatrix Medical Group, Inc. Common Stock"
  },
  {
    "s": "MDA",
    "n": "MDA Space Ltd. Common Shares"
  },
  {
    "s": "MDAI",
    "n": "Spectral AI, Inc. - Class A Common Stock"
  },
  {
    "s": "MDAIW",
    "n": "Spectral AI, Inc. - Warrants"
  },
  {
    "s": "MDB",
    "n": "MongoDB, Inc. - Class A Common Stock"
  },
  {
    "s": "MDBH",
    "n": "MDB Capital Holdings, LLC - Class A common "
  },
  {
    "s": "MDCX",
    "n": "Medicus Pharma Ltd. - Common Stock"
  },
  {
    "s": "MDGL",
    "n": "Madrigal Pharmaceuticals, Inc. - Common Stock"
  },
  {
    "s": "MDIA",
    "n": "Mediaco Holding Inc. - Class A Common Stock"
  },
  {
    "s": "MDLN",
    "n": "Medline Inc. - Class A common stock"
  },
  {
    "s": "MDLZ",
    "n": "Mondelez International, Inc. - Class A Common Stock"
  },
  {
    "s": "MDRR",
    "n": "Medalist Diversified, Inc. - Common Stock"
  },
  {
    "s": "MDT",
    "n": "Medtronic plc. Ordinary Shares"
  },
  {
    "s": "MDU",
    "n": "MDU Resources Group, Inc. Common Stock (Holding Company)"
  },
  {
    "s": "MDWD",
    "n": "MediWound Ltd. - Ordinary Shares"
  },
  {
    "s": "MDXG",
    "n": "MiMedx Group, Inc - Common Stock"
  },
  {
    "s": "MDXH",
    "n": "MDxHealth SA - Ordinary Shares"
  },
  {
    "s": "MEC",
    "n": "Mayville Engineering Company, Inc. Common Stock"
  },
  {
    "s": "MED",
    "n": "MEDIFAST INC Common Stock"
  },
  {
    "s": "MEDP",
    "n": "Medpace Holdings, Inc. - Common Stock"
  },
  {
    "s": "MEDS",
    "n": "DataMeds AI, Inc. - Common Stock"
  },
  {
    "s": "MEGL",
    "n": "Magic Empire Global Limited - Class A Ordinary Shares"
  },
  {
    "s": "MEI",
    "n": "Methode Electronics, Inc. Common Stock"
  },
  {
    "s": "MELI",
    "n": "MercadoLibre, Inc. - Common Stock"
  },
  {
    "s": "MENS",
    "n": "Jyong Biotech Ltd. - Ordinary shares"
  },
  {
    "s": "MEOH",
    "n": "Methanex Corporation - Common Stock"
  },
  {
    "s": "MERC",
    "n": "Mercer International Inc. - Common Stock"
  },
  {
    "s": "MESH",
    "n": "Meshflow Acquisition Corp. - Class A Ordinary Shares"
  },
  {
    "s": "MESHU",
    "n": "Meshflow Acquisition Corp. - Units"
  },
  {
    "s": "MESHW",
    "n": "Meshflow Acquisition Corp. - Warrants"
  },
  {
    "s": "MESO",
    "n": "Mesoblast Limited - American Depositary Shares"
  },
  {
    "s": "MET",
    "n": "MetLife, Inc. Common Stock"
  },
  {
    "s": "META",
    "n": "Meta Platforms, Inc. - Class A Common Stock"
  },
  {
    "s": "METC",
    "n": "Ramaco Resources, Inc. - Class A Common Stock"
  },
  {
    "s": "METCB",
    "n": "Ramaco Resources, Inc. - Class B Common Stock"
  },
  {
    "s": "METCI",
    "n": "Ramaco Resources, Inc. - 8.250% Senior Notes due 2030"
  },
  {
    "s": "METCZ",
    "n": "Ramaco Resources, Inc. - 8.375% Senior Notes due 2029"
  },
  {
    "s": "MEVO",
    "n": "M Evo Global Acquisition Corp II - Class A Ordinary Shares"
  },
  {
    "s": "MEVOU",
    "n": "M Evo Global Acquisition Corp II - Units"
  },
  {
    "s": "MEVOW",
    "n": "M Evo Global Acquisition Corp II - Warrants"
  },
  {
    "s": "MF",
    "n": "MindForge Inc. - Class A Ordinary Shares"
  },
  {
    "s": "MFA",
    "n": "MFA Financial, Inc."
  },
  {
    "s": "MFAN",
    "n": "MFA Financial, Inc. 8.875% Senior Notes due 2029"
  },
  {
    "s": "MFAO",
    "n": "MFA Financial, Inc. 9.000% Senior Notes due 2029"
  },
  {
    "s": "MFC",
    "n": "Manulife Financial Corporation Common Stock"
  },
  {
    "s": "MFG",
    "n": "Mizuho Financial Group, Inc. Sponosred ADR (Japan)"
  },
  {
    "s": "MFI",
    "n": "mF International Limited - Class A Ordinary Shares"
  },
  {
    "s": "MFICL",
    "n": "MidCap Financial Investment Corporation - 8.00% Notes due 2028"
  },
  {
    "s": "MFIN",
    "n": "Medallion Financial Corp. - Common Stock"
  },
  {
    "s": "MFP",
    "n": "Midera Food Processing, Inc. - Common Stock"
  },
  {
    "s": "MG",
    "n": "Mistras Group Inc Common Stock"
  },
  {
    "s": "MGA",
    "n": "Magna International, Inc. Common Stock"
  },
  {
    "s": "MGEE",
    "n": "MGE Energy Inc. - Common Stock"
  },
  {
    "s": "MGIH",
    "n": "Millennium Group International Holdings Limited - Ordinary Shares"
  },
  {
    "s": "MGLD",
    "n": "The Marygold Companies, Inc. Common Stock"
  },
  {
    "s": "MGM",
    "n": "MGM Resorts International Common Stock"
  },
  {
    "s": "MGN",
    "n": "Megan Holdings Limited - Class A Ordinary Shares"
  },
  {
    "s": "MGNI",
    "n": "Magnite, Inc. - Common Stock"
  },
  {
    "s": "MGNX",
    "n": "MacroGenics, Inc. - Common Stock"
  },
  {
    "s": "MGPI",
    "n": "MGP Ingredients, Inc. - Common Stock"
  },
  {
    "s": "MGR",
    "n": "Affiliated Managers Group, Inc. 5.875% Junior Subordinated Notes due 2059"
  },
  {
    "s": "MGRB",
    "n": "Affiliated Managers Group, Inc. 4.750% Junior Subordinated Notes due 2060"
  },
  {
    "s": "MGRC",
    "n": "McGrath RentCorp - Common Stock"
  },
  {
    "s": "MGRD",
    "n": "Affiliated Managers Group, Inc. 4.200% Junior Subordinated Notes due 2061"
  },
  {
    "s": "MGRE",
    "n": "Affiliated Managers Group, Inc. 6.750% Junior Subordinated Notes due 2064"
  },
  {
    "s": "MGRT",
    "n": "Mega Fortune Company Limited - Ordinary Shares"
  },
  {
    "s": "MGRX",
    "n": "Mangoceuticals, Inc. - Common Stock"
  },
  {
    "s": "MGTX",
    "n": "MeiraGTx Holdings plc - Ordinary Shares"
  },
  {
    "s": "MGX",
    "n": "Metagenomi Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "MGY",
    "n": "Magnolia Oil & Gas Corporation Class A Common Stock"
  },
  {
    "s": "MGYR",
    "n": "Magyar Bancorp, Inc. - Common Stock"
  },
  {
    "s": "MH",
    "n": "McGraw Hill, Inc. Common Stock"
  },
  {
    "s": "MHH",
    "n": "Mastech Digital, Inc Common Stock"
  },
  {
    "s": "MHK",
    "n": "Mohawk Industries, Inc. Common Stock"
  },
  {
    "s": "MHLA",
    "n": "Maiden Holdings, Ltd. 6.625% Notes due 2046"
  },
  {
    "s": "MHNC",
    "n": "Maiden Holdings North America, Ltd. 7.75% Notes due 2043"
  },
  {
    "s": "MHO",
    "n": "M/I Homes, Inc. Common Stock"
  },
  {
    "s": "MI",
    "n": "NFT Limited Class A Ordinary Share"
  },
  {
    "s": "MIAC",
    "n": "Meridian3 Industrials Acquisition Corp - Class A Ordinary Shares"
  },
  {
    "s": "MIACU",
    "n": "Meridian3 Industrials Acquisition Corp - Units"
  },
  {
    "s": "MIAX",
    "n": "Miami International Holdings, Inc. Common Stock"
  },
  {
    "s": "MICC",
    "n": "The Magnum Ice Cream Company N.V. Ordinary Shares"
  },
  {
    "s": "MIDD",
    "n": "The Middleby Corporation - Common Stock"
  },
  {
    "s": "MIMI",
    "n": "Mint Incorporation Limited - Class A Ordinary Shares"
  },
  {
    "s": "MIND",
    "n": "MIND Technology, Inc. - Common Stock"
  },
  {
    "s": "MINE",
    "n": "Mayfair Gold Corp. Common Shares"
  },
  {
    "s": "MIR",
    "n": "Mirion Technologies, Inc. Class A Common Stock"
  },
  {
    "s": "MIRA",
    "n": "MIRA Pharmaceuticals, Inc. - Common Stock"
  },
  {
    "s": "MIRM",
    "n": "Mirum Pharmaceuticals, Inc. - common stock"
  },
  {
    "s": "MIST",
    "n": "Milestone Pharmaceuticals Inc. - Common Shares"
  },
  {
    "s": "MITK",
    "n": "Mitek Systems, Inc. - Common Stock"
  },
  {
    "s": "MITN",
    "n": "TPG Mortgage Investment Trust, Inc. 9.500% Senior Notes due 2029"
  },
  {
    "s": "MITP",
    "n": "TPG Mortgage Investment Trust, Inc. 9.500% Senior Notes due 2029"
  },
  {
    "s": "MITQ",
    "n": "Moving iMage Technologies, Inc. Common Stock"
  },
  {
    "s": "MITT",
    "n": "TPG Mortgage Investment Trust, Inc. Common Stock"
  },
  {
    "s": "MKC",
    "n": "McCormick & Company, Incorporated Common Stock"
  },
  {
    "s": "MKC-V",
    "n": "McCormick & Company, Incorporated Common Stock"
  },
  {
    "s": "MKDW",
    "n": "MKDWELL Tech Inc. - Ordinary Shares"
  },
  {
    "s": "MKDWW",
    "n": "MKDWELL Tech Inc. - Warrants"
  },
  {
    "s": "MKL",
    "n": "Markel Group Inc. Common Stock"
  },
  {
    "s": "MKLY",
    "n": "McKinley Acquisition Corporation - Class A Ordinary Shares"
  },
  {
    "s": "MKLYU",
    "n": "McKinley Acquisition Corporation - Units"
  },
  {
    "s": "MKSI",
    "n": "MKS Inc. - Common Stock"
  },
  {
    "s": "MKTW",
    "n": "MarketWise, Inc. - Class A Common Stock"
  },
  {
    "s": "MKTX",
    "n": "MarketAxess Holdings, Inc. - Common Stock"
  },
  {
    "s": "MKZR",
    "n": "MacKenzie Realty Capital, Inc. - Common Stock"
  },
  {
    "s": "MLAA",
    "n": "Mountain Lake Acquisition Corp. II - Class A Ordinary Shares"
  },
  {
    "s": "MLAAU",
    "n": "Mountain Lake Acquisition Corp. II - Units"
  },
  {
    "s": "MLAAW",
    "n": "Mountain Lake Acquisition Corp. II - Warrants"
  },
  {
    "s": "MLAB",
    "n": "Mesa Laboratories, Inc. - Common Stock"
  },
  {
    "s": "MLCI",
    "n": "Mount Logan Capital Inc. - Common Stock"
  },
  {
    "s": "MLCIL",
    "n": "Mount Logan Capital Inc. - 8.00% Notes Due 2031"
  },
  {
    "s": "MLCO",
    "n": "Melco Resorts & Entertainment Limited - American Depositary Shares "
  },
  {
    "s": "MLEC",
    "n": "Moolec Science SA - Ordinary Shares"
  },
  {
    "s": "MLGO",
    "n": "MicroAlgo, Inc. - Ordinary Shares"
  },
  {
    "s": "MLI",
    "n": "Mueller Industries, Inc. Common Stock"
  },
  {
    "s": "MLKN",
    "n": "MillerKnoll, Inc. - Common Stock"
  },
  {
    "s": "MLM",
    "n": "Martin Marietta Materials, Inc. Common Stock"
  },
  {
    "s": "MLP",
    "n": "Maui Land & Pineapple Company, Inc. Common Stock"
  },
  {
    "s": "MLR",
    "n": "Miller Industries, Inc. Common Stock"
  },
  {
    "s": "MLSS",
    "n": "Milestone Scientific, Inc. Common Stock"
  },
  {
    "s": "MLTX",
    "n": "MoonLake Immunotherapeutics - Class A Ordinary Shares"
  },
  {
    "s": "MLYS",
    "n": "Mineralys Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "MMA",
    "n": "Mixed Martial Arts Group Limited Ordinary Shares"
  },
  {
    "s": "MMED",
    "n": "MiniMed Group, Inc. - Common Stock"
  },
  {
    "s": "MMEDV",
    "n": "MiniMed Group, Inc. - Common Stock When Issued"
  },
  {
    "s": "MMI",
    "n": "Marcus & Millichap, Inc. Common Stock"
  },
  {
    "s": "MMLP",
    "n": "Martin Midstream Partners L.P. - Common Units Representing Limited Partnership Interests"
  },
  {
    "s": "MMM",
    "n": "3M Company Common Stock"
  },
  {
    "s": "MMS",
    "n": "Maximus, Inc. Common Stock"
  },
  {
    "s": "MMSI",
    "n": "Merit Medical Systems, Inc. - Common Stock"
  },
  {
    "s": "MMTX",
    "n": "Miluna Acquisition Corp - Class A Ordinary Shares"
  },
  {
    "s": "MMTXU",
    "n": "Miluna Acquisition Corp - Units"
  },
  {
    "s": "MMYT",
    "n": "MakeMyTrip Limited - Ordinary Shares"
  },
  {
    "s": "MNDO",
    "n": "MIND C.T.I. Ltd. - Ordinary Shares"
  },
  {
    "s": "MNDR",
    "n": "Mobile-health Network Solutions - Class A Ordinary Shares"
  },
  {
    "s": "MNDY",
    "n": "monday.com Ltd. - Ordinary Shares"
  },
  {
    "s": "MNKD",
    "n": "MannKind Corporation - Common Stock"
  },
  {
    "s": "MNOV",
    "n": "MediciNova, Inc. - Common Stock"
  },
  {
    "s": "MNPR",
    "n": "Monopar Therapeutics Inc. - Common Stock"
  },
  {
    "s": "MNRO",
    "n": "Monro, Inc.  - Common Stock"
  },
  {
    "s": "MNSB",
    "n": "MainStreet Bancshares, Inc. - Common Stock"
  },
  {
    "s": "MNSBP",
    "n": "MainStreet Bancshares, Inc. - Depositary Shares"
  },
  {
    "s": "MNSO",
    "n": "MINISO Group Holding Limited American Depositary Shares, each representing four Ordinary Shares"
  },
  {
    "s": "MNST",
    "n": "Monster Beverage Corporation - Common Stock"
  },
  {
    "s": "MNTK",
    "n": "Montauk Renewables, Inc. - Common Stock"
  },
  {
    "s": "MNTN",
    "n": "MNTN, Inc. Class A Common Stock"
  },
  {
    "s": "MNTS",
    "n": "Momentus Inc. - Class A Common Stock"
  },
  {
    "s": "MNY",
    "n": "MoneyHero Limited - Class A Ordinary Shares"
  },
  {
    "s": "MNYWW",
    "n": "MoneyHero Limited - Warrants"
  },
  {
    "s": "MO",
    "n": "Altria Group, Inc."
  },
  {
    "s": "MOB",
    "n": "Mobilicom Limited - Ordinary Shares"
  },
  {
    "s": "MOBBW",
    "n": "Mobilicom Limited - Warrants"
  },
  {
    "s": "MOBI",
    "n": "Mobia Medical, Inc. - Common Stock"
  },
  {
    "s": "MOBX",
    "n": "Mobix Labs, Inc. - Class A Common Stock"
  },
  {
    "s": "MOBXW",
    "n": "Mobix Labs, Inc. - Warrants"
  },
  {
    "s": "MOD",
    "n": "Modine Manufacturing Company Common Stock"
  },
  {
    "s": "MODD",
    "n": "Modular Medical, Inc. - common stock"
  },
  {
    "s": "MOG-A",
    "n": "Moog Inc. Class A Common Stock"
  },
  {
    "s": "MOG-B",
    "n": "Moog Inc. Class B Common Stock"
  },
  {
    "s": "MOGU",
    "n": "MOGU Inc. American Depositary Shares (each  representing 25 Class A Ordinary Shares)"
  },
  {
    "s": "MOH",
    "n": "Molina Healthcare Inc Common Stock"
  },
  {
    "s": "MOLN",
    "n": "Molecular Partners AG - American Depositary Shares"
  },
  {
    "s": "MOMO",
    "n": "Hello Group Inc.  - American Depositary Shares"
  },
  {
    "s": "MORN",
    "n": "Morningstar, Inc. - Common Stock"
  },
  {
    "s": "MOS",
    "n": "Mosaic Company (The) Common Stock"
  },
  {
    "s": "MOV",
    "n": "Movado Group Inc. Common Stock"
  },
  {
    "s": "MOVE",
    "n": "Corvex, Inc. - Common Stock"
  },
  {
    "s": "MP",
    "n": "MP Materials Corp. Common Stock"
  },
  {
    "s": "MPAA",
    "n": "Motorcar Parts of America, Inc. - Common Stock"
  },
  {
    "s": "MPB",
    "n": "Mid Penn Bancorp - Common Stock"
  },
  {
    "s": "MPC",
    "n": "Marathon Petroleum Corporation Common Stock"
  },
  {
    "s": "MPLT",
    "n": "MapLight Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "MPT",
    "n": "Medical Properties Trust, Inc. common stock"
  },
  {
    "s": "MPTI",
    "n": "M-tron Industries, Inc. Common Stock"
  },
  {
    "s": "MPU",
    "n": "Mega Matrix Inc. Class A Ordinary Shares"
  },
  {
    "s": "MPV",
    "n": "Barings Participation Investors Common Stock"
  },
  {
    "s": "MPWR",
    "n": "Monolithic Power Systems, Inc. - Common Stock"
  },
  {
    "s": "MQ",
    "n": "Marqeta, Inc. - Class A Common Stock"
  },
  {
    "s": "MRAM",
    "n": "Everspin Technologies, Inc. - Common Stock"
  },
  {
    "s": "MRBK",
    "n": "Meridian Corporation - Common Stock"
  },
  {
    "s": "MRCO",
    "n": "Mercator Acquisition Corp. - Class A Ordinary Shares"
  },
  {
    "s": "MRCOU",
    "n": "Mercator Acquisition Corp. - Units"
  },
  {
    "s": "MRCY",
    "n": "Mercury Systems Inc - Common Stock"
  },
  {
    "s": "MRDN",
    "n": "Meridian Holdings Inc. - Common Stock"
  },
  {
    "s": "MREO",
    "n": "Mereo BioPharma Group plc - American Depositary Shares"
  },
  {
    "s": "MRK",
    "n": "Merck & Company, Inc. Common Stock (new)"
  },
  {
    "s": "MRKR",
    "n": "Marker Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "MRLN",
    "n": "Merlin, Inc. - Common Stock"
  },
  {
    "s": "MRM",
    "n": "MEDIROM Healthcare Technologies Inc. - American Depositary Share"
  },
  {
    "s": "MRNA",
    "n": "Moderna, Inc. - Common Stock"
  },
  {
    "s": "MRNO",
    "n": "Murano Global Investments PLC - Ordinary Shares"
  },
  {
    "s": "MRNOW",
    "n": "Murano Global Investments PLC - Warrants"
  },
  {
    "s": "MRP",
    "n": "Millrose Properties, Inc. Class A Common Stock"
  },
  {
    "s": "MRSH",
    "n": "Marsh Common Stock"
  },
  {
    "s": "MRT",
    "n": "Marti Technologies, Inc. Class A Ordinary Shares"
  },
  {
    "s": "MRTN",
    "n": "Marten Transport, Ltd. - Common Stock"
  },
  {
    "s": "MRVI",
    "n": "Maravai LifeSciences Holdings, Inc. - Class A common stock"
  },
  {
    "s": "MRVL",
    "n": "Marvell Technology, Inc. - Common Stock"
  },
  {
    "s": "MRX",
    "n": "Marex Group Limited - Ordinary Shares"
  },
  {
    "s": "MS",
    "n": "Morgan Stanley Common Stock"
  },
  {
    "s": "MSA",
    "n": "MSA Safety Incorporated Common Stock"
  },
  {
    "s": "MSAI",
    "n": "MultiSensor AI Holdings, Inc. - Common Stock"
  },
  {
    "s": "MSAIW",
    "n": "MultiSensor AI Holdings, Inc. - Warrants"
  },
  {
    "s": "MSB",
    "n": "Mesabi Trust Common Stock"
  },
  {
    "s": "MSBI",
    "n": "Midland States Bancorp, Inc. - Common Stock"
  },
  {
    "s": "MSC",
    "n": "Studio City International Holdings Limited American depositary shares, each representing four  Class A ordinary shares"
  },
  {
    "s": "MSCI",
    "n": "MSCI Inc. Common Stock"
  },
  {
    "s": "MSEX",
    "n": "Middlesex Water Company - Common Stock"
  },
  {
    "s": "MSFT",
    "n": "Microsoft Corporation - Common Stock"
  },
  {
    "s": "MSGE",
    "n": "Madison Square Garden Entertainment Corp. Class A Common Stock"
  },
  {
    "s": "MSGM",
    "n": "Motorsport Games Inc. - Class A Common Stock"
  },
  {
    "s": "MSGS",
    "n": "Madison Square Garden Sports Corp. Class A Common Stock (New)"
  },
  {
    "s": "MSGY",
    "n": "Masonglory Limited - Class A Ordinary Shares"
  },
  {
    "s": "MSI",
    "n": "Motorola Solutions, Inc. Common Stock"
  },
  {
    "s": "MSLE",
    "n": "Satellos Bioscience Inc. - Common Stock"
  },
  {
    "s": "MSM",
    "n": "MSC Industrial Direct Company, Inc. Common Stock"
  },
  {
    "s": "MSN",
    "n": "Emerson Radio Corporation Common Stock"
  },
  {
    "s": "MSS",
    "n": "Maison Solutions Inc. - Class A Common Stock"
  },
  {
    "s": "MSTR",
    "n": "Strategy Inc - Class A Common Stock"
  },
  {
    "s": "MT",
    "n": "Arcelor Mittal NY Registry Shares NEW"
  },
  {
    "s": "MTA",
    "n": "Metalla Royalty & Streaming Ltd. Common Shares"
  },
  {
    "s": "MTAK",
    "n": "Market Technology Acquisition Corp - Class A Ordinary Shares"
  },
  {
    "s": "MTAKU",
    "n": "Market Technology Acquisition Corp - Unit"
  },
  {
    "s": "MTAKW",
    "n": "Market Technology Acquisition Corp - Warrants"
  },
  {
    "s": "MTAL",
    "n": "Metals Acquisition Corp. II Class A Ordinary Shares"
  },
  {
    "s": "MTB",
    "n": "M&T Bank Corporation Common Stock"
  },
  {
    "s": "MTC",
    "n": "MMTec, Inc. - Common Shares"
  },
  {
    "s": "MTCH",
    "n": "Match Group, Inc. - Common Stock"
  },
  {
    "s": "MTD",
    "n": "Mettler-Toledo International, Inc. Common Stock"
  },
  {
    "s": "MTDR",
    "n": "Matador Resources Company Common Stock"
  },
  {
    "s": "MTEK",
    "n": "Maris-Tech Ltd. - ordinary shares"
  },
  {
    "s": "MTEKW",
    "n": "Maris-Tech Ltd. - Warrants"
  },
  {
    "s": "MTEN",
    "n": "Mingteng International Corporation Inc. - Class A Ordinary Shares"
  },
  {
    "s": "MTEX",
    "n": "Mannatech, Incorporated - Common Stock"
  },
  {
    "s": "MTG",
    "n": "MGIC Investment Corporation Common Stock"
  },
  {
    "s": "MTH",
    "n": "Meritage Homes Corporation Common Stock"
  },
  {
    "s": "MTLS",
    "n": "Materialise NV - American Depositary Shares"
  },
  {
    "s": "MTN",
    "n": "Vail Resorts, Inc. Common Stock"
  },
  {
    "s": "MTNB",
    "n": "Matinas Biopharma Holdings, Inc. Common Stock"
  },
  {
    "s": "MTNE",
    "n": "CH4 Natural Solutions Corporation Class A Ordinary Shares"
  },
  {
    "s": "MTR",
    "n": "Mesa Royalty Trust Common Stock"
  },
  {
    "s": "MTRN",
    "n": "Materion Corporation"
  },
  {
    "s": "MTRX",
    "n": "Matrix Service Company - Common Stock"
  },
  {
    "s": "MTSI",
    "n": "MACOM Technology Solutions Holdings, Inc. - Common Stock"
  },
  {
    "s": "MTUS",
    "n": "Metallus Inc. Common Shares"
  },
  {
    "s": "MTVA",
    "n": "MetaVia Inc.  - Common Stock"
  },
  {
    "s": "MTW",
    "n": "Manitowoc Company, Inc. (The) Common Stock"
  },
  {
    "s": "MTX",
    "n": "Minerals Technologies Inc. Common Stock"
  },
  {
    "s": "MTZ",
    "n": "MasTec, Inc. Common Stock"
  },
  {
    "s": "MU",
    "n": "Micron Technology, Inc. - Common Stock"
  },
  {
    "s": "MUFG",
    "n": "Mitsubishi UFJ Financial Group, Inc. Common Stock"
  },
  {
    "s": "MUR",
    "n": "Murphy Oil Corporation Common Stock"
  },
  {
    "s": "MUSA",
    "n": "Murphy USA Inc. Common Stock"
  },
  {
    "s": "MUX",
    "n": "McEwen Inc. Common Stock"
  },
  {
    "s": "MUZE",
    "n": "Muzero Acquisition Corp - Class A Ordinary Shares"
  },
  {
    "s": "MUZEU",
    "n": "Muzero Acquisition Corp - Unit"
  },
  {
    "s": "MVBF",
    "n": "MVB Financial Corp. - Common Stock"
  },
  {
    "s": "MVIS",
    "n": "MicroVision, Inc. - Common Stock"
  },
  {
    "s": "MVST",
    "n": "Microvast Holdings, Inc. - Common Stock"
  },
  {
    "s": "MWA",
    "n": "MUELLER WATER PRODUCTS Common Stock"
  },
  {
    "s": "MWC",
    "n": "Micware Co., Ltd. - American Depositary Shares"
  },
  {
    "s": "MWG",
    "n": "Multi Ways Holdings Limited Class A Ordinary Shares"
  },
  {
    "s": "MWH",
    "n": "SOLV Energy, Inc. - Class A common stock"
  },
  {
    "s": "MWYN",
    "n": "Marwynn Holdings, Inc. - Common stock"
  },
  {
    "s": "MX",
    "n": "Magnachip Semiconductor Corporation Common Stock"
  },
  {
    "s": "MXC",
    "n": "Mexco Energy Corporation Common Stock"
  },
  {
    "s": "MXCT",
    "n": "MaxCyte, Inc. - Common Stock"
  },
  {
    "s": "MXL",
    "n": "MaxLinear, Inc - Common Stock"
  },
  {
    "s": "MYE",
    "n": "Myers Industries, Inc. Common Stock"
  },
  {
    "s": "MYFW",
    "n": "First Western Financial, Inc. - Common Stock"
  },
  {
    "s": "MYGN",
    "n": "Myriad Genetics, Inc. - Common Stock"
  },
  {
    "s": "MYND",
    "n": "Mynd.ai, Inc. American Depositary Shares"
  },
  {
    "s": "MYO",
    "n": "Myomo Inc. Common Stock"
  },
  {
    "s": "MYPS",
    "n": "PLAYSTUDIOS, Inc.  - Class A Common Stock"
  },
  {
    "s": "MYRG",
    "n": "MYR Group, Inc. - Common Stock"
  },
  {
    "s": "MYSE",
    "n": "Myseum.AI, Inc. - Common Stock"
  },
  {
    "s": "MYSZ",
    "n": "My Size, Inc. - Common Stock"
  },
  {
    "s": "MYX",
    "n": "Maywood Acquisition Corp. 2 - Class A Ordinary Share"
  },
  {
    "s": "MYXXU",
    "n": "Maywood Acquisition Corp. 2 - Units"
  },
  {
    "s": "MYXXW",
    "n": "Maywood Acquisition Corp. 2 - Warrants"
  },
  {
    "s": "MZTI",
    "n": "The Marzetti Company - Common Stock"
  },
  {
    "s": "MZYX",
    "n": "MOZAYYX Acquisition Corp. Class A Ordinary Shares"
  },
  {
    "s": "NA",
    "n": "Nano Labs Ltd - Class A Ordinary Shares"
  },
  {
    "s": "NAAS",
    "n": "NaaS Technology Inc. - American Depositary Shares"
  },
  {
    "s": "NABL",
    "n": "N-able, Inc. Common Stock"
  },
  {
    "s": "NAGE",
    "n": "Niagen Bioscience, Inc. - Common Stock"
  },
  {
    "s": "NAII",
    "n": "Natural Alternatives International, Inc. - Common Stock"
  },
  {
    "s": "NAK",
    "n": "Northern Dynasty Minerals, Ltd. Common Stock"
  },
  {
    "s": "NAKA",
    "n": "Nakamoto Inc. - Common Stock"
  },
  {
    "s": "NAMI",
    "n": "Jinxin Technology Holding Company - American Depositary Shares"
  },
  {
    "s": "NAMM",
    "n": "Namib Minerals - Ordinary Shares"
  },
  {
    "s": "NAMMW",
    "n": "Namib Minerals - Warrants"
  },
  {
    "s": "NAMS",
    "n": "NewAmsterdam Pharma Company N.V. - Ordinary Shares"
  },
  {
    "s": "NAT",
    "n": "Nordic American Tankers Limited Common Stock"
  },
  {
    "s": "NATH",
    "n": "Nathan's Famous, Inc. - Common Stock"
  },
  {
    "s": "NATL",
    "n": "NCR Atleos Corporation Common Stock"
  },
  {
    "s": "NATR",
    "n": "Nature's Sunshine Products, Inc. - Common Stock"
  },
  {
    "s": "NAUT",
    "n": "Nautilus Biotechnology, Inc. - Common Stock"
  },
  {
    "s": "NAVI",
    "n": "Navient Corporation - Common Stock"
  },
  {
    "s": "NAVN",
    "n": "Navan, Inc. - Class A Common Stock"
  },
  {
    "s": "NB",
    "n": "NioCorp Developments Ltd. - Common Stock"
  },
  {
    "s": "NBBK",
    "n": "NB Bancorp, Inc. - Common Stock"
  },
  {
    "s": "NBHC",
    "n": "National Bank Holdings Corporation Common Stock"
  },
  {
    "s": "NBIS",
    "n": "Nebius Group N.V. - Class A Ordinary Shares"
  },
  {
    "s": "NBIX",
    "n": "Neurocrine Biosciences, Inc. - Common Stock"
  },
  {
    "s": "NBN",
    "n": "Northeast Bank - Common Stock"
  },
  {
    "s": "NBP",
    "n": "NovaBridge Biosciences - American Depositary Shares"
  },
  {
    "s": "NBR",
    "n": "Nabors Industries Ltd."
  },
  {
    "s": "NBRG",
    "n": "Newbridge Acquisition Limited - Class A Ordinary Share"
  },
  {
    "s": "NBRGU",
    "n": "Newbridge Acquisition Limited - Unit"
  },
  {
    "s": "NBTB",
    "n": "NBT Bancorp Inc. - Common Stock"
  },
  {
    "s": "NBTX",
    "n": "Nanobiotix S.A. - ADSs"
  },
  {
    "s": "NC",
    "n": "NACCO Industries, Inc. Common Stock"
  },
  {
    "s": "NCDL",
    "n": "Nuveen Churchill Direct Lending Corp. Common Stock"
  },
  {
    "s": "NCEL",
    "n": "NewcelX Ltd. - Ordinary Shares"
  },
  {
    "s": "NCEW",
    "n": "New Century Logistics (BVI) Limited - Ordinary Shares"
  },
  {
    "s": "NCI",
    "n": "Neo-Concept International Group Holdings Limited - Class A Ordinary Shares"
  },
  {
    "s": "NCLH",
    "n": "Norwegian Cruise Line Holdings Ltd. Ordinary Shares"
  },
  {
    "s": "NCMI",
    "n": "National CineMedia, Inc. - Common Stock"
  },
  {
    "s": "NCNA",
    "n": "NuCana plc - American Depositary Shares"
  },
  {
    "s": "NCNO",
    "n": "nCino, Inc. - Common Stock"
  },
  {
    "s": "NCO",
    "n": "Southern Cross Acquisition I Corp. - Ordinary Shares"
  },
  {
    "s": "NCOOU",
    "n": "Southern Cross Acquisition I Corp. - Units"
  },
  {
    "s": "NCOOW",
    "n": "Southern Cross Acquisition I Corp. - Warrants"
  },
  {
    "s": "NCPL",
    "n": "Netcapital Inc. - Common Stock"
  },
  {
    "s": "NCPLW",
    "n": "Netcapital Inc. - warrants"
  },
  {
    "s": "NCRA",
    "n": "Nocera, Inc. - common stock"
  },
  {
    "s": "NCT",
    "n": "Intercont (Cayman) Limited - Class A Ordinary shares"
  },
  {
    "s": "NCTY",
    "n": "The9 Limited - American Depository Shares"
  },
  {
    "s": "NDAQ",
    "n": "Nasdaq, Inc. - Common Stock"
  },
  {
    "s": "NDLS",
    "n": "Noodles & Company - Class A Common Stock"
  },
  {
    "s": "NDRA",
    "n": "ENDRA Life Sciences Inc. - Common Stock"
  },
  {
    "s": "NDSN",
    "n": "Nordson Corporation - Common Stock"
  },
  {
    "s": "NE",
    "n": "Noble Corporation plc A Ordinary Shares"
  },
  {
    "s": "NE-A",
    "n": "Noble Corporation plc Tranche 2 Warrants"
  },
  {
    "s": "NE-W",
    "n": "Noble Corporation plc Tranche 1 Warrants"
  },
  {
    "s": "NECB",
    "n": "NorthEast Community Bancorp, Inc. - Common Stock"
  },
  {
    "s": "NEE",
    "n": "NextEra Energy, Inc. Common Stock"
  },
  {
    "s": "NEGG",
    "n": "Newegg Commerce, Inc. - Common Shares"
  },
  {
    "s": "NEM",
    "n": "Newmont Corporation"
  },
  {
    "s": "NEN",
    "n": "New England Realty Associates Limited Partnership Class A Depositary Receipts Evidencing Units of Limited Partnership"
  },
  {
    "s": "NEO",
    "n": "NeoGenomics, Inc. - Common Stock"
  },
  {
    "s": "NEOG",
    "n": "Neogen Corporation - Common Stock"
  },
  {
    "s": "NEON",
    "n": "Neonode Inc. - Common Stock"
  },
  {
    "s": "NEOV",
    "n": "NeoVolta Inc. - Common Stock"
  },
  {
    "s": "NEPH",
    "n": "Nephros, Inc. - Common Stock"
  },
  {
    "s": "NERV",
    "n": "Minerva Neurosciences, Inc - Common Stock"
  },
  {
    "s": "NESR",
    "n": "National Energy Services Reunited Corp - Ordinary Shares"
  },
  {
    "s": "NET",
    "n": "Cloudflare, Inc. Class A Common Stock"
  },
  {
    "s": "NEU",
    "n": "NewMarket Corp Common Stock"
  },
  {
    "s": "NEUP",
    "n": "Neuphoria Therapeutics Inc. - Common Stock"
  },
  {
    "s": "NEWP",
    "n": "New Pacific Metals Corp. Common Shares"
  },
  {
    "s": "NEWT",
    "n": "NewtekOne, Inc. - Common Stock"
  },
  {
    "s": "NEWTG",
    "n": "NewtekOne, Inc. - 8.50% Fixed Rate Senior Notes due 2029"
  },
  {
    "s": "NEWTH",
    "n": "NewtekOne, Inc. - 8.625% Fixed Rate Senior Notes due 2029"
  },
  {
    "s": "NEWTI",
    "n": "NewtekOne, Inc. - 8.00% Fixed Rate Senior Notes due 2028"
  },
  {
    "s": "NEWTO",
    "n": "NewtekOne, Inc. - 8.50% Fixed Rate Senior Notes due 2031"
  },
  {
    "s": "NEXA",
    "n": "Nexa Resources S.A. Common Shares"
  },
  {
    "s": "NEXM",
    "n": "NexMetals Mining Corp. - Common Stock"
  },
  {
    "s": "NEXN",
    "n": "Nexxen International Ltd. - Ordinary Shares"
  },
  {
    "s": "NEXR",
    "n": "Nexera Technologies Ltd - Ordinary Shares"
  },
  {
    "s": "NEXT",
    "n": "NextDecade Corporation - Common Stock"
  },
  {
    "s": "NFE",
    "n": "New Fortress Energy Inc. - Class A Common Stock"
  },
  {
    "s": "NFG",
    "n": "National Fuel Gas Company Common Stock"
  },
  {
    "s": "NFGC",
    "n": "New Found Gold Corp Common Shares"
  },
  {
    "s": "NFLX",
    "n": "Netflix, Inc. - Common Stock"
  },
  {
    "s": "NG",
    "n": "Novagold Resources Inc."
  },
  {
    "s": "NGEN",
    "n": "NervGen Pharma Corp. - Common stock"
  },
  {
    "s": "NGG",
    "n": "National Grid Transco, PLC National Grid PLC (NEW) American Depositary Shares"
  },
  {
    "s": "NGNE",
    "n": "Neurogene Inc. - Common Stock"
  },
  {
    "s": "NGS",
    "n": "Natural Gas Services Group, Inc. Common Stock"
  },
  {
    "s": "NGVC",
    "n": "Natural Grocers by Vitamin Cottage, Inc. Common Stock"
  },
  {
    "s": "NGVT",
    "n": "Ingevity Corporation Common Stock "
  },
  {
    "s": "NHC",
    "n": "National HealthCare Corporation Common Stock"
  },
  {
    "s": "NHI",
    "n": "National Health Investors, Inc. Common Stock"
  },
  {
    "s": "NHIV",
    "n": "NewHold Investment Corp IV - Class A Ordinary Shares"
  },
  {
    "s": "NHIVU",
    "n": "NewHold Investment Corp IV - Units"
  },
  {
    "s": "NHIVW",
    "n": "NewHold Investment Corp IV - Warrants"
  },
  {
    "s": "NHP",
    "n": "National Healthcare Properties, Inc. - Class A Common Stock"
  },
  {
    "s": "NHTC",
    "n": "Natural Health Trends Corp. - Common Stock"
  },
  {
    "s": "NI",
    "n": "NiSource Inc Common Stock"
  },
  {
    "s": "NIC",
    "n": "Nicolet Bankshares Inc. Common Stock"
  },
  {
    "s": "NICE",
    "n": "NICE Ltd - American Depositary Shares each representing one Ordinary Share"
  },
  {
    "s": "NICM",
    "n": "Nicola Mining Inc. - American Depositary Shares"
  },
  {
    "s": "NIKI",
    "n": "Niki BioSolutions, Inc. - Common Stock"
  },
  {
    "s": "NINE",
    "n": "Nine Energy Service, Inc. Common Stock"
  },
  {
    "s": "NIO",
    "n": "NIO Inc. American depositary shares, each  representing one Class A ordinary share"
  },
  {
    "s": "NIPG",
    "n": "NIP Group Inc. - American Depositary Shares"
  },
  {
    "s": "NIQ",
    "n": "NIQ Global Intelligence plc Ordinary Shares"
  },
  {
    "s": "NIU",
    "n": "Niu Technologies - American Depositary Shares"
  },
  {
    "s": "NIVF",
    "n": "NewGenIvf Group Limited - Class A Ordinary Shares"
  },
  {
    "s": "NIVFW",
    "n": "NewGenIvf Group Limited - Warrants"
  },
  {
    "s": "NIXX",
    "n": "Nixxy, Inc. - Common Stock"
  },
  {
    "s": "NJR",
    "n": "NewJersey Resources Corporation Common Stock"
  },
  {
    "s": "NKE",
    "n": "Nike, Inc. Common Stock"
  },
  {
    "s": "NKLR",
    "n": "Terra Innovatum Global N.V. - Ordinary shares"
  },
  {
    "s": "NKSH",
    "n": "National Bankshares, Inc. - Common Stock"
  },
  {
    "s": "NKTR",
    "n": "Nektar Therapeutics - Common Stock"
  },
  {
    "s": "NKTX",
    "n": "Nkarta, Inc. - Common Stock"
  },
  {
    "s": "NL",
    "n": "NLI Holdings, Inc. Common Stock"
  },
  {
    "s": "NLOP",
    "n": "Net Lease Office Properties Common Shares of Beneficial Interest"
  },
  {
    "s": "NLY",
    "n": "Annaly Capital Management Inc. Common Stock"
  },
  {
    "s": "NMAD",
    "n": "Nomad Power Solutions, Inc. - Common Stock"
  },
  {
    "s": "NMAX",
    "n": "Newsmax, Inc. Class B Common Stock"
  },
  {
    "s": "NMFC",
    "n": "New Mountain Finance Corporation - Common Stock"
  },
  {
    "s": "NMFCZ",
    "n": "New Mountain Finance Corporation - 8.250% Notes due 2028"
  },
  {
    "s": "NMG",
    "n": "Nouveau Monde Graphite Inc. Common Shares"
  },
  {
    "s": "NMIH",
    "n": "NMI Holdings Inc - Common Stock"
  },
  {
    "s": "NMP",
    "n": "NMP Acquisition Corp. - Class A Ordinary Shares"
  },
  {
    "s": "NMPAR",
    "n": "NMP Acquisition Corp. - Right"
  },
  {
    "s": "NMPAU",
    "n": "NMP Acquisition Corp. - Units"
  },
  {
    "s": "NMR",
    "n": "Nomura Holdings Inc ADR American Depositary Shares"
  },
  {
    "s": "NMRA",
    "n": "Neumora Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "NMRK",
    "n": "Newmark Group, Inc. - Class A Common Stock"
  },
  {
    "s": "NMTC",
    "n": "NeuroOne Medical Technologies Corporation - Common Stock"
  },
  {
    "s": "NN",
    "n": "NextNav Inc. - Common stock"
  },
  {
    "s": "NNBR",
    "n": "NN, Inc. - Common Stock"
  },
  {
    "s": "NNDM",
    "n": "Nano Dimension Ltd. - American Depositary Shares"
  },
  {
    "s": "NNE",
    "n": "Nano Nuclear Energy Inc. - common stock"
  },
  {
    "s": "NNI",
    "n": "Nelnet, Inc. Common Stock"
  },
  {
    "s": "NNNN",
    "n": "Anbio Biotechnology - Class A Ordinary Shares"
  },
  {
    "s": "NNOX",
    "n": "NANO-X IMAGING LTD - Ordinary Shares"
  },
  {
    "s": "NNVC",
    "n": "NanoViricides, Inc. Common Stock"
  },
  {
    "s": "NOA",
    "n": "North American Construction Group Ltd. Common Shares (no par)"
  },
  {
    "s": "NOAH",
    "n": "Noah Holdings Limited American Depositary Shares"
  },
  {
    "s": "NOC",
    "n": "Northrop Grumman Corporation Common Stock"
  },
  {
    "s": "NODK",
    "n": "NI Holdings, Inc. - Common Stock"
  },
  {
    "s": "NOEM",
    "n": "CO2 Energy Transition Corp. - Common Stock"
  },
  {
    "s": "NOEMR",
    "n": "CO2 Energy Transition Corp. - Right"
  },
  {
    "s": "NOEMU",
    "n": "CO2 Energy Transition Corp. - Unit"
  },
  {
    "s": "NOG",
    "n": "Northern Oil and Gas, Inc. Common Stock"
  },
  {
    "s": "NOK",
    "n": "Nokia Corporation Sponsored American Depositary Shares"
  },
  {
    "s": "NOMA",
    "n": "NOMADAR Corp. - Class A Common Stock"
  },
  {
    "s": "NOMD",
    "n": "Nomad Foods Limited Ordinary Shares"
  },
  {
    "s": "NOV",
    "n": "NOV Inc. Common Stock"
  },
  {
    "s": "NOVT",
    "n": "Novanta Inc. - Common Shares"
  },
  {
    "s": "NOVTU",
    "n": "Novanta Inc. - Tangible Equity Units"
  },
  {
    "s": "NOW",
    "n": "ServiceNow, Inc. Common Stock"
  },
  {
    "s": "NP",
    "n": "Neptune Insurance Holdings Inc. Class A Common Stock"
  },
  {
    "s": "NPAC",
    "n": "New Providence Acquisition Corp. III - Ordinary Shares"
  },
  {
    "s": "NPACU",
    "n": "New Providence Acquisition Corp. III - Units"
  },
  {
    "s": "NPACW",
    "n": "New Providence Acquisition Corp. III - Warrants"
  },
  {
    "s": "NPB",
    "n": "Northpointe Bancshares, Inc. Common Stock"
  },
  {
    "s": "NPCE",
    "n": "Neuropace, Inc. - Common Stock"
  },
  {
    "s": "NPK",
    "n": "National Presto Industries, Inc. Common Stock"
  },
  {
    "s": "NPKI",
    "n": "NPK International Inc. Common Stock"
  },
  {
    "s": "NPO",
    "n": "Enpro Inc. Common Stock"
  },
  {
    "s": "NPT",
    "n": "Texxon Holding Limited - Ordinary shares"
  },
  {
    "s": "NPWR",
    "n": "NET Power Inc. Class A Common Stock"
  },
  {
    "s": "NRC",
    "n": "NRC Health - Common Stock"
  },
  {
    "s": "NRDS",
    "n": "NerdWallet, Inc. - Class A Common Stock"
  },
  {
    "s": "NRDY",
    "n": "Nerdy Inc. Class A Common Stock"
  },
  {
    "s": "NREF",
    "n": "NexPoint Real Estate Finance, Inc. Common Stock"
  },
  {
    "s": "NRG",
    "n": "NRG Energy, Inc. Common Stock"
  },
  {
    "s": "NRGV",
    "n": "Energy Vault Holdings, Inc. Common Stock"
  },
  {
    "s": "NRIM",
    "n": "Northrim BanCorp Inc - Common Stock"
  },
  {
    "s": "NRIX",
    "n": "Nurix Therapeutics, Inc. - Common stock"
  },
  {
    "s": "NRSN",
    "n": "NeuroSense Therapeutics Ltd. - Ordinary Shares"
  },
  {
    "s": "NRT",
    "n": "North European Oil Royality Trust Common Stock"
  },
  {
    "s": "NRUC",
    "n": "National Rural Utilities Cooperative Finance Corporation 5.500% Subordinated Notes due 2064 (Subordinated Deferrable Interest Notes)"
  },
  {
    "s": "NRXP",
    "n": "NRX Pharmaceuticals, Inc. - Common Stock"
  },
  {
    "s": "NRXS",
    "n": "Neuraxis, Inc. Common Stock"
  },
  {
    "s": "NSAI",
    "n": "NorthStrive Acquisition Corp I. - Class A Ordinary Shares"
  },
  {
    "s": "NSAIU",
    "n": "NorthStrive Acquisition Corp I. - Units"
  },
  {
    "s": "NSAIW",
    "n": "NorthStrive Acquisition Corp I. - Warrants"
  },
  {
    "s": "NSC",
    "n": "Norfolk Southern Corporation Common Stock"
  },
  {
    "s": "NSIT",
    "n": "Insight Enterprises, Inc. - Common Stock"
  },
  {
    "s": "NSLRL",
    "n": "Neostellar Capital Corp. - 6.00% Notes due 2026"
  },
  {
    "s": "NSP",
    "n": "Insperity, Inc. Common Stock"
  },
  {
    "s": "NSPR",
    "n": "InspireMD Inc. - Common Stock"
  },
  {
    "s": "NSRX",
    "n": "Nasus Pharma Ltd. Ordinary Shares"
  },
  {
    "s": "NSSC",
    "n": "NAPCO Security Technologies, Inc. - Common Stock"
  },
  {
    "s": "NSTR",
    "n": "NorthStar Earth & Space Enterprises, Inc. Common Shares"
  },
  {
    "s": "NSTR-W",
    "n": "NorthStar Earth & Space Enterprises, Inc. Warrants"
  },
  {
    "s": "NSYS",
    "n": "Nortech Systems Incorporated - Common Stock"
  },
  {
    "s": "NTAP",
    "n": "NetApp, Inc. - Common Stock"
  },
  {
    "s": "NTB",
    "n": "Bank of N.T. Butterfield & Son Limited (The) Voting Ordinary Shares"
  },
  {
    "s": "NTCL",
    "n": "NETCLASS TECHNOLOGY INC - Class A Ordinary Shares"
  },
  {
    "s": "NTCT",
    "n": "NetScout Systems, Inc. - Common Stock"
  },
  {
    "s": "NTES",
    "n": "NetEase, Inc. - American Depositary Shares, each representing 5 ordinary shares"
  },
  {
    "s": "NTGR",
    "n": "NETGEAR, Inc. - Common Stock"
  },
  {
    "s": "NTHI",
    "n": "NeOnc Technologies Holdings, Inc. - Common Stock"
  },
  {
    "s": "NTIC",
    "n": "Northern Technologies International Corporation - Common Stock"
  },
  {
    "s": "NTIP",
    "n": "Network-1 Technologies, Inc. Common Stock"
  },
  {
    "s": "NTLA",
    "n": "Intellia Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "NTNX",
    "n": "Nutanix, Inc. - Class A Common Stock"
  },
  {
    "s": "NTR",
    "n": "Nutrien Ltd. Common Shares"
  },
  {
    "s": "NTRA",
    "n": "Natera, Inc. - Common Stock"
  },
  {
    "s": "NTRB",
    "n": "Nutriband Inc. - Common Stock"
  },
  {
    "s": "NTRP",
    "n": "NextTrip, Inc. - Common Stock"
  },
  {
    "s": "NTRS",
    "n": "Northern Trust Corporation - Common Stock"
  },
  {
    "s": "NTSK",
    "n": "Netskope, Inc. - Class A Common Stock"
  },
  {
    "s": "NTST",
    "n": "NetSTREIT Corp. Common Stock"
  },
  {
    "s": "NTWK",
    "n": "NETSOL Technologies Inc. - Common Stock"
  },
  {
    "s": "NTWO",
    "n": "Newbury Street II Acquisition Corp - Class A Ordinary Shares"
  },
  {
    "s": "NTWOU",
    "n": "Newbury Street II Acquisition Corp - Unit"
  },
  {
    "s": "NU",
    "n": "Nu Holdings Ltd. Class A Ordinary Shares"
  },
  {
    "s": "NUAI",
    "n": "New Era Energy & Digital, Inc. - Common Stock"
  },
  {
    "s": "NUAIW",
    "n": "New Era Energy & Digital, Inc. - Warrants"
  },
  {
    "s": "NUCL",
    "n": "Eagle Nuclear Energy Corp. - Common stock"
  },
  {
    "s": "NUCLW",
    "n": "Eagle Nuclear Energy Corp. - Warrants"
  },
  {
    "s": "NUE",
    "n": "Nucor Corporation Common Stock"
  },
  {
    "s": "NUR",
    "n": "Nuran Wireless Inc. - Common Shares"
  },
  {
    "s": "NUS",
    "n": "Nu Skin Enterprises, Inc. Common Stock"
  },
  {
    "s": "NUTX",
    "n": "Nutex Health Inc. - Common Stock"
  },
  {
    "s": "NUVB",
    "n": "Nuvation Bio Inc. Class A Common Stock"
  },
  {
    "s": "NUWE",
    "n": "Nuwellis, Inc. - Common Stock"
  },
  {
    "s": "NVA",
    "n": "Nova Minerals Corp Common Stock"
  },
  {
    "s": "NVA-W",
    "n": "Nova Minerals Corp Warrants to Purchase Common Stock"
  },
  {
    "s": "NVAX",
    "n": "Novavax, Inc. - Common Stock"
  },
  {
    "s": "NVCR",
    "n": "NovoCure Limited - Ordinary Shares"
  },
  {
    "s": "NVCT",
    "n": "Nuvectis Pharma, Inc. - Common Stock"
  },
  {
    "s": "NVDA",
    "n": "NVIDIA Corporation - Common Stock"
  },
  {
    "s": "NVEC",
    "n": "NVE Corporation - Common Stock"
  },
  {
    "s": "NVGS",
    "n": "Navigator Holdings Ltd. Ordinary Shares (Marshall Islands)"
  },
  {
    "s": "NVMI",
    "n": "Nova Ltd. - Ordinary Shares"
  },
  {
    "s": "NVNO",
    "n": "enVVeno Medical Corporation - Common Stock"
  },
  {
    "s": "NVO",
    "n": "Novo Nordisk A/S Common Stock"
  },
  {
    "s": "NVR",
    "n": "NVR, Inc. Common Stock"
  },
  {
    "s": "NVRI",
    "n": "Enviri Corporation Common Stock"
  },
  {
    "s": "NVS",
    "n": "Novartis AG Common Stock"
  },
  {
    "s": "NVST",
    "n": "Envista Holdings Corporation Common Stock"
  },
  {
    "s": "NVT",
    "n": "nVent Electric plc Ordinary Shares "
  },
  {
    "s": "NVTS",
    "n": "Navitas Semiconductor Corporation - Common Stock"
  },
  {
    "s": "NVX",
    "n": "NOVONIX Limited - American Depository Shares"
  },
  {
    "s": "NWAX",
    "n": "New America Acquisition I Corp. Class A Common Stock"
  },
  {
    "s": "NWBI",
    "n": "Northwest Bancshares, Inc. - Common Stock"
  },
  {
    "s": "NWCL",
    "n": "newcleo plc - Ordinary Shares"
  },
  {
    "s": "NWCLW",
    "n": "newcleo plc - Warrants"
  },
  {
    "s": "NWE",
    "n": "NorthWestern Energy Group, Inc.  - Common Stock"
  },
  {
    "s": "NWFL",
    "n": "Norwood Financial Corp. - Common Stock"
  },
  {
    "s": "NWG",
    "n": "NatWest Group plc American Depositary Shares, (each representing two (2) Ordinary Shares)"
  },
  {
    "s": "NWGL",
    "n": "CL Workshop Group Limited - American Depositary Shares"
  },
  {
    "s": "NWL",
    "n": "Newell Brands Inc. - Common Stock"
  },
  {
    "s": "NWN",
    "n": "Northwest Natural Holding Company Common Stock"
  },
  {
    "s": "NWPX",
    "n": "NWPX Infrastructure, Inc. - Common Stock"
  },
  {
    "s": "NWS",
    "n": "News Corporation - Class B Common Stock"
  },
  {
    "s": "NWSA",
    "n": "News Corporation - Class A Common Stock"
  },
  {
    "s": "NWTG",
    "n": "Newton Golf Company, Inc. - Common Stock"
  },
  {
    "s": "NX",
    "n": "Quanex Building Products Corporation Common Stock"
  },
  {
    "s": "NXAT",
    "n": "Nexus Advanced Technologies Inc. - Ordinary Shares"
  },
  {
    "s": "NXB",
    "n": "NextBoat Inc. Common Stcok"
  },
  {
    "s": "NXDR",
    "n": "Nextdoor Holdings, Inc. Class A Common Stock"
  },
  {
    "s": "NXDT",
    "n": "NexPoint Diversified Real Estate Trust Common Stock"
  },
  {
    "s": "NXE",
    "n": "Nexgen Energy Ltd. Common Shares"
  },
  {
    "s": "NXGL",
    "n": "NexGel, Inc - Common Stock"
  },
  {
    "s": "NXH",
    "n": "Neighborhood Intelligence, Inc.  - Common Stock"
  },
  {
    "s": "NXL",
    "n": "Nexalin Technology, Inc. - Common Stock"
  },
  {
    "s": "NXP",
    "n": "Nuveen Select Tax Free Income Portfolio Common Stock"
  },
  {
    "s": "NXPI",
    "n": "NXP Semiconductors N.V. - Common Stock"
  },
  {
    "s": "NXPL",
    "n": "NextPlat Corp - Common Stock"
  },
  {
    "s": "NXRT",
    "n": "NexPoint Residential Trust, Inc. Common Stock"
  },
  {
    "s": "NXST",
    "n": "Nexstar Media Group, Inc. - Common Stock"
  },
  {
    "s": "NXT",
    "n": "Nextpower Inc. - Common Stock"
  },
  {
    "s": "NXTC",
    "n": "NextCure, Inc. - Common Stock"
  },
  {
    "s": "NXTS",
    "n": "Nexentis Technologies Inc. - Common Stock"
  },
  {
    "s": "NXTT",
    "n": "Next Technology Holding Inc. - Ordinary Shares"
  },
  {
    "s": "NXXT",
    "n": "NextNRG, Inc. - Common Stock"
  },
  {
    "s": "NYAX",
    "n": "Nayax Ltd. - Ordinary Shares"
  },
  {
    "s": "NYC",
    "n": "American Strategic Investment Co. Class A Common Stock"
  },
  {
    "s": "NYT",
    "n": "New York Times Company (The) Common Stock"
  },
  {
    "s": "NYXH",
    "n": "Nyxoah SA - Ordinary Shares"
  },
  {
    "s": "O",
    "n": "Realty Income Corporation Common Stock"
  },
  {
    "s": "OABI",
    "n": "OmniAb, Inc. - Common Stock"
  },
  {
    "s": "OACC",
    "n": "Oaktree Acquisition Corp. III Life Sciences - Class A Ordinary Share"
  },
  {
    "s": "OACCU",
    "n": "Oaktree Acquisition Corp. III Life Sciences - Unit"
  },
  {
    "s": "OBA",
    "n": "Oxley Bridge Acquisition Limited - Class A Ordinary Shares"
  },
  {
    "s": "OBAI",
    "n": "Our Bond, Inc. - Common Stock"
  },
  {
    "s": "OBAWU",
    "n": "Oxley Bridge Acquisition Limited - Unit"
  },
  {
    "s": "OBAWW",
    "n": "Oxley Bridge Acquisition Limited - Warrants"
  },
  {
    "s": "OBDC",
    "n": "Blue Owl Capital Corporation Common Stock"
  },
  {
    "s": "OBE",
    "n": "Obsidian Energy Ltd. Common Shares"
  },
  {
    "s": "OBIO",
    "n": "Orchestra BioMed Holdings, Inc. - Ordinary Shares"
  },
  {
    "s": "OBK",
    "n": "Origin Bancorp, Inc. Common Stock"
  },
  {
    "s": "OBT",
    "n": "Orange County Bancorp, Inc. - Common Stock"
  },
  {
    "s": "OBX",
    "n": "Obsidian Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "OC",
    "n": "Owens Corning Inc Common Stock New"
  },
  {
    "s": "OCAC",
    "n": "Ocean Capital Acquisition Corporation Ordinary Shares"
  },
  {
    "s": "OCAC-W",
    "n": "Ocean Capital Acquisition Corporation Warrants, each exercisable for one ordinary share"
  },
  {
    "s": "OCC",
    "n": "Optical Cable Corporation - Common Stock"
  },
  {
    "s": "OCFC",
    "n": "OceanFirst Financial Corp. - Common Stock"
  },
  {
    "s": "OCG",
    "n": "Oriental Culture Holding LTD - Ordinary Shares"
  },
  {
    "s": "OCGN",
    "n": "Ocugen, Inc. - Common Stock"
  },
  {
    "s": "OCLT",
    "n": "OceanLight Acquisition Corporation - Ordinary Shares"
  },
  {
    "s": "OCLTU",
    "n": "OceanLight Acquisition Corporation - Units"
  },
  {
    "s": "OCLTW",
    "n": "OceanLight Acquisition Corporation - Warrants"
  },
  {
    "s": "OCS",
    "n": "Oculis Holding AG - Ordinary shares"
  },
  {
    "s": "OCSAW",
    "n": "Oculis Holding AG - Warrants"
  },
  {
    "s": "OCTV",
    "n": "Octave Intelligence plc - Class B Ordinary Shares"
  },
  {
    "s": "OCUL",
    "n": "Ocular Therapeutix, Inc. - Common Stock"
  },
  {
    "s": "ODC",
    "n": "Oil-Dri Corporation Of America Common Stock"
  },
  {
    "s": "ODD",
    "n": "ODDITY Tech Ltd. - Class A Ordinary Shares"
  },
  {
    "s": "ODFL",
    "n": "Old Dominion Freight Line, Inc. - Common Stock"
  },
  {
    "s": "ODTX",
    "n": "Odyssey Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "ODYS",
    "n": "Odysight.ai Inc. - Common Stock"
  },
  {
    "s": "OEC",
    "n": "Orion S.A. Common Shares"
  },
  {
    "s": "OESX",
    "n": "Orion Energy Systems, Inc. - Common Stock"
  },
  {
    "s": "OFAL",
    "n": "OFA Group - Class A Ordinary Shares"
  },
  {
    "s": "OFG",
    "n": "OFG Bancorp Common Stock"
  },
  {
    "s": "OFIX",
    "n": "Orthofix Medical Inc.  - Common Stock"
  },
  {
    "s": "OFLX",
    "n": "Omega Flex, Inc. - Common Stock"
  },
  {
    "s": "OFRM",
    "n": "Once Upon a Farm, PBC Common Stock"
  },
  {
    "s": "OFSSH",
    "n": "OFS Capital Corporation - 4.95% Notes due 2028"
  },
  {
    "s": "OFSSO",
    "n": "OFS Capital Corporation - 7.50% Notes due 2028"
  },
  {
    "s": "OGC",
    "n": "OceanaGold Corporation Common Shares"
  },
  {
    "s": "OGCP",
    "n": "Empire State Realty OP, L.P. Series 60 Operating Partnership Units Representing Limited Partnership Interests"
  },
  {
    "s": "OGE",
    "n": "OGE Energy Corp Common Stock"
  },
  {
    "s": "OGEN",
    "n": "Oragenics Inc. Common Stock"
  },
  {
    "s": "OGG",
    "n": "Osisko Gold Group Inc. Common Shares"
  },
  {
    "s": "OGI",
    "n": "Organigram Global Inc. - Common Shares"
  },
  {
    "s": "OGN",
    "n": "Organon & Co. Common Stock "
  },
  {
    "s": "OGS",
    "n": "ONE Gas, Inc. Common Stock"
  },
  {
    "s": "OHAC",
    "n": "Oceanhawk Acquisition Corp. - Class A Ordinary Shares"
  },
  {
    "s": "OHACU",
    "n": "Oceanhawk Acquisition Corp. - Units"
  },
  {
    "s": "OHI",
    "n": "Omega Healthcare Investors, Inc. Common Stock"
  },
  {
    "s": "OI",
    "n": "O-I Glass, Inc. Common Stock"
  },
  {
    "s": "OIA",
    "n": "Invesco Municipal Income Opportunities Trust Common Stock"
  },
  {
    "s": "OIG",
    "n": "Orion180 Insurance Group Inc. - Class A Common Stock"
  },
  {
    "s": "OII",
    "n": "Oceaneering International, Inc. Common Stock"
  },
  {
    "s": "OIM",
    "n": "OneIM Acquisition Corp. - Class A Ordinary Shares"
  },
  {
    "s": "OIMAU",
    "n": "OneIM Acquisition Corp. - Units"
  },
  {
    "s": "OIO",
    "n": "OIO Group - Ordinary Shares"
  },
  {
    "s": "OIOWW",
    "n": "OIO Group - Warrants"
  },
  {
    "s": "OIS",
    "n": "Oil States International, Inc. Common Stock"
  },
  {
    "s": "OKE",
    "n": "ONEOK, Inc. Common Stock"
  },
  {
    "s": "OKLO",
    "n": "Oklo Inc. Class A common stock"
  },
  {
    "s": "OKTA",
    "n": "Okta, Inc. - Class A Common Stock"
  },
  {
    "s": "OKUR",
    "n": "OnKure Therapeutics, Inc. - Class A Common Stock"
  },
  {
    "s": "OKYO",
    "n": "OKYO Pharma Limited - Ordinary Shares"
  },
  {
    "s": "OLB",
    "n": "The OLB Group, Inc. - Common Stock"
  },
  {
    "s": "OLED",
    "n": "Universal Display Corporation - Common Stock"
  },
  {
    "s": "OLLI",
    "n": "Ollie's Bargain Outlet Holdings, Inc. - Common Stock"
  },
  {
    "s": "OLMA",
    "n": "Olema Pharmaceuticals, Inc. - Common Stock"
  },
  {
    "s": "OLN",
    "n": "Olin Corporation Common Stock"
  },
  {
    "s": "OLOX",
    "n": "Olenox Industries Inc. - Common Stock"
  },
  {
    "s": "OLP",
    "n": "One Liberty Properties, Inc. Common Stock"
  },
  {
    "s": "OM",
    "n": "Outset Medical, Inc. - Common Stock"
  },
  {
    "s": "OMAB",
    "n": "Grupo Aeroportuario del Centro Norte S.A.B. de C.V. - American Depositary Shares each representing 8 Series B shares"
  },
  {
    "s": "OMC",
    "n": "Omnicom Group Inc. Common Stock"
  },
  {
    "s": "OMCL",
    "n": "Omnicell, Inc. - Common Stock"
  },
  {
    "s": "OMDA",
    "n": "Omada Health, Inc. - Common Stock"
  },
  {
    "s": "OMER",
    "n": "Omeros Corporation - Common Stock"
  },
  {
    "s": "OMEX",
    "n": "Odyssey Marine Exploration, Inc. - Common Stock"
  },
  {
    "s": "OMF",
    "n": "OneMain Holdings, Inc. Common Stock"
  },
  {
    "s": "OMH",
    "n": "Ohmyhome Limited - Class A Ordinary Shares"
  },
  {
    "s": "OMSE",
    "n": "OMS Energy Technologies Inc. - Ordinary Shares"
  },
  {
    "s": "ON",
    "n": "ON Semiconductor Corporation - Common Stock"
  },
  {
    "s": "ONB",
    "n": "Old National Bancorp - Common Stock"
  },
  {
    "s": "ONC",
    "n": "BeOne Medicines Ltd. - American Depositary Shares"
  },
  {
    "s": "ONCH",
    "n": "1RT Acquisition Corp. - Class A Ordinary Share"
  },
  {
    "s": "ONCHU",
    "n": "1RT Acquisition Corp. - Units"
  },
  {
    "s": "ONCO",
    "n": "Onconetix, Inc.  - Common Stock"
  },
  {
    "s": "ONCY",
    "n": "Oncolytics Biotech Inc. - Common Stock"
  },
  {
    "s": "ONDS",
    "n": "Ondas Inc - Common Stock"
  },
  {
    "s": "ONEG",
    "n": "OneConstruction Group Limited - Ordinary Shares"
  },
  {
    "s": "ONEN",
    "n": "ONE Nuclear Energy Inc. - Common Stock"
  },
  {
    "s": "ONEW",
    "n": "OneWater Marine Inc. - Class A Common Stock"
  },
  {
    "s": "ONFO",
    "n": "Onfolio Holdings Inc. - Common Stock"
  },
  {
    "s": "ONIT",
    "n": "Onity Group Inc. Common Stock"
  },
  {
    "s": "ONL",
    "n": "Orion Properties Inc. Common Stock"
  },
  {
    "s": "ONMD",
    "n": "OneMedNet Corp - Class A Common Stock"
  },
  {
    "s": "ONON",
    "n": "On Holding AG Class A Ordinary Shares"
  },
  {
    "s": "ONT",
    "n": "Onterris, Inc. Common Stock"
  },
  {
    "s": "ONTO",
    "n": "Onto Innovation Inc. Common Stock"
  },
  {
    "s": "OOMA",
    "n": "Ooma, Inc. Common Stock"
  },
  {
    "s": "OPAD",
    "n": "Offerpad Solutions Inc.  - Class A Common Stock"
  },
  {
    "s": "OPAL",
    "n": "OPAL Fuels Inc. - Class A Common Stock"
  },
  {
    "s": "OPBK",
    "n": "OP Bancorp - Common Stock"
  },
  {
    "s": "OPCH",
    "n": "Option Care Health, Inc. - Common Stock"
  },
  {
    "s": "OPEN",
    "n": "Opendoor Technologies Inc  - Common Stock"
  },
  {
    "s": "OPFI",
    "n": "OppFi Inc. Class A Common Stock"
  },
  {
    "s": "OPHC",
    "n": "OptimumBank Holdings, Inc. Common Stock"
  },
  {
    "s": "OPI",
    "n": "Office Properties Income Trust - Common shares of beneficial interest"
  },
  {
    "s": "OPK",
    "n": "Opko Health, Inc. - Common Stock"
  },
  {
    "s": "OPLN",
    "n": "OPENLANE, Inc. Common Stock"
  },
  {
    "s": "OPNW",
    "n": "OpenWorld, Inc. - Common Stock"
  },
  {
    "s": "OPRA",
    "n": "Opera Limited - American Depositary Shares"
  },
  {
    "s": "OPRT",
    "n": "Oportun Financial Corporation - common stock"
  },
  {
    "s": "OPRX",
    "n": "OptimizeRx Corporation - Common Stock"
  },
  {
    "s": "OPTH",
    "n": "Optimi Health Corp. - Common Shares"
  },
  {
    "s": "OPTT",
    "n": "Ocean Power Technologies, Inc. Common Stock"
  },
  {
    "s": "OPTU",
    "n": "Optimum Communications, Inc. Class A common stock"
  },
  {
    "s": "OPTX",
    "n": "Syntec Optics Holdings, Inc. - Class A Common Stock"
  },
  {
    "s": "OPXS",
    "n": "Optex Systems Holdings, Inc. - Common Stock"
  },
  {
    "s": "OPY",
    "n": "Oppenheimer Holdings, Inc. Class A Common Stock (DE)"
  },
  {
    "s": "OR",
    "n": "OR Royalties Inc. Common Shares"
  },
  {
    "s": "ORA",
    "n": "Ormat Technologies, Inc. Common Stock"
  },
  {
    "s": "ORBS",
    "n": "Eightco Holdings Inc. - Common Stock"
  },
  {
    "s": "ORC",
    "n": "Orchid Island Capital, Inc. Common Stock"
  },
  {
    "s": "ORCL",
    "n": "Oracle Corporation Common Stock"
  },
  {
    "s": "ORGO",
    "n": "Organogenesis Holdings Inc.  - Class A "
  },
  {
    "s": "ORI",
    "n": "Old Republic International Corporation Common Stock"
  },
  {
    "s": "ORIC",
    "n": "Oric Pharmaceuticals, Inc. - Common Stock"
  },
  {
    "s": "ORIO",
    "n": "Orion Digital Corp. - Common Shares"
  },
  {
    "s": "ORIQ",
    "n": "Origin Investment Corp I - Ordinary Shares"
  },
  {
    "s": "ORIQU",
    "n": "Origin Investment Corp I - Units"
  },
  {
    "s": "ORKA",
    "n": "Oruka Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "ORKT",
    "n": "Orangekloud Technology Inc. - Class A Ordinary Shares"
  },
  {
    "s": "ORLY",
    "n": "O'Reilly Automotive, Inc. - Common Stock"
  },
  {
    "s": "ORMP",
    "n": "Oramed Pharmaceuticals Inc. - Common Stock"
  },
  {
    "s": "ORN",
    "n": "Orion Group Holdings, Inc. Common"
  },
  {
    "s": "ORRF",
    "n": "Orrstown Financial Services, Inc. - Common Stock"
  },
  {
    "s": "OSBC",
    "n": "Old Second Bancorp, Inc. - Common Stock"
  },
  {
    "s": "OSCR",
    "n": "Oscar Health, Inc. Class A Common Stock"
  },
  {
    "s": "OSG",
    "n": "Octave Specialty Group, Inc. Common Stock"
  },
  {
    "s": "OSIS",
    "n": "OSI Systems, Inc. - Common Stock"
  },
  {
    "s": "OSK",
    "n": "Oshkosh Corporation (Holding Company)Common Stock"
  },
  {
    "s": "OSPN",
    "n": "OneSpan Inc. - Common Stock"
  },
  {
    "s": "OSPR",
    "n": "Osprey Acquisition Corp. III - Class A Ordinary Shares"
  },
  {
    "s": "OSPRU",
    "n": "Osprey Acquisition Corp. III - Units"
  },
  {
    "s": "OSPRW",
    "n": "Osprey Acquisition Corp. III - Warrants"
  },
  {
    "s": "OSS",
    "n": "One Stop Systems, Inc. - Common Stock"
  },
  {
    "s": "OST",
    "n": "Ostin Technology Group Co., Ltd. - Class A Ordinary Shares"
  },
  {
    "s": "OSTX",
    "n": "OS Therapies Incorporated Common Stock"
  },
  {
    "s": "OSUR",
    "n": "OraSure Technologies, Inc. - Common Stock"
  },
  {
    "s": "OSW",
    "n": "OneSpaWorld Holdings Limited - Common Shares"
  },
  {
    "s": "OTAI",
    "n": "Starlink AI Acquisition Corporation Ordinary Shares"
  },
  {
    "s": "OTAI-U",
    "n": "Starlink AI Acquisition Corporation Units, each consisting of one Ordinary Share, and one Right to receive one-fourth (1/4) of one ordinary share"
  },
  {
    "s": "OTEX",
    "n": "Open Text Corporation - Common Shares"
  },
  {
    "s": "OTF",
    "n": "Blue Owl Technology Finance Corp. Common Stock"
  },
  {
    "s": "OTGA",
    "n": "OTG Acquisition Corp. I - Class A Ordinary Share"
  },
  {
    "s": "OTGAU",
    "n": "OTG Acquisition Corp. I - Unit"
  },
  {
    "s": "OTGAW",
    "n": "OTG Acquisition Corp. I - Warrants"
  },
  {
    "s": "OTIS",
    "n": "Otis Worldwide Corporation Common Stock "
  },
  {
    "s": "OTLK",
    "n": "Outlook Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "OTLY",
    "n": "Oatly Group AB - American Depositary Shares"
  },
  {
    "s": "OTTR",
    "n": "Otter Tail Corporation - Common Stock"
  },
  {
    "s": "OUST",
    "n": "Ouster, Inc. - Common Stock"
  },
  {
    "s": "OUT",
    "n": "OUTFRONT Media Inc. Common Stock"
  },
  {
    "s": "OVBC",
    "n": "Ohio Valley Banc Corp. - Common Stock"
  },
  {
    "s": "OVID",
    "n": "Ovid Therapeutics Inc. - Common Stock"
  },
  {
    "s": "OVLY",
    "n": "Oak Valley Bancorp (CA) - Common Stock"
  },
  {
    "s": "OVV",
    "n": "Ovintiv Inc. (DE)"
  },
  {
    "s": "OWL",
    "n": "Blue Owl Capital Inc. Class A Common Stock"
  },
  {
    "s": "OWLS",
    "n": "OBOOK Holdings Inc. - Class A Common Shares"
  },
  {
    "s": "OWLT",
    "n": "Owlet, Inc. Class A Common Stock"
  },
  {
    "s": "OXBR",
    "n": "Oxbridge Re Holdings Limited - Ordinary Shares"
  },
  {
    "s": "OXLCG",
    "n": "Oxford Lane Capital Corp. - 7.95% Notes due 2032"
  },
  {
    "s": "OXLCI",
    "n": "Oxford Lane Capital Corp. - 8.75% Notes due 2030"
  },
  {
    "s": "OXLCL",
    "n": "Oxford Lane Capital Corp. - 6.75% Notes due 2031"
  },
  {
    "s": "OXLCZ",
    "n": "Oxford Lane Capital Corp. - 5.00% Notes due 2027"
  },
  {
    "s": "OXM",
    "n": "Oxford Industries, Inc. Common Stock"
  },
  {
    "s": "OXSQG",
    "n": "Oxford Square Capital Corp. - 5.50% Notes due 2028"
  },
  {
    "s": "OXSQH",
    "n": "Oxford Square Capital Corp. - 7.75% Notes due 2030"
  },
  {
    "s": "OXY",
    "n": "Occidental Petroleum Corporation Common Stock"
  },
  {
    "s": "OXY-W",
    "n": "Occidental Petroleum Corporation Warrants "
  },
  {
    "s": "OYSE",
    "n": "Oyster Enterprises II Acquisition Corp - Class A Ordinary Shares"
  },
  {
    "s": "OYSEU",
    "n": "Oyster Enterprises II Acquisition Corp - Units"
  },
  {
    "s": "OZ",
    "n": "Belpointe PREP, LLC Class A Units"
  },
  {
    "s": "OZK",
    "n": "Bank OZK - Common Stock"
  },
  {
    "s": "P",
    "n": "Everpure, Inc. Class A common stock"
  },
  {
    "s": "PAA",
    "n": "Plains All American Pipeline, L.P. - Common Units representing Limited Partner Interests"
  },
  {
    "s": "PAAC",
    "n": "Proem Acquisition Corp I - Ordinary Shares"
  },
  {
    "s": "PAACU",
    "n": "Proem Acquisition Corp I - Units"
  },
  {
    "s": "PAACW",
    "n": "Proem Acquisition Corp I - Warrants"
  },
  {
    "s": "PAAI",
    "n": "Paradium.AI, Inc. Common Stock"
  },
  {
    "s": "PAAS",
    "n": "Pan American Silver Corp. Common Stock"
  },
  {
    "s": "PAC",
    "n": "Grupo Aeroportuario Del Pacifico, S.A. B. de C.V. Grupo Aeroportuario Del Pacifico, S.A. de C.V. (each representing 10 Series B shares)"
  },
  {
    "s": "PACB",
    "n": "Pacific Biosciences of California, Inc. - Common Stock"
  },
  {
    "s": "PACH",
    "n": "Pioneer Acquisition I Corp - Class A Ordinary Shares"
  },
  {
    "s": "PACHU",
    "n": "Pioneer Acquisition I Corp - Units"
  },
  {
    "s": "PACHW",
    "n": "Pioneer Acquisition I Corp - Warrants"
  },
  {
    "s": "PACK",
    "n": "Ranpak Holdings Corp Class A Common Stock"
  },
  {
    "s": "PACS",
    "n": "PACS Group, Inc. Common Stock"
  },
  {
    "s": "PAG",
    "n": "Penske Automotive Group, Inc. Common Stock"
  },
  {
    "s": "PAGP",
    "n": "Plains GP Holdings, L.P. - Class A Shares representing limited partner interests"
  },
  {
    "s": "PAGS",
    "n": "PagSeguro Digital Ltd. Class A Common Shares"
  },
  {
    "s": "PAHC",
    "n": "Phibro Animal Health Corporation - Class A Common Stock"
  },
  {
    "s": "PAII",
    "n": "Pyrophyte Acquisition Corp. II Class A Ordinary Shares"
  },
  {
    "s": "PAL",
    "n": "Proficient Auto Logistics, Inc. - Common Stock"
  },
  {
    "s": "PALI",
    "n": "Palisade Bio, Inc. - Common Stock"
  },
  {
    "s": "PALO",
    "n": "Paloma Acquisition Corp I - Class A Ordinary Shares"
  },
  {
    "s": "PALOU",
    "n": "Paloma Acquisition Corp I - Units"
  },
  {
    "s": "PALOW",
    "n": "Paloma Acquisition Corp I - Warrants"
  },
  {
    "s": "PAM",
    "n": "Pampa Energia S.A."
  },
  {
    "s": "PAMT",
    "n": "PAMT CORP - Common Stock"
  },
  {
    "s": "PANL",
    "n": "Pangaea Logistics Solutions Ltd. - Common Stock"
  },
  {
    "s": "PANW",
    "n": "Palo Alto Networks, Inc. - Common Stock"
  },
  {
    "s": "PAPL",
    "n": "Pineapple Financial Inc. Common Stock"
  },
  {
    "s": "PAR",
    "n": "PAR Technology Corporation Common Stock"
  },
  {
    "s": "PARA",
    "n": "Banzai International, Inc. - Class A Common Stock"
  },
  {
    "s": "PARK",
    "n": "Park Dental Partners, Inc. - Common Stock"
  },
  {
    "s": "PARR",
    "n": "Par Pacific Holdings, Inc.  Common Stock"
  },
  {
    "s": "PASG",
    "n": "Passage Bio, Inc. - Common Stock"
  },
  {
    "s": "PASW",
    "n": "Ping An Biomedical Co., Ltd. - Class A Ordinary Shares"
  },
  {
    "s": "PATH",
    "n": "UiPath, Inc. Class A Common Stock"
  },
  {
    "s": "PATK",
    "n": "Patrick Industries, Inc. - Common Stock"
  },
  {
    "s": "PAVM",
    "n": "PAVmed Inc. - Common Stock"
  },
  {
    "s": "PAVS",
    "n": "Paranovus Entertainment Technology Ltd. - Class A Ordinary Shares"
  },
  {
    "s": "PAX",
    "n": "Patria Investments Limited - Class A Common Shares"
  },
  {
    "s": "PAXGU",
    "n": "Pine Tree Acquisition Corp. - Units"
  },
  {
    "s": "PAY",
    "n": "Paymentus Holdings, Inc. Class A Common Stock"
  },
  {
    "s": "PAYC",
    "n": "Paycom Software, Inc. Common Stock"
  },
  {
    "s": "PAYO",
    "n": "Payoneer Global Inc. - Common Stock"
  },
  {
    "s": "PAYP",
    "n": "PayPay Corporation - American Depository Shares"
  },
  {
    "s": "PAYS",
    "n": "Paysign, Inc. - Common Stock"
  },
  {
    "s": "PAYX",
    "n": "Paychex, Inc. - Common Stock"
  },
  {
    "s": "PB",
    "n": "Prosperity Bancshares, Inc. Common Stock"
  },
  {
    "s": "PBA",
    "n": "Pembina Pipeline Corp. Ordinary Shares (Canada)"
  },
  {
    "s": "PBAM",
    "n": "Private Bancorp of America, Inc. - Common Stock"
  },
  {
    "s": "PBF",
    "n": "PBF Energy Inc. Class A Common Stock"
  },
  {
    "s": "PBFS",
    "n": "Pioneer Bancorp, Inc. - Common Stock"
  },
  {
    "s": "PBH",
    "n": "Prestige Consumer Healthcare Inc. Common Stock"
  },
  {
    "s": "PBHC",
    "n": "Pathfinder Bancorp, Inc. - Common Stock"
  },
  {
    "s": "PBI",
    "n": "Pitney Bowes Inc. Common Stock"
  },
  {
    "s": "PBK",
    "n": "PowerBank Corporation - Common Stock"
  },
  {
    "s": "PBLS",
    "n": "Parabilis Medicines, Inc. - Common Stock"
  },
  {
    "s": "PBM",
    "n": "Psyence Biomedical Ltd. - Common Shares"
  },
  {
    "s": "PBR",
    "n": "Petroleo Brasileiro S.A. Petrobras ADS"
  },
  {
    "s": "PBT",
    "n": "Permian Basin Royalty Trust Common Stock"
  },
  {
    "s": "PBYI",
    "n": "Puma Biotechnology Inc - Common Stock"
  },
  {
    "s": "PC",
    "n": "Premium Catering (Holdings) Limited - Ordinary Shares"
  },
  {
    "s": "PCAP",
    "n": "ProCap Acquisition Corp - Class A Ordinary Shares"
  },
  {
    "s": "PCAPU",
    "n": "ProCap Acquisition Corp - Unit"
  },
  {
    "s": "PCAR",
    "n": "PACCAR Inc. - Common Stock"
  },
  {
    "s": "PCB",
    "n": "PCB Bancorp - Common Stock"
  },
  {
    "s": "PCG",
    "n": "Pacific Gas & Electric Co. Common Stock"
  },
  {
    "s": "PCLA",
    "n": "PicoCELA Inc. - American Depositary Shares"
  },
  {
    "s": "PCOR",
    "n": "Procore Technologies, Inc. Common Stock"
  },
  {
    "s": "PCRX",
    "n": "Pacira BioSciences, Inc. - Common Stock"
  },
  {
    "s": "PCSA",
    "n": "Processa Pharmaceuticals, Inc. - Common Stock"
  },
  {
    "s": "PCT",
    "n": "PureCycle Technologies, Inc. - Common stock"
  },
  {
    "s": "PCTTU",
    "n": "PureCycle Technologies, Inc. - Unit"
  },
  {
    "s": "PCTY",
    "n": "Paylocity Holding Corporation - Common Stock"
  },
  {
    "s": "PCVX",
    "n": "Vaxcyte, Inc. - Common Stock"
  },
  {
    "s": "PCYO",
    "n": "Pure Cycle Corporation - Common Stock"
  },
  {
    "s": "PD",
    "n": "PagerDuty, Inc. Common Stock"
  },
  {
    "s": "PDC",
    "n": "Perpetuals.com Ltd - American Depositary Shares"
  },
  {
    "s": "PDCC",
    "n": "Pearl Diver Credit Company Inc. Common Stock"
  },
  {
    "s": "PDD",
    "n": "PDD Holdings Inc. - American Depositary Shares"
  },
  {
    "s": "PDEX",
    "n": "Pro-Dex, Inc. - Common Stock"
  },
  {
    "s": "PDFS",
    "n": "PDF Solutions, Inc. - Common Stock"
  },
  {
    "s": "PDLB",
    "n": "Ponce Financial Group, Inc. - Common Stock"
  },
  {
    "s": "PDM",
    "n": "Piedmont Realty Trust, Inc. Class A Common Stock"
  },
  {
    "s": "PDS",
    "n": "Precision Drilling Corporation Common Stock"
  },
  {
    "s": "PDSB",
    "n": "PDS Biotechnology Corporation - Common Stock"
  },
  {
    "s": "PDYN",
    "n": "Palladyne AI Corp. - Common stock"
  },
  {
    "s": "PEB",
    "n": "Pebblebrook Hotel Trust Common Shares of Beneficial Interest"
  },
  {
    "s": "PEBK",
    "n": "Peoples Bancorp of North Carolina, Inc. - Common Stock"
  },
  {
    "s": "PEBO",
    "n": "Peoples Bancorp Inc. - Common Stock"
  },
  {
    "s": "PECE",
    "n": "Peace Acquisition Corp - Ordinary Shares"
  },
  {
    "s": "PECER",
    "n": "Peace Acquisition Corp - Right"
  },
  {
    "s": "PECEU",
    "n": "Peace Acquisition Corp - Units"
  },
  {
    "s": "PECO",
    "n": "Phillips Edison & Company, Inc. - Common Stock"
  },
  {
    "s": "PED",
    "n": "Pedevco Corp. Common Stock"
  },
  {
    "s": "PEG",
    "n": "Public Service Enterprise Group Incorporated Common Stock"
  },
  {
    "s": "PEGA",
    "n": "Pegasystems Inc. - Common Stock"
  },
  {
    "s": "PEN",
    "n": "Penumbra, Inc. Common Stock"
  },
  {
    "s": "PENG",
    "n": "Penguin Solutions, Inc. - Common Stock"
  },
  {
    "s": "PENN",
    "n": "PENN Entertainment, Inc. - Common Stock"
  },
  {
    "s": "PEP",
    "n": "PepsiCo, Inc. - Common Stock"
  },
  {
    "s": "PEPG",
    "n": "PepGen Inc. - Common Stock"
  },
  {
    "s": "PERF",
    "n": "Perfect Corp. Class A Ordinary Share"
  },
  {
    "s": "PERI",
    "n": "Perion Network Ltd - Ordinary Shares"
  },
  {
    "s": "PESI",
    "n": "Perma-Fix Environmental Services, Inc. - Common Stock"
  },
  {
    "s": "PETS",
    "n": "PetMed Express, Inc. - Common Stock"
  },
  {
    "s": "PETZ",
    "n": "TDH Holdings, Inc. - Common Shares"
  },
  {
    "s": "PEW",
    "n": "GrabAGun Digital Holdings Inc. Common Stock"
  },
  {
    "s": "PFAI",
    "n": "Pinnacle Food Group Limited - Class A Common Shares"
  },
  {
    "s": "PFE",
    "n": "Pfizer, Inc. Common Stock"
  },
  {
    "s": "PFG",
    "n": "Principal Financial Group Inc - Common Stock"
  },
  {
    "s": "PFGC",
    "n": "Performance Food Group Company Common Stock"
  },
  {
    "s": "PFH",
    "n": "Prudential Financial, Inc. 4.125% Junior Subordinated Notes due 2060"
  },
  {
    "s": "PFIS",
    "n": "Peoples Financial Services Corp.  - Common Stock"
  },
  {
    "s": "PFLA",
    "n": "PennantPark Floating Rate Capital Ltd. 7.375% Notes Due 2031"
  },
  {
    "s": "PFLT",
    "n": "PennantPark Floating Rate Capital Ltd. Common Stock"
  },
  {
    "s": "PFS",
    "n": "Provident Financial Services, Inc Common Stock"
  },
  {
    "s": "PFSA",
    "n": "Profusa, Inc. - Common Stock"
  },
  {
    "s": "PFSI",
    "n": "PennyMac Financial Services, Inc. Common Stock"
  },
  {
    "s": "PFX",
    "n": "PhenixFIN Corporation  - Common Stock"
  },
  {
    "s": "PFXNZ",
    "n": "PhenixFIN Corporation  - 5.25% Notes due 2028"
  },
  {
    "s": "PG",
    "n": "Procter & Gamble Company (The) Common Stock"
  },
  {
    "s": "PGAC",
    "n": "Pantages Capital Acquisition Corporation - Class A Ordinary Shares"
  },
  {
    "s": "PGACR",
    "n": "Pantages Capital Acquisition Corporation - Right"
  },
  {
    "s": "PGACU",
    "n": "Pantages Capital Acquisition Corporation - Unit"
  },
  {
    "s": "PGC",
    "n": "Peapack-Gladstone Financial Corporation - Common Stock"
  },
  {
    "s": "PGEN",
    "n": "Precigen, Inc. - Common Stock"
  },
  {
    "s": "PGNY",
    "n": "Progyny, Inc. - Common Stock"
  },
  {
    "s": "PGR",
    "n": "Progressive Corporation (The) Common Stock"
  },
  {
    "s": "PGY",
    "n": "Pagaya Technologies Ltd. - Class A Ordinary Shares"
  },
  {
    "s": "PGYWW",
    "n": "Pagaya Technologies Ltd. - Warrants"
  },
  {
    "s": "PH",
    "n": "Parker-Hannifin Corporation Common Stock"
  },
  {
    "s": "PHAR",
    "n": "Pharming Group N.V. - ADS, each representing 10 ordinary shares"
  },
  {
    "s": "PHAT",
    "n": "Phathom Pharmaceuticals, Inc. - Common Stock"
  },
  {
    "s": "PHG",
    "n": "Koninklijke Philips N.V. NY Registry Shares"
  },
  {
    "s": "PHI",
    "n": "PLDT Inc. Sponsored ADR"
  },
  {
    "s": "PHIN",
    "n": "PHINIA Inc. Common Stock"
  },
  {
    "s": "PHIO",
    "n": "Phio Pharmaceuticals Corp. - Common Stock"
  },
  {
    "s": "PHM",
    "n": "PulteGroup, Inc. Common Stock"
  },
  {
    "s": "PHOE",
    "n": "Phoenix Asia Holdings Limited - Ordinary Shares"
  },
  {
    "s": "PHOS",
    "n": "First Phosphate Corp. - American Depositary Shares"
  },
  {
    "s": "PHR",
    "n": "Phreesia, Inc. Common Stock"
  },
  {
    "s": "PHUN",
    "n": "Phunware, Inc. - Common Stock"
  },
  {
    "s": "PHVS",
    "n": "Pharvaris N.V. - Ordinary Shares"
  },
  {
    "s": "PI",
    "n": "Impinj, Inc. - Common Stock"
  },
  {
    "s": "PICS",
    "n": "PicS N.V. - Class A Common Shares"
  },
  {
    "s": "PII",
    "n": "Polaris Inc. Common Stock"
  },
  {
    "s": "PIII",
    "n": "P3 Health Partners Inc. - Class A Common Stock"
  },
  {
    "s": "PIM",
    "n": "Franklin Master Intermediate Income Trust Shares of Beneficial Interest"
  },
  {
    "s": "PINE",
    "n": "Alpine Income Property Trust, Inc. Common Stock"
  },
  {
    "s": "PINS",
    "n": "Pinterest, Inc. Class A Common Stock"
  },
  {
    "s": "PIPR",
    "n": "Piper Sandler Companies Common Stock"
  },
  {
    "s": "PJT",
    "n": "PJT Partners Inc. Class A Common Stock"
  },
  {
    "s": "PK",
    "n": "Park Hotels & Resorts Inc. Common Stock "
  },
  {
    "s": "PKBK",
    "n": "Parke Bancorp, Inc. - Common Stock"
  },
  {
    "s": "PKE",
    "n": "Park Aerospace Corp. Common Stock"
  },
  {
    "s": "PKG",
    "n": "Packaging Corporation of America Common Stock"
  },
  {
    "s": "PKOH",
    "n": "Park-Ohio Holdings Corp. - Common Stock"
  },
  {
    "s": "PKX",
    "n": "POSCO HOLDINGS INC. American Depositary Shares (Each representing 1/4th of a share of Common Stock)"
  },
  {
    "s": "PL",
    "n": "Planet Labs PBC Class A Common Stock"
  },
  {
    "s": "PLAB",
    "n": "Photronics, Inc. - Common Stock"
  },
  {
    "s": "PLAG",
    "n": "Planet Green Holdings Corp. Common Stock"
  },
  {
    "s": "PLAY",
    "n": "Dave & Buster's Entertainment, Inc. - Common Stock"
  },
  {
    "s": "PLBC",
    "n": "Plumas Bancorp - Common Stock"
  },
  {
    "s": "PLBL",
    "n": "Polibeli Group Ltd - Class A Ordinary Shares"
  },
  {
    "s": "PLBY",
    "n": "Playboy, Inc. - Common Stock"
  },
  {
    "s": "PLCE",
    "n": "Children's Place, Inc. (The) - Common Stock"
  },
  {
    "s": "PLCI",
    "n": "Pelican Acquisition II Corporation - Ordinary Shares"
  },
  {
    "s": "PLCIR",
    "n": "Pelican Acquisition II Corporation - Right"
  },
  {
    "s": "PLCIU",
    "n": "Pelican Acquisition II Corporation - Unit"
  },
  {
    "s": "PLD",
    "n": "Prologis, Inc. Common Stock"
  },
  {
    "s": "PLG",
    "n": "Platinum Group Metals Ltd. Ordinary Shares (Canada)"
  },
  {
    "s": "PLGO",
    "n": "Pelagos Insurance Capital Limited Common Shares"
  },
  {
    "s": "PLMK",
    "n": "Plum Acquisition Corp. IV - Class A Ordinary Shares"
  },
  {
    "s": "PLMKU",
    "n": "Plum Acquisition Corp. IV - Unit"
  },
  {
    "s": "PLMKW",
    "n": "Plum Acquisition Corp. IV - Warrants"
  },
  {
    "s": "PLMR",
    "n": "Palomar Holdings, Inc. - Common stock"
  },
  {
    "s": "PLNT",
    "n": "Planet Fitness, Inc. Common Stock"
  },
  {
    "s": "PLOW",
    "n": "Douglas Dynamics, Inc. Common Stock"
  },
  {
    "s": "PLPC",
    "n": "Preformed Line Products Company - Common Stock"
  },
  {
    "s": "PLRX",
    "n": "Pliant Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "PLRZ",
    "n": "Polyrizon Ltd. - Ordinary Shares"
  },
  {
    "s": "PLSE",
    "n": "Pulse Biosciences, Inc - Common Stock"
  },
  {
    "s": "PLSM",
    "n": "Pulsenmore Ltd. - Ordinary Shares"
  },
  {
    "s": "PLTK",
    "n": "Playtika Holding Corp. - Common Stock"
  },
  {
    "s": "PLTR",
    "n": "Palantir Technologies Inc. - Class A Common Stock"
  },
  {
    "s": "PLUG",
    "n": "Plug Power, Inc. - Common Stock"
  },
  {
    "s": "PLUN",
    "n": "Plutonian Acquisition Corp II Class A Ordinary Shares"
  },
  {
    "s": "PLUN-U",
    "n": "Plutonian Acquisition Corp II Units, each consisting of one Class A Ordinary Share and one right entitling the holder to one-fourth of one Class A Ordinary Share"
  },
  {
    "s": "PLUR",
    "n": "Pluri Inc. - Common Stock"
  },
  {
    "s": "PLUS",
    "n": "ePlus inc. - Common Stock"
  },
  {
    "s": "PLUT",
    "n": "Plutus Financial Group Limited - Ordinary Shares"
  },
  {
    "s": "PLX",
    "n": "Protalix BioTherapeutics, Inc. (DE) Common Stock"
  },
  {
    "s": "PLXS",
    "n": "Plexus Corp. - Common Stock"
  },
  {
    "s": "PLYX",
    "n": "Polaryx Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "PM",
    "n": "Philip Morris International Inc Common Stock"
  },
  {
    "s": "PMA",
    "n": "PMA Graphene Technology Group Inc. - Class A Ordinary Shares"
  },
  {
    "s": "PMAX",
    "n": "Powell Max Limited - Class A Ordinary Shares"
  },
  {
    "s": "PMCB",
    "n": "PharmaCyte  Biotech, Inc. - Common Stock"
  },
  {
    "s": "PMEC",
    "n": "Primech Holdings Ltd. - Ordinary Shares"
  },
  {
    "s": "PMI",
    "n": "Picard Medical, Inc. Common Stock"
  },
  {
    "s": "PMM",
    "n": "Franklin Managed Municipal Income Trust Shares of Beneficial Interest"
  },
  {
    "s": "PMN",
    "n": "ProMIS Neurosciences Inc. - Common Shares"
  },
  {
    "s": "PMO",
    "n": "Franklin Municipal Opportunities Trust Shares of Beneficial Interest"
  },
  {
    "s": "PMT",
    "n": "PennyMac Mortgage Investment Trust Common Shares of Beneficial Interest"
  },
  {
    "s": "PMTR",
    "n": "Perimeter Acquisition Corp. I - Class A Ordinary Shares"
  },
  {
    "s": "PMTRU",
    "n": "Perimeter Acquisition Corp. I - Unit"
  },
  {
    "s": "PMTS",
    "n": "CPI Card Group Inc. - Common Stock"
  },
  {
    "s": "PMTU",
    "n": "PennyMac Mortgage Investment Trust 8.50% Senior Notes due 2028"
  },
  {
    "s": "PMTV",
    "n": "PennyMac Mortgage Investment Trust 9.00% Senior Notes due 2030"
  },
  {
    "s": "PMTW",
    "n": "PennyMac Mortgage Investment Trust 9.00% Senior Notes due 2030"
  },
  {
    "s": "PMVP",
    "n": "PMV Pharmaceuticals, Inc. - Common Stock"
  },
  {
    "s": "PN",
    "n": "PN Smart Energy Limited - Class A Ordinary Shares"
  },
  {
    "s": "PNAQ",
    "n": "Pinnacle Acquisition Corporation Class A Ordinary Shares"
  },
  {
    "s": "PNAQ-U",
    "n": "Pinnacle Acquisition Corporation Units, each consisting of one Class A ordinary share and one right"
  },
  {
    "s": "PNBK",
    "n": "Patriot National Bancorp Inc. - Common Stock"
  },
  {
    "s": "PNC",
    "n": "PNC Financial Services Group, Inc. (The) Common Stock"
  },
  {
    "s": "PNFP",
    "n": "Pinnacle Financial Partners, Inc. Common stock"
  },
  {
    "s": "PNNT",
    "n": "PennantPark Investment Corporation Common Stock"
  },
  {
    "s": "PNR",
    "n": "Pentair plc. Ordinary Share"
  },
  {
    "s": "PNRG",
    "n": "PrimeEnergy Resources Corporation - Common Stock"
  },
  {
    "s": "PNTG",
    "n": "The Pennant Group, Inc. - Common Stock"
  },
  {
    "s": "PNW",
    "n": "Pinnacle West Capital Corporation Common Stock"
  },
  {
    "s": "POAS",
    "n": "Phaos Technology Holdings (Cayman) Limited Class A Ordinary Shares"
  },
  {
    "s": "POCI",
    "n": "Precision Optics Corporation, Inc. - Common stock"
  },
  {
    "s": "PODC",
    "n": "PodcastOne, Inc. - Common Stock"
  },
  {
    "s": "PODD",
    "n": "Insulet Corporation - Common Stock"
  },
  {
    "s": "POET",
    "n": "POET Technologies Inc. - Common Shares"
  },
  {
    "s": "POLA",
    "n": "Polar Power, Inc. - Common Stock"
  },
  {
    "s": "POLE",
    "n": "Andretti Acquisition Corp. II - Class A Ordinary Shares"
  },
  {
    "s": "POLEU",
    "n": "Andretti Acquisition Corp. II - Unit"
  },
  {
    "s": "POM",
    "n": "POMDOCTOR LIMITED - American Depositary Shares"
  },
  {
    "s": "PONO",
    "n": "Pono Capital Four, Inc. - Class A Ordinary Shares"
  },
  {
    "s": "PONOU",
    "n": "Pono Capital Four, Inc. - Units"
  },
  {
    "s": "PONY",
    "n": "Pony AI Inc. - American Depositary Shares"
  },
  {
    "s": "POOL",
    "n": "Pool Corporation - Common Stock"
  },
  {
    "s": "POR",
    "n": "Portland General Electric Co Common Stock"
  },
  {
    "s": "POST",
    "n": "Post Holdings, Inc. Common Stock"
  },
  {
    "s": "POWI",
    "n": "Power Integrations, Inc. - Common Stock"
  },
  {
    "s": "POWL",
    "n": "Powell Industries, Inc. - Common Stock"
  },
  {
    "s": "POWW",
    "n": "Outdoor Holding Company - Common Stock"
  },
  {
    "s": "PPBT",
    "n": "Purple Biotech Ltd. - American Depositary Shares"
  },
  {
    "s": "PPC",
    "n": "Pilgrim's Pride Corporation - Common Stock"
  },
  {
    "s": "PPCB",
    "n": "Propanc Biopharma, Inc. - Common Stock"
  },
  {
    "s": "PPG",
    "n": "PPG Industries, Inc. Common Stock"
  },
  {
    "s": "PPHC",
    "n": "Public Policy Holding Company, Inc. - Common Stock"
  },
  {
    "s": "PPIH",
    "n": "Perma-Pipe International Holdings, Inc. - Common Stock"
  },
  {
    "s": "PPL",
    "n": "PPL Corporation Common Stock"
  },
  {
    "s": "PPLC",
    "n": "PPL Corporation Corporate Units"
  },
  {
    "s": "PPLI",
    "n": "People Incorporated - Common Stock"
  },
  {
    "s": "PPSI",
    "n": "Pioneer Power Solutions, Inc. - Common Stock"
  },
  {
    "s": "PPT",
    "n": "Franklin Premier Income Trust Shares of Beneficial Interest"
  },
  {
    "s": "PPTA",
    "n": "Perpetua Resources Corp. - Common Shares"
  },
  {
    "s": "PR",
    "n": "Permian Resources Corporation Class A Common Stock"
  },
  {
    "s": "PRAA",
    "n": "PRA Group, Inc. - Common Stock"
  },
  {
    "s": "PRAX",
    "n": "Praxis Precision Medicines, Inc. - Common Stock"
  },
  {
    "s": "PRCH",
    "n": "Porch Group, Inc. - Common Stock"
  },
  {
    "s": "PRCT",
    "n": "PROCEPT BioRobotics Corporation - Common Stock"
  },
  {
    "s": "PRDO",
    "n": "Perdoceo Education Corporation - Common Stock"
  },
  {
    "s": "PRE",
    "n": "Prenetics Global Limited - Class A Ordinary Share"
  },
  {
    "s": "PRFX",
    "n": "PRF Technologies Ltd. - Ordinary Shares"
  },
  {
    "s": "PRG",
    "n": "PROG Holdings, Inc. Common Stock"
  },
  {
    "s": "PRGO",
    "n": "Perrigo Company plc Ordinary Shares"
  },
  {
    "s": "PRGS",
    "n": "Progress Software Corporation - Common Stock"
  },
  {
    "s": "PRH",
    "n": "Prudential Financial, Inc. 5.950% Junior Subordinated Notes due 2062"
  },
  {
    "s": "PRHI",
    "n": "Presurance Holdings, Inc. - Common Stock"
  },
  {
    "s": "PRHIZ",
    "n": "Presurance Holdings, Inc. - 9.75% Senior Unsecured Notes due 2028"
  },
  {
    "s": "PRI",
    "n": "Primerica, Inc. Common Stock"
  },
  {
    "s": "PRIM",
    "n": "Primoris Services Corporation Common Stock"
  },
  {
    "s": "PRK",
    "n": "Park National Corporation Common Stock"
  },
  {
    "s": "PRKS",
    "n": "United Parks & Resorts Inc. Common Stock"
  },
  {
    "s": "PRLB",
    "n": "Proto Labs, Inc. Common stock"
  },
  {
    "s": "PRLD",
    "n": "Prelude Therapeutics Incorporated - Common Stock"
  },
  {
    "s": "PRM",
    "n": "Perimeter Solutions, SA Common Stock"
  },
  {
    "s": "PRMB",
    "n": "Primo Brands Corporation Class A Common Stock"
  },
  {
    "s": "PRME",
    "n": "Prime Medicine, Inc. - Common Stock"
  },
  {
    "s": "PROF",
    "n": "Profound Medical Corp. - common stock"
  },
  {
    "s": "PROK",
    "n": "ProKidney Corp. - Class A Ordinary Shares"
  },
  {
    "s": "PROP",
    "n": "Prairie Operating Co. - Common Stock"
  },
  {
    "s": "PROV",
    "n": "Provident Financial Holdings, Inc. - Common Stock"
  },
  {
    "s": "PRPL",
    "n": "Purple Innovation, Inc. - Common Stock"
  },
  {
    "s": "PRPO",
    "n": "Precipio, Inc. - Common Stock"
  },
  {
    "s": "PRQR",
    "n": "ProQR Therapeutics N.V. - Ordinary Shares"
  },
  {
    "s": "PRS",
    "n": "Prudential Financial, Inc. 5.625% Junior Subordinated Notes due 2058"
  },
  {
    "s": "PRSO",
    "n": "Peraso Inc. - Common Stock"
  },
  {
    "s": "PRSU",
    "n": "Pursuit Attractions and Hospitality, Inc. Common Stock"
  },
  {
    "s": "PRT",
    "n": "PermRock Royalty Trust Units of Beneficial Interest"
  },
  {
    "s": "PRTA",
    "n": "Prothena Corporation plc - Ordinary Shares"
  },
  {
    "s": "PRTH",
    "n": "Priority Technology Holdings, Inc. - Common Stock"
  },
  {
    "s": "PRTS",
    "n": "CarParts.com, Inc. - Common Stock"
  },
  {
    "s": "PRU",
    "n": "Prudential Financial, Inc. Common Stock"
  },
  {
    "s": "PRVA",
    "n": "Privia Health Group, Inc. - Common Stock"
  },
  {
    "s": "PRZO",
    "n": "ParaZero Technologies Ltd. - Ordinary Shares"
  },
  {
    "s": "PS",
    "n": "Pershing Square Inc. Common Stock"
  },
  {
    "s": "PSA",
    "n": "Public Storage Common Stock"
  },
  {
    "s": "PSBD",
    "n": "Palmer Square Capital BDC Inc. Common Stock"
  },
  {
    "s": "PSFE",
    "n": "Paysafe Limited Common Shares"
  },
  {
    "s": "PSHG",
    "n": "Performance Shipping Inc. - Common Shares"
  },
  {
    "s": "PSIG",
    "n": "PS International Group Ltd. - Ordinary Shares"
  },
  {
    "s": "PSIX",
    "n": "Power Solutions International, Inc. - Common Stock"
  },
  {
    "s": "PSMT",
    "n": "PriceSmart, Inc. - Common Stock"
  },
  {
    "s": "PSN",
    "n": "Parsons Corporation Common Stock"
  },
  {
    "s": "PSNL",
    "n": "Personalis, Inc. - Common Stock"
  },
  {
    "s": "PSNY",
    "n": "Polestar Automotive Holding UK Limited - Class A ADS"
  },
  {
    "s": "PSNYW",
    "n": "Polestar Automotive Holding UK Limited - Class C-1 ADS (ADW)"
  },
  {
    "s": "PSO",
    "n": "Pearson, Plc Common Stock"
  },
  {
    "s": "PSQH",
    "n": "PSQ Holdings, Inc. Class A Common Stock"
  },
  {
    "s": "PSQH-W",
    "n": "PSQ Holdings, Inc. Warrants, each exercisable for one share of Class A common stock at an exercise price of $11.50 per share"
  },
  {
    "s": "PSQL",
    "n": "Pasqal Holding SA - Ordinary Shares"
  },
  {
    "s": "PSTL",
    "n": "Postal Realty Trust, Inc. Class A Common Stock"
  },
  {
    "s": "PSUS",
    "n": "Pershing Square USA, Ltd. Common Shares"
  },
  {
    "s": "PSX",
    "n": "Phillips 66 Common Stock"
  },
  {
    "s": "PTAC",
    "n": "Patriot Acquisition Corp. - Class A Ordinary Shares"
  },
  {
    "s": "PTACU",
    "n": "Patriot Acquisition Corp. - Units"
  },
  {
    "s": "PTACW",
    "n": "Patriot Acquisition Corp. - Warrants"
  },
  {
    "s": "PTC",
    "n": "PTC Inc. - Common Stock"
  },
  {
    "s": "PTCT",
    "n": "PTC Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "PTEN",
    "n": "Patterson-UTI Energy, Inc. - Common Stock"
  },
  {
    "s": "PTGX",
    "n": "Protagonist Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "PTHS",
    "n": "Pelthos Therapeutics Inc. Common Stock"
  },
  {
    "s": "PTLE",
    "n": "PTL LTD - Class A Ordinary Shares"
  },
  {
    "s": "PTLO",
    "n": "Portillo's Inc. - Class A Common Stock"
  },
  {
    "s": "PTN",
    "n": "Palatin Technologies, Inc. - Common Stock"
  },
  {
    "s": "PTON",
    "n": "Peloton Interactive, Inc. - Common Stock"
  },
  {
    "s": "PTOR",
    "n": "Praetorian Acquisition Corp. - Class A Ordinary Shares"
  },
  {
    "s": "PTORU",
    "n": "Praetorian Acquisition Corp. - Units"
  },
  {
    "s": "PTRN",
    "n": "Pattern Group Inc. - Series A Common Stock"
  },
  {
    "s": "PUBM",
    "n": "PubMatic, Inc. - Class A Common Stock"
  },
  {
    "s": "PUK",
    "n": "Prudential Public Limited Company Common Stock"
  },
  {
    "s": "PULM",
    "n": "Pulmatrix, Inc. - Common Stock"
  },
  {
    "s": "PUMP",
    "n": "ProPetro Holding Corp. Common Stock"
  },
  {
    "s": "PURR",
    "n": "Hyperliquid Strategies Inc - Common Stock"
  },
  {
    "s": "PUSA",
    "n": "Powerus Corporation - Common Stock"
  },
  {
    "s": "PVH",
    "n": "PVH Corp. Common Stock"
  },
  {
    "s": "PVL",
    "n": "Permianville Royalty Trust Units of Beneficial Interest"
  },
  {
    "s": "PVLA",
    "n": "Palvella Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "PWCM",
    "n": "PowerCompute, Inc. - Common Stock"
  },
  {
    "s": "PWP",
    "n": "Perella Weinberg Partners - Class A Common Stock"
  },
  {
    "s": "PWR",
    "n": "Quanta Services, Inc. Common Stock"
  },
  {
    "s": "PWRL",
    "n": "Powerlaw Corp. - Common Stock"
  },
  {
    "s": "PXED",
    "n": "Phoenix Education Partners, Inc. Common Stock"
  },
  {
    "s": "PXLW",
    "n": "Pixelworks, Inc. - Common Stock"
  },
  {
    "s": "PXS",
    "n": "Pyxis Tankers Inc. - Common Stock"
  },
  {
    "s": "PYPD",
    "n": "PolyPid Ltd. - Ordinary Shares"
  },
  {
    "s": "PYPL",
    "n": "PayPal Holdings, Inc. - Common Stock"
  },
  {
    "s": "PYT",
    "n": "PPlus Tr GSC-2 Tr Ctf Fltg Rate"
  },
  {
    "s": "PYXS",
    "n": "Pyxis Oncology, Inc. - Common Stock"
  },
  {
    "s": "PZG",
    "n": "Paramount Gold Nevada Corp. Common Stock"
  },
  {
    "s": "PZZA",
    "n": "Papa John's International, Inc. - Common Stock"
  },
  {
    "s": "Q",
    "n": "Qnity Electronics, Inc. Common Stock"
  },
  {
    "s": "QADR",
    "n": "QDRO Acquisition Corp. - Class A Ordinary Shares"
  },
  {
    "s": "QADRU",
    "n": "QDRO Acquisition Corp. - Units"
  },
  {
    "s": "QBTS",
    "n": "D-Wave Quantum Inc. - Common Stock"
  },
  {
    "s": "QCLS",
    "n": "Q/C Technologies, Inc. - Common Stock"
  },
  {
    "s": "QCOM",
    "n": "QUALCOMM Incorporated - Common Stock"
  },
  {
    "s": "QCRH",
    "n": "QCR Holdings, Inc. - Common Stock"
  },
  {
    "s": "QDEL",
    "n": "QuidelOrtho Corporation - Common Stock"
  },
  {
    "s": "QETA",
    "n": "Quetta Acquisition Corporation - Common Stock"
  },
  {
    "s": "QETAR",
    "n": "Quetta Acquisition Corporation - Right"
  },
  {
    "s": "QETAU",
    "n": "Quetta Acquisition Corporation - Unit"
  },
  {
    "s": "QFIN",
    "n": "Qfin Holdings, Inc.  - American Depositary Shares"
  },
  {
    "s": "QGEN",
    "n": "Qiagen N.V. Common Shares"
  },
  {
    "s": "QH",
    "n": "Quhuo Limited - Class A Ordinary Shares"
  },
  {
    "s": "QLEP",
    "n": "Quantum Leap Acquisition Corp Class A Ordinary Shares"
  },
  {
    "s": "QLYS",
    "n": "Qualys, Inc. - Common Stock"
  },
  {
    "s": "QMCO",
    "n": "Quantum Corporation - Common Stock"
  },
  {
    "s": "QMLS",
    "n": "QumulusAI, Inc. - Common Stock"
  },
  {
    "s": "QNBC",
    "n": "QNB Corp. - Common Stock"
  },
  {
    "s": "QNC",
    "n": "Quantum eMotion Corp. Common Shares"
  },
  {
    "s": "QNCX",
    "n": "Quince Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "QNME",
    "n": "Quanome Technologies, Inc. - Common Stock"
  },
  {
    "s": "QNRX",
    "n": "Quoin Pharmaceuticals, Ltd. - American Depositary Shares"
  },
  {
    "s": "QNST",
    "n": "QuinStreet, Inc. - Common Stock"
  },
  {
    "s": "QNT",
    "n": "Quantinuum Inc. - Class A Common Stock"
  },
  {
    "s": "QNTM",
    "n": "Quantum Biopharma Ltd. - Class B Subordinate Voting Shares"
  },
  {
    "s": "QRED",
    "n": "QuasarEdge Acquisition Corporation Ordinary Shares"
  },
  {
    "s": "QRED-U",
    "n": "QuasarEdge Acquisition Corporation Units, each consisting of one Ordinary Share and one right entitling the holder to receive one-fourth (1/4) of one Ordinary Share"
  },
  {
    "s": "QRHC",
    "n": "Quest Resource Holding Corporation - Common Stock"
  },
  {
    "s": "QS",
    "n": "QuantumScape Corporation - Common Stock"
  },
  {
    "s": "QSEA",
    "n": "Quartzsea Acquisition Corporation - Ordinary Shares"
  },
  {
    "s": "QSEAU",
    "n": "Quartzsea Acquisition Corporation - Units"
  },
  {
    "s": "QSI",
    "n": "Quantum-Si Incorporated - Class A Common Stock"
  },
  {
    "s": "QSR",
    "n": "Restaurant Brands International Inc. Common Shares"
  },
  {
    "s": "QTEX",
    "n": "QTREX Quantum Ltd. - Ordinary Shares"
  },
  {
    "s": "QTI",
    "n": "QT Imaging Holdings, Inc. - Common Stock"
  },
  {
    "s": "QTRX",
    "n": "Quanterix Corporation - Common Stock"
  },
  {
    "s": "QTTB",
    "n": "Q32 Bio Inc. - Common Stock"
  },
  {
    "s": "QTWO",
    "n": "Q2 Holdings, Inc. Common Stock"
  },
  {
    "s": "QUAD",
    "n": "Quad Graphics, Inc Class A Common Stock"
  },
  {
    "s": "QUBT",
    "n": "Quantum Computing Inc. - Common Stock"
  },
  {
    "s": "QUCY",
    "n": "Quantum Cyber N.V. - Ordinary Shares"
  },
  {
    "s": "QUIK",
    "n": "QuickLogic Corporation - Common Stock"
  },
  {
    "s": "QUMS",
    "n": "Quantumsphere Acquisition Corp. - Ordinary Shares"
  },
  {
    "s": "QUMSU",
    "n": "Quantumsphere Acquisition Corp. - Units"
  },
  {
    "s": "QURE",
    "n": "uniQure N.V. - Ordinary Shares"
  },
  {
    "s": "QVCG",
    "n": "QVC Group, Inc. - Common Stock"
  },
  {
    "s": "QXL",
    "n": "Quantum X Labs Inc. - Common Stock"
  },
  {
    "s": "QXO",
    "n": "QXO, Inc. Common Stock"
  },
  {
    "s": "R",
    "n": "Ryder System, Inc. Common Stock"
  },
  {
    "s": "RAC",
    "n": "Rithm Acquisition Corp. Class A Ordinary Shares"
  },
  {
    "s": "RACC",
    "n": "Research Alliance Corporation III - Class A Ordinary Shares"
  },
  {
    "s": "RACD",
    "n": "Research Alliance Corporation IV - Class A Ordinary Shares"
  },
  {
    "s": "RACE",
    "n": "Ferrari N.V. Common Shares"
  },
  {
    "s": "RADX",
    "n": "Radiopharm Theranostics Limited - American Depositary Shares"
  },
  {
    "s": "RAIL",
    "n": "Freightcar America, Inc. - Common Stock"
  },
  {
    "s": "RAIN",
    "n": "Rain Enhancement Technologies Holdco, Inc. - Class A Common Stock"
  },
  {
    "s": "RAINW",
    "n": "Rain Enhancement Technologies Holdco, Inc. - Warrants"
  },
  {
    "s": "RAL",
    "n": "Ralliant Corporation Common Stock"
  },
  {
    "s": "RAMP",
    "n": "LiveRamp Holdings, Inc. Common Stock"
  },
  {
    "s": "RANG",
    "n": "Range Capital Acquisition Corp. - Ordinary Shares"
  },
  {
    "s": "RANGU",
    "n": "Range Capital Acquisition Corp. - Units"
  },
  {
    "s": "RANI",
    "n": "Rani Therapeutics Holdings, Inc. - Class A Common Stock"
  },
  {
    "s": "RAPP",
    "n": "Rapport Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "RARE",
    "n": "Ultragenyx Pharmaceutical Inc. - Common Stock"
  },
  {
    "s": "RAVE",
    "n": "Rave Restaurant Group, Inc. - Common Stock"
  },
  {
    "s": "RAYA",
    "n": "Erayak Power Solution Group Inc. - Class A Ordinary Shares"
  },
  {
    "s": "RBA",
    "n": "RB Global, Inc. Common Stock"
  },
  {
    "s": "RBB",
    "n": "RBB Bancorp - Common Stock"
  },
  {
    "s": "RBBN",
    "n": "Ribbon Communications Inc.  - Common Stock"
  },
  {
    "s": "RBC",
    "n": "RBC Bearings Incorporated Common Stock"
  },
  {
    "s": "RBCAA",
    "n": "Republic Bancorp, Inc. - Class A Common Stock"
  },
  {
    "s": "RBKB",
    "n": "Rhinebeck Bancorp, Inc. - Common Stock"
  },
  {
    "s": "RBLX",
    "n": "Roblox Corporation Class A Common Stock"
  },
  {
    "s": "RBNE",
    "n": "Robin Energy Ltd. - Common Stock"
  },
  {
    "s": "RBRK",
    "n": "Rubrik, Inc. Class A Common Stock"
  },
  {
    "s": "RC",
    "n": "Ready Capital Corporation Common Stock"
  },
  {
    "s": "RCAT",
    "n": "Red Cat Holdings, Inc. - Common Stock"
  },
  {
    "s": "RCBC",
    "n": "River City Bank - Common stock"
  },
  {
    "s": "RCD",
    "n": "Ready Capital Corporation 9.00% Senior Notes due 2029"
  },
  {
    "s": "RCEL",
    "n": "Avita Medical, Inc. - Common Stock"
  },
  {
    "s": "RCI",
    "n": "Rogers Communication, Inc. Common Stock"
  },
  {
    "s": "RCKT",
    "n": "Rocket Pharmaceuticals, Inc. - Common Stock"
  },
  {
    "s": "RCKY",
    "n": "Rocky Brands, Inc. - Common Stock"
  },
  {
    "s": "RCL",
    "n": "Royal Caribbean Cruises Ltd. Common Stock"
  },
  {
    "s": "RCMT",
    "n": "RCM Technologies, Inc. - Common Stock"
  },
  {
    "s": "RCON",
    "n": "Recon Technology, Ltd. - Class A Ordinary Shares"
  },
  {
    "s": "RCT",
    "n": "RedCloud Holdings plc - Ordinary Shares"
  },
  {
    "s": "RCUS",
    "n": "Arcus Biosciences, Inc. Common Stock"
  },
  {
    "s": "RDAC",
    "n": "Rising Dragon Acquisition Corp. - Ordinary Shares"
  },
  {
    "s": "RDACU",
    "n": "Rising Dragon Acquisition Corp. - Unit"
  },
  {
    "s": "RDAG",
    "n": "Republic Digital Acquisition Company - Class A Ordinary Shares"
  },
  {
    "s": "RDAGU",
    "n": "Republic Digital Acquisition Company - Unit"
  },
  {
    "s": "RDAGW",
    "n": "Republic Digital Acquisition Company - Warrants"
  },
  {
    "s": "RDCM",
    "n": "Radcom Ltd. - Ordinary Shares"
  },
  {
    "s": "RDDT",
    "n": "Reddit, Inc. Class A Common Stock"
  },
  {
    "s": "RDGT",
    "n": "Ridgetech, Inc. - Ordinary Shares"
  },
  {
    "s": "RDHL",
    "n": "Redhill Biopharma Ltd. - American Depositary Shares"
  },
  {
    "s": "RDI",
    "n": "Reading International Inc - Class A Non-voting Common Stock"
  },
  {
    "s": "RDIB",
    "n": "Reading International Inc - Class B Voting Common Stock"
  },
  {
    "s": "RDN",
    "n": "Radian Group Inc. Common Stock"
  },
  {
    "s": "RDNT",
    "n": "RadNet, Inc. - Common Stock"
  },
  {
    "s": "RDNW",
    "n": "RideNow Group, Inc. - Class B Common Stock"
  },
  {
    "s": "RDVT",
    "n": "Red Violet, Inc. - Common Stock "
  },
  {
    "s": "RDW",
    "n": "Redwire Corporation Common Stock"
  },
  {
    "s": "RDWR",
    "n": "Radware Ltd. - Ordinary Shares"
  },
  {
    "s": "RDY",
    "n": "Dr. Reddy's Laboratories Ltd Common Stock"
  },
  {
    "s": "RDZN",
    "n": "Roadzen, Inc. - Ordinary Shares"
  },
  {
    "s": "RDZNW",
    "n": "Roadzen, Inc. - Warrants"
  },
  {
    "s": "REA",
    "n": "Rare Earths Americas, Inc. Common Stock"
  },
  {
    "s": "REAL",
    "n": "The RealReal, Inc. - Common Stock"
  },
  {
    "s": "REAX",
    "n": "Real REMAX Group Inc. - Common Stock"
  },
  {
    "s": "REBN",
    "n": "Reborn Coffee, Inc. - Common Stock"
  },
  {
    "s": "RECT",
    "n": "Rectitude Holdings Ltd - Ordinary Shares"
  },
  {
    "s": "REED",
    "n": "Reed's, Inc. Common Stock"
  },
  {
    "s": "REF",
    "n": "Reformation Inc. Common Stock"
  },
  {
    "s": "REFI",
    "n": "Chicago Atlantic Real Estate Finance, Inc. - Common Stock"
  },
  {
    "s": "REFR",
    "n": "Research Frontiers Incorporated - Common Stock"
  },
  {
    "s": "REG",
    "n": "Regency Centers Corporation - Common Stock"
  },
  {
    "s": "REGN",
    "n": "Regeneron Pharmaceuticals, Inc. - Common Stock"
  },
  {
    "s": "REI",
    "n": "Ring Energy, Inc. Common Stock"
  },
  {
    "s": "REKR",
    "n": "Rekor Systems, Inc. - Common Stock"
  },
  {
    "s": "RELL",
    "n": "Richardson Electronics, Ltd. - Common Stock"
  },
  {
    "s": "RELX",
    "n": "RELX PLC PLC American Depositary Shares (Each representing One Ordinary Share)"
  },
  {
    "s": "RELY",
    "n": "Remitly Global, Inc. - Common stock"
  },
  {
    "s": "RENT",
    "n": "Rent the Runway, Inc. - Class A Common Stock"
  },
  {
    "s": "RENX",
    "n": "RenX Enterprises Corp. - Common Stock"
  },
  {
    "s": "REPL",
    "n": "Replimune Group, Inc. - Common Stock"
  },
  {
    "s": "REPX",
    "n": "Riley Exploration Permian, Inc. Common Stock"
  },
  {
    "s": "RERE",
    "n": "ATRenew Inc. American Depositary Shares (every three of which representing two Class A ordinary shares)"
  },
  {
    "s": "RES",
    "n": "RPC, Inc. Common Stock"
  },
  {
    "s": "RETO",
    "n": "ReTo Eco-Solutions, Inc. - Class A Shares"
  },
  {
    "s": "REVB",
    "n": "Revelation Biosciences, Inc. - Common Stock"
  },
  {
    "s": "REX",
    "n": "REX American Resources Corporation"
  },
  {
    "s": "REXR",
    "n": "Rexford Industrial Realty, Inc. Common Stock"
  },
  {
    "s": "REYN",
    "n": "Reynolds Consumer Products Inc. - Common Stock"
  },
  {
    "s": "REZI",
    "n": "Resideo Technologies, Inc. Common Stock "
  },
  {
    "s": "RF",
    "n": "Regions Financial Corporation Common Stock"
  },
  {
    "s": "RFAI",
    "n": "RF Acquisition Corp II - Ordinary Shares"
  },
  {
    "s": "RFAIR",
    "n": "RF Acquisition Corp II - Right"
  },
  {
    "s": "RFAIU",
    "n": "RF Acquisition Corp II - Unit"
  },
  {
    "s": "RFAM",
    "n": "RF Acquisition Corp III - Ordinary Shares"
  },
  {
    "s": "RFAMU",
    "n": "RF Acquisition Corp III - Units"
  },
  {
    "s": "RFIL",
    "n": "RF Industries, Ltd. - Common Stock"
  },
  {
    "s": "RFL",
    "n": "Rafael Holdings, Inc. Class B Common Stock"
  },
  {
    "s": "RGA",
    "n": "Reinsurance Group of America, Incorporated Common Stock"
  },
  {
    "s": "RGC",
    "n": "Regencell Bioscience Holdings Limited - Ordinary Shares"
  },
  {
    "s": "RGCO",
    "n": "RGC Resources Inc. - Common Stock"
  },
  {
    "s": "RGEN",
    "n": "Repligen Corporation - Common Stock"
  },
  {
    "s": "RGLD",
    "n": "Royal Gold, Inc. - Common Stock"
  },
  {
    "s": "RGNT",
    "n": "Regentis Biomaterials Ltd. Ordinary Shares"
  },
  {
    "s": "RGNX",
    "n": "REGENXBIO Inc. - Common Stock"
  },
  {
    "s": "RGP",
    "n": "Resources Connection, Inc. - Common Stock"
  },
  {
    "s": "RGR",
    "n": "Sturm, Ruger & Company, Inc. Common Stock"
  },
  {
    "s": "RGS",
    "n": "Regis Corporation - Common Stock"
  },
  {
    "s": "RGT",
    "n": "Royce Global Trust, Inc. Common Stock"
  },
  {
    "s": "RGTI",
    "n": "Rigetti Computing, Inc.  - Common stock"
  },
  {
    "s": "RH",
    "n": "RH Common Stock"
  },
  {
    "s": "RHI",
    "n": "Robert Half Inc. Common Stock"
  },
  {
    "s": "RHLD",
    "n": "Resolute Holdings Management Common Stock "
  },
  {
    "s": "RIBB",
    "n": "Ribbon Acquisition Corp - Class A Ordinary Shares"
  },
  {
    "s": "RIBBU",
    "n": "Ribbon Acquisition Corp - Unit"
  },
  {
    "s": "RICK",
    "n": "RCI Hospitality Holdings, Inc. - Common Stock"
  },
  {
    "s": "RIG",
    "n": "Transocean Ltd (Switzerland) Common Stock"
  },
  {
    "s": "RIGL",
    "n": "Rigel Pharmaceuticals, Inc. - Common Stock"
  },
  {
    "s": "RILY",
    "n": "BRC Group Holdings, Inc. - Common Stock"
  },
  {
    "s": "RILYG",
    "n": "BRC Group Holdings, Inc. - 5.00% Senior Notes due 2026"
  },
  {
    "s": "RILYT",
    "n": "BRC Group Holdings, Inc. - 6.00% Senior Notes Due 2028"
  },
  {
    "s": "RILYZ",
    "n": "BRC Group Holdings, Inc. - 5.25% Senior Notes due 2028"
  },
  {
    "s": "RIME",
    "n": "Algorhythm Holdings, Inc. - Common Stock"
  },
  {
    "s": "RIO",
    "n": "Rio Tinto Plc Common Stock"
  },
  {
    "s": "RIOT",
    "n": "Riot Platforms, Inc. - Common Stock"
  },
  {
    "s": "RITM",
    "n": "Rithm Capital Corp. Common Stock"
  },
  {
    "s": "RIVN",
    "n": "Rivian Automotive, Inc. - Class A Common Stock"
  },
  {
    "s": "RJET",
    "n": "Republic Airways Holdings Inc. - Common Stock"
  },
  {
    "s": "RJF",
    "n": "Raymond James Financial, Inc. Common Stock"
  },
  {
    "s": "RKDA",
    "n": "Arcadia Biosciences, Inc. - Common Stock"
  },
  {
    "s": "RKLB",
    "n": "Rocket Lab Corporation - Common Stock"
  },
  {
    "s": "RKT",
    "n": "Rocket Companies, Inc. Class A Common Stock"
  },
  {
    "s": "RKTO",
    "n": "Rocket One Inc. - Common Stock"
  },
  {
    "s": "RL",
    "n": "Ralph Lauren Corporation Common Stock"
  },
  {
    "s": "RLAY",
    "n": "Relay Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "RLGT",
    "n": "Radiant Logistics, Inc. Common Stock"
  },
  {
    "s": "RLI",
    "n": "RLI Corp. Common Stock (DE)"
  },
  {
    "s": "RLJ",
    "n": "RLJ Lodging Trust Common Shares of Beneficial Interest $0.01 par value"
  },
  {
    "s": "RLMD",
    "n": "Relmada Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "RLX",
    "n": "RLX Technology Inc. American Depositary Shares, each representing the right to receive one (1) Class A ordinary share"
  },
  {
    "s": "RLYB",
    "n": "Rallybio Corporation - Common Stock"
  },
  {
    "s": "RM",
    "n": "Regional Management Corp. Common Stock"
  },
  {
    "s": "RMBI",
    "n": "Richmond Mutual Bancorporation, Inc. - Common Stock"
  },
  {
    "s": "RMBS",
    "n": "Rambus, Inc. - Common Stock"
  },
  {
    "s": "RMCF",
    "n": "Rocky Mountain Chocolate Factory, Inc. - Common Stock"
  },
  {
    "s": "RMCO",
    "n": "Royalty Management Holding Corporation - Class A Common Stock"
  },
  {
    "s": "RMD",
    "n": "ResMed Inc. Common Stock"
  },
  {
    "s": "RMIX",
    "n": "Suncrete, Inc. - Class A Common Stock"
  },
  {
    "s": "RML",
    "n": "Resolution Minerals Ltd - American Depositary Shares"
  },
  {
    "s": "RMNI",
    "n": "Rimini Street, Inc. - Common Stock"
  },
  {
    "s": "RMR",
    "n": "The RMR Group Inc. - Class A Common Stock"
  },
  {
    "s": "RMSG",
    "n": "Real Messenger Corporation - Ordinary Shares"
  },
  {
    "s": "RMSGW",
    "n": "Real Messenger Corporation - Warrants"
  },
  {
    "s": "RMT",
    "n": "Royce Micro-Cap Trust, Inc. Common Stock"
  },
  {
    "s": "RMTI",
    "n": "Rockwell Medical, Inc. - Common Stock"
  },
  {
    "s": "RNA",
    "n": "Atrium Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "RNAC",
    "n": "Cartesian Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "RNAQ",
    "n": "Rainier Acquisition Corporation - Class A Ordinary Shares"
  },
  {
    "s": "RNAQU",
    "n": "Rainier Acquisition Corporation - Units"
  },
  {
    "s": "RNAQW",
    "n": "Rainier Acquisition Corporation - Warrants"
  },
  {
    "s": "RNAZ",
    "n": "TransCode Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "RNG",
    "n": "RingCentral, Inc. Class A Common Stock"
  },
  {
    "s": "RNGR",
    "n": "Ranger Energy Services, Inc. Class A Common Stock"
  },
  {
    "s": "RNGT",
    "n": "Range Capital Acquisition Corp II - Class A Ordinary Shares"
  },
  {
    "s": "RNGTU",
    "n": "Range Capital Acquisition Corp II - Units"
  },
  {
    "s": "RNGTW",
    "n": "Range Capital Acquisition Corp II - Warrants"
  },
  {
    "s": "RNR",
    "n": "RenaissanceRe Holdings Ltd. Common Stock"
  },
  {
    "s": "RNST",
    "n": "Renasant Corporation Common Stock"
  },
  {
    "s": "RNTX",
    "n": "Rein Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "RNW",
    "n": "ReNew Energy Global plc - Class A Shares"
  },
  {
    "s": "RNXT",
    "n": "RenovoRx, Inc. - Common Stock"
  },
  {
    "s": "ROAD",
    "n": "Construction Partners, Inc. - Common Stock"
  },
  {
    "s": "ROC",
    "n": "Rank One Computing Corporation - Common stock"
  },
  {
    "s": "ROCK",
    "n": "Gibraltar Industries, Inc. - Common Stock"
  },
  {
    "s": "ROG",
    "n": "Rogers Corporation Common Stock"
  },
  {
    "s": "ROIV",
    "n": "Roivant Sciences Ltd. - Common Shares"
  },
  {
    "s": "ROK",
    "n": "Rockwell Automation, Inc. Common Stock"
  },
  {
    "s": "ROKU",
    "n": "Roku, Inc. - Class A Common Stock"
  },
  {
    "s": "ROL",
    "n": "Rollins, Inc. Common Stock"
  },
  {
    "s": "ROLR",
    "n": "High Roller Technologies, Inc. Common Stock"
  },
  {
    "s": "ROMA",
    "n": "Roma Green Finance Limited - Class A Ordinary Shares"
  },
  {
    "s": "ROOT",
    "n": "Root, Inc. - Common Stock"
  },
  {
    "s": "ROP",
    "n": "Roper Technologies, Inc. - Common Stock"
  },
  {
    "s": "ROST",
    "n": "Ross Stores, Inc. - Common Stock"
  },
  {
    "s": "RPAY",
    "n": "Repay Holdings Corporation - Class A Common Stock"
  },
  {
    "s": "RPC",
    "n": "Ridgepost Capital, Inc. Class A Common Stock"
  },
  {
    "s": "RPD",
    "n": "Rapid7, Inc. - Common Stock"
  },
  {
    "s": "RPGL",
    "n": "Republic Power Group Limited - Class A Ordinary Shares"
  },
  {
    "s": "RPID",
    "n": "Rapid Micro Biosystems, Inc. - Class A Common Stock"
  },
  {
    "s": "RPM",
    "n": "RPM International Inc. Common Stock"
  },
  {
    "s": "RPRX",
    "n": "Royalty Pharma plc - Class A Ordinary Shares"
  },
  {
    "s": "RPT",
    "n": "Rithm Property Trust Inc. Common stock"
  },
  {
    "s": "RR",
    "n": "Richtech Robotics Inc. - Class B Common Stock"
  },
  {
    "s": "RRBI",
    "n": "Red River Bancshares, Inc. - Common Stock"
  },
  {
    "s": "RRC",
    "n": "Range Resources Corporation Common Stock"
  },
  {
    "s": "RREV",
    "n": "RRE Ventures Acquisition Corp. - Class A Ordinary Shares"
  },
  {
    "s": "RREVU",
    "n": "RRE Ventures Acquisition Corp. - Units"
  },
  {
    "s": "RREVW",
    "n": "RRE Ventures Acquisition Corp. - Warrants"
  },
  {
    "s": "RRGB",
    "n": "Red Robin Gourmet Burgers, Inc. - Common Stock"
  },
  {
    "s": "RRR",
    "n": "Red Rock Resorts, Inc. - Class A Common Stock"
  },
  {
    "s": "RRX",
    "n": "Regal Rexnord Corporation Common Stock"
  },
  {
    "s": "RS",
    "n": "Reliance, Inc. Common Stock"
  },
  {
    "s": "RSG",
    "n": "Republic Services, Inc. Common Stock"
  },
  {
    "s": "RSI",
    "n": "Rush Street Interactive, Inc. Class A Common Stock"
  },
  {
    "s": "RSKD",
    "n": "Riskified Ltd. Class A Ordinary Shares"
  },
  {
    "s": "RSSS",
    "n": "Research Solutions, Inc - Common Stock"
  },
  {
    "s": "RSVR",
    "n": "Reservoir Media, Inc.. - Common Stock"
  },
  {
    "s": "RTAC",
    "n": "Renatus Tactical Acquisition Corp I - Class A Ordinary Shares"
  },
  {
    "s": "RTACU",
    "n": "Renatus Tactical Acquisition Corp I - Unit"
  },
  {
    "s": "RTB",
    "n": "RTB Digital, Inc. - Common Stock"
  },
  {
    "s": "RTO",
    "n": "Rentokil Initial plc American Depositary Shares (each representing five (5) Ordinary Shares)"
  },
  {
    "s": "RTSN",
    "n": "Retension Pharmaceuticals, Inc. - Common Stock"
  },
  {
    "s": "RTX",
    "n": "RTX Corporation Common Stock"
  },
  {
    "s": "RUBI",
    "n": "Rubico Inc. - Common Stock"
  },
  {
    "s": "RUM",
    "n": "RUM Group Inc. - Class A Common Stock"
  },
  {
    "s": "RUN",
    "n": "Sunrun Inc. - Common Stock"
  },
  {
    "s": "RUSHA",
    "n": "Rush Enterprises, Inc. - Class A Common Stock"
  },
  {
    "s": "RUSHB",
    "n": "Rush Enterprises, Inc. - Class B Common Stock"
  },
  {
    "s": "RVLV",
    "n": "Revolve Group, Inc. Class A Common Stock"
  },
  {
    "s": "RVMD",
    "n": "Revolution Medicines, Inc. - Common Stock"
  },
  {
    "s": "RVP",
    "n": "Retractable Technologies, Inc. Common Stock"
  },
  {
    "s": "RVSB",
    "n": "Riverview Bancorp Inc - Common Stock"
  },
  {
    "s": "RVSN",
    "n": "Rail Vision Ltd. - Ordinary Shares"
  },
  {
    "s": "RVT",
    "n": "Royce Small-Cap Trust, Inc. Common Stock"
  },
  {
    "s": "RVTY",
    "n": "Revvity, Inc. Common Stock"
  },
  {
    "s": "RWAY",
    "n": "Runway Growth Finance Corp. - Common Stock"
  },
  {
    "s": "RWAYI",
    "n": "Runway Growth Finance Corp. - 7.25% Notes due 2031"
  },
  {
    "s": "RWAYL",
    "n": "Runway Growth Finance Corp. - 7.50% Notes due 2027"
  },
  {
    "s": "RWAYM",
    "n": "Runway Growth Finance Corp. - 7.75% Notes Due 2031"
  },
  {
    "s": "RWT",
    "n": "Redwood Trust, Inc. Common Stock"
  },
  {
    "s": "RWTN",
    "n": "Redwood Trust, Inc. 9.125% Senior Notes Due 2029"
  },
  {
    "s": "RWTO",
    "n": "Redwood Trust, Inc. 9.00% Senior Notes Due 2029"
  },
  {
    "s": "RWTP",
    "n": "Redwood Trust, Inc. 9.125% Senior Notes Due 2030"
  },
  {
    "s": "RWTQ",
    "n": "Redwood Trust, Inc. 9.500% Senior Notes Due 2030"
  },
  {
    "s": "RWTS",
    "n": "Redwood Trust, Inc. 9.75% Senior Notes Due 2031"
  },
  {
    "s": "RXO",
    "n": "RXO, Inc. Common Stock"
  },
  {
    "s": "RXRX",
    "n": "Recursion Pharmaceuticals, Inc. - Class A Common Stock"
  },
  {
    "s": "RXST",
    "n": "RxSight, Inc. - Common Stock"
  },
  {
    "s": "RXT",
    "n": "Rackspace Technology, Inc. - Common Stock"
  },
  {
    "s": "RY",
    "n": "Royal Bank Of Canada Common Stock"
  },
  {
    "s": "RYAAY",
    "n": "Ryanair Holdings plc - American Depositary Shares, each representing five Ordinary Shares"
  },
  {
    "s": "RYAM",
    "n": "Rayonier Advanced Materials Inc. Common Stock"
  },
  {
    "s": "RYAN",
    "n": "Ryan Specialty Holdings, Inc. Class A Common Stock"
  },
  {
    "s": "RYDE",
    "n": "Ryde Group Ltd. Class A Ordinary Shares"
  },
  {
    "s": "RYET",
    "n": "Ruanyun Edai Technology Inc. - Ordinary shares"
  },
  {
    "s": "RYM",
    "n": "RYTHM, Inc. - Common Stock"
  },
  {
    "s": "RYOJ",
    "n": "rYojbaba Co., Ltd. - Common Shares"
  },
  {
    "s": "RYTM",
    "n": "Rhythm Pharmaceuticals, Inc. - Common Stock"
  },
  {
    "s": "RYZ",
    "n": "Ryerson Holding Corporation Common Stock"
  },
  {
    "s": "RZAI",
    "n": "Roze AI Inc. - Common Shares"
  },
  {
    "s": "RZC",
    "n": "Reinsurance Group of America, Incorporated 7.125% Fixed-Rate Reset Subordinated Debentures due 2052"
  },
  {
    "s": "RZLT",
    "n": "Rezolute, Inc. - Common Stock (NV)"
  },
  {
    "s": "RZLV",
    "n": "Rezolve AI PLC - Ordinary Shares"
  },
  {
    "s": "RZLVW",
    "n": "Rezolve AI PLC - Warrants"
  },
  {
    "s": "S",
    "n": "SentinelOne, Inc. Class A Common Stock"
  },
  {
    "s": "SA",
    "n": "Seabridge Gold, Inc. Common Shares New"
  },
  {
    "s": "SAAQ",
    "n": "Space Asset Acquisition Corp. - Class A Ordinary Shares"
  },
  {
    "s": "SAAQU",
    "n": "Space Asset Acquisition Corp. - Units"
  },
  {
    "s": "SAAQW",
    "n": "Space Asset Acquisition Corp. - Warrants"
  },
  {
    "s": "SABR",
    "n": "Sabre Corporation - Common Stock"
  },
  {
    "s": "SABS",
    "n": "SAB Biotherapeutics, Inc. - Common Stock"
  },
  {
    "s": "SAC",
    "n": "Safeguard Acquisition Corp. Class A Ordinary Shares"
  },
  {
    "s": "SACH",
    "n": "Sachem Capital Corp. Common Shares"
  },
  {
    "s": "SAFE",
    "n": "Safehold Inc. New Common Stock "
  },
  {
    "s": "SAFT",
    "n": "Safety Insurance Group, Inc. - Common Stock"
  },
  {
    "s": "SAFX",
    "n": "XCF Global, Inc. - Class A Common Stock"
  },
  {
    "s": "SAGT",
    "n": "SAGTEC GLOBAL LIMITED - Class A Ordinary shares"
  },
  {
    "s": "SAGU",
    "n": "Shreya Acquisition Group Class A Ordinary Shares"
  },
  {
    "s": "SAGU-W",
    "n": "Shreya Acquisition Group Redeemable warrants, entitling the holder to purchase one Class A Ordinary Share at $11.50 per share"
  },
  {
    "s": "SAH",
    "n": "Sonic Automotive, Inc. Common Stock"
  },
  {
    "s": "SAIA",
    "n": "Saia, Inc. - Common Stock"
  },
  {
    "s": "SAIC",
    "n": "Science Applications International Corporation - Common Stock"
  },
  {
    "s": "SAIH",
    "n": "SAIHEAT Limited - Class A Ordinary Shares"
  },
  {
    "s": "SAIL",
    "n": "SailPoint, Inc. - Common Stock"
  },
  {
    "s": "SAIQ",
    "n": "WISeSat.Space Holdings Corp. - Ordinary Shares"
  },
  {
    "s": "SAJ",
    "n": "Saratoga Investment Corp 8.00% Notes due 2027"
  },
  {
    "s": "SAM",
    "n": "Boston Beer Company, Inc. (The) Common Stock"
  },
  {
    "s": "SAMG",
    "n": "Silvercrest Asset Management Group Inc. - Common Stock"
  },
  {
    "s": "SAMO",
    "n": "Samos Energy Acquisition Corporation Class A Ordinary Shares"
  },
  {
    "s": "SAN",
    "n": "Banco Santander, S.A. Sponsored ADR (Spain)"
  },
  {
    "s": "SANA",
    "n": "Sana Biotechnology, Inc. - Common Stock"
  },
  {
    "s": "SANG",
    "n": "Sangoma Technologies Corporation - Common Shares"
  },
  {
    "s": "SANM",
    "n": "Sanmina Corporation - Common Stock"
  },
  {
    "s": "SAP",
    "n": "SAP  SE ADS"
  },
  {
    "s": "SAR",
    "n": "Saratoga Investment Corp New"
  },
  {
    "s": "SARO",
    "n": "StandardAero, Inc. Common Stock"
  },
  {
    "s": "SATL",
    "n": "Satellogic Inc. - Class A Common Stock"
  },
  {
    "s": "SAV",
    "n": "Saratoga Investment Corp 7.50% Notes due 2031"
  },
  {
    "s": "SAX",
    "n": "Saratoga Investment Corp 8.00% Notes due 2031"
  },
  {
    "s": "SAY",
    "n": "Saratoga Investment Corp 8.125% Notes due 2027"
  },
  {
    "s": "SAZ",
    "n": "Saratoga Investment Corp 8.50% Notes due 2028"
  },
  {
    "s": "SB",
    "n": "Safe Bulkers, Inc Common Stock ($0.001 par value)"
  },
  {
    "s": "SBAC",
    "n": "SBA Communications Corporation - Class A Common Stock"
  },
  {
    "s": "SBC",
    "n": "SBC Medical Group Holdings Incorporated - Common Stock"
  },
  {
    "s": "SBCF",
    "n": "Seacoast Banking Corporation of Florida - Common Stock"
  },
  {
    "s": "SBCWW",
    "n": "SBC Medical Group Holdings Incorporated - Warrants"
  },
  {
    "s": "SBET",
    "n": "Sharplink, Inc. - Common Stock"
  },
  {
    "s": "SBFG",
    "n": "SB Financial Group, Inc. - Common Stock"
  },
  {
    "s": "SBFM",
    "n": "Sunshine Biopharma Inc. - Common stock"
  },
  {
    "s": "SBGI",
    "n": "Sinclair, Inc. - Class A Common Stock"
  },
  {
    "s": "SBH",
    "n": "Sally Beauty Holdings, Inc. (Name to be changed from Sally Holdings, Inc.) Common Stock"
  },
  {
    "s": "SBLK",
    "n": "Star Bulk Carriers Corp. - Common Shares"
  },
  {
    "s": "SBMT",
    "n": "Silver Bow Mining Corp. Common Shares"
  },
  {
    "s": "SBR",
    "n": "Sabine Royalty Trust Common Stock"
  },
  {
    "s": "SBS",
    "n": "Companhia de saneamento Basico Do Estado De Sao Paulo - Sabesp American Depositary Shares (Each repstg 250 Common Shares)"
  },
  {
    "s": "SBSI",
    "n": "Southside Bancshares, Inc. Common Stock"
  },
  {
    "s": "SBSW",
    "n": "D/B/A Sibanye-Stillwater Limited ADS"
  },
  {
    "s": "SBUX",
    "n": "Starbucks Corporation - Common Stock"
  },
  {
    "s": "SBXE",
    "n": "SilverBox Corp V Class A Ordinary Shares"
  },
  {
    "s": "SCAG",
    "n": "Scage Future - American Depositary Shares"
  },
  {
    "s": "SCAGW",
    "n": "Scage Future - Warrants"
  },
  {
    "s": "SCAT",
    "n": "Southern Cross Acquisition II Corp. - Ordinary Shares"
  },
  {
    "s": "SCATU",
    "n": "Southern Cross Acquisition II Corp. - Units"
  },
  {
    "s": "SCATW",
    "n": "Southern Cross Acquisition II Corp. - Warrants"
  },
  {
    "s": "SCCD",
    "n": "Sachem Capital Corp. 6.00% Notes due 2026"
  },
  {
    "s": "SCCE",
    "n": "Sachem Capital Corp. 6.00% Notes due 2027"
  },
  {
    "s": "SCCF",
    "n": "Sachem Capital Corp. 7.125% Notes due 2027"
  },
  {
    "s": "SCCG",
    "n": "Sachem Capital Corp. 8.00% Notes due 2027"
  },
  {
    "s": "SCCO",
    "n": "Southern Copper Corporation Common Stock"
  },
  {
    "s": "SCHL",
    "n": "Scholastic Corporation - Common Stock"
  },
  {
    "s": "SCHW",
    "n": "Charles Schwab Corporation (The) Common Stock"
  },
  {
    "s": "SCI",
    "n": "Service Corporation International Common Stock"
  },
  {
    "s": "SCII",
    "n": "SC II Acquisition Corp. - Class A ordinary share"
  },
  {
    "s": "SCIIU",
    "n": "SC II Acquisition Corp. - Units"
  },
  {
    "s": "SCKT",
    "n": "Socket Mobile, Inc. - Common Stock"
  },
  {
    "s": "SCL",
    "n": "Stepan Company Common Stock"
  },
  {
    "s": "SCLX",
    "n": "Scilex Holding Company - Common Stock"
  },
  {
    "s": "SCM",
    "n": "Stellus Capital Investment Corporation Common Stock"
  },
  {
    "s": "SCNI",
    "n": "Scinai Immunotherapeutics Ltd. - American Depositary Shares"
  },
  {
    "s": "SCNX",
    "n": "Scienture Holdings, Inc. - Common Stock"
  },
  {
    "s": "SCOR",
    "n": "comScore, Inc. - Common Stock"
  },
  {
    "s": "SCPQ",
    "n": "Social Commerce Partners Corporation - Class A Ordinary Shares"
  },
  {
    "s": "SCPQU",
    "n": "Social Commerce Partners Corporation - Unit"
  },
  {
    "s": "SCSC",
    "n": "ScanSource, Inc. - Common Stock"
  },
  {
    "s": "SCTX",
    "n": "Scribe Therapeutics Inc. - Common Stock"
  },
  {
    "s": "SCWO",
    "n": "374Water Inc. - common stock"
  },
  {
    "s": "SCYX",
    "n": "SCYNEXIS, Inc. - Common Stock"
  },
  {
    "s": "SCZM",
    "n": "Santacruz Silver Mining Ltd. - Common Shares"
  },
  {
    "s": "SD",
    "n": "SandRidge Energy, Inc. Common Stock"
  },
  {
    "s": "SDA",
    "n": "SunCar Technology Group Inc. - Ordinary Shares"
  },
  {
    "s": "SDEV",
    "n": "Stablecoin Development Corporation Common Stock"
  },
  {
    "s": "SDGR",
    "n": "Schrodinger, Inc. - Common Stock"
  },
  {
    "s": "SDHC",
    "n": "Smith Douglas Homes Corp. Class A Common Stock"
  },
  {
    "s": "SDHI",
    "n": "Siddhi Acquisition Corp - Class A Common stock"
  },
  {
    "s": "SDHIR",
    "n": "Siddhi Acquisition Corp - Right"
  },
  {
    "s": "SDHIU",
    "n": "Siddhi Acquisition Corp - Unit"
  },
  {
    "s": "SDOT",
    "n": "Sadot Group Inc. - Common Stock"
  },
  {
    "s": "SDRL",
    "n": "Seadrill Limited Common Shares"
  },
  {
    "s": "SDST",
    "n": "Stardust Power Inc. - Common Stock"
  },
  {
    "s": "SE",
    "n": "Sea Limited American Depositary Shares, each representing one Class A Ordinary Share"
  },
  {
    "s": "SEAT",
    "n": "Vivid Seats Inc. - Class A common stock"
  },
  {
    "s": "SEB",
    "n": "Seaboard Corporation Common Stock"
  },
  {
    "s": "SECZ",
    "n": "Securitize Corp. Common Stock"
  },
  {
    "s": "SEDG",
    "n": "SolarEdge Technologies, Inc. - Common Stock"
  },
  {
    "s": "SEED",
    "n": "Origin Agritech Limited - Ordinary Shares"
  },
  {
    "s": "SEER",
    "n": "Seer, Inc. - Class A Common Stock"
  },
  {
    "s": "SEG",
    "n": "Seaport Entertainment Group Inc. Common Stock"
  },
  {
    "s": "SEGG",
    "n": "Sports Entertainment Gaming Global Corporation  - Common Stock"
  },
  {
    "s": "SEI",
    "n": "Solaris Energy Infrastructure, Inc. Class A Common Stock"
  },
  {
    "s": "SEIC",
    "n": "SEI Investments Company - Common Stock"
  },
  {
    "s": "SELF",
    "n": "Global Self Storage, Inc. - Common Stock"
  },
  {
    "s": "SENEA",
    "n": "Seneca Foods Corp. - Class A Common Stock"
  },
  {
    "s": "SENEB",
    "n": "Seneca Foods Corp. - Class B Common Stock"
  },
  {
    "s": "SENS",
    "n": "Senseonics Holdings, Inc. - Common Stock"
  },
  {
    "s": "SEPN",
    "n": "Septerna, Inc. - Common Stock"
  },
  {
    "s": "SER",
    "n": "Serina Therapeutics, Inc. Common Stock"
  },
  {
    "s": "SERA",
    "n": "Sera Prognostics, Inc. - Class A Common Stock"
  },
  {
    "s": "SERV",
    "n": "Serve Robotics Inc. - Common Stock"
  },
  {
    "s": "SES",
    "n": "SES AI Corporation Class A Common Stock"
  },
  {
    "s": "SEV",
    "n": "Aptera Motors Corp. - Class B Common Stock"
  },
  {
    "s": "SEVN",
    "n": "Seven Hills Realty Trust  - Common Stock"
  },
  {
    "s": "SEZL",
    "n": "Sezzle Inc. - Common Stock"
  },
  {
    "s": "SF",
    "n": "Stifel Financial Corporation Common Stock"
  },
  {
    "s": "SFB",
    "n": "Stifel Financial Corporation 5.20% Senior Notes due 2047"
  },
  {
    "s": "SFBC",
    "n": "Sound Financial Bancorp, Inc. - Common Stock"
  },
  {
    "s": "SFBS",
    "n": "ServisFirst Bancshares, Inc. Common Stock"
  },
  {
    "s": "SFD",
    "n": "Smithfield Foods, Inc. - Common Stock"
  },
  {
    "s": "SFHG",
    "n": "Samfine Creation Holdings Group Limited - Class A Ordinary Share"
  },
  {
    "s": "SFIX",
    "n": "Stitch Fix, Inc. - Class A Common Stock"
  },
  {
    "s": "SFL",
    "n": "SFL Corporation Ltd"
  },
  {
    "s": "SFM",
    "n": "Sprouts Farmers Market, Inc. - Common Stock"
  },
  {
    "s": "SFNC",
    "n": "Simmons First National Corporation - Common Stock"
  },
  {
    "s": "SFST",
    "n": "Southern First Bancshares, Inc. - Common Stock"
  },
  {
    "s": "SFWL",
    "n": "Shengfeng Development Limited - Class A Ordinary Shares"
  },
  {
    "s": "SG",
    "n": "Sweetgreen, Inc. Class A Common Stock"
  },
  {
    "s": "SGA",
    "n": "Saga Communications, Inc. - Class A Common Stock"
  },
  {
    "s": "SGC",
    "n": "Superior Group of Companies, Inc. - Common Stock"
  },
  {
    "s": "SGHC",
    "n": "Super Group (SGHC) Limited Ordinary Shares"
  },
  {
    "s": "SGHT",
    "n": "Sight Sciences, Inc. - Common Stock"
  },
  {
    "s": "SGI",
    "n": "Somnigroup International Inc. Common Stock"
  },
  {
    "s": "SGLD",
    "n": "Scorpio Gold Corporation - Common Stock"
  },
  {
    "s": "SGLY",
    "n": "Singularity Future Technology Ltd. - Common Stock"
  },
  {
    "s": "SGML",
    "n": "Sigma Lithium Corporation - common shares"
  },
  {
    "s": "SGMT",
    "n": "Sagimet Biosciences Inc. - Series A Common Stock"
  },
  {
    "s": "SGP",
    "n": "SpyGlass Pharma, Inc. - Common Stock"
  },
  {
    "s": "SGRX",
    "n": "SANGRIX INC. - Class A Ordinary Shares"
  },
  {
    "s": "SGRY",
    "n": "Surgery Partners, Inc. - Common Stock"
  },
  {
    "s": "SGU",
    "n": "Star Group L.P. Common Stock"
  },
  {
    "s": "SHAK",
    "n": "Shake Shack, Inc. Class A Common Stock"
  },
  {
    "s": "SHAZ",
    "n": "SharonAI Holdings, Inc. - Class A Common Stock"
  },
  {
    "s": "SHBI",
    "n": "Shore Bancshares, Inc. - Common Stock"
  },
  {
    "s": "SHC",
    "n": "Sotera Health Company - Common Stock"
  },
  {
    "s": "SHEL",
    "n": "Shell PLC American Depositary Shares (each representing two (2) Ordinary Shares) "
  },
  {
    "s": "SHEN",
    "n": "Shenandoah Telecommunications Co - Common Stock"
  },
  {
    "s": "SHFS",
    "n": "SHF Holdings, Inc. - Class A Common Stock"
  },
  {
    "s": "SHFSW",
    "n": "SHF Holdings, Inc. - Warrants"
  },
  {
    "s": "SHG",
    "n": "Shinhan Financial Group Co Ltd American Depositary Shares"
  },
  {
    "s": "SHIM",
    "n": "Shimmick Corporation - Common Stock"
  },
  {
    "s": "SHIP",
    "n": "Seanergy Maritime Holdings Corp. - Common Stock"
  },
  {
    "s": "SHLS",
    "n": "Shoals Technologies Group, Inc. - Class A Common Stock"
  },
  {
    "s": "SHMD",
    "n": "SCHMID Group N.V. - Class A Ordinary Shares"
  },
  {
    "s": "SHMDW",
    "n": "SCHMID Group N.V. - Warrants"
  },
  {
    "s": "SHO",
    "n": "Sunstone Hotel Investors, Inc. Sunstone Hotel Investors, Inc. Common Shares"
  },
  {
    "s": "SHOE",
    "n": "Shoe Station Group, Inc. - Common Stock"
  },
  {
    "s": "SHOO",
    "n": "Steven Madden, Ltd. - Common Stock"
  },
  {
    "s": "SHOP",
    "n": "Shopify Inc. - Class A Subordinate Voting Shares"
  },
  {
    "s": "SHOT",
    "n": "RMG ML Sports Holdings - Class A Ordinary Shares"
  },
  {
    "s": "SHOTU",
    "n": "RMG ML Sports Holdings - Unit"
  },
  {
    "s": "SHPH",
    "n": "Shuttle Pharmaceuticals Holdings, Inc. - common stock"
  },
  {
    "s": "SHW",
    "n": "Sherwin-Williams Company (The) Common Stock"
  },
  {
    "s": "SI",
    "n": "Shoulder Innovations, Inc. Common Stock"
  },
  {
    "s": "SIBN",
    "n": "SI-BONE, Inc. - Common Stock"
  },
  {
    "s": "SID",
    "n": "Companhia Siderurgica Nacional S.A. Common Stock"
  },
  {
    "s": "SIDU",
    "n": "Sidus Space, Inc. - Class A Common Stock"
  },
  {
    "s": "SIEB",
    "n": "Siebert Financial Corp. - Common Stock"
  },
  {
    "s": "SIF",
    "n": "SIFCO Industries, Inc. Common Stock"
  },
  {
    "s": "SIFY",
    "n": "Sify Technologies Limited - American Depository Shares"
  },
  {
    "s": "SIG",
    "n": "Signet Jewelers Limited Common Shares"
  },
  {
    "s": "SIGA",
    "n": "SIGA Technologies Inc. - Common Stock"
  },
  {
    "s": "SIGI",
    "n": "Selective Insurance Group, Inc. - Common Stock"
  },
  {
    "s": "SII",
    "n": "Sprott Inc. Common Shares"
  },
  {
    "s": "SILC",
    "n": "Silicom Ltd - Ordinary Shares"
  },
  {
    "s": "SILO",
    "n": "Silo Pharma, Inc. - Common Stock"
  },
  {
    "s": "SIM",
    "n": "Grupo Simec, S.A.B. de C.V. American Depositary Shares"
  },
  {
    "s": "SIMA",
    "n": "SIM Acquisition Corp. I - Class A Ordinary Shares"
  },
  {
    "s": "SIMAU",
    "n": "SIM Acquisition Corp. I - Unit"
  },
  {
    "s": "SIMO",
    "n": "Silicon Motion Technology Corporation - American Depositary Shares, each representing four ordinary shares"
  },
  {
    "s": "SIND",
    "n": "Sinda Ltd. Common Stock"
  },
  {
    "s": "SINT",
    "n": "SiNtx Technologies, Inc. - Common Stock"
  },
  {
    "s": "SION",
    "n": "Sionna Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "SIRI",
    "n": "SiriusXM Holdings Inc. - Common Stock"
  },
  {
    "s": "SITC",
    "n": "SITE Centers Corp. Common Stock"
  },
  {
    "s": "SITE",
    "n": "SiteOne Landscape Supply, Inc. Common Stock"
  },
  {
    "s": "SITM",
    "n": "SiTime Corporation - Common Stock"
  },
  {
    "s": "SJ",
    "n": "Scienjoy Holding Corporation - Class A Ordinary Shares"
  },
  {
    "s": "SJM",
    "n": "The J.M. Smucker Company Common Stock"
  },
  {
    "s": "SJT",
    "n": "San Juan Basin Royalty Trust Common Stock"
  },
  {
    "s": "SKE",
    "n": "Skeena Resources Limited Common Shares"
  },
  {
    "s": "SKHY",
    "n": "SK hynix Inc. - American Depositary Shares"
  },
  {
    "s": "SKIL",
    "n": "Skillsoft Corp. Class A Common Stock"
  },
  {
    "s": "SKIN",
    "n": "SkinHealth Systems Inc. - Class A Common Stock"
  },
  {
    "s": "SKK",
    "n": "SKK Holdings Limited - Class A Ordinary Shares"
  },
  {
    "s": "SKM",
    "n": "SK Telecom Co., Ltd. Common Stock"
  },
  {
    "s": "SKT",
    "n": "Tanger Inc. Common Stock"
  },
  {
    "s": "SKWD",
    "n": "Skyward Specialty Insurance Group, Inc. - Common Stock"
  },
  {
    "s": "SKY",
    "n": "Champion Homes, Inc. Common Stock"
  },
  {
    "s": "SKYA",
    "n": "SkyAI, Inc. - Common Stock"
  },
  {
    "s": "SKYD",
    "n": "Skydance Corporation Class B Common Stock"
  },
  {
    "s": "SKYE",
    "n": "Skye Bioscience, Inc. - Common Stock"
  },
  {
    "s": "SKYH",
    "n": "Sky Harbour Group Corporation Class A Common Stock"
  },
  {
    "s": "SKYQ",
    "n": "Sky Quarry Inc. - Common Stock"
  },
  {
    "s": "SKYW",
    "n": "SkyWest, Inc. - Common Stock"
  },
  {
    "s": "SKYX",
    "n": "SKYX Platforms Corp. - Common Stock"
  },
  {
    "s": "SLAB",
    "n": "Silicon Laboratories, Inc. - Common Stock"
  },
  {
    "s": "SLB",
    "n": "SLB Limited Common Shares"
  },
  {
    "s": "SLBT",
    "n": "SL Science Holding Limited - Ordinary Shares"
  },
  {
    "s": "SLDB",
    "n": "Solid Biosciences Inc. - Common Stock"
  },
  {
    "s": "SLDE",
    "n": "Slide Insurance Holdings, Inc. - Common Stock"
  },
  {
    "s": "SLDP",
    "n": "Solid Power, Inc. - Class A Common Stock"
  },
  {
    "s": "SLE",
    "n": "Super League Enterprise, Inc. - Common Stock"
  },
  {
    "s": "SLF",
    "n": "Sun Life Financial Inc. Common Stock"
  },
  {
    "s": "SLG",
    "n": "SL Green Realty Corp Common Stock"
  },
  {
    "s": "SLGB",
    "n": "Smart Logistics Global Limited - Class A Ordinary Shares"
  },
  {
    "s": "SLGL",
    "n": "Sol-Gel Technologies Ltd. - Ordinary Shares"
  },
  {
    "s": "SLGN",
    "n": "Silgan Holdings Inc. Common Stock"
  },
  {
    "s": "SLI",
    "n": "Standard Lithium Ltd. Common Shares"
  },
  {
    "s": "SLM",
    "n": "SLM Corporation - Common Stock"
  },
  {
    "s": "SLMT",
    "n": "Brera Holdings PLC - Class B Ordinary Shares"
  },
  {
    "s": "SLN",
    "n": "Silence Therapeutics Plc - American Depository Share"
  },
  {
    "s": "SLND",
    "n": "Southland Holdings, Inc. Common Stock"
  },
  {
    "s": "SLND-W",
    "n": "Southland Holdings, Inc. Warrants"
  },
  {
    "s": "SLNG",
    "n": "Stabilis Solutions, Inc. - Common Stock"
  },
  {
    "s": "SLNH",
    "n": "Soluna Holdings, Inc. - Common Stock"
  },
  {
    "s": "SLQT",
    "n": "SelectQuote, Inc. Common Stock"
  },
  {
    "s": "SLS",
    "n": "SELLAS Life Sciences Group, Inc.  - Common Stock"
  },
  {
    "s": "SLSN",
    "n": "Solesence, Inc. - Common stock"
  },
  {
    "s": "SLSR",
    "n": "Solaris Resources Inc. Common Shares"
  },
  {
    "s": "SLVM",
    "n": "Sylvamo Corporation Common Stock"
  },
  {
    "s": "SLXN",
    "n": "Silexion Therapeutics Corp - Ordinary Shares"
  },
  {
    "s": "SM",
    "n": "SM Energy Company Common Stock"
  },
  {
    "s": "SMBC",
    "n": "Southern Missouri Bancorp, Inc. - Common Stock"
  },
  {
    "s": "SMBK",
    "n": "SmartFinancial, Inc. Common Stock"
  },
  {
    "s": "SMC",
    "n": "Summit Midstream Corporation Common Stock"
  },
  {
    "s": "SMCI",
    "n": "Super Micro Computer, Inc. - Common Stock"
  },
  {
    "s": "SMFG",
    "n": "Sumitomo Mitsui Financial Group Inc Unsponsored American Depositary Shares (Japan)"
  },
  {
    "s": "SMG",
    "n": "Scotts Miracle-Gro Company (The) Common Stock"
  },
  {
    "s": "SMHI",
    "n": "SEACOR Marine Holdings Inc. Common Stock "
  },
  {
    "s": "SMID",
    "n": "Smith-Midland Corporation - Common Stock"
  },
  {
    "s": "SMJF",
    "n": "SMJ International Holdings Inc. Class A Ordinary Shares"
  },
  {
    "s": "SMMT",
    "n": "Summit Therapeutics Inc.  - Common Stock"
  },
  {
    "s": "SMP",
    "n": "Standard Motor Products, Inc. Common Stock"
  },
  {
    "s": "SMPL",
    "n": "The Simply Good Foods Company - Common Stock"
  },
  {
    "s": "SMR",
    "n": "NuScale Power Corporation Class A Common Stock"
  },
  {
    "s": "SMRT",
    "n": "SmartRent, Inc. Class A Common Stock"
  },
  {
    "s": "SMSI",
    "n": "Smith Micro Software, Inc. - Common Stock"
  },
  {
    "s": "SMTC",
    "n": "Semtech Corporation - Common Stock"
  },
  {
    "s": "SMTI",
    "n": "Sanara MedTech Inc. - Common Stock"
  },
  {
    "s": "SMTK",
    "n": "SmartKem, Inc. - Common Stock"
  },
  {
    "s": "SMWB",
    "n": "Similarweb Ltd. Ordinary Shares"
  },
  {
    "s": "SMX",
    "n": "SMX (Security Matters) Public Limited Company - Ordinary Shares"
  },
  {
    "s": "SMXT",
    "n": "Solarmax Technology Inc. - Common Stock"
  },
  {
    "s": "SN",
    "n": "SharkNinja, Inc. Ordinary Shares"
  },
  {
    "s": "SNA",
    "n": "Snap-On Incorporated Common Stock"
  },
  {
    "s": "SNAL",
    "n": "Snail, Inc. - Class A Common Stock"
  },
  {
    "s": "SNAP",
    "n": "Snap Inc. Class A Common Stock"
  },
  {
    "s": "SND",
    "n": "Smart Sand, Inc. - Common Stock"
  },
  {
    "s": "SNDA",
    "n": "Sonida Senior Living, Inc. Common Stock"
  },
  {
    "s": "SNDK",
    "n": "Sandisk Corporation - Common Stock When-Issued"
  },
  {
    "s": "SNDL",
    "n": "SNDL Inc. - Common Shares"
  },
  {
    "s": "SNDR",
    "n": "Schneider National, Inc. Common Stock"
  },
  {
    "s": "SNDX",
    "n": "Syndax Pharmaceuticals, Inc. - Common Stock"
  },
  {
    "s": "SNES",
    "n": "SenesTech, Inc. - Common Stock"
  },
  {
    "s": "SNEX",
    "n": "StoneX Group Inc. - Common Stock"
  },
  {
    "s": "SNFCA",
    "n": "Security National Financial Corporation - Class A Common Stock"
  },
  {
    "s": "SNGX",
    "n": "Soligenix, Inc. - Common Stock"
  },
  {
    "s": "SNN",
    "n": "Smith & Nephew SNATS, Inc. Common Stock"
  },
  {
    "s": "SNOA",
    "n": "Sonoma Pharmaceuticals, Inc. - Common Stock"
  },
  {
    "s": "SNOW",
    "n": "Snowflake Inc. Common Stock"
  },
  {
    "s": "SNPS",
    "n": "Synopsys, Inc. - Common Stock"
  },
  {
    "s": "SNSC",
    "n": "SunScout Holding Limited Class A Ordinary Shares"
  },
  {
    "s": "SNT",
    "n": "Senstar Technologies Corporation - Common Shares"
  },
  {
    "s": "SNTG",
    "n": "Sentage Holdings Inc. - Class A Ordinary Shares"
  },
  {
    "s": "SNTI",
    "n": "Senti Biosciences Holdings, Inc. - Common Stock"
  },
  {
    "s": "SNWV",
    "n": "SANUWAVE Health, Inc. - Common Stock"
  },
  {
    "s": "SNX",
    "n": "TD SYNNEX Corporation Common Stock"
  },
  {
    "s": "SNY",
    "n": "Sanofi - American Depositary Shares"
  },
  {
    "s": "SO",
    "n": "Southern Company (The) Common Stock"
  },
  {
    "s": "SOAR",
    "n": "Volato Group, Inc. Class A Common Stock"
  },
  {
    "s": "SOBO",
    "n": "South Bow Corporation Common Shares"
  },
  {
    "s": "SOC",
    "n": "Sable Offshore Corp. Common Stock"
  },
  {
    "s": "SOCA",
    "n": "Solarius Capital Acquisition Corp. - Class A Ordinary Share"
  },
  {
    "s": "SOCAU",
    "n": "Solarius Capital Acquisition Corp. - Units"
  },
  {
    "s": "SOFI",
    "n": "SoFi Technologies, Inc.  - Common Stock"
  },
  {
    "s": "SOGP",
    "n": "Sound Group Inc. - American Depositary Shares"
  },
  {
    "s": "SOHU",
    "n": "Sohu.com Limited  - American Depositary Shares"
  },
  {
    "s": "SOJC",
    "n": "Southern Company (The) Series 2017B 5.25% Junior Subordinated Notes due December 1, 2077"
  },
  {
    "s": "SOJD",
    "n": "Southern Company (The) Series 2020A 4.95% Junior Subordinated Notes due January 30, 2080"
  },
  {
    "s": "SOJE",
    "n": "Southern Company (The) Series 2020C 4.20% Junior Subordinated Notes due October 15, 2060"
  },
  {
    "s": "SOJF",
    "n": "Southern Company (The) Series 2025A 6.50% Junior Subordinated Notes due March 15, 2085"
  },
  {
    "s": "SOLS",
    "n": "Solstice Advanced Materials Inc. - Common Stock"
  },
  {
    "s": "SOLV",
    "n": "Solventum Corporation Common Stock"
  },
  {
    "s": "SOMN",
    "n": "Southern Company (The) 2025 Series A Corporate Units"
  },
  {
    "s": "SON",
    "n": "Sonoco Products Company Common Stock"
  },
  {
    "s": "SONM",
    "n": "DNA X, Inc. - Common Stock"
  },
  {
    "s": "SONO",
    "n": "Sonos, Inc. - Common Stock"
  },
  {
    "s": "SONY",
    "n": "Sony Group Corporation American Depositary Shares "
  },
  {
    "s": "SOPH",
    "n": "SOPHiA GENETICS SA - Ordinary Shares"
  },
  {
    "s": "SOR",
    "n": "Source Capital, Inc. Cmn Shs of BI"
  },
  {
    "s": "SORA",
    "n": "AsiaStrategy - Ordinary Shares"
  },
  {
    "s": "SORN",
    "n": "Soren Acquisition Corp. - Class A Ordinary Shares"
  },
  {
    "s": "SORNU",
    "n": "Soren Acquisition Corp. - Unit"
  },
  {
    "s": "SOS",
    "n": "SOS Limited Class A Ordinary Shares"
  },
  {
    "s": "SOTK",
    "n": "Sono-Tek Corporation - Common Stock"
  },
  {
    "s": "SOUL",
    "n": "Soulpower Acquisition Corporation Class A Ordinary Shares"
  },
  {
    "s": "SOUL-U",
    "n": "Soulpower Acquisition Corporation Units, each consisting of one Class A ordinary share and one right"
  },
  {
    "s": "SOUN",
    "n": "SoundHound AI, Inc. - Class A Common Stock"
  },
  {
    "s": "SOWG",
    "n": "Sow Good Inc. - Common Stock"
  },
  {
    "s": "SPAI",
    "n": "Safe Pro Group Inc. - Common Stock"
  },
  {
    "s": "SPB",
    "n": "Spectrum Brands Holdings, Inc. Common Stock"
  },
  {
    "s": "SPCB",
    "n": "SuperCom, Ltd. - Ordinary Shares"
  },
  {
    "s": "SPCE",
    "n": "Virgin Galactic Holdings, Inc. Common Stock"
  },
  {
    "s": "SPCX",
    "n": "Space Exploration Technologies Corp. - Class A Common Stock"
  },
  {
    "s": "SPEG",
    "n": "Silver Pegasus Acquisition Corp - Class A Ordinary Shares"
  },
  {
    "s": "SPEGU",
    "n": "Silver Pegasus Acquisition Corp - Unit"
  },
  {
    "s": "SPFI",
    "n": "South Plains Financial, Inc. - Common Stock"
  },
  {
    "s": "SPG",
    "n": "Simon Property Group, Inc. Common Stock"
  },
  {
    "s": "SPGI",
    "n": "S&P Global Inc. Common Stock"
  },
  {
    "s": "SPH",
    "n": "Suburban Propane Partners, L.P. Common Stock"
  },
  {
    "s": "SPHL",
    "n": "Springview Holdings Ltd - Ordinary shares"
  },
  {
    "s": "SPHR",
    "n": "Sphere Entertainment Co. Class A Common Stock"
  },
  {
    "s": "SPIR",
    "n": "Spire Global, Inc. Class A Common Stock"
  },
  {
    "s": "SPMC",
    "n": "Sound Point Meridian Capital, Inc. Common Stock"
  },
  {
    "s": "SPNT",
    "n": "SiriusPoint Ltd. Common Shares"
  },
  {
    "s": "SPOK",
    "n": "Spok Holdings, Inc. - Common Stock"
  },
  {
    "s": "SPOT",
    "n": "Spotify Technology S.A. Ordinary Shares"
  },
  {
    "s": "SPPL",
    "n": "SIMPPLE LTD. - Ordinary Shares"
  },
  {
    "s": "SPRB",
    "n": "Spruce Biosciences, Inc. - Common Stock"
  },
  {
    "s": "SPRC",
    "n": "SciSparc Ltd. - Ordinary Shares"
  },
  {
    "s": "SPRO",
    "n": "Spero Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "SPRU",
    "n": "Spruce Power Holding Corporation Class A Common Stock"
  },
  {
    "s": "SPRY",
    "n": "ARS Pharmaceuticals, Inc. - Common Stock"
  },
  {
    "s": "SPSC",
    "n": "SPS Commerce, Inc. - Common Stock"
  },
  {
    "s": "SPT",
    "n": "Sprout Social, Inc - Class A Common Stock"
  },
  {
    "s": "SPTX",
    "n": "Seaport Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "SPWH",
    "n": "Sportsman's Warehouse Holdings, Inc. - Common Stock"
  },
  {
    "s": "SPWR",
    "n": "SunPower Inc. - Common Stock"
  },
  {
    "s": "SPXC",
    "n": "SPX Technologies, Inc. Common Stock"
  },
  {
    "s": "SQFT",
    "n": "Presidio Property Trust, Inc. - Class A Common Stock"
  },
  {
    "s": "SQFTW",
    "n": "Presidio Property Trust, Inc. - Series A Common Stock Purchase Warrants"
  },
  {
    "s": "SQM",
    "n": "Sociedad Quimica y Minera S.A. Common Stock"
  },
  {
    "s": "SQNS",
    "n": "Sequans Communications S.A. American Depositary Shares (each representing one hundred (100) Ordinary Shares)"
  },
  {
    "s": "SR",
    "n": "Spire Inc. Common Stock"
  },
  {
    "s": "SRAD",
    "n": "Sportradar Group AG - Class A Ordinary Shares"
  },
  {
    "s": "SRBK",
    "n": "SR Bancorp, Inc. - Common stock"
  },
  {
    "s": "SRCE",
    "n": "1st Source Corporation - Common Stock"
  },
  {
    "s": "SRE",
    "n": "DBA Sempra Common Stock"
  },
  {
    "s": "SREA",
    "n": "DBA Sempra 5.750% Junior Subordinated Notes due 2079"
  },
  {
    "s": "SRFM",
    "n": "Surf Air Mobility Inc. Common Stock"
  },
  {
    "s": "SRG",
    "n": "Seritage Growth Properties Class A Common Stock"
  },
  {
    "s": "SRI",
    "n": "Stoneridge, Inc. Common Stock"
  },
  {
    "s": "SRJN",
    "n": "Spire Inc. 6.375% Junior Subordinated Notes due 2086"
  },
  {
    "s": "SRL",
    "n": "Scully Royalty Ltd."
  },
  {
    "s": "SRPT",
    "n": "Sarepta Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "SRRK",
    "n": "Scholar Rock Holding Corporation - Common Stock"
  },
  {
    "s": "SRTA",
    "n": "Strata Critical Medical, Inc. - Class A Common Stock"
  },
  {
    "s": "SRTS",
    "n": "Sensus Healthcare, Inc. - Common Stock"
  },
  {
    "s": "SRXH",
    "n": "SRX Global Inc. Common Stock"
  },
  {
    "s": "SRZN",
    "n": "Surrozen, Inc. - Common Stock"
  },
  {
    "s": "SSAC",
    "n": "SPACSphere Acquisition Corp. - Class A Ordinary Shares"
  },
  {
    "s": "SSACU",
    "n": "SPACSphere Acquisition Corp. - Unit"
  },
  {
    "s": "SSB",
    "n": "SouthState Bank Corporation Common Stock"
  },
  {
    "s": "SSBI",
    "n": "Summit State Bank - Common Stock"
  },
  {
    "s": "SSD",
    "n": "Simpson Manufacturing Company, Inc. Common Stock"
  },
  {
    "s": "SSEA",
    "n": "Starry Sea Acquisition Corp - Ordinary Shares"
  },
  {
    "s": "SSEAU",
    "n": "Starry Sea Acquisition Corp - Unit"
  },
  {
    "s": "SSII",
    "n": "SS Innovations International Inc. - Common Stock"
  },
  {
    "s": "SSL",
    "n": "Sasol Ltd. American Depositary Shares"
  },
  {
    "s": "SSM",
    "n": "Sono Group N.V. - Ordinary Shares"
  },
  {
    "s": "SSMR",
    "n": "Sunshine Silver Mining & Refining Company Common Stock"
  },
  {
    "s": "SSNC",
    "n": "SS&C Technologies Holdings, Inc. - Common Stock"
  },
  {
    "s": "SSP",
    "n": "E.W. Scripps Company (The) - Class A Common Stock"
  },
  {
    "s": "SSRM",
    "n": "SSR Mining Inc. - Common Stock"
  },
  {
    "s": "SST",
    "n": "System1, Inc. Class A Common Stock"
  },
  {
    "s": "SSTI",
    "n": "SoundThinking, Inc. - Common Stock"
  },
  {
    "s": "SSTK",
    "n": "Shutterstock, Inc. Common Stock"
  },
  {
    "s": "SSYS",
    "n": "Stratasys, Ltd. - Common Stock"
  },
  {
    "s": "ST",
    "n": "Sensata Technologies Holding plc Ordinary Shares"
  },
  {
    "s": "STAA",
    "n": "STAAR Surgical Company - Common Stock"
  },
  {
    "s": "STAG",
    "n": "Stag Industrial, Inc. Common Stock"
  },
  {
    "s": "STAK",
    "n": "STAK Inc. - Class A Ordinary Shares"
  },
  {
    "s": "STBA",
    "n": "S&T Bancorp, Inc. - Common Stock"
  },
  {
    "s": "STC",
    "n": "Stewart Information Services Corporation Common Stock"
  },
  {
    "s": "STDN",
    "n": "Standard Nuclear, Inc. Class A Common Stock"
  },
  {
    "s": "STE",
    "n": "STERIS plc (Ireland) Ordinary Shares"
  },
  {
    "s": "STEM",
    "n": "Stem, Inc. Class A Common Stock"
  },
  {
    "s": "STEP",
    "n": "StepStone Group Inc. - Class A Common Stock"
  },
  {
    "s": "STEX",
    "n": "Streamex Corp. - Common Stock"
  },
  {
    "s": "STFS",
    "n": "Star Fashion Culture Holdings Limited - Class A Ordinary Shares"
  },
  {
    "s": "STG",
    "n": "Sunlands Technology Group American Depositary Shares, representing Class A ordinary shares"
  },
  {
    "s": "STGW",
    "n": "Stagwell Inc. - Class A Common Stock"
  },
  {
    "s": "STHO",
    "n": "Star Holdings - Shares of Beneficial Interest"
  },
  {
    "s": "STI",
    "n": "Solidion Technology, Inc. - Common Stock"
  },
  {
    "s": "STIM",
    "n": "Neuronetics, Inc. - Common Stock"
  },
  {
    "s": "STKE",
    "n": "Sol Strategies Inc. - Common Shares"
  },
  {
    "s": "STKH",
    "n": "Steakholder Foods Ltd. - American Depositary Shares"
  },
  {
    "s": "STKS",
    "n": "The ONE Group Hospitality, Inc. - Common Stock"
  },
  {
    "s": "STLA",
    "n": "Stellantis N.V. Common Shares"
  },
  {
    "s": "STLD",
    "n": "Steel Dynamics, Inc. - Common Stock"
  },
  {
    "s": "STLN",
    "n": "Starling Oncology, Inc. - Common Stock"
  },
  {
    "s": "STM",
    "n": "STMicroelectronics N.V. Common Stock"
  },
  {
    "s": "STN",
    "n": "Stantec Inc Common Stock"
  },
  {
    "s": "STNE",
    "n": "StoneCo Ltd. - Class A Common Share"
  },
  {
    "s": "STNG",
    "n": "Scorpio Tankers Inc. Common Shares"
  },
  {
    "s": "STOK",
    "n": "Stoke Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "STRA",
    "n": "Strategic Education, Inc. - Common Stock"
  },
  {
    "s": "STRL",
    "n": "Sterling Infrastructure, Inc. - Common Stock"
  },
  {
    "s": "STRO",
    "n": "Sutro Biopharma, Inc. - Common Stock"
  },
  {
    "s": "STRR",
    "n": "Star Equity Holdings, Inc. - Common Stock"
  },
  {
    "s": "STRT",
    "n": "STRATTEC SECURITY CORPORATION - Common Stock"
  },
  {
    "s": "STRZ",
    "n": "Starz Entertainment Corp. - Common Shares"
  },
  {
    "s": "STT",
    "n": "State Street Corporation Common Stock"
  },
  {
    "s": "STTK",
    "n": "Shattuck Labs, Inc. - Common Stock"
  },
  {
    "s": "STUB",
    "n": "StubHub Holdings, Inc. Class A Common Stock"
  },
  {
    "s": "STVN",
    "n": "Stevanato Group S.p.A. Ordinary Shares"
  },
  {
    "s": "STWD",
    "n": "STARWOOD PROPERTY TRUST, INC. Starwood Property Trust Inc."
  },
  {
    "s": "STX",
    "n": "Seagate Technology Holdings PLC - Ordinary Shares (Ireland)"
  },
  {
    "s": "STXS",
    "n": "Stereotaxis, Inc. Common Stock"
  },
  {
    "s": "STZ",
    "n": "Constellation Brands, Inc. Common Stock"
  },
  {
    "s": "SU",
    "n": "Suncor Energy  Inc. Common Stock"
  },
  {
    "s": "SUGP",
    "n": "SU Group Holdings Limited - Class A Ordinary Shares"
  },
  {
    "s": "SUI",
    "n": "Sun Communities, Inc. Common Stock"
  },
  {
    "s": "SUIG",
    "n": "Sui Group Holdings Limited - Common Stock"
  },
  {
    "s": "SUJA",
    "n": "Suja Life, Inc. - Class A Common Stock"
  },
  {
    "s": "SUMA",
    "n": "SUMA Acquisition Corporation - Class A Ordinary Shares"
  },
  {
    "s": "SUMAU",
    "n": "SUMA Acquisition Corporation - Units"
  },
  {
    "s": "SUNB",
    "n": "Sunbelt Rentals Holdings, Inc. Common Stock"
  },
  {
    "s": "SUNC",
    "n": "SunocoCorp LLC Common Units, representing limited liability company interests"
  },
  {
    "s": "SUNE",
    "n": "SUNation Energy, Inc. - Common Stock"
  },
  {
    "s": "SUNS",
    "n": "Sunrise Realty Trust, Inc. - Common Stock"
  },
  {
    "s": "SUPN",
    "n": "Supernus Pharmaceuticals, Inc. - Common Stock"
  },
  {
    "s": "SUPV",
    "n": "Grupo Supervielle S.A. American Depositary Shares each Representing five Class B shares"
  },
  {
    "s": "SUPX",
    "n": "SuperX AI Technology Limited - Ordinary Shares"
  },
  {
    "s": "SURG",
    "n": "SurgePays, Inc. - Common Stock"
  },
  {
    "s": "SUZ",
    "n": "Suzano S.A. American Depositary Shares (each representing One Ordinary Share)"
  },
  {
    "s": "SVA",
    "n": "Sinovac Biotech, Ltd. - Ordinary Shares (Antigua/Barbudo)"
  },
  {
    "s": "SVAQ",
    "n": "Silicon Valley Acquisition Corp. - Class A Ordinary Shares"
  },
  {
    "s": "SVAQU",
    "n": "Silicon Valley Acquisition Corp. - Units"
  },
  {
    "s": "SVAQW",
    "n": "Silicon Valley Acquisition Corp. - Warrants"
  },
  {
    "s": "SVC",
    "n": "Service Properties Trust - Common Shares of Beneficial Interest"
  },
  {
    "s": "SVCC",
    "n": "Stellar V Capital Corp. - Class A Ordinary Shares"
  },
  {
    "s": "SVCCU",
    "n": "Stellar V Capital Corp. - Unit"
  },
  {
    "s": "SVCO",
    "n": "Silvaco Group, Inc. - Common Stock"
  },
  {
    "s": "SVIA",
    "n": "Silvia, Inc. - Common Stock"
  },
  {
    "s": "SVIV",
    "n": "Spring Valley Acquisition Corp. IV - Class A Ordinary Shares"
  },
  {
    "s": "SVIVU",
    "n": "Spring Valley Acquisition Corp. IV - Units"
  },
  {
    "s": "SVIVW",
    "n": "Spring Valley Acquisition Corp. IV - Warrants"
  },
  {
    "s": "SVM",
    "n": "Silvercorp Metals Inc. Common Shares"
  },
  {
    "s": "SVRA",
    "n": "Savara, Inc. - Common Stock"
  },
  {
    "s": "SVRE",
    "n": "SaverOne 2014 Ltd. - American Depositary Shares"
  },
  {
    "s": "SVRN",
    "n": "SVRN, Inc. - Common Stock"
  },
  {
    "s": "SVV",
    "n": "Savers Value Village, Inc. Common Stock"
  },
  {
    "s": "SW",
    "n": "Smurfit WestRock plc Ordinary Shares"
  },
  {
    "s": "SWAG",
    "n": "Stran & Company, Inc. - Common Stock"
  },
  {
    "s": "SWBI",
    "n": "Smith & Wesson Brands, Inc. - Common Stock"
  },
  {
    "s": "SWIM",
    "n": "Latham Group, Inc. - Common Stock"
  },
  {
    "s": "SWK",
    "n": "Stanley Black & Decker, Inc. Common Stock"
  },
  {
    "s": "SWKHL",
    "n": "SWK Holdings Corporation - 9.00% Senior Notes due 2027"
  },
  {
    "s": "SWKS",
    "n": "Skyworks Solutions, Inc. - Common Stock"
  },
  {
    "s": "SWMR",
    "n": "Swarmer, Inc - common stock"
  },
  {
    "s": "SWRD",
    "n": "Stewards Inc - Common Stock"
  },
  {
    "s": "SWVL",
    "n": "Swvl Holdings Corp - Ordinary Shares"
  },
  {
    "s": "SWX",
    "n": "Southwest Gas Holdings, Inc. Common Stock (DE)"
  },
  {
    "s": "SXC",
    "n": "SunCoke Energy, Inc. Common Stock"
  },
  {
    "s": "SXI",
    "n": "Standex International Corporation Common Stock"
  },
  {
    "s": "SXT",
    "n": "Sensient Technologies Corporation Common Stock"
  },
  {
    "s": "SXTC",
    "n": "China SXT Pharmaceuticals, Inc. - Class A Ordinary Shares"
  },
  {
    "s": "SXTP",
    "n": "60 Degrees Pharmaceuticals, Inc. - Common Stock"
  },
  {
    "s": "SY",
    "n": "So-Young International Inc. - American Depository Shares"
  },
  {
    "s": "SYBT",
    "n": "Stock Yards Bancorp, Inc. - Common Stock"
  },
  {
    "s": "SYF",
    "n": "Synchrony Financial Common Stock"
  },
  {
    "s": "SYK",
    "n": "Stryker Corporation Common Stock"
  },
  {
    "s": "SYM",
    "n": "Symbotic Inc. - Class A Common Stock"
  },
  {
    "s": "SYNA",
    "n": "Synaptics Incorporated - Common Stock"
  },
  {
    "s": "SYNX",
    "n": "Silynxcom Ltd. Ordinary Shares"
  },
  {
    "s": "SYPR",
    "n": "Sypris Solutions, Inc. - Common Stock"
  },
  {
    "s": "SYRE",
    "n": "Spyre Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "SYY",
    "n": "Sysco Corporation Common Stock"
  },
  {
    "s": "SZZL",
    "n": "Sizzle Acquisition Corp. II - Class A ordinary shares"
  },
  {
    "s": "SZZLR",
    "n": "Sizzle Acquisition Corp. II - Right"
  },
  {
    "s": "SZZLU",
    "n": "Sizzle Acquisition Corp. II - Unit"
  },
  {
    "s": "T",
    "n": "AT&T Inc."
  },
  {
    "s": "TAC",
    "n": "TransAlta Corporation Ordinary Shares"
  },
  {
    "s": "TACH",
    "n": "Titan Acquisition Corp. - Class A Ordinary Shares"
  },
  {
    "s": "TACHU",
    "n": "Titan Acquisition Corp. - Units"
  },
  {
    "s": "TACHW",
    "n": "Titan Acquisition Corp. - Warrants"
  },
  {
    "s": "TACO",
    "n": "Berto Acquisition Corp. - Ordinary Shares"
  },
  {
    "s": "TACOU",
    "n": "Berto Acquisition Corp. - unit"
  },
  {
    "s": "TACT",
    "n": "TransAct Technologies Incorporated - Common Stock"
  },
  {
    "s": "TAK",
    "n": "Takeda Pharmaceutical Company Limited American Depositary Shares (each representing 1/2 of a share of Common Stock)"
  },
  {
    "s": "TAL",
    "n": "TAL Education Group American Depositary Shares"
  },
  {
    "s": "TALO",
    "n": "Talos Energy, Inc. Common Stock"
  },
  {
    "s": "TANH",
    "n": "Tantech Holdings Ltd. - Class A Common Shares"
  },
  {
    "s": "TAOP",
    "n": "Taoping Inc. - Ordinary Shares"
  },
  {
    "s": "TAOX",
    "n": "Tao Synergies Inc. - Common Stock"
  },
  {
    "s": "TAP",
    "n": "Molson Coors Beverage Company Class B Common Stock"
  },
  {
    "s": "TAP-A",
    "n": "Molson Coors Beverage Company Class A Common Stock"
  },
  {
    "s": "TARA",
    "n": "Protara Therapeutics, Inc.  - Common Stock"
  },
  {
    "s": "TARS",
    "n": "Tarsus Pharmaceuticals, Inc. - Common Stock"
  },
  {
    "s": "TASK",
    "n": "TaskUs, Inc. - Class A Common Stock"
  },
  {
    "s": "TATT",
    "n": "TAT Technologies Ltd. - Ordinary Shares"
  },
  {
    "s": "TAVI",
    "n": "Tavia Acquisition Corp. - Ordinary Shares"
  },
  {
    "s": "TAVIR",
    "n": "Tavia Acquisition Corp. - Right"
  },
  {
    "s": "TAVIU",
    "n": "Tavia Acquisition Corp. - Unit"
  },
  {
    "s": "TAYD",
    "n": "Taylor Devices, Inc. - Common Stock"
  },
  {
    "s": "TBB",
    "n": "AT&T Inc. 5.350% Global Notes due 2066"
  },
  {
    "s": "TBBB",
    "n": "BBB Foods Inc. Class A Common Shares"
  },
  {
    "s": "TBBK",
    "n": "The Bancorp, Inc. - Common Stock"
  },
  {
    "s": "TBCH",
    "n": "Turtle Beach Corporation - Common Stock"
  },
  {
    "s": "TBCV",
    "n": "Thunder Bridge Capital Partners V, Ltd. - Class A Ordinary Shares"
  },
  {
    "s": "TBCVU",
    "n": "Thunder Bridge Capital Partners V, Ltd. - Units"
  },
  {
    "s": "TBCVW",
    "n": "Thunder Bridge Capital Partners V, Ltd. - Warrants"
  },
  {
    "s": "TBI",
    "n": "TrueBlue, Inc. Common Stock"
  },
  {
    "s": "TBLA",
    "n": "Taboola.com Ltd. - Ordinary Shares"
  },
  {
    "s": "TBN",
    "n": "Tamboran Resources Corporation Common stock"
  },
  {
    "s": "TC",
    "n": "Token Cat Limited - American Depositary Shares"
  },
  {
    "s": "TCBI",
    "n": "Texas Capital Bancshares, Inc. Common Stock"
  },
  {
    "s": "TCBK",
    "n": "TriCo Bancshares - Common Stock"
  },
  {
    "s": "TCBS",
    "n": "Texas Community Bancshares, Inc. - Common Stock"
  },
  {
    "s": "TCBX",
    "n": "Third Coast Bancshares, Inc. Common Stock"
  },
  {
    "s": "TCGX",
    "n": "TCGX Acquisition Corp. - Class A Ordinary Shares"
  },
  {
    "s": "TCI",
    "n": "Transcontinental Realty Investors, Inc. Common Stock"
  },
  {
    "s": "TCMD",
    "n": "Tactile Systems Technology, Inc. - Common Stock"
  },
  {
    "s": "TCOM",
    "n": "Trip.com Group Limited - American Depositary Shares"
  },
  {
    "s": "TCPA",
    "n": "TransCanada PipeLines Limited 6.250% Junior Subordinated Notes due 2085"
  },
  {
    "s": "TCRT",
    "n": "Alaunos Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "TCRX",
    "n": "TScan Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "TCX",
    "n": "Tucows Inc. - Common Stock"
  },
  {
    "s": "TD",
    "n": "Toronto Dominion Bank (The) Common Stock"
  },
  {
    "s": "TDAC",
    "n": "Translational Development Acquisition Corp. - Ordinary Shares"
  },
  {
    "s": "TDACU",
    "n": "Translational Development Acquisition Corp. - Units"
  },
  {
    "s": "TDACW",
    "n": "Translational Development Acquisition Corp. - Warrants"
  },
  {
    "s": "TDAY",
    "n": "USA TODAY Co., Inc. Common Stock"
  },
  {
    "s": "TDC",
    "n": "Teradata Corporation Common Stock"
  },
  {
    "s": "TDG",
    "n": "Transdigm Group Incorporated Common Stock"
  },
  {
    "s": "TDIC",
    "n": "Dreamland Limited - Class A Ordinary Shares"
  },
  {
    "s": "TDOC",
    "n": "Teladoc Health, Inc. Common Stock"
  },
  {
    "s": "TDS",
    "n": "Telephone and Data Systems, Inc. Common Shares"
  },
  {
    "s": "TDTH",
    "n": "Trident Digital Tech Holdings Ltd - Class B Ordinary Shares"
  },
  {
    "s": "TDUP",
    "n": "ThredUp Inc. - Class A Common Stock"
  },
  {
    "s": "TDW",
    "n": "Tidewater Inc. Common Stock"
  },
  {
    "s": "TDWD",
    "n": "Tailwind 2.0 Acquisition Corp. - Class A Ordinary Shares"
  },
  {
    "s": "TDWDU",
    "n": "Tailwind 2.0 Acquisition Corp. - Unit"
  },
  {
    "s": "TDY",
    "n": "Teledyne Technologies Incorporated Common Stock"
  },
  {
    "s": "TE",
    "n": "T1 Energy Inc. Common Stock"
  },
  {
    "s": "TEAD",
    "n": "Teads Holding Co. - Common Stock"
  },
  {
    "s": "TEAM",
    "n": "Atlassian Corporation  - Class A Common Stock"
  },
  {
    "s": "TECH",
    "n": "Bio-Techne Corp - Common Stock"
  },
  {
    "s": "TECK",
    "n": "Teck Resources Ltd Ordinary Shares"
  },
  {
    "s": "TECX",
    "n": "Tectonic Therapeutic, Inc. - Common Stock"
  },
  {
    "s": "TEL",
    "n": "TE Connectivity plc Ordinary Shares"
  },
  {
    "s": "TELA",
    "n": "TELA Bio, Inc. - Common stock"
  },
  {
    "s": "TELO",
    "n": "Telomir Pharmaceuticals, Inc. - Common Stock"
  },
  {
    "s": "TEM",
    "n": "Tempus AI, Inc. - Class A Common Stock"
  },
  {
    "s": "TEN",
    "n": "Tsakos Energy Navigation Ltd Common Shares"
  },
  {
    "s": "TENB",
    "n": "Tenable Holdings, Inc. - Common Stock"
  },
  {
    "s": "TENX",
    "n": "Tenax Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "TEO",
    "n": "Telecom Argentina SA"
  },
  {
    "s": "TER",
    "n": "Teradyne, Inc. - Common Stock"
  },
  {
    "s": "TEVA",
    "n": "Teva Pharmaceutical Industries Limited Ordinary Shares"
  },
  {
    "s": "TEX",
    "n": "Terex Corporation Common Stock"
  },
  {
    "s": "TFC",
    "n": "Truist Financial Corporation Common Stock"
  },
  {
    "s": "TFII",
    "n": "TFI International Inc. Common Shares"
  },
  {
    "s": "TFIN",
    "n": "Triumph Financial, Inc. Common Stock"
  },
  {
    "s": "TFPM",
    "n": "Triple Flag Precious Metals Corp. Common Shares"
  },
  {
    "s": "TFSL",
    "n": "TFS Financial Corporation - Common Stock"
  },
  {
    "s": "TFX",
    "n": "Teleflex Incorporated Common Stock"
  },
  {
    "s": "TG",
    "n": "Tredegar Corporation Common Stock"
  },
  {
    "s": "TGB",
    "n": "Trekor Metals Limited Common Shares"
  },
  {
    "s": "TGE",
    "n": "The Generation Essentials Group Class A Ordinary Shares"
  },
  {
    "s": "TGEN",
    "n": "Tecogen Inc. Common Stock"
  },
  {
    "s": "TGHL",
    "n": "The GrowHub Limited - Class A Ordinary Shares"
  },
  {
    "s": "TGL",
    "n": "Treasure Global Inc. - Common Stock"
  },
  {
    "s": "TGLS",
    "n": "Tecnoglass Holdings Inc. Common Stock"
  },
  {
    "s": "TGS",
    "n": "Transportadora de Gas del Sur SA TGS Common Stock"
  },
  {
    "s": "TGT",
    "n": "Target Corporation Common Stock"
  },
  {
    "s": "TGTX",
    "n": "TG Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "TH",
    "n": "Target Hospitality Corp. - Common Stock"
  },
  {
    "s": "THC",
    "n": "Tenet Healthcare Corporation Common Stock"
  },
  {
    "s": "THCH",
    "n": "TH International Limited - Ordinary shares"
  },
  {
    "s": "THEO",
    "n": "BOA Acquisition Corp. II - Class A Ordinary Shares"
  },
  {
    "s": "THEOU",
    "n": "BOA Acquisition Corp. II - Units"
  },
  {
    "s": "THFF",
    "n": "First Financial Corporation  - Common Stock"
  },
  {
    "s": "THG",
    "n": "Hanover Insurance Group Inc"
  },
  {
    "s": "THH",
    "n": "TryHard Holdings Limited - Ordinary Shares"
  },
  {
    "s": "THM",
    "n": "International Tower Hill Mines, Ltd. Ordinary Shares (Canada)"
  },
  {
    "s": "THO",
    "n": "Thor Industries, Inc. Common Stock"
  },
  {
    "s": "THRM",
    "n": "Gentherm Inc - Common Stock"
  },
  {
    "s": "THRY",
    "n": "Thryv Holdings, Inc. - Common Stock"
  },
  {
    "s": "TIC",
    "n": "TIC Solutions, Inc. Common Stock"
  },
  {
    "s": "TIGO",
    "n": "Millicom International Cellular S.A. - Common Stock"
  },
  {
    "s": "TIGR",
    "n": "UP Fintech Holding Limited - American Depositary Shares representing fifteen Class A Ordinary Shares"
  },
  {
    "s": "TII",
    "n": "Titan Mining Corporation Common Shares"
  },
  {
    "s": "TIL",
    "n": "Instil Bio, Inc. - Common Stock"
  },
  {
    "s": "TILE",
    "n": "Interface, Inc. - Common Stock"
  },
  {
    "s": "TIMB",
    "n": "TIM S.A. American Depositary Shares (Each representing 5 Common Shares) "
  },
  {
    "s": "TIPT",
    "n": "Tiptree Inc. - Common Stock"
  },
  {
    "s": "TISI",
    "n": "Team, Inc. Common Stock"
  },
  {
    "s": "TITN",
    "n": "Titan Machinery Inc. - Common Stock"
  },
  {
    "s": "TJGC",
    "n": "TJGC Group Limited - Class A Ordinary Shares"
  },
  {
    "s": "TJX",
    "n": "TJX Companies, Inc. (The) Common Stock"
  },
  {
    "s": "TK",
    "n": "Teekay Corporation Ltd. Common Stock"
  },
  {
    "s": "TKC",
    "n": "Turkcell Iletisim Hizmetleri AS Common Stock"
  },
  {
    "s": "TKLF",
    "n": "Tokyo Lifestyle Co., Ltd. - American Depositary Shares"
  },
  {
    "s": "TKNO",
    "n": "Alpha Teknova, Inc. - Common Stock"
  },
  {
    "s": "TKO",
    "n": "TKO Group Holdings, Inc. Class A Common Stock"
  },
  {
    "s": "TKR",
    "n": "Timken Company (The) Common Stock"
  },
  {
    "s": "TLAC",
    "n": "Three Lions Acquisition Corp. - Ordinary Shares"
  },
  {
    "s": "TLACU",
    "n": "Three Lions Acquisition Corp. - Units"
  },
  {
    "s": "TLACW",
    "n": "Three Lions Acquisition Corp. - Warrants"
  },
  {
    "s": "TLF",
    "n": "Tandy Leather Factory, Inc. - common stock"
  },
  {
    "s": "TLIH",
    "n": "Ten-League International Holdings Limited - Ordinary Shares"
  },
  {
    "s": "TLK",
    "n": "PT Telekomunikasi Indonesia, Tbk"
  },
  {
    "s": "TLN",
    "n": "Talen Energy Corporation - Common Stock"
  },
  {
    "s": "TLNC",
    "n": "Talon Capital Corp. - Class A Ordinary Shares"
  },
  {
    "s": "TLNCU",
    "n": "Talon Capital Corp. - Units"
  },
  {
    "s": "TLNCW",
    "n": "Talon Capital Corp. - Warrants"
  },
  {
    "s": "TLPH",
    "n": "Talphera, Inc. - Common Stock"
  },
  {
    "s": "TLRY",
    "n": "Tilray Brands, Inc. - Common Stock"
  },
  {
    "s": "TLS",
    "n": "Telos Corporation - Common Stock"
  },
  {
    "s": "TLSA",
    "n": "Tiziana Life Sciences Ltd - Common Shares"
  },
  {
    "s": "TLSI",
    "n": "TriSalus Life Sciences, Inc. - Common Stock"
  },
  {
    "s": "TLX",
    "n": "Telix Pharmaceuticals Limited - American Depositary Shares"
  },
  {
    "s": "TLYS",
    "n": "Tilly's, Inc. Common Stock"
  },
  {
    "s": "TM",
    "n": "Toyota Motor Corporation Common Stock"
  },
  {
    "s": "TMC",
    "n": "TMC the metals company Inc. - Common Stock"
  },
  {
    "s": "TMCI",
    "n": "Treace Medical Concepts, Inc. - Common Stock"
  },
  {
    "s": "TMCR",
    "n": "The Metals Royalty Company Inc. - Common Stock"
  },
  {
    "s": "TMDE",
    "n": "TMD Energy Limited Ordinary Shares"
  },
  {
    "s": "TMDX",
    "n": "TransMedics Group, Inc. - Common Stock"
  },
  {
    "s": "TME",
    "n": "Tencent Music Entertainment Group American Depositary Shares, each representing two Class A Ordinary Shares"
  },
  {
    "s": "TMO",
    "n": "Thermo Fisher Scientific Inc Common Stock"
  },
  {
    "s": "TMP",
    "n": "Tompkins Financial Corporation Common Stock"
  },
  {
    "s": "TMQ",
    "n": "Trilogy Metals Inc. Common Stock"
  },
  {
    "s": "TMS",
    "n": "Teamshares Inc. - Common Stock"
  },
  {
    "s": "TMSWW",
    "n": "Teamshares Inc. - Warrants"
  },
  {
    "s": "TMTS",
    "n": "Spartacus Acquisition Corp. II - Class A Ordinary Shares"
  },
  {
    "s": "TMTSU",
    "n": "Spartacus Acquisition Corp. II - Unit"
  },
  {
    "s": "TMTSW",
    "n": "Spartacus Acquisition Corp. II - Warrants"
  },
  {
    "s": "TMUS",
    "n": "T-Mobile US, Inc. - Common Stock"
  },
  {
    "s": "TMUSI",
    "n": "T-Mobile US, Inc. - 5.500% Senior Notes due June 2070"
  },
  {
    "s": "TMUSL",
    "n": "T-Mobile US, Inc. - 6.250% Senior Notes due 2069"
  },
  {
    "s": "TMUSZ",
    "n": "T-Mobile US, Inc. - 5.500% Senior Notes due March 2070"
  },
  {
    "s": "TNC",
    "n": "Tennant Company Common Stock"
  },
  {
    "s": "TNDM",
    "n": "Tandem Diabetes Care, Inc. - Common Stock"
  },
  {
    "s": "TNET",
    "n": "TriNet Group, Inc. Common Stock"
  },
  {
    "s": "TNGX",
    "n": "Tango Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "TNK",
    "n": "Teekay Tankers Ltd."
  },
  {
    "s": "TNL",
    "n": "Travel   Leisure Co. Common  Stock"
  },
  {
    "s": "TNMG",
    "n": "TNL Mediagene - Ordinary Shares"
  },
  {
    "s": "TNON",
    "n": "Tenon Medical, Inc. - Common Stock"
  },
  {
    "s": "TNXP",
    "n": "Tonix Pharmaceuticals Holding Corp. - Common Stock"
  },
  {
    "s": "TNYA",
    "n": "Tenaya Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "TOL",
    "n": "Toll Brothers, Inc. Common Stock"
  },
  {
    "s": "TOMZ",
    "n": "TOMI Environmental Solutions, Inc. - Common Stock"
  },
  {
    "s": "TONT",
    "n": "Graf Global Corp. Class A ordinary shares"
  },
  {
    "s": "TONX",
    "n": "TON Strategy Company - Common Stock"
  },
  {
    "s": "TOON",
    "n": "Kartoon Studios, Inc. Common Stock"
  },
  {
    "s": "TOP",
    "n": "TOP Financial Group Limited - Class A Ordinary Shares"
  },
  {
    "s": "TOPP",
    "n": "Toppoint Holdings Inc. Common Stock"
  },
  {
    "s": "TOPS",
    "n": "TOP Ships, Inc. Common Stock"
  },
  {
    "s": "TORO",
    "n": "Toro Corp. - Common Shares"
  },
  {
    "s": "TOST",
    "n": "Toast, Inc. Class A Common Stock"
  },
  {
    "s": "TOUR",
    "n": "Tuniu Corporation - American Depositary Shares"
  },
  {
    "s": "TOVX",
    "n": "Theriva Biologics, Inc. Common Stock"
  },
  {
    "s": "TOWN",
    "n": "Towne Bank - Common Stock"
  },
  {
    "s": "TOYO",
    "n": "TOYO Co., Ltd - Ordinary Shares"
  },
  {
    "s": "TP",
    "n": "Ticketplus Ltd. Ordinary Shares"
  },
  {
    "s": "TPB",
    "n": "Turning Point Brands, Inc. Common Stock"
  },
  {
    "s": "TPC",
    "n": "Tutor Perini Corporation Common Stock"
  },
  {
    "s": "TPCS",
    "n": "TechPrecision Corporation - Common stock"
  },
  {
    "s": "TPET",
    "n": "Trio Petroleum Corp. Common Stock"
  },
  {
    "s": "TPG",
    "n": "TPG Inc. - Class A Common Stock"
  },
  {
    "s": "TPGXL",
    "n": "TPG Inc. - 6.950% Fixed-Rate Junior Subordinated Notes due 2064"
  },
  {
    "s": "TPL",
    "n": "Texas Pacific Land Corporation Common Stock"
  },
  {
    "s": "TPR",
    "n": "Tapestry, Inc. Common Stock"
  },
  {
    "s": "TPST",
    "n": "Tempest Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "TPTS",
    "n": "Terra Property Trust, Inc. 7.00% Senior Secured Notes due 2029"
  },
  {
    "s": "TPVG",
    "n": "TriplePoint Venture Growth BDC Corp. Common Stock"
  },
  {
    "s": "TR",
    "n": "Tootsie Roll Industries, Inc. Common Stock"
  },
  {
    "s": "TRAD",
    "n": "APEX Tech Acquisition Inc. Ordinary Shares"
  },
  {
    "s": "TRAD-U",
    "n": "APEX Tech Acquisition Inc. Units, each consisting of one Class A ordinary share and one right to receive one sixth (1/6) of a Class A ordinary share"
  },
  {
    "s": "TRAK",
    "n": "ReposiTrak, Inc. Common Stock"
  },
  {
    "s": "TRAW",
    "n": "Traws Pharma, Inc. - Common Stock"
  },
  {
    "s": "TRAX",
    "n": "First Tracks Biotherapeutics, Inc. - Ordinary Shares"
  },
  {
    "s": "TRBG",
    "n": "TurboGen Ltd. - Ordinary Shares"
  },
  {
    "s": "TRC",
    "n": "Tejon Ranch Co Common Stock"
  },
  {
    "s": "TRDA",
    "n": "Entrada Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "TREE",
    "n": "LendingTree, Inc. - Common Stock"
  },
  {
    "s": "TREO",
    "n": "Tactical Resources Corp. - Common Shares"
  },
  {
    "s": "TREX",
    "n": "Trex Company, Inc. Common Stock"
  },
  {
    "s": "TRGP",
    "n": "Targa Resources, Inc. Common Stock"
  },
  {
    "s": "TRGS",
    "n": "TRG Latin America Acquisitions Corp. - Class A Ordinary Shares"
  },
  {
    "s": "TRGSU",
    "n": "TRG Latin America Acquisitions Corp. - Units"
  },
  {
    "s": "TRI",
    "n": "Thomson Reuters Corp - Common Shares"
  },
  {
    "s": "TRIB",
    "n": "Trinity Biotech plc - American Depositary Shares"
  },
  {
    "s": "TRIN",
    "n": "Trinity Capital Inc. Common Stock"
  },
  {
    "s": "TRIP",
    "n": "TripAdvisor, Inc. - Common Stock"
  },
  {
    "s": "TRLV",
    "n": "Trulieve Cannabis Corp. Subordinate Voting Shares"
  },
  {
    "s": "TRMB",
    "n": "Trimble Inc. - Common Stock"
  },
  {
    "s": "TRMD",
    "n": "TORM plc - Class A Common Stock"
  },
  {
    "s": "TRMK",
    "n": "Trustmark Corporation - Common Stock"
  },
  {
    "s": "TRN",
    "n": "Trinity Industries, Inc. Common Stock"
  },
  {
    "s": "TRNI",
    "n": "Trinity Capital Inc. 7.875% Notes Due 2029"
  },
  {
    "s": "TRNO",
    "n": "Terreno Realty Corporation Common Stock"
  },
  {
    "s": "TRNR",
    "n": "Interactive Strength Inc. - Common Stock"
  },
  {
    "s": "TRNS",
    "n": "Transcat, Inc. - Common Stock"
  },
  {
    "s": "TRNZ",
    "n": "Trinity Capital Inc. 7.875% Notes due 2029"
  },
  {
    "s": "TRON",
    "n": "Tron Inc. - Common Stock"
  },
  {
    "s": "TROO",
    "n": "TROOPS, Inc.  - Ordinary Shares"
  },
  {
    "s": "TROW",
    "n": "T. Rowe Price Group, Inc. - Common Stock"
  },
  {
    "s": "TROX",
    "n": "Tronox Holdings plc Ordinary Shares (UK)"
  },
  {
    "s": "TRP",
    "n": "TC Energy Corporation Common Stock"
  },
  {
    "s": "TRS",
    "n": "TriMas Corporation - Common Stock"
  },
  {
    "s": "TRSG",
    "n": "Tungray Technologies Inc - Class A Ordinary Shares"
  },
  {
    "s": "TRST",
    "n": "TrustCo Bank Corp NY - Common Stock"
  },
  {
    "s": "TRT",
    "n": "Trio-Tech International - Common Stock"
  },
  {
    "s": "TRTX",
    "n": "TPG RE Finance Trust, Inc. Common Stock"
  },
  {
    "s": "TRU",
    "n": "TransUnion Common Stock"
  },
  {
    "s": "TRUG",
    "n": "TruGolf Holdings, Inc. - Class A Common Stock"
  },
  {
    "s": "TRUP",
    "n": "Trupanion, Inc. - Common Stock"
  },
  {
    "s": "TRV",
    "n": "The Travelers Companies, Inc. Common Stock"
  },
  {
    "s": "TRVG",
    "n": "trivago N.V. - American Depositary Shares"
  },
  {
    "s": "TRVI",
    "n": "Trevi Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "TRX",
    "n": "TRX Gold Corporation Common Stock"
  },
  {
    "s": "TRXB",
    "n": "TRex Bio, Inc. - Common stock"
  },
  {
    "s": "TS",
    "n": "Tenaris S.A. American Depositary Shares"
  },
  {
    "s": "TSAT",
    "n": "Telesat Corporation - Class A Common Shares and Class B Variable Voting Shares"
  },
  {
    "s": "TSBK",
    "n": "Timberland Bancorp, Inc. - Common Stock"
  },
  {
    "s": "TSCO",
    "n": "Tractor Supply Company - Common Stock"
  },
  {
    "s": "TSEM",
    "n": "Tower Semiconductor Ltd. - Ordinary Shares"
  },
  {
    "s": "TSHA",
    "n": "Taysha Gene Therapies, Inc. - Common Stock"
  },
  {
    "s": "TSLA",
    "n": "Tesla, Inc.  - Common Stock"
  },
  {
    "s": "TSLX",
    "n": "Sixth Street Specialty Lending, Inc. Common Stock"
  },
  {
    "s": "TSM",
    "n": "Taiwan Semiconductor Manufacturing Company Ltd."
  },
  {
    "s": "TSN",
    "n": "Tyson Foods, Inc. Common Stock"
  },
  {
    "s": "TSQ",
    "n": "Townsquare Media, Inc. Class A Common Stock"
  },
  {
    "s": "TSSI",
    "n": "TSS, Inc. - Common Stock"
  },
  {
    "s": "TT",
    "n": "Trane Technologies plc"
  },
  {
    "s": "TTAM",
    "n": "Titan America SA Common Shares"
  },
  {
    "s": "TTAN",
    "n": "ServiceTitan, Inc. - Class A Common Stock"
  },
  {
    "s": "TTC",
    "n": "Toro Company (The) Common Stock"
  },
  {
    "s": "TTD",
    "n": "The Trade Desk, Inc. - Class A Common Stock"
  },
  {
    "s": "TTE",
    "n": "TotalEnergies SE Ordinary Shares"
  },
  {
    "s": "TTEC",
    "n": "TTEC Holdings, Inc. - Common Stock"
  },
  {
    "s": "TTEK",
    "n": "Tetra Tech, Inc. - Common Stock"
  },
  {
    "s": "TTGT",
    "n": "TechTarget, Inc. - Common Stock"
  },
  {
    "s": "TTI",
    "n": "Tetra Technologies, Inc. Common Stock"
  },
  {
    "s": "TTMI",
    "n": "TTM Technologies, Inc. - Common Stock"
  },
  {
    "s": "TTRX",
    "n": "Turn Therapeutics Inc. - Common Stock"
  },
  {
    "s": "TTWO",
    "n": "Take-Two Interactive Software, Inc. - Common Stock"
  },
  {
    "s": "TU",
    "n": "Telus Corporation Ordinary Shares"
  },
  {
    "s": "TULP",
    "n": "Bloomia Holdings, Inc. - Common Stock"
  },
  {
    "s": "TURB",
    "n": "Turbo Energy, S.A. - American Depositary Shares"
  },
  {
    "s": "TUSK",
    "n": "Mammoth Energy Services, Inc. - Common Stock"
  },
  {
    "s": "TUYA",
    "n": "Tuya Inc. American Depositary Shares, each representing one Class A Ordinary Share"
  },
  {
    "s": "TV",
    "n": "Grupo Televisa S.A.B. Common Stock"
  },
  {
    "s": "TVA",
    "n": "Texas Ventures Acquisition III Corp - Class A Ordinary Share"
  },
  {
    "s": "TVACU",
    "n": "Texas Ventures Acquisition III Corp - Unit"
  },
  {
    "s": "TVACW",
    "n": "Texas Ventures Acquisition III Corp - Warrants"
  },
  {
    "s": "TVAI",
    "n": "Thayer Ventures Acquisition Corporation II - Class A Ordinary Shares"
  },
  {
    "s": "TVAIU",
    "n": "Thayer Ventures Acquisition Corporation II - Unit"
  },
  {
    "s": "TVC",
    "n": "Tennessee Valley Authority Common Stock"
  },
  {
    "s": "TVE",
    "n": "Tennessee Valley Authority"
  },
  {
    "s": "TVGN",
    "n": "Tevogen Inc. - Common Stock"
  },
  {
    "s": "TVIV",
    "n": "Texas Ventures Acquisition IV Corp - Class A Ordinary Shares"
  },
  {
    "s": "TVIVU",
    "n": "Texas Ventures Acquisition IV Corp - Units"
  },
  {
    "s": "TVRD",
    "n": "Tvardi Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "TVTX",
    "n": "Travere Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "TW",
    "n": "Tradeweb Markets Inc. - Class A Common Stock"
  },
  {
    "s": "TWAV",
    "n": "TaoWeave, Inc. - Common Stock"
  },
  {
    "s": "TWFG",
    "n": "TWFG, Inc. - Common Stock"
  },
  {
    "s": "TWG",
    "n": "Top Wealth Group Holding Limited - Class A Ordinary Shares"
  },
  {
    "s": "TWI",
    "n": "Titan International, Inc. (DE) Common Stock"
  },
  {
    "s": "TWIN",
    "n": "Twin Disc, Incorporated - Common Stock"
  },
  {
    "s": "TWLO",
    "n": "Twilio Inc. Class A Common Stock"
  },
  {
    "s": "TWLV",
    "n": "Twelve Seas Investment Company III - Class A Ordinary Shares"
  },
  {
    "s": "TWLVU",
    "n": "Twelve Seas Investment Company III - Units"
  },
  {
    "s": "TWST",
    "n": "Twist Bioscience Corporation - Common Stock"
  },
  {
    "s": "TX",
    "n": "Ternium S.A. Ternium S.A. American Depositary Shares (each representing ten shares, USD1.00 par value)"
  },
  {
    "s": "TXG",
    "n": "10x Genomics, Inc. - Common Stock"
  },
  {
    "s": "TXMD",
    "n": "TherapeuticsMD, Inc. - Common Stock"
  },
  {
    "s": "TXN",
    "n": "Texas Instruments Incorporated - Common Stock"
  },
  {
    "s": "TXNM",
    "n": "TXNM Energy, Inc. Common Stock"
  },
  {
    "s": "TXO",
    "n": "TXO Partners, L.P. Common Units Representing Limited Partner Interests"
  },
  {
    "s": "TXRH",
    "n": "Texas Roadhouse, Inc. - Common Stock"
  },
  {
    "s": "TXT",
    "n": "Textron Inc. Common Stock"
  },
  {
    "s": "TY",
    "n": "Tri Continental Corporation Common Stock"
  },
  {
    "s": "TYG",
    "n": "Tortoise Energy Infrastructure Corporation Common Stock"
  },
  {
    "s": "TYGO",
    "n": "Tigo Energy, Inc. - Common Stock"
  },
  {
    "s": "TYL",
    "n": "Tyler Technologies, Inc. Common Stock"
  },
  {
    "s": "TYRA",
    "n": "Tyra Biosciences, Inc. - Common Stock"
  },
  {
    "s": "TZOO",
    "n": "Travelzoo - Common Stock"
  },
  {
    "s": "U",
    "n": "Unity Software Inc. Common Stock"
  },
  {
    "s": "UA",
    "n": "Under Armour, Inc. Class C Common Stock"
  },
  {
    "s": "UAA",
    "n": "Under Armour, Inc. Class A Common Stock"
  },
  {
    "s": "UAC",
    "n": "United Acquisition Corp. I Class A Ordinary Shares"
  },
  {
    "s": "UAL",
    "n": "United Airlines Holdings, Inc. - Common Stock"
  },
  {
    "s": "UAMY",
    "n": "United States Antimony Corporation Common Stock"
  },
  {
    "s": "UAVS",
    "n": "AgEagle Aerial Systems, Inc. Common Stock"
  },
  {
    "s": "UBCP",
    "n": "United Bancorp, Inc. - Common Stock"
  },
  {
    "s": "UBER",
    "n": "Uber Technologies, Inc. Common Stock"
  },
  {
    "s": "UBS",
    "n": "UBS Group AG Registered Ordinary Shares"
  },
  {
    "s": "UBSI",
    "n": "United Bankshares, Inc. - Common Stock"
  },
  {
    "s": "UCAR",
    "n": "U Power Limited - Class A Ordinary Shares"
  },
  {
    "s": "UCB",
    "n": "United Community Banks, Inc. Common Stock"
  },
  {
    "s": "UCFI",
    "n": "CN Healthy Food Tech Group Corp. - Common Stock"
  },
  {
    "s": "UCL",
    "n": "uCloudlink Group Inc. - American Depositary Shares"
  },
  {
    "s": "UCTT",
    "n": "Ultra Clean Holdings, Inc. - Common Stock"
  },
  {
    "s": "UDR",
    "n": "UDR, Inc. Common Stock"
  },
  {
    "s": "UE",
    "n": "Urban Edge Properties Common Shares of Beneficial Interest"
  },
  {
    "s": "UEC",
    "n": "Uranium Energy Corp. Common Stock"
  },
  {
    "s": "UEIC",
    "n": "Universal Electronics Inc. - Common Stock"
  },
  {
    "s": "UFCS",
    "n": "United Fire Group, Inc - Common Stock"
  },
  {
    "s": "UFG",
    "n": "Uni-Fuels Holdings Limited - Class A Ordinary Shares"
  },
  {
    "s": "UFI",
    "n": "Unifi, Inc. New Common Stock"
  },
  {
    "s": "UFPI",
    "n": "UFP Industries, Inc. - Common Stock"
  },
  {
    "s": "UFPT",
    "n": "UFP Technologies, Inc. - Common Stock"
  },
  {
    "s": "UG",
    "n": "United-Guardian, Inc. - Common Stock"
  },
  {
    "s": "UGI",
    "n": "UGI Corporation Common Stock"
  },
  {
    "s": "UGP",
    "n": "Ultrapar Participacoes S.A. (New) American Depositary Shares (Each representing one Common Share)"
  },
  {
    "s": "UHAL",
    "n": "U-Haul Holding Company Common Stock"
  },
  {
    "s": "UHAL-B",
    "n": "U-Haul Holding Company Series N Non-Voting Common Stock "
  },
  {
    "s": "UHS",
    "n": "Universal Health Services, Inc. Common Stock"
  },
  {
    "s": "UHT",
    "n": "Universal Health Realty Income Trust Common Stock"
  },
  {
    "s": "UI",
    "n": "Ubiquiti Inc. Common Stock"
  },
  {
    "s": "UIS",
    "n": "Unisys Corporation New Common Stock"
  },
  {
    "s": "UK",
    "n": "Ucommune International Ltd  - Class A Ordinary Shares"
  },
  {
    "s": "UL",
    "n": "Unilever PLC American Depositary Shares (each representing One Ordinary Share)"
  },
  {
    "s": "ULBI",
    "n": "Ultralife Corporation - Common Stock"
  },
  {
    "s": "ULCC",
    "n": "Frontier Group Holdings, Inc. - Common Stock"
  },
  {
    "s": "ULH",
    "n": "Universal Logistics Holdings, Inc. - Common Stock"
  },
  {
    "s": "ULS",
    "n": "UL Solutions Inc. Class A Common Stock"
  },
  {
    "s": "ULTA",
    "n": "Ulta Beauty, Inc. - Common Stock"
  },
  {
    "s": "UMAC",
    "n": "Unusual Machines, Inc. Common Stock"
  },
  {
    "s": "UMBF",
    "n": "UMB Financial Corporation - Common Stock"
  },
  {
    "s": "UMC",
    "n": "United Microelectronics Corporation (NEW) Common Stock"
  },
  {
    "s": "UMH",
    "n": "UMH Properties, Inc. Common Stock"
  },
  {
    "s": "UNB",
    "n": "Union Bankshares, Inc. - Common Stock"
  },
  {
    "s": "UNCY",
    "n": "Unicycive Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "UNF",
    "n": "Unifirst Corporation Common Stock"
  },
  {
    "s": "UNFI",
    "n": "United Natural Foods, Inc. Common Stock"
  },
  {
    "s": "UNH",
    "n": "UnitedHealth Group Incorporated Common Stock (DE)"
  },
  {
    "s": "UNIT",
    "n": "Uniti Group Inc. - Common Stock"
  },
  {
    "s": "UNM",
    "n": "Unum Group Common Stock"
  },
  {
    "s": "UNMA",
    "n": "Unum Group 6.250% Junior Subordinated Notes due 2058"
  },
  {
    "s": "UNP",
    "n": "Union Pacific Corporation Common Stock"
  },
  {
    "s": "UNTY",
    "n": "Unity Bancorp, Inc. - Common Stock"
  },
  {
    "s": "UONE",
    "n": "Urban One, Inc.  - Class A Common Stock"
  },
  {
    "s": "UONEK",
    "n": "Urban One, Inc.  - Class D Common Stock"
  },
  {
    "s": "UP",
    "n": "Wheels Up Experience Inc. Class A Common Stock"
  },
  {
    "s": "UPB",
    "n": "Upstream Bio, Inc. - Common Stock"
  },
  {
    "s": "UPBD",
    "n": "Upbound Group, Inc. - Common Stock"
  },
  {
    "s": "UPC",
    "n": "Universe Pharmaceuticals Inc - Class A Ordinary Shares"
  },
  {
    "s": "UPLD",
    "n": "Upland Software, Inc. - Common Stock"
  },
  {
    "s": "UPS",
    "n": "United Parcel Service, Inc. Common Stock"
  },
  {
    "s": "UPST",
    "n": "Upstart Holdings, Inc. - Common stock"
  },
  {
    "s": "UPWK",
    "n": "Upwork Inc. - Common Stock"
  },
  {
    "s": "UPXI",
    "n": "Upexi, Inc. - Common Stock"
  },
  {
    "s": "URBN",
    "n": "Urban Outfitters, Inc. - Common Stock"
  },
  {
    "s": "URG",
    "n": "Ur Energy Inc Common Shares (Canada)"
  },
  {
    "s": "URGN",
    "n": "UroGen Pharma Ltd. - Ordinary Shares"
  },
  {
    "s": "URI",
    "n": "United Rentals, Inc. Common Stock"
  },
  {
    "s": "UROY",
    "n": "Uranium Royalty Corp. - Common Stock"
  },
  {
    "s": "USAR",
    "n": "USA Rare Earth, Inc. - Common Stock"
  },
  {
    "s": "USAS",
    "n": "Americas Gold and Silver Corporation Common Shares, no par value"
  },
  {
    "s": "USAU",
    "n": "U.S. Gold Corp. - Common Stock"
  },
  {
    "s": "USB",
    "n": "U.S. Bancorp Common Stock"
  },
  {
    "s": "USBC",
    "n": "USBC, Inc. Common Stock"
  },
  {
    "s": "USCB",
    "n": "USCB Financial Holdings, Inc.  - Class A Common Stock"
  },
  {
    "s": "USDE",
    "n": "StablecoinX Inc. - Class A Common Stock"
  },
  {
    "s": "USDEW",
    "n": "StablecoinX Inc. - Warrants"
  },
  {
    "s": "USEA",
    "n": "United Maritime Corporation - Common Stock"
  },
  {
    "s": "USFD",
    "n": "US Foods Holding Corp. Common Stock"
  },
  {
    "s": "USGO",
    "n": "U.S. GoldMining Inc. - Common stock"
  },
  {
    "s": "USIO",
    "n": "Usio, Inc. - Common Stock"
  },
  {
    "s": "USLM",
    "n": "United States Lime & Minerals, Inc. - Common Stock"
  },
  {
    "s": "USNA",
    "n": "USANA Health Sciences, Inc. Common Stock"
  },
  {
    "s": "USPH",
    "n": "U.S. Physical Therapy, Inc. Common Stock"
  },
  {
    "s": "UTHR",
    "n": "United Therapeutics Corporation - Common Stock"
  },
  {
    "s": "UTI",
    "n": "Universal Technical Institute Inc Common Stock"
  },
  {
    "s": "UTL",
    "n": "UNITIL Corporation Common Stock"
  },
  {
    "s": "UTMD",
    "n": "Utah Medical Products, Inc. - Common Stock"
  },
  {
    "s": "UTSI",
    "n": "UTStarcom Holdings Corp - Ordinary Shares"
  },
  {
    "s": "UTZ",
    "n": "Utz Brands Inc Class A Common Stock "
  },
  {
    "s": "UUU",
    "n": "Universal Safety Products, Inc. Common Stock"
  },
  {
    "s": "UUUU",
    "n": "Energy Fuels Inc Ordinary Shares (Canada)"
  },
  {
    "s": "UVE",
    "n": "UNIVERSAL INSURANCE HOLDINGS INC Common Stock"
  },
  {
    "s": "UVSP",
    "n": "Univest Financial Corporation - Common Stock"
  },
  {
    "s": "UVV",
    "n": "Universal Corporation Common Stock"
  },
  {
    "s": "UWMC",
    "n": "UWM Holdings Corporation Class A Common Stock"
  },
  {
    "s": "UXIN",
    "n": "Uxin Limited - American Depositary Shares"
  },
  {
    "s": "UYSC",
    "n": "UY Scuti Acquisition Corp. - Ordinary Shares"
  },
  {
    "s": "UYSCU",
    "n": "UY Scuti Acquisition Corp. - Units"
  },
  {
    "s": "UZD",
    "n": "Array Digital Infrastructure, Inc. 6.250% Senior Notes due 2069"
  },
  {
    "s": "UZE",
    "n": "Array Digital Infrastructure, Inc. 5.500% Senior Notes due 2070"
  },
  {
    "s": "UZF",
    "n": "Array Digital Infrastructure, Inc. 5.500% Senior Notes due 2070"
  },
  {
    "s": "UZX",
    "n": "Linkage Global Inc - Class A Ordinary Shares"
  },
  {
    "s": "V",
    "n": "Visa Inc."
  },
  {
    "s": "VABK",
    "n": "Virginia National Bankshares Corporation - Common Stock"
  },
  {
    "s": "VAC",
    "n": "Marriott Vacations Worldwide Corporation Common Stock"
  },
  {
    "s": "VAI",
    "n": "Valor Energy Incorporated - Common Stock"
  },
  {
    "s": "VAL",
    "n": "Valaris Limited Common Shares"
  },
  {
    "s": "VAL-W",
    "n": "Valaris Limited Warrants"
  },
  {
    "s": "VALE",
    "n": "VALE S.A.  American Depositary Shares Each Representing one common share"
  },
  {
    "s": "VALN",
    "n": "Valneva SE - American Depositary Shares"
  },
  {
    "s": "VALU",
    "n": "Value Line, Inc. - Common Stock"
  },
  {
    "s": "VANI",
    "n": "Vivani Medical, Inc.  - Common Stock"
  },
  {
    "s": "VATE",
    "n": "INNOVATE Corp. Common Stock"
  },
  {
    "s": "VBIO",
    "n": "Valion Bio, Inc. - Common stock"
  },
  {
    "s": "VBNK",
    "n": "VersaBank - Common Shares"
  },
  {
    "s": "VC",
    "n": "Visteon Corporation - Common Stock"
  },
  {
    "s": "VCEL",
    "n": "Vericel Corporation - Common Stock"
  },
  {
    "s": "VCIG",
    "n": "VCI Global Limited - Ordinary Share"
  },
  {
    "s": "VCRE",
    "n": "Vicore Pharma Holding AB - American Depositary Shares"
  },
  {
    "s": "VCTR",
    "n": "Victory Capital Holdings, Inc. - Common Stock"
  },
  {
    "s": "VCV",
    "n": "Invesco California Value Municipal Income Trust Common Stock"
  },
  {
    "s": "VCYT",
    "n": "Veracyte, Inc. - Common Stock"
  },
  {
    "s": "VECA",
    "n": "Vernal Capital Acquisition Corp. Ordinary Shares"
  },
  {
    "s": "VECA-U",
    "n": "Vernal Capital Acquisition Corp. Units, each consisting of one ordinary share and one right"
  },
  {
    "s": "VECO",
    "n": "Veeco Instruments Inc. - Common Stock"
  },
  {
    "s": "VEEA",
    "n": "Veea Inc. - Common Stock"
  },
  {
    "s": "VEEE",
    "n": "Twin Vee PowerCats Co. - Common Stock"
  },
  {
    "s": "VEEV",
    "n": "Veeva Systems Inc. Class A Common Stock"
  },
  {
    "s": "VEL",
    "n": "Velocity Financial, Inc. Common Stock"
  },
  {
    "s": "VELO",
    "n": "Velo3D, Inc. - Common stock"
  },
  {
    "s": "VENU",
    "n": "Venu Holding Corporation Common Stock"
  },
  {
    "s": "VEON",
    "n": "VEON Ltd. - American Depositary Shares"
  },
  {
    "s": "VERA",
    "n": "Vera Therapeutics, Inc. - Class A Common Stock"
  },
  {
    "s": "VERI",
    "n": "Veritone, Inc. - Common Stock"
  },
  {
    "s": "VERU",
    "n": "Veru Inc. - Common Stock"
  },
  {
    "s": "VERX",
    "n": "Vertex, Inc. - Class A Common Stock"
  },
  {
    "s": "VET",
    "n": "Vermilion Energy Inc. Common (Canada)"
  },
  {
    "s": "VFC",
    "n": "V.F. Corporation Common Stock"
  },
  {
    "s": "VFF",
    "n": "Village Farms International, Inc. - Common Shares"
  },
  {
    "s": "VFS",
    "n": "VinFast Auto Ltd. - Ordinary Shares"
  },
  {
    "s": "VG",
    "n": "Venture Global, Inc. Class A common stock"
  },
  {
    "s": "VGAS",
    "n": "Verde Clean Fuels, Inc. - Class A Common Stock"
  },
  {
    "s": "VGM",
    "n": "Invesco Trust for Investment Grade Municipals Common Stock (DE)"
  },
  {
    "s": "VGNT",
    "n": "Versigent PLC Ordinary Shares"
  },
  {
    "s": "VGZ",
    "n": "Vista Gold Corp Common Stock"
  },
  {
    "s": "VHC",
    "n": "VirnetX Holding Corp - Common Stock"
  },
  {
    "s": "VHCP",
    "n": "Vine Hill Capital Investment Corp. II - Class A Ordinary Shares"
  },
  {
    "s": "VHCPU",
    "n": "Vine Hill Capital Investment Corp. II - Units"
  },
  {
    "s": "VHCPW",
    "n": "Vine Hill Capital Investment Corp. II - Warrants"
  },
  {
    "s": "VHI",
    "n": "Valhi, Inc. Common Stock"
  },
  {
    "s": "VHUB",
    "n": "VenHub Global, Inc. - Common Stock"
  },
  {
    "s": "VIA",
    "n": "Via Transportation, Inc. Class A Common Stock"
  },
  {
    "s": "VIAV",
    "n": "Viavi Solutions Inc. - Common Stock"
  },
  {
    "s": "VICI",
    "n": "VICI Properties Inc. Common Stock"
  },
  {
    "s": "VICR",
    "n": "Vicor Corporation - Common Stock"
  },
  {
    "s": "VIDA",
    "n": "VIDA Global Inc. Class A Common Stock"
  },
  {
    "s": "VII",
    "n": "Viking Acquisition Corp. II Class A Ordinary Shares"
  },
  {
    "s": "VII-W",
    "n": "Viking Acquisition Corp. II Warrants to purchase one Class A Ordinary Share"
  },
  {
    "s": "VIK",
    "n": "Viking Holdings Ltd Ordinary Shares"
  },
  {
    "s": "VINP",
    "n": "Vinci Compass Investments Ltd. - Class A Common Shares"
  },
  {
    "s": "VIOT",
    "n": "Viomi Technology Co., Ltd - American Depositary Shares"
  },
  {
    "s": "VIP",
    "n": "Vulcan Infrastructure and Power Inc. - Class A Common Stock"
  },
  {
    "s": "VIPS",
    "n": "Vipshop Holdings Limited American Depositary Shares, each representing two ordinary shares"
  },
  {
    "s": "VIR",
    "n": "Vir Biotechnology, Inc. - Common Stock"
  },
  {
    "s": "VIRC",
    "n": "Virco Manufacturing Corporation - Common Stock"
  },
  {
    "s": "VIRT",
    "n": "Virtu Financial, Inc. Class A Common Stock"
  },
  {
    "s": "VISN",
    "n": "Vistance Networks, Inc.  - Common Stock"
  },
  {
    "s": "VIST",
    "n": "Vista Energy S.A.B. de C.V. American Depositary Shares, each representing one series A share, with no par value"
  },
  {
    "s": "VITL",
    "n": "Vital Farms, Inc. - Common Stock"
  },
  {
    "s": "VIV",
    "n": "Telefonica Brasil S.A. American Depositary Shares (Each representing One Common Share)"
  },
  {
    "s": "VIVK",
    "n": "Vivakor, Inc. - Common Stock"
  },
  {
    "s": "VIVO",
    "n": "VivoPower PLC - Class A Ordinary Shares"
  },
  {
    "s": "VIVS",
    "n": "VivoSim Labs, Inc. - Common Stock"
  },
  {
    "s": "VJET",
    "n": "Flyte Aviation, Inc. Common Stock"
  },
  {
    "s": "VKI",
    "n": "Invesco Advantage Municipal Income Trust II Common Shares of Beneficial Interest (DE)"
  },
  {
    "s": "VKQ",
    "n": "Invesco Municipal Trust Common Stock"
  },
  {
    "s": "VKTX",
    "n": "Viking Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "VLGEA",
    "n": "Village Super Market, Inc. - Class A Common Stock"
  },
  {
    "s": "VLN",
    "n": "Valens Semiconductor Ltd. Ordinary Shares"
  },
  {
    "s": "VLO",
    "n": "Valero Energy Corporation Common Stock"
  },
  {
    "s": "VLOS",
    "n": "Velos Acquisition I Corp. - Class A Ordinary shares"
  },
  {
    "s": "VLOSU",
    "n": "Velos Acquisition I Corp. - Units"
  },
  {
    "s": "VLRS",
    "n": "Controladora Vuela Compania de Aviacion, S.A.B. de C.V. American Depositary Shares, each representing ten (10) Ordinary Participation Certificates"
  },
  {
    "s": "VLT",
    "n": "Invesco High Income Trust II"
  },
  {
    "s": "VLTO",
    "n": "Veralto Corp Common Stock "
  },
  {
    "s": "VLY",
    "n": "Valley National Bancorp - Common Stock"
  },
  {
    "s": "VMAR",
    "n": "Vision Marine Technologies Inc. - Common Shares"
  },
  {
    "s": "VMC",
    "n": "Vulcan Materials Company (Holding Company) Common Stock"
  },
  {
    "s": "VMD",
    "n": "Viemed Healthcare, Inc. - Common Shares"
  },
  {
    "s": "VMET",
    "n": "Versamet Royalties Corporation - Common Stock"
  },
  {
    "s": "VMI",
    "n": "Valmont Industries, Inc. Common Stock"
  },
  {
    "s": "VMO",
    "n": "Invesco Municipal Opportunity Trust Common Stock"
  },
  {
    "s": "VMRK",
    "n": "Vivmark Residential Common Shares of Beneficial Interest"
  },
  {
    "s": "VNCE",
    "n": "Vince Holding Corp. - Common Stock"
  },
  {
    "s": "VNDA",
    "n": "Vanda Pharmaceuticals Inc. - Common Stock"
  },
  {
    "s": "VNET",
    "n": "VNET Group, Inc. - American Depositary Shares"
  },
  {
    "s": "VNME",
    "n": "Vendome Acquisition Corporation I - Class A Ordinary Shares"
  },
  {
    "s": "VNMEU",
    "n": "Vendome Acquisition Corporation I - Unit"
  },
  {
    "s": "VNO",
    "n": "Vornado Realty Trust Common Stock"
  },
  {
    "s": "VNOM",
    "n": "Viper Energy, Inc.  - Class A Common Stock"
  },
  {
    "s": "VNRX",
    "n": "VolitionRX Limited Common Stock"
  },
  {
    "s": "VNT",
    "n": "Vontier Corporation Common Stock "
  },
  {
    "s": "VNTG",
    "n": "Vantage Corp Class A Ordinary Shares"
  },
  {
    "s": "VOC",
    "n": "VOC Energy Trust Units of Beneficial Interest"
  },
  {
    "s": "VOD",
    "n": "Vodafone Group Plc - American Depositary Shares each representing ten Ordinary Shares"
  },
  {
    "s": "VOGX",
    "n": "Vogenx Inc - Common Stock"
  },
  {
    "s": "VOR",
    "n": "Vor Biopharma Inc. - Common Stock"
  },
  {
    "s": "VOXR",
    "n": "Vox Royalty Corp. - common stock"
  },
  {
    "s": "VOYA",
    "n": "Voya Financial, Inc. Common Stock"
  },
  {
    "s": "VOYG",
    "n": "Voyager Technologies, Inc. Class A Common Stock"
  },
  {
    "s": "VPG",
    "n": "Vishay Precision Group, Inc. Common Stock"
  },
  {
    "s": "VPV",
    "n": "Invesco Pennsylvania Value Municipal Income Trust Common Stock (DE)"
  },
  {
    "s": "VRA",
    "n": "Vera Bradley, Inc. - Common Stock"
  },
  {
    "s": "VRAX",
    "n": "Virax Biolabs Group Limited - Ordinary Shares"
  },
  {
    "s": "VRCA",
    "n": "Verrica Pharmaceuticals Inc. - Common Stock"
  },
  {
    "s": "VRDN",
    "n": "Viridian Therapeutics, Inc.  - Common Stock"
  },
  {
    "s": "VREX",
    "n": "Varex Imaging Corporation - Common Stock"
  },
  {
    "s": "VRM",
    "n": "Vroom, Inc. - Common Stock"
  },
  {
    "s": "VRNS",
    "n": "Varonis Systems, Inc. - Common Stock"
  },
  {
    "s": "VRRM",
    "n": "Verra Mobility Corporation - Class A Common Stock"
  },
  {
    "s": "VRSK",
    "n": "Verisk Analytics, Inc. - Common Stock"
  },
  {
    "s": "VRSN",
    "n": "VeriSign, Inc. - Common Stock"
  },
  {
    "s": "VRT",
    "n": "Vertiv Holdings, LLC Class A Common Stock"
  },
  {
    "s": "VRTS",
    "n": "Virtus Investment Partners, Inc. Common Stock"
  },
  {
    "s": "VRTX",
    "n": "Vertex Pharmaceuticals Incorporated - Common Stock"
  },
  {
    "s": "VRXA",
    "n": "Veraxa Biotech AG - Ordinary Shares"
  },
  {
    "s": "VRXAW",
    "n": "Veraxa Biotech AG - Warrants"
  },
  {
    "s": "VS",
    "n": "Versus Systems Inc. - Common Stock"
  },
  {
    "s": "VSA",
    "n": "VisionSys AI Inc. - American Depositary Shares"
  },
  {
    "s": "VSAT",
    "n": "ViaSat, Inc. - Common Stock"
  },
  {
    "s": "VSEC",
    "n": "VSE Corporation - Common Stock"
  },
  {
    "s": "VSECU",
    "n": "VSE Corporation - Tangible Equity Units"
  },
  {
    "s": "VSH",
    "n": "Vishay Intertechnology, Inc. Common Stock"
  },
  {
    "s": "VSME",
    "n": "VS Media Holdings Limited - Class A Ordinary Shares"
  },
  {
    "s": "VSNT",
    "n": "Versant Media Group, Inc. - Class A Common Stock"
  },
  {
    "s": "VST",
    "n": "Vistra Corp. Common Stock"
  },
  {
    "s": "VSTM",
    "n": "Verastem, Inc. - Common Stock"
  },
  {
    "s": "VSTS",
    "n": "Vestis Corporation Common Stock"
  },
  {
    "s": "VSXY",
    "n": "Victorias Secret & Co. Common Stock "
  },
  {
    "s": "VTEX",
    "n": "VTEX Class A Common Shares"
  },
  {
    "s": "VTGN",
    "n": "Vistagen Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "VTIX",
    "n": "Virtuix Holdings Inc. - Class A Common Stock"
  },
  {
    "s": "VTMX",
    "n": "Corporacion Inmobiliaria Vesta, S.A.B de C.V. American Depositary Shares, each representing ten (10) Common Shares"
  },
  {
    "s": "VTN",
    "n": "Invesco Trust for Investment Grade New York Municipals Common Stock"
  },
  {
    "s": "VTOL",
    "n": "Bristow Group, Inc. Common Stock"
  },
  {
    "s": "VTR",
    "n": "Ventas, Inc. Common Stock"
  },
  {
    "s": "VTRS",
    "n": "Viatris Inc. - Common Stock"
  },
  {
    "s": "VTS",
    "n": "Vitesse Energy, Inc. Common Stock"
  },
  {
    "s": "VTSI",
    "n": "VirTra, Inc. - Common Stock"
  },
  {
    "s": "VTVT",
    "n": "vTv Therapeutics Inc. - Class A Common Stock"
  },
  {
    "s": "VUZI",
    "n": "Vuzix Corporation  - Common Stock"
  },
  {
    "s": "VVOS",
    "n": "Vivos Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "VVR",
    "n": "Invesco Senior Income Trust Common Stock (DE)"
  },
  {
    "s": "VVV",
    "n": "Valvoline Inc. Common Stock"
  },
  {
    "s": "VVX",
    "n": "V2X, Inc. Common Stock"
  },
  {
    "s": "VWAV",
    "n": "VisionWave Holdings, Inc. - Common Stock"
  },
  {
    "s": "VYGR",
    "n": "Voyager Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "VYLR",
    "n": "Vylor Inc. Common Stock"
  },
  {
    "s": "VYX",
    "n": "NCR Voyix Corporation Common Stock"
  },
  {
    "s": "VZ",
    "n": "Verizon Communications Inc. Common Stock"
  },
  {
    "s": "VZLA",
    "n": "Vizsla Silver Corp. Common Shares"
  },
  {
    "s": "W",
    "n": "Wayfair Inc. Class A Common Stock"
  },
  {
    "s": "WAB",
    "n": "Westinghouse Air Brake Technologies Corporation Common Stock"
  },
  {
    "s": "WABC",
    "n": "Westamerica Bancorporation - Common Stock"
  },
  {
    "s": "WAFD",
    "n": "WaFd, Inc. - Common Stock"
  },
  {
    "s": "WAFDP",
    "n": "WaFd, Inc. - Depositary Shares"
  },
  {
    "s": "WAFU",
    "n": "Wah Fu Education Group Limited - Ordinary Shares"
  },
  {
    "s": "WAL",
    "n": "Western Alliance Bancorporation Common Stock (DE)"
  },
  {
    "s": "WASH",
    "n": "Washington Trust Bancorp, Inc. - Common Stock"
  },
  {
    "s": "WAT",
    "n": "Waters Corporation Common Stock"
  },
  {
    "s": "WATR",
    "n": "Air Water Ventures Limited - Ordinary Shares"
  },
  {
    "s": "WATT",
    "n": "Energous Corporation - Common Stock"
  },
  {
    "s": "WAVE",
    "n": "Eco Wave Power Global AB (publ) - American Depositary Shares"
  },
  {
    "s": "WAY",
    "n": "Waystar Holding Corp. - Common Stock"
  },
  {
    "s": "WB",
    "n": "Weibo Corporation - American Depositary Shares"
  },
  {
    "s": "WBI",
    "n": "WaterBridge Infrastructure LLC Class A Shares Representing Limited Liability Company Interests"
  },
  {
    "s": "WBTN",
    "n": "WEBTOON Entertainment Inc. - Common stock"
  },
  {
    "s": "WBUY",
    "n": "WEBUY GLOBAL LTD. - Class A Ordinary Shares"
  },
  {
    "s": "WBX",
    "n": "Wallbox N.V. Class A Ordinary Shares"
  },
  {
    "s": "WCC",
    "n": "WESCO International, Inc. Common Stock"
  },
  {
    "s": "WCCB",
    "n": "West Coast Community Bancorp - Common Stock"
  },
  {
    "s": "WCN",
    "n": "Waste Connections, Inc. Common Shares"
  },
  {
    "s": "WCT",
    "n": "Wellchange Holdings Company Limited - Class A Ordinary shares"
  },
  {
    "s": "WD",
    "n": "Walker & Dunlop, Inc Common Stock"
  },
  {
    "s": "WDAY",
    "n": "Workday, Inc. - Class A Common Stock"
  },
  {
    "s": "WDC",
    "n": "Western Digital Corporation - Common Stock"
  },
  {
    "s": "WDFC",
    "n": "WD-40 Company - Common Stock"
  },
  {
    "s": "WDH",
    "n": "Waterdrop Inc. American Depositary Shares (each representing the right to receive 10 Class A Ordinary Shares)"
  },
  {
    "s": "WDS",
    "n": "Woodside Energy Group Limited American Depositary Shares, each representing one Ordinary Share"
  },
  {
    "s": "WEAV",
    "n": "Weave Communications, Inc. Common Stock"
  },
  {
    "s": "WEC",
    "n": "WEC Energy Group, Inc. Common Stock"
  },
  {
    "s": "WELL",
    "n": "Welltower Inc. Common Stock"
  },
  {
    "s": "WEN",
    "n": "Wendy's Company (The) - Common Stock"
  },
  {
    "s": "WENC",
    "n": "West Enclave Merger Corp. Ordinary Shares"
  },
  {
    "s": "WENC-U",
    "n": "West Enclave Merger Corp. Units, each consisting of one Ordinary Share and one Right to acquire one-tenth (1/10) of one Ordinary Share"
  },
  {
    "s": "WENN",
    "n": "Wen Acquisition Corp - Class A Ordinary Shares"
  },
  {
    "s": "WENNU",
    "n": "Wen Acquisition Corp - Unit"
  },
  {
    "s": "WERN",
    "n": "Werner Enterprises, Inc. - Common Stock"
  },
  {
    "s": "WEST",
    "n": "Westrock Coffee Company - Common Stock"
  },
  {
    "s": "WETH",
    "n": "Wetouch Technology Inc. - Common Stock"
  },
  {
    "s": "WETO",
    "n": "Wetour Robotics Limited - Ordinary Shares"
  },
  {
    "s": "WEX",
    "n": "WEX Inc. common stock"
  },
  {
    "s": "WEYS",
    "n": "Weyco Group, Inc. - Common Stock"
  },
  {
    "s": "WF",
    "n": "Woori Financial Group Inc. American Depositary Shares (each representing three (3) shares of Common Stock)"
  },
  {
    "s": "WFC",
    "n": "Wells Fargo & Company Common Stock"
  },
  {
    "s": "WFCF",
    "n": "Where Food Comes From, Inc. - Common Stock"
  },
  {
    "s": "WFF",
    "n": "WF Holding Limited - Ordinary Shares"
  },
  {
    "s": "WFG",
    "n": "West Fraser Timber Co. Ltd Common stock"
  },
  {
    "s": "WFRD",
    "n": "Weatherford International plc - Ordinary shares"
  },
  {
    "s": "WGO",
    "n": "Winnebago Industries, Inc. Common Stock"
  },
  {
    "s": "WGS",
    "n": "GeneDx Holdings Corp. - Class A Common Stock"
  },
  {
    "s": "WH",
    "n": "Wyndham Hotels & Resorts, Inc. Common Stock "
  },
  {
    "s": "WHD",
    "n": "Cactus, Inc. Class A Common Stock"
  },
  {
    "s": "WHFCL",
    "n": "WhiteHorse Finance, Inc. - 7.875% Notes due 2028"
  },
  {
    "s": "WHG",
    "n": "Westwood Holdings Group Inc Common Stock"
  },
  {
    "s": "WHK",
    "n": "WhiteHawk Minerals Corp Class A Common Stock"
  },
  {
    "s": "WHLR",
    "n": "Wheeler Real Estate Investment Trust, Inc. - Common Stock"
  },
  {
    "s": "WHLRL",
    "n": "Wheeler Real Estate Investment Trust, Inc. - 7.00% Senior Subordinated Convertible Notes Due 2031"
  },
  {
    "s": "WHR",
    "n": "Whirlpool Corporation Common Stock"
  },
  {
    "s": "WHWK",
    "n": "Whitehawk Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "WIMI",
    "n": "WiMi Hologram Cloud Inc. - Class B Ordinary Shares"
  },
  {
    "s": "WINA",
    "n": "Winmark Corporation - Common Stock"
  },
  {
    "s": "WING",
    "n": "Wingstop Inc. - Common Stock"
  },
  {
    "s": "WIT",
    "n": "Wipro Limited Common Stock"
  },
  {
    "s": "WIX",
    "n": "Wix.com Ltd. - Ordinary Shares"
  },
  {
    "s": "WK",
    "n": "Workiva Inc. Class A Common Stock"
  },
  {
    "s": "WKC",
    "n": "World Kinect Corporation Common Stock"
  },
  {
    "s": "WKHS",
    "n": "Workhorse Group, Inc. - Common Stock"
  },
  {
    "s": "WKSP",
    "n": "Worksport, Ltd. - Common Stock"
  },
  {
    "s": "WLCO",
    "n": "Wilco 63 Corporation - Class A Ordinary Shares"
  },
  {
    "s": "WLCOU",
    "n": "Wilco 63 Corporation - Units"
  },
  {
    "s": "WLDN",
    "n": "Willdan Group, Inc. - Common Stock"
  },
  {
    "s": "WLDS",
    "n": "Wearable Devices Ltd. - Ordinary Share"
  },
  {
    "s": "WLFC",
    "n": "Willis Lease Finance Corporation - Common Stock"
  },
  {
    "s": "WLII",
    "n": "Willow Lane Acquisition Corp. II - Class A Ordinary Shares"
  },
  {
    "s": "WLIIU",
    "n": "Willow Lane Acquisition Corp. II - Unit"
  },
  {
    "s": "WLIIW",
    "n": "Willow Lane Acquisition Corp. II - Warrants"
  },
  {
    "s": "WLK",
    "n": "Westlake Corporation Common Stock"
  },
  {
    "s": "WLTH",
    "n": "Wealthfront Corporation - Common Stock"
  },
  {
    "s": "WLY",
    "n": "John Wiley & Sons, Inc. Common Stock"
  },
  {
    "s": "WLYB",
    "n": "John Wiley & Sons, Inc. Common Stock"
  },
  {
    "s": "WM",
    "n": "Waste Management, Inc. Common Stock"
  },
  {
    "s": "WMB",
    "n": "Williams Companies, Inc. (The) Common Stock"
  },
  {
    "s": "WMG",
    "n": "Warner Music Group Corp. - Class A Common Stock"
  },
  {
    "s": "WMK",
    "n": "Weis Markets, Inc. Common Stock"
  },
  {
    "s": "WMS",
    "n": "Advanced Drainage Systems, Inc. Common Stock"
  },
  {
    "s": "WMT",
    "n": "Walmart Inc. - Common Stock"
  },
  {
    "s": "WNC",
    "n": "Wabash National Corporation Common Stock"
  },
  {
    "s": "WNEB",
    "n": "Western New England Bancorp, Inc. - Common Stock"
  },
  {
    "s": "WNW",
    "n": "Meiwu Technology Company Limited - Ordinary Shares"
  },
  {
    "s": "WOK",
    "n": "WORK Medical Technology Group LTD - Class A Ordinary Shares"
  },
  {
    "s": "WOLF",
    "n": "Wolfspeed, Inc. Common Stock New"
  },
  {
    "s": "WOOF",
    "n": "Petco Health and Wellness Company, Inc. - Class A Common Stock"
  },
  {
    "s": "WOR",
    "n": "Worthington Enterprises, Inc. Common Shares"
  },
  {
    "s": "WORX",
    "n": "SCWorx Corp. - Common Stock"
  },
  {
    "s": "WPAC",
    "n": "White Pearl Acquisition Corp. Class A Ordinary Shares"
  },
  {
    "s": "WPAC-U",
    "n": "White Pearl Acquisition Corp. Units, each consisting of one Class A ordinary share and one right to receive one-fifth (1/5) of one Class A ordinary share"
  },
  {
    "s": "WPM",
    "n": "Wheaton Precious Metals Corp Common Shares (Canada)"
  },
  {
    "s": "WPP",
    "n": "WPP plc American Depositary Shares"
  },
  {
    "s": "WPRT",
    "n": "Westport Fuel Systems Inc - Common Shares"
  },
  {
    "s": "WQEY",
    "n": "WISeQey Corp - Ordinary Shares"
  },
  {
    "s": "WRAP",
    "n": "Wrap Technologies, Inc. - Common Stock"
  },
  {
    "s": "WRB",
    "n": "W.R. Berkley Corporation Common Stock"
  },
  {
    "s": "WRBY",
    "n": "Warby Parker Inc. Class A Common Stock"
  },
  {
    "s": "WRD",
    "n": "WeRide Inc. - American Depositary Shares"
  },
  {
    "s": "WRLD",
    "n": "World Acceptance Corporation - Common Stock"
  },
  {
    "s": "WRN",
    "n": "Western Copper and Gold Corporation Common Stock"
  },
  {
    "s": "WS",
    "n": "Worthington Steel, Inc. Common Shares"
  },
  {
    "s": "WSBC",
    "n": "WesBanco, Inc. - Common Stock"
  },
  {
    "s": "WSBF",
    "n": "Waterstone Financial, Inc. - Common Stock"
  },
  {
    "s": "WSBK",
    "n": "Winchester Bancorp, Inc. - Common Stock"
  },
  {
    "s": "WSC",
    "n": "WillScot Holdings Corporation - Class A Common Stock"
  },
  {
    "s": "WSE",
    "n": "Wise Group plc - Class A Ordinary Shares"
  },
  {
    "s": "WSFS",
    "n": "WSFS Financial Corporation - Common Stock"
  },
  {
    "s": "WSHP",
    "n": "WeShop Holdings Limited - Class A Ordinary Shares"
  },
  {
    "s": "WSM",
    "n": "Williams-Sonoma, Inc. Common Stock (DE)"
  },
  {
    "s": "WSO",
    "n": "Watsco, Inc. Common Stock"
  },
  {
    "s": "WSO-B",
    "n": "Watsco, Inc. Class B Common Stock"
  },
  {
    "s": "WST",
    "n": "West Pharmaceutical Services, Inc. Common Stock"
  },
  {
    "s": "WSTN",
    "n": "Westin Acquisition Corp - Class A Ordinary Share"
  },
  {
    "s": "WSTNR",
    "n": "Westin Acquisition Corp - Right"
  },
  {
    "s": "WSTNU",
    "n": "Westin Acquisition Corp - Units"
  },
  {
    "s": "WT",
    "n": "WisdomTree, Inc. Common Stock"
  },
  {
    "s": "WTBA",
    "n": "West Bancorporation - Common Stock"
  },
  {
    "s": "WTF",
    "n": "Waton Financial Limited - Ordinary Shares"
  },
  {
    "s": "WTFC",
    "n": "Wintrust Financial Corporation - Common Stock"
  },
  {
    "s": "WTG",
    "n": "Wintergreen Acquisition Corp. - Ordinary Shares"
  },
  {
    "s": "WTGUU",
    "n": "Wintergreen Acquisition Corp. - Unit"
  },
  {
    "s": "WTI",
    "n": "W&T Offshore, Inc. Common Stock"
  },
  {
    "s": "WTM",
    "n": "White Mountains Insurance Group, Ltd. Common Stock"
  },
  {
    "s": "WTRG",
    "n": "Essential Utilities, Inc. Common Stock"
  },
  {
    "s": "WTS",
    "n": "Watts Water Technologies, Inc. Class A Common Stock"
  },
  {
    "s": "WTTR",
    "n": "Select Water Solutions, Inc. Class A common stock"
  },
  {
    "s": "WTW",
    "n": "Willis Towers Watson Public Limited Company - Ordinary Shares"
  },
  {
    "s": "WU",
    "n": "Western Union Company (The) Common Stock"
  },
  {
    "s": "WULF",
    "n": "TeraWulf Inc. - Common Stock"
  },
  {
    "s": "WVE",
    "n": "Wave Life Sciences, Inc. - Common Stock"
  },
  {
    "s": "WVVI",
    "n": "Willamette Valley Vineyards, Inc. - Common Stock"
  },
  {
    "s": "WW",
    "n": "WW International, Inc.  - Common Stock"
  },
  {
    "s": "WWD",
    "n": "Woodward, Inc. - Common Stock"
  },
  {
    "s": "WWR",
    "n": "Westwater Resources, Inc. Common Stock"
  },
  {
    "s": "WWW",
    "n": "Wolverine World Wide, Inc. Common Stock"
  },
  {
    "s": "WXM",
    "n": "WF International Limited - Ordinary Shares"
  },
  {
    "s": "WY",
    "n": "Weyerhaeuser Company Common Stock"
  },
  {
    "s": "WYFI",
    "n": "WhiteFiber, Inc. - Ordinary Shares"
  },
  {
    "s": "WYHG",
    "n": "Wing Yip Food Holdings Group Limited - American Depositary Shares"
  },
  {
    "s": "WYNN",
    "n": "Wynn Resorts, Limited - Common Stock"
  },
  {
    "s": "WYY",
    "n": "WidePoint Corporation Common Stock"
  },
  {
    "s": "XAIR",
    "n": "Beyond Air, Inc. - Common Stock"
  },
  {
    "s": "XBIO",
    "n": "Xenetic Biosciences, Inc. - Common Stock"
  },
  {
    "s": "XBIT",
    "n": "XBiotech Inc. - Common Stock"
  },
  {
    "s": "XBP",
    "n": "XBP Global Holdings, Inc. - Common Stock"
  },
  {
    "s": "XCBE",
    "n": "X3 Acquisition Corp. Ltd. - Class A Ordinary Shares"
  },
  {
    "s": "XCBEU",
    "n": "X3 Acquisition Corp. Ltd. - Unit"
  },
  {
    "s": "XCH",
    "n": "XCHG Limited - ADS"
  },
  {
    "s": "XCUR",
    "n": "Exicure, Inc. - Common Stock"
  },
  {
    "s": "XE",
    "n": "X-Energy, Inc. - Class A Common Stock"
  },
  {
    "s": "XEL",
    "n": "Xcel Energy Inc. - Common Stock"
  },
  {
    "s": "XELB",
    "n": "Xcel Brands, Inc - Common Stock"
  },
  {
    "s": "XELLL",
    "n": "Xcel Energy Inc. - 6.25% Junior Subordinated Notes, Series due 2085"
  },
  {
    "s": "XENE",
    "n": "Xenon Pharmaceuticals Inc. - Common Shares"
  },
  {
    "s": "XERS",
    "n": "Xeris Biopharma Holdings, Inc. - Common Stock"
  },
  {
    "s": "XFLH",
    "n": "XFLH Capital Corporation Ordinary Shares"
  },
  {
    "s": "XFLH-U",
    "n": "XFLH Capital Corporation Units, each consisting of one Ordinary Share and one Right"
  },
  {
    "s": "XFLT",
    "n": "XAI Floating Rate & Alternative Income Trust Common Shares of Beneficial Interest"
  },
  {
    "s": "XFOR",
    "n": "X4 Pharmaceuticals, Inc. - Common Stock"
  },
  {
    "s": "XGN",
    "n": "Exagen Inc. - Common Stock"
  },
  {
    "s": "XHG",
    "n": "XChange TEC.INC - American Depositary Shares"
  },
  {
    "s": "XHLD",
    "n": "TEN Holdings, Inc. - Common Stock"
  },
  {
    "s": "XHR",
    "n": "Xenia Hotels & Resorts, Inc. Common Stock"
  },
  {
    "s": "XIII",
    "n": "Churchill Capital Corp XIII - Class A Ordinary Shares"
  },
  {
    "s": "XIIIU",
    "n": "Churchill Capital Corp XIII - Units"
  },
  {
    "s": "XIIIW",
    "n": "Churchill Capital Corp XIII - Warrants"
  },
  {
    "s": "XLAB",
    "n": "Exascale Labs Holdings Inc. - Class A Common Stock"
  },
  {
    "s": "XLO",
    "n": "Xilio Therapeutics, Inc. - Common Stock"
  },
  {
    "s": "XMAX",
    "n": "XMAX, Inc. - Common Stock"
  },
  {
    "s": "XMTR",
    "n": "Xometry, Inc. - Class A Common Stock"
  },
  {
    "s": "XNCR",
    "n": "Xencor, Inc. - Common Stock"
  },
  {
    "s": "XNDU",
    "n": "Xanadu Quantum Technologies Limited - Class B Subordinate Voting Shares"
  },
  {
    "s": "XNET",
    "n": "Xunlei Limited - American Depositary Shares"
  },
  {
    "s": "XOM",
    "n": "ExxonMobil Holdings Corporation Common Stock"
  },
  {
    "s": "XOS",
    "n": "Xos, Inc. - Common Stock"
  },
  {
    "s": "XP",
    "n": "XP Inc. - Class A Common Stock"
  },
  {
    "s": "XPEL",
    "n": "XPEL, Inc. - Common Stock"
  },
  {
    "s": "XPER",
    "n": "Xperi Inc. Common Stock "
  },
  {
    "s": "XPEV",
    "n": "XPeng Inc. American depositary shares, each representing two Class A ordinary shares"
  },
  {
    "s": "XPL",
    "n": "Solitario Resources Corp. Common Stock"
  },
  {
    "s": "XPO",
    "n": "XPO, Inc. Common Stock"
  },
  {
    "s": "XPOF",
    "n": "Xponential Fitness, Inc. Class A Common Stock"
  },
  {
    "s": "XPON",
    "n": "Expion Energy, Inc. - Common Stock"
  },
  {
    "s": "XPRO",
    "n": "Expro Ltd Ordinary Shares"
  },
  {
    "s": "XRAY",
    "n": "DENTSPLY SIRONA Inc. - Common Stock"
  },
  {
    "s": "XRN",
    "n": "Chiron Real Estate Inc. Common Stock"
  },
  {
    "s": "XRPN",
    "n": "Armada Acquisition Corp. II - Class A Ordinary Shares"
  },
  {
    "s": "XRPNU",
    "n": "Armada Acquisition Corp. II - Units"
  },
  {
    "s": "XRTX",
    "n": "XORTX Therapeutics Inc. - Common Shares"
  },
  {
    "s": "XRX",
    "n": "Xerox Holdings Corporation - Common Stock"
  },
  {
    "s": "XRXDW",
    "n": "Xerox Holdings Corporation - Warrants"
  },
  {
    "s": "XSLL",
    "n": "Xsolla SPAC 1 - Class A Ordinary Shares"
  },
  {
    "s": "XSLLU",
    "n": "Xsolla SPAC 1 - Units"
  },
  {
    "s": "XSLLW",
    "n": "Xsolla SPAC 1 - Warrants"
  },
  {
    "s": "XTER",
    "n": "Karman Line Acquisition Corp. - Class A Ordinary Shares"
  },
  {
    "s": "XTERU",
    "n": "Karman Line Acquisition Corp. - Units"
  },
  {
    "s": "XTERW",
    "n": "Karman Line Acquisition Corp. - Warrants"
  },
  {
    "s": "XTIA",
    "n": "XTI Aerospace, Inc. Common Stock  - Common Stock"
  },
  {
    "s": "XTLB",
    "n": "XTL Biopharmaceuticals Ltd. - American Depositary Shares"
  },
  {
    "s": "XTND",
    "n": "Xtend AI Robotics, Inc. Common Stock"
  },
  {
    "s": "XTNT",
    "n": "Xtant Medical Holdings, Inc. Common Stock"
  },
  {
    "s": "XWEL",
    "n": "XWELL, Inc. - Common Stock"
  },
  {
    "s": "XXI",
    "n": "Twenty One Capital, Inc. Class A Common Stock"
  },
  {
    "s": "XXII",
    "n": "22nd Century Group, Inc - Common Stock"
  },
  {
    "s": "XYF",
    "n": "X Financial American Depositary Shares, each representing six Class A Ordinary Shares"
  },
  {
    "s": "XYL",
    "n": "Xylem Inc. Common Stock New"
  },
  {
    "s": "XYZ",
    "n": "Block, Inc. Class A Common Stock,"
  },
  {
    "s": "XZO",
    "n": "Exzeo Group, Inc. Common Stock"
  },
  {
    "s": "YAAS",
    "n": "Youxin Technology Ltd - Class A Ordinary shares"
  },
  {
    "s": "YALA",
    "n": "Yalla Group Limited American Depositary Shares, each representing one Class A Ordinary Share"
  },
  {
    "s": "YARW",
    "n": "Yarrow Bioscience, Inc. - Common Stock"
  },
  {
    "s": "YB",
    "n": "Yuanbao Inc. - American Depositary Shares"
  },
  {
    "s": "YCBD",
    "n": "cbdMD, Inc. Common Stock"
  },
  {
    "s": "YCY",
    "n": "AA Mission Acquisition Corp. II Class A Ordinary Shares"
  },
  {
    "s": "YDDL",
    "n": "One and One Green Technologies. INC - Class A Ordinary Shares"
  },
  {
    "s": "YDES",
    "n": "YD Bio Limited - Ordinary Shares"
  },
  {
    "s": "YDESW",
    "n": "YD Bio Limited - Warrants"
  },
  {
    "s": "YDKG",
    "n": "Yueda Digital Holding - Class A Ordinary Share"
  },
  {
    "s": "YELP",
    "n": "Yelp Inc. Common Stock"
  },
  {
    "s": "YETI",
    "n": "YETI Holdings, Inc. Common Stock"
  },
  {
    "s": "YEXT",
    "n": "Yext, Inc. Common Stock"
  },
  {
    "s": "YFOR",
    "n": "YYForce Inc. - Class A Ordinary Shares"
  },
  {
    "s": "YHC",
    "n": "LQR House Inc. - Common Stock"
  },
  {
    "s": "YHGJ",
    "n": "Yunhong Green CTI Ltd. - Common Stock"
  },
  {
    "s": "YHNA",
    "n": "YHN Acquisition I Limited - Ordinary Shares"
  },
  {
    "s": "YHNAR",
    "n": "YHN Acquisition I Limited - Right"
  },
  {
    "s": "YHNAU",
    "n": "YHN Acquisition I Limited - Unit"
  },
  {
    "s": "YI",
    "n": "111, Inc. - American Depositary Shares"
  },
  {
    "s": "YIBO",
    "n": "Planet Image International Limited - Class A Ordinary Shares"
  },
  {
    "s": "YICC",
    "n": "Yorkville International Capital Corp. - Class A Ordinary Shares"
  },
  {
    "s": "YICCU",
    "n": "Yorkville International Capital Corp. - Units"
  },
  {
    "s": "YICCW",
    "n": "Yorkville International Capital Corp. - Warrants"
  },
  {
    "s": "YJ",
    "n": "Yunji Inc. - American Depository Shares"
  },
  {
    "s": "YMAT",
    "n": "J-Star Holding Co., Ltd. - Class A Ordinary Shares"
  },
  {
    "s": "YMM",
    "n": "Full Truck Alliance Co. Ltd. American Depositary Shares (each representing 20 Class A Ordinary Shares)"
  },
  {
    "s": "YMT",
    "n": "Yimutian Inc. - American Depositary Shares; each representing 25 Class A ordinary shares"
  },
  {
    "s": "YORW",
    "n": "The York Water Company - Common Stock"
  },
  {
    "s": "YOU",
    "n": "Clear Secure, Inc. Class A Common Stock"
  },
  {
    "s": "YOUL",
    "n": "Youlife Group Inc. - American Depositary Shares"
  },
  {
    "s": "YPF",
    "n": "YPF Sociedad Anonima American Depositary Shares"
  },
  {
    "s": "YQ",
    "n": "17 Education & Technology Group Inc. - American Depositary Shares"
  },
  {
    "s": "YRD",
    "n": "Yiren Digital Ltd. American Depositary Shares, each representing two ordinary shares"
  },
  {
    "s": "YSG",
    "n": "Yatsen Holding Limited American Depositary Shares, each representing twenty (20) Class A Ordinary Shares"
  },
  {
    "s": "YSS",
    "n": "York Space Systems Inc. Common Stock"
  },
  {
    "s": "YSWY",
    "n": "Yesway, Inc. - Class A Common Stock"
  },
  {
    "s": "YSXT",
    "n": "YSX Tech. Co., Ltd  - Class A Ordinary Shares"
  },
  {
    "s": "YTRA",
    "n": "Yatra Online, Inc. - Ordinary Shares"
  },
  {
    "s": "YUM",
    "n": "Yum! Brands, Inc."
  },
  {
    "s": "YUMC",
    "n": "Yum China Holdings, Inc. Common Stock"
  },
  {
    "s": "YXT",
    "n": "YXT.COM GROUP HOLDING LIMITED - American Depository Shares"
  },
  {
    "s": "YYAI",
    "n": "AiRWA Inc. - Common Stock"
  },
  {
    "s": "Z",
    "n": "Zillow Group, Inc. - Class C Capital Stock"
  },
  {
    "s": "ZBAO",
    "n": "Zhibao Technology Inc. - Class A Ordinary Shares"
  },
  {
    "s": "ZBH",
    "n": "Zimmer Biomet Holdings, Inc. Common Stock"
  },
  {
    "s": "ZBIO",
    "n": "Zenas BioPharma, Inc. - Common Stock"
  },
  {
    "s": "ZBRA",
    "n": "Zebra Technologies Corporation - Class A Common Stock"
  },
  {
    "s": "ZCMD",
    "n": "Zhongchao Inc. - Class A Ordinary Shares"
  },
  {
    "s": "ZD",
    "n": "Ziff Davis, Inc. - Common Stock"
  },
  {
    "s": "ZDAI",
    "n": "DirectBooking Technology Co., Ltd. - Class A Ordinary Shares"
  },
  {
    "s": "ZDGE",
    "n": "Zedge, Inc. Class B Common Stock "
  },
  {
    "s": "ZENA",
    "n": "ZenaTech, Inc. - Common Stock"
  },
  {
    "s": "ZEO",
    "n": "Zeo Energy Corporation - Class A Common Stock"
  },
  {
    "s": "ZEOWW",
    "n": "Zeo Energy Corporation - Warrants"
  },
  {
    "s": "ZEPP",
    "n": "Zepp Health Corporation American depositary shares, each representing sixteen Class A ordinary shares"
  },
  {
    "s": "ZETA",
    "n": "Zeta Global Holdings Corp. Class A Common Stock"
  },
  {
    "s": "ZG",
    "n": "Zillow Group, Inc. - Class A Common Stock"
  },
  {
    "s": "ZGN",
    "n": "Ermenegildo Zegna N.V. Ordinary Shares"
  },
  {
    "s": "ZH",
    "n": "Zhihu Inc. American Depositary Shares, each representing three (3) Class A Ordinary Shares"
  },
  {
    "s": "ZIM",
    "n": "ZIM Integrated Shipping Services Ltd. Ordinary Shares"
  },
  {
    "s": "ZION",
    "n": "Zions Bancorporation N.A. - Common Stock"
  },
  {
    "s": "ZIP",
    "n": "ZipRecruiter, Inc. Class A Common Stock"
  },
  {
    "s": "ZJK",
    "n": "ZJK Industrial Co., Ltd. - Class A Ordinary Shares"
  },
  {
    "s": "ZJYL",
    "n": "JIN MEDICAL INTERNATIONAL LTD. - Class A Ordinary Shares"
  },
  {
    "s": "ZKH",
    "n": "ZKH Group Limited American Depositary Shares, each representing thirty-five (35) Class A Ordinary Shares"
  },
  {
    "s": "ZKIN",
    "n": "ZK International Group Co., Ltd - Ordinary Share"
  },
  {
    "s": "ZKP",
    "n": "Lafayette Digital Acquisition Corp. I - Class A Ordinary Shares"
  },
  {
    "s": "ZKPU",
    "n": "Lafayette Digital Acquisition Corp. I - Unit"
  },
  {
    "s": "ZLAB",
    "n": "Zai Lab Limited - American Depositary Shares"
  },
  {
    "s": "ZM",
    "n": "Zoom Communications, Inc. - Class A Common Stock"
  },
  {
    "s": "ZNB",
    "n": "Zeta Network Group - Class A Ordinary Shares"
  },
  {
    "s": "ZNTL",
    "n": "Zentalis Pharmaceuticals, Inc. - common stock"
  },
  {
    "s": "ZONE",
    "n": "Zone Frontier Inc. Class B Common Stock"
  },
  {
    "s": "ZOOZ",
    "n": "ZOOZ Strategy Ltd. - Ordinary Shares"
  },
  {
    "s": "ZS",
    "n": "Zscaler, Inc. - Common Stock"
  },
  {
    "s": "ZSQR",
    "n": "Z Squared Inc. - Common Stock"
  },
  {
    "s": "ZSTK",
    "n": "ZeroStack Corp. - Common Stock"
  },
  {
    "s": "ZTG",
    "n": "Zenta Group Company Limited - Class A Ordinary Shares"
  },
  {
    "s": "ZTO",
    "n": "ZTO Express (Cayman) Inc. American Depositary Shares, each representing one Class A ordinary share."
  },
  {
    "s": "ZTS",
    "n": "Zoetis Inc. Class A Common Stock"
  },
  {
    "s": "ZUMZ",
    "n": "Zumiez Inc. - Common Stock"
  },
  {
    "s": "ZURA",
    "n": "Zura Bio Limited - Class A Ordinary shares"
  },
  {
    "s": "ZVIA",
    "n": "Zevia PBC Class A Common Stock"
  },
  {
    "s": "ZVRA",
    "n": "Zevra Therapeutics, Inc.  - Common Stock"
  },
  {
    "s": "ZWS",
    "n": "Zurn Elkay Water Solutions Corporation Common Stock"
  },
  {
    "s": "ZYBT",
    "n": "Zhengye Biotechnology Holding Limited - Class A Ordinary Shares"
  },
  {
    "s": "ZYME",
    "n": "Zymeworks Inc. - Common Stock"
  }
];
