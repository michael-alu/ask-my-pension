# Error analysis

System: `reader_reader-roberta-base-squad2-100pct-matched_retriever-bge-small-en-v1.5-100pct`, 134 test questions.

## Outcomes

| Outcome | Count |
|---|---|
| correct | 43 |
| retriever missed the gold passage | 39 |
| gold passage read, answer taken from another | 28 |
| answered but should have refused | 8 |
| partly right, too short | 6 |
| partly right, partial overlap | 4 |
| refused but answerable | 4 |
| right passage, wrong span | 1 |
| correctly refused | 1 |

Correct but hard to read (answer passage Flesch Reading Ease below 30): 18

## Outcomes by slice

- **origin=faq_rule**: correct: 35, gold passage read, answer taken from another: 23, retriever missed the gold passage: 18, partly right, partial overlap: 3, partly right, too short: 2, right passage, wrong span: 1
- **origin=own**: retriever missed the gold passage: 21, correct: 8, answered but should have refused: 8, gold passage read, answer taken from another: 5, refused but answerable: 4, partly right, too short: 4, partly right, partial overlap: 1, correctly refused: 1
- **style=legal**: retriever missed the gold passage: 12, answered but should have refused: 8, gold passage read, answer taken from another: 3, refused but answerable: 3, correct: 2, partly right, too short: 1, partly right, partial overlap: 1, correctly refused: 1
- **style=plain**: correct: 41, retriever missed the gold passage: 27, gold passage read, answer taken from another: 25, partly right, too short: 5, partly right, partial overlap: 3, right passage, wrong span: 1, refused but answerable: 1
- **level=beginner**: retriever missed the gold passage: 10, correct: 6, gold passage read, answer taken from another: 5, answered but should have refused: 5, refused but answerable: 2, partly right, too short: 2, correctly refused: 1
- **level=detailed**: retriever missed the gold passage: 11, answered but should have refused: 3, partly right, too short: 2, correct: 2, refused but answerable: 2, partly right, partial overlap: 1
- **level=unlabelled**: correct: 35, gold passage read, answer taken from another: 23, retriever missed the gold passage: 18, partly right, partial overlap: 3, partly right, too short: 2, right passage, wrong span: 1

## Out of domain

Refusal rate 0.689, by distance {'far': 1.0, 'mid': 0.467, 'near': 0.6}.

- [near] Can I get a loan from my bank using my salary account? -> "No. MPP account cannot be used as collateral for a loan."
- [near] What is the current minimum wage in Nigeria? -> "A minimum of 18% of monthly basic salary, housing and transport allowances, with the employer contributing at least 10%."
- [near] How do I check my BVN on my phone? -> "Bank Verification Number (BVN): 11-digit number issued by banks to their customers as their universal ID in all commercial banks in Nigeria."
- [near] What is the difference between a current account and a savings account? -> "Yes. MPP is different from savings account maintained with a commercial bank because any savings made under the Plan can only be withdrawn a..."
- [near] How much tax should be deducted from my monthly salary? -> "3.29 The tax deductions shall be based on both income earned and principal amount when withdrawal is less than five (5) years for the exempt..."
- [near] Can my employer deduct money from my salary for a staff loan? -> "An employer can make all the contributions on behalf of the employee without making any deduction from the employee’s salary except that suc..."
- [mid] How do I renew my Nigerian international passport? -> "a) International Passport or any of the following: b) National Driver's License c) Permanent Voter's Card d) National Identity Card or enrol..."
- [mid] How do I register my small business with CAC? -> "To register with us, simply click ENROLL NOW OR download our Retirement Savings Account Form Account Opening Form (RSA) . Fill and walk into..."
- [mid] How do I verify that a land in Abuja has genuine documents? -> "5.1.4 The Mortgage Lender shall review the application form and verify the genuineness of the property offer."
- [mid] How do I change my name officially after marriage in Nigeria? -> "i. Marriage Certificate (only applicable in the case of marriage) ii) Newspaper publication iii) Sworn affidavit (for change of name) iv) Le..."
- [mid] How do I get a driver's licence in Nigeria? -> "ii. Staff Identity Card or any of the following a) National Driver's License b) Permanent Voter's Card c) International Passport (mandatory ..."
- [mid] What documents do I need to start an import business? -> "a) International Passport or any of the following: b) National Driver's License c) Permanent Voter's Card d) National Identity Card or enrol..."
- [mid] How do I report a fraud alert on my bank account? -> "We send SMS notification on any remittance made into Retirement Savings Accounts as they occur. It may be that your phone number changed and..."
- [mid] How do I apply for a Nigerian government job? -> "ii. Staff Identity Card or any of the following a) National Driver's License b) Permanent Voter's Card c) International Passport (mandatory ..."

## Human review

36 answers taken from another passage were checked by hand: 5 acceptable, 7 partly, 24 not. Correct answers: 43 by the automatic score, 48 after review, out of 134.

## Examples

### correct

- **Q** (faq_rule, plain): Has the MPP been successful in other Countries?
  - gold: Yes, MPP has been successful in countries like Ghana, Kenya, India, etc.
  - system: Yes, MPP has been successful in countries like Ghana, Kenya, India, etc.
- **Q** (faq_rule, plain): Can one have more than one RSA under the MPP?
  - gold: No. A contributor under the MPP shall only have one RSA in his/her lifetime.
  - system: No. A contributor under the MPP shall only have one RSA in his/her lifetime.
- **Q** (faq_rule, plain): Can an individual in the formal sector who already has an RSA also participate in the MPP?
  - gold: No. An individual who is contributing under the mandatory pension arrangement cannot participate in the MPP.
  - system: No. An individual who is contributing under the mandatory pension arrangement cannot participate in the MPP.
- **Q** (faq_rule, plain): What measures have been put in place by PenCom to safeguard the funds under the MPP?
  - gold: There is effective monitoring and supervision of the MPP funds by PenCom through daily monitoring of the Plan asset and investment decisions...
  - system: There is effective monitoring and supervision of the MPP funds by PenCom through daily monitoring of the Plan asset and investment decisions...

### retriever missed the gold passage

- **Q** (faq_rule, plain): Who can participate in the MPP?
  - gold: A Micro Pension participant must: i. Be a Nigerian; ii. Not below 18 years of age; iii. Have a legitimate source of income; iv. Belong to a ...
  - system: No. Retirees from the Formal Sector cannot participate in the MPP. MPP allows participation by the self-employed and person working in organ...
- **Q** (faq_rule, plain): Is there a provision for the guarantee of the safety of assets under the MPP?
  - gold: Yes. The PFC has provided full guarantee of the total pension assets under its custody. Thus, any asset lost will be refunded by the Custodi...
  - system: 2.8 Protection of Consumer Pension Assets, Data and Privacy The Commission shall ensure that appropriate measures are established to guarant...
- **Q** (faq_rule, plain): Would my Contributions under the MPP be subject to any taxes?
  - gold: No. Subject to the provisions of PRA 2014 and extant tax laws, all interests, dividends, profits, investments and other income accrued to Mi...
  - system: No. MPP only allows for conversion from MPP to mandatory CPS.
- **Q** (faq_rule, plain): Can I decide which financial instruments my Contributions should be invested in?
  - gold: No. Investment decisions are made by the PFAs in line with Investment Regulations issued by PenCom.
  - system: PFAs can only invest in the following instruments: Equities; Federal Government Securities; State/Local Government Bonds; Corporate Debt Sec...

### gold passage read, answer taken from another

- **Q** (faq_rule, plain): Why Micro Pension?
  - gold: Micro Pension guarantees secured future through steady income at retirement. It reduces old age poverty and the process has been made easy, ...
  - system: Micro Pension Plan: An arrangement under the CPS, which allows the self-employed and persons working in organizations with less than three e...
- **Q** (faq_rule, plain): Is the mandatory CPS different from the MPP?
  - gold: The mandatory pension and MPP are arrangements under the CPS. A major difference between the two is the nature of participation. The mandato...
  - system: No. MPP only allows for conversion from MPP to mandatory CPS.
- **Q** (faq_rule, plain): How do I register/enroll for MPP?
  - gold: A prospective Micro Pension contributor can enroll/register through any PFA of his/her choice, obtain and complete the RSA Opening Form eith...
  - system: 1.6.10 PFAs shall register MPP Contributors in line with the provisions of these Guidelines and the Guidelines for Micro Pension Plan, issue...
- **Q** (faq_rule, plain): Where do I locate the PFA of my choice?
  - gold: The detailed list and addresses of all Licensed PFAs can be accessed via PenCom's website- www.pencom.gov.ng.
  - system: 5.2.1 PFA shall confirm from its database the existence of the applicants Personal Identification Number (PIN), whether the applicant is on ...

### answered but should have refused

- **Q** (own, legal): Is there a limit to how much extra money I can add to my pension account on my own?
  - gold: (no answer)
  - system: There is no stipulated minimum amount of contribution under the MPP because it is dependent on the Contributor’s pension aspiration and fina...
- **Q** (own, legal): Who can see my details once my pension company sends them to the national database?
  - gold: (no answer)
  - system: Yes, you can view your RSA details online 24/7, simply log on to https://web.fcmbpensions.com/clientportal/Account/Login supply your usernam...
- **Q** (own, legal): Will my pension company charge me to update my phone number and address?
  - gold: (no answer)
  - system: Yes, in accordance with the guidelines of the National Pension Commission. We charge administrative and management fees as stipulated by Pen...
- **Q** (own, legal): Can I register for my pension account online from my phone, or must I go to the office?
  - gold: (no answer)
  - system: A retiree/prospective retiree who has successfully completed his/her data recapture, can register on the Online Enrolment Application hosted...

### partly right, too short

- **Q** (faq_rule, plain): What happens if the Micro Pension Contributor gets a formal employment?
  - gold: The Micro Pension Contributor who secures a formal employment shall notify his/her PFA for conversion into the mandatory pension. The Micro ...
  - system: The Micro Pension Contributor who secures a formal employment shall notify his/her PFA for conversion into the mandatory pension.
- **Q** (faq_rule, plain): WHO IS A CUSTODIAN?
  - gold: A Pension Fund Custodian (PFC) is a company licensed by the National Pension Commission to keep pension money and assets in the RSA on trust...
  - system: Pension Fund Custodian (PFC): A company licensed by National Pension Commission to keep custody of the pension funds and assets in Nigeria.
- **Q** (own, plain): I just got my first job. Can I pick any pension company I want, or does my boss choose for me?
  - gold: Employees are at liberty to open an RSA with any PFA of their choice. However, there are exceptions where a State has an arrangement to sele...
  - system: Employees are at liberty to open an RSA with any PFA of their choice.
- **Q** (own, plain): My company has its own pension company just for its staff. Can I move my pension to a different one I like?
  - gold: Every employee may decide to join the contributory pension scheme or move his RSA from a closed PFA to a PFA of his choice subject to such r...
  - system: Every employee may decide to join the contributory pension scheme or move his RSA from a closed PFA to a PFA of his choice subject to such r...

### partly right, partial overlap

- **Q** (faq_rule, plain): What is Micro Pension Plan (MPP)?
  - gold: MPP refers to an arrangement under the CPS that allows the self employed and persons working in organizations with less than three (3) emplo...
  - system: Micro Pension Plan: An arrangement under the CPS, which allows the self-employed and persons working in organizations with less than three e...
- **Q** (faq_rule, plain): What is the minimum amount of contribution acceptable under the MPP?
  - gold: There is no stipulated minimum amount of contribution under the MPP because it is dependent on the Contributor’s pension aspiration and fina...
  - system: There is no stipulated minimum amount of contribution under the MPP because it is dependent on the Contributor’s pension aspiration and fina...
- **Q** (faq_rule, plain): WHAT IS A RETIREMENT SAVINGS ACCOUNT (RSA)?
  - gold: Every employee or contributor under the new pension scheme is expected to open a RSA in his/her name with any PFA of his/her choice into whi...
  - system: Retirement Savings Account (RSA): This is an account opened by an employee with a PFA of his/her choice into which all his/her pension contr...
- **Q** (own, legal): My company registered me for pension when I joined. How will I get proof that I’m registered?
  - gold: In the case of registrations initiated by employers, PFAs shall issue evidence of registration to employees through their employers within 5...
  - system: 1.6.14 In the case of registrations initiated by employers, PFAs shall issue evidence of registration to employees through their employers w...

### refused but answerable

- **Q** (own, legal): A PFA agent told me my current pension company is bad and will lose my money, so I should move to them. Are they even allowed to talk like that?
  - gold: It should be noted that encouraging a free market environment is vital to enhance effective service delivery for consumers. Therefore, Pensi...
  - system: (refused)
- **Q** (own, plain): I’m a tailor on micro pension and I need some money urgently. Can I take some out before I retire?
  - gold: A Micro Pension Contributor can withdraw an amount from his/her contingent portion by applying to his/her PFA in a prescribed format.
  - system: (refused)
- **Q** (own, legal): I’ve had my pension account for years and they want me to redo my registration. Do I need the same documents as someone opening a new account?
  - gold: Except as otherwise stated in Section 5.3 of these Guidelines, all data and documentation requirements applicable to New RSA registrations o...
  - system: (refused)
- **Q** (own, legal): I’m a Muslim worried about my pension being invested the halal way. Who advises PenCom on Islamic finance?
  - gold: The FRACE shall serve as an advisory body to the Commission on Islamic Finance matters and specifically on all subsidiary legislations on in...
  - system: (refused)

### right passage, wrong span

- **Q** (faq_rule, plain): What is the length of the Annuity Guaranteed Period under the MPP?
  - gold: The Retiree Life Annuity is guaranteed for 10 years. Thus, if a retiree dies before 10 years, the balance of the equivalent monthly pension ...
  - system: The Retiree Life Annuity is guaranteed for 10 years.

### correctly refused

- **Q** (own, legal): A pension advert said I will get 15% return. What return should I really expect from my pension?
  - gold: (no answer)
  - system: (refused)

