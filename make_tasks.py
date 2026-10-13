"""Generates task sets. Documents are SYNTHETIC: fictional names, invalid-by-design IDs. No real personal data."""
import json, random
random.seed(7)
def w(name, rows):
    with open(f"tasks/{name}.jsonl", "w", encoding="utf-8") as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")

qa = [("hi","भारत की राजधानी क्या है?","नई दिल्ली"),("hi","एक साल में कितने महीने होते हैं? केवल संख्या लिखें।","12"),
      ("hi","गंगा नदी किस समुद्र/खाड़ी में गिरती है?","बंगाल की खाड़ी"),("ta","இந்தியாவின் தேசிய பறவை எது?","மயில்"),
      ("ta","ஒரு வாரத்தில் எத்தனை நாட்கள்? எண் மட்டும்.","7"),("bn","ভারতের জাতীয় পশু কী?","বাঘ"),
      ("bn","এক ঘণ্টায় কত মিনিট? শুধু সংখ্যা।","60"),("mr","महाराष्ट्राची राजधानी कोणती?","मुंबई"),
      ("mr","एका दिवसात किती तास असतात? फक्त संख्या.","24")]
w("indic_qa", [{"id":f"qa-{i:03d}","suite":"indic_qa","lang":l,"scorer":"exact",
   "prompt":f"Answer in the same language, as briefly as possible.\nQuestion: {q}","reference":a} for i,(l,q,a) in enumerate(qa,1)])

tr = [("hi","Please send the invoice by Friday.","कृपया शुक्रवार तक चालान भेजें।"),
      ("hi","The bank branch is closed on Sunday.","बैंक शाखा रविवार को बंद रहती है।"),
      ("ta","The train is late by two hours.","ரயில் இரண்டு மணி நேரம் தாமதமாக உள்ளது."),
      ("bn","Your loan application has been approved.","আপনার ঋণের আবেদন অনুমোদিত হয়েছে।"),
      ("mr","Please pay the electricity bill today.","कृपया आज वीज बिल भरा.")]
names={"hi":"Hindi","ta":"Tamil","bn":"Bengali","mr":"Marathi"}
w("translation", [{"id":f"tr-{i:03d}","suite":"translation","lang":l,"scorer":"chrf",
   "prompt":f"Translate into {names[l]}. Reply with the translation only.\n{s}","reference":t} for i,(l,s,t) in enumerate(tr,1)])

first=["Aarav","Diya","Kabir","Meera","Rohan","Ananya","Vikram","Isha"]; last=["Sharma","Iyer","Das","Patil","Reddy","Khan","Nair","Gupta"]
docs=[]
for i in range(1,7):
    nm=f"{random.choice(first)} {random.choice(last)}"
    pan="ZZ"+"".join(random.choice("ABCDEFGHJK") for _ in range(3))+f"{random.randint(1000,9999)}Z"  # ZZ prefix: synthetic marker
    dob=f"{random.randint(1,28):02d}/{random.randint(1,12):02d}/{random.randint(1965,2000)}"
    txt=f"INCOME TAX DEPARTMENT  GOVT. OF INDIA  [SYNTHETIC SAMPLE]\nPermanent Account Number Card\n{pan}\nName / नाम\n{nm.upper()}\nDate of Birth / जन्म की तारीख\n{dob}"
    docs.append({"id":f"doc-pan-{i:03d}","suite":"doc_extraction","lang":"en","scorer":"fields",
      "prompt":"Extract JSON with keys pan, name, dob from this card text:\n"+txt,"reference":{"pan":pan,"name":nm.upper(),"dob":dob}})
for i in range(1,6):
    gst=f"99ZZZZZ{random.randint(1000,9999)}Z1Z{random.randint(0,9)}"; taxable=random.randint(5,90)*1000; rate=random.choice([5,12,18])
    tax=taxable*rate//100; inv=f"INV/25-26/{random.randint(100,999)}"
    txt=(f"TAX INVOICE [SYNTHETIC]\nSeller: {random.choice(last)} Traders, Pune\nGSTIN: {gst}\nInvoice No: {inv}\n"
         f"Taxable value: Rs {taxable:,}\nCGST @{rate/2:g}%: Rs {tax/2:,.2f}\nSGST @{rate/2:g}%: Rs {tax/2:,.2f}\nTotal: Rs {taxable+tax:,.2f}")
    docs.append({"id":f"doc-gst-{i:03d}","suite":"doc_extraction","lang":"en","scorer":"fields",
      "prompt":"Extract JSON with keys gstin, invoice_no, taxable_value, total (numbers without commas or symbols) from:\n"+txt,
      "reference":{"gstin":gst,"invoice_no":inv,"taxable_value":taxable,"total":f"{taxable+tax:.2f}".rstrip("0").rstrip(".")}})
for i in range(1,5):
    bal=random.randint(20,200)*1000; lines=[]; txns=[]
    for d in range(1,6):
        amt=random.randint(1,40)*250; cr=random.random()<0.4; bal=bal+amt if cr else bal-amt
        lines.append(f"0{d}-09-2025  {'UPI/CR' if cr else 'UPI/DR'}/{random.randint(10**8,10**9)}  {'' if cr else amt}  {amt if cr else ''}  {bal}")
        txns.append((cr,amt))
    debit=sum(a for c,a in txns if not c); credit=sum(a for c,a in txns if c)
    txt="STATEMENT OF ACCOUNT [SYNTHETIC]  Acct XXXX0000\nDate  Narration  Debit  Credit  Balance\n"+"\n".join(lines)
    docs.append({"id":f"doc-bank-{i:03d}","suite":"doc_extraction","lang":"en","scorer":"fields",
      "prompt":"Extract JSON with keys total_debit, total_credit, closing_balance (integers) from:\n"+txt,
      "reference":{"total_debit":debit,"total_credit":credit,"closing_balance":bal}})
w("doc_extraction", docs)
print("ok")
