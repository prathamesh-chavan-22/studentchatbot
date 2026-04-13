#!/usr/bin/env python3
"""
Bulk import script to add Hinglish questions and additional variants 
for all 48 FAQ entries.
"""

import json
from pathlib import Path

# Hinglish questions for each FAQ ID
HINGLISH_QUESTIONS = {
    "faq_1": [
        "FYJC online admission process kya hai?",
        "11th admission kaise hota hai Maharashtra me?",
        "FYJC portal kya hai?",
        "Online admission kaise karein?"
    ],
    "faq_2": [
        "11th admission ke liye kaun apply kar sakta hai?",
        "Kaun students 11th class le sakte hain?",
        "10th pass students admission le sakte hain?"
    ],
    "faq_3": [
        "Online registration zaroori hai kya?",
        "Kya offline application accept hota hai?",
        "Registration compulsory hai?"
    ],
    "faq_4": [
        "Online register kaise karein?",
        "Login ID aur password kaise milega?",
        "Registration process kya hai?",
        "Website par account kaise banayein?"
    ],
    "faq_5": [
        "Application form edit kar sakte hain kya?",
        "Form me sudhar kaise karein?",
        "Correction kaise possible hai?"
    ],
    "faq_6": [
        "Kitne colleges ki preference de sakte hain?",
        "Maximum kitne college choose kar sakte hain?",
        "Minimum kitne college zaroori hain?"
    ],
    "faq_7": [
        "Admission ke liye kaun se documents chahiye?",
        "Kaunsi papers submit karni hoti hain?",
        "Documents list kya hai?"
    ],
    "faq_8": [
        "Main dusre board se hoon, kya karun?",
        "Other board students kaise apply karein?",
        "CBSE/ICSE se hoon toh kya karna hai?"
    ],
    "faq_9": [
        "ATKT kya hai aur kaun eligible hai?",
        "ATKT wale students kab apply karein?",
        "Agar 1-2 subjects me fail hoon toh?"
    ],
    "faq_10": [
        "Quota types kya kya hain?",
        "Kitne prakar ke quota hote hain?",
        "Management quota kya hai?"
    ],
    "faq_11": [
        "Quota seats ke liye online application zaroori hai kya?",
        "Kya quota ke liye bhi form bharna padta hai?"
    ],
    "faq_12": [
        "Kitne rounds hote hain admission ke?",
        "Admission rounds kab hote hain?",
        "Open to all round kya hai?"
    ],
    "faq_13": [
        "Agar first preference college me admission nahi liya toh?",
        "First choice college chhodne se kya hoga?",
        "Admission lene se mana karun toh?"
    ],
    "faq_14": [
        "Kya main multiple rounds me participate kar sakta hoon?",
        "Har round me apply kar sakte hain kya?"
    ],
    "faq_15": [
        "Registration fee kitni hai?",
        "Fee kaise pay karein?",
        "Payment options kya hain?"
    ],
    "faq_16": [
        "Kya offline payment option hai?",
        "Cash payment kar sakte hain kya?"
    ],
    "faq_17": [
        "Login details bhool gaya toh kya karun?",
        "Password reset kaise karein?",
        "ID password yaad nahi aa raha?"
    ],
    "faq_18": [
        "Application me problem ho toh kahan contact karein?",
        "Help kahan se milegi?",
        "Support number kya hai?"
    ],
    "faq_19": [
        "College preference change kar sakte hain kya?",
        "Choice kaise badlein?",
        "College list update kaise karein?"
    ],
    "faq_20": [
        "Merit list me naam aane ke baad kya karein?",
        "Admission confirm kaise hota hai?",
        "Documents kab submit karein?"
    ],
    "faq_21": [
        "Admission cancel kaise karein?",
        "Withdrawal kaise karein application ka?",
        "Admission process se bahar kaise niklein?"
    ],
    "faq_22": [
        "Original documents verify kaun karega?",
        "Documents checking kahan hoti hai?",
        "College verification kaise hota hai?"
    ],
    "faq_23": [
        "Stream change kar sakte hain kya submission ke baad?",
        "Arts se Science ja sakte hain kya?",
        "Stream kaise badlein?"
    ],
    "faq_24": [
        "Agar application aur documents me farak mila toh?",
        "Information mismatch hone par kya hoga?",
        "Documents galat nikle toh?"
    ],
    "faq_25": [
        "Agar marksheet fake nikla toh kya hoga?",
        "Fake documents ka kya punishment hai?",
        "Bogus certificate se kya hoga?"
    ],
    "faq_26": [
        "Zero Round kya hota hai?",
        "Zero Round me kya hota hai?",
        "Pehle round se pehle kya process hai?"
    ],
    "faq_27": [
        "Night school ke liye online process hai kya?",
        "Evening college me admission kaise lein?",
        "Raatri shala admission process?"
    ],
    "faq_28": [
        "Open to All Round kya hai?",
        "Special round kaise hota hai?",
        "Bina quota ke admission kaise milega?"
    ],
    "faq_29": [
        "HSVC admission kaise honge is saal?",
        "HSVC ke liye kya process hai?",
        "Vocational course admission?"
    ],
    "faq_30": [
        "Original documents kab submit karein?",
        "Documents kab jama karne hain?",
        "Certificate kab dikhana hai?"
    ],
    "faq_31": [
        "Athletes ke liye kaun se documents chahiye?",
        "Sports quota ke liye kya lagega?",
        "Khiladi reservation kaise milegi?"
    ],
    "faq_32": [
        "Non-Creamy Layer certificate nahi hai toh?",
        "OBC certificate kaise milega?",
        "Certificate nahi toh kya karun?"
    ],
    "faq_33": [
        "Leaving Certificate par kaunsi date honi chahiye?",
        "LC date kaise hoti hai?",
        "School leaving certificate date issue?"
    ],
    "faq_34": [
        "Document file size kitni honi chahiye?",
        "Maximum file size kya hai upload ke liye?",
        "Photo size kya rakhein?"
    ],
    "faq_35": [
        "Open School student ke paas LC nahi hai toh?",
        "NIOS students kaise apply karein?",
        "Bina LC ke admission possible hai?"
    ],
    "faq_36": [
        "Admission cancel kar sakte hain kya?",
        "Admission withdrawal kaise karein?",
        "Taken admission se bahar kaise niklein?"
    ],
    "faq_37": [
        "Freedom Fighter ward ke liye kya documents chahiye?",
        "Swatantrata Sainik quota kaise milega?",
        "FF certificate kahan se milega?"
    ],
    "faq_38": [
        "Anath bachon ke liye kya documents chahiye?",
        "Orphan certificate kaise milega?",
        "Bina mata-pita ke students ke liye?"
    ],
    "faq_39": [
        "Foreign se aaye students ke liye kya chahiye?",
        "NRI admission process kya hai?",
        "Embassy certificate kaise milega?"
    ],
    "faq_40": [
        "Maharashtra ke bahar se aaye students marks kaise dalein?",
        "Other state board marks kaise calculate honge?",
        "Best 5 subjects kaise choose karein?"
    ],
    "faq_41": [
        "Science stream ka medium Marathi dikh raha hai, English kaise karein?",
        "Medium change kaise karein?",
        "English medium science kaise milega?"
    ],
    "faq_42": [
        "Kya Arts/Sports ke extra marks Best 5 me judenge?",
        "Extra marks add hote hain kya?",
        "Sports marks consideration?"
    ],
    "faq_43": [
        "Marksheet par maa ka naam nahi hai, registration kaise karein?",
        "Mother name missing toh kya karein?",
        "Bina mother name ke form kaise bharein?"
    ],
    "faq_44": [
        "Galat mobile number/email daal diya, kaise badlein?",
        "Contact details kaise update karein?",
        "Phone number change kaise karein?"
    ],
    "faq_45": [
        "CBSE additional subject marks kab count honge?",
        "6th subject kab consider hota hai?",
        "Extra subject kab use kar sakte hain?"
    ],
    "faq_46": [
        "ICSE marks bharte waqt kya dhyan rakhein?",
        "ICSE me kaun se marks lene chahiye?",
        "Group III subjects count honge kya?"
    ],
    "faq_47": [
        "Deadline khatam ho gaya, ab kaise apply karein?",
        "Late application kaise karein?",
        "Time cross ho gaya toh?"
    ],
    "faq_48": [
        "11th me fail ho gaya, dobara apply kar sakta hoon?",
        "Previously Passed kya hai?",
        "Repeat admission kaise lein?"
    ]
}

# Additional English questions for better coverage
ADDITIONAL_EN_QUESTIONS = {
    "faq_1": [
        "How to apply for FYJC admission?",
        "Explain the 11th standard admission procedure"
    ],
    "faq_2": [
        "Eligibility criteria for 11th admission?",
        "Who is eligible for FYJC?"
    ],
    "faq_3": [
        "Is offline form available?",
        "Can I submit paper application?"
    ],
    "faq_4": [
        "Steps for student registration?",
        "How to create account on FYJC portal?"
    ],
    "faq_5": [
        "How to unlock form for editing?",
        "Can I make changes after submission?"
    ],
    "faq_6": [
        "How many college options can I fill?",
        "Maximum and minimum college choices?"
    ],
    "faq_7": [
        "What certificates are needed for admission?",
        "Required documents list for FYJC"
    ],
    "faq_8": [
        "I'm from CBSE board, how to apply?",
        "Non-State Board student admission process"
    ],
    "faq_9": [
        "Provisional admission for ATKT students?",
        "When can ATKT students apply?"
    ],
    "faq_10": [
        "What are the different quota categories?",
        "Explain reservation types in FYJC"
    ],
    "faq_11": [
        "Is online form required for quota seats?",
        "Do I need to apply online for reservation?"
    ],
    "faq_12": [
        "How many admission rounds are there?",
        "Explain the round-wise admission process"
    ],
    "faq_13": [
        "What if I skip my first allotment?",
        "Consequences of not taking admitted seat?"
    ],
    "faq_14": [
        "Can I try for better college in next round?",
        "Multiple round participation rules?"
    ],
    "faq_15": [
        "What is the application fee?",
        "How to pay registration charges?"
    ],
    "faq_16": [
        "Can I pay fee at center?",
        "Is cash payment accepted?"
    ],
    "faq_17": [
        "Forgot login credentials, help?",
        "How to recover my account?"
    ],
    "faq_18": [
        "Where to get help for application?",
        "Helpline number for FYJC admission?"
    ],
    "faq_19": [
        "How to modify college preferences?",
        "Can I rearrange college choices?"
    ],
    "faq_20": [
        "What to do after seat allotment?",
        "Steps to confirm admission?"
    ],
    "faq_21": [
        "How to withdraw from admission process?",
        "Cancel my application procedure?"
    ],
    "faq_22": [
        "Who verifies original documents?",
        "Document verification process at college?"
    ],
    "faq_23": [
        "Can I switch from Arts to Science?",
        "How to change stream after form submission?"
    ],
    "faq_24": [
        "What if documents don't match application?",
        "Discrepancy in submitted information?"
    ],
    "faq_25": [
        "What happens if marksheet is fraudulent?",
        "Penalty for fake documents?"
    ],
    "faq_26": [
        "What is Zero Round in FYJC?",
        "Purpose of Zero Round?"
    ],
    "faq_27": [
        "Is online admission for night schools?",
        "Evening school admission process?"
    ],
    "faq_28": [
        "What is Open to All Round?",
        "How does special round work?"
    ],
    "faq_29": [
        "How are HSVC admissions conducted?",
        "Vocational stream admission process?"
    ],
    "faq_30": [
        "When to submit original certificates?",
        "Document submission timeline?"
    ],
    "faq_31": [
        "Documents for sports quota admission?",
        "Athlete reservation requirements?"
    ],
    "faq_32": [
        "What if I don't have NC certificate?",
        "OBC non-creamy layer certificate issue?"
    ],
    "faq_33": [
        "What date should be on TC?",
        "School leaving certificate date format?"
    ],
    "faq_34": [
        "Maximum file size for document upload?",
        "Photo and document size limit?"
    ],
    "faq_35": [
        "NIOS student without TC, what to do?",
        "Open school admission without LC?"
    ],
    "faq_36": [
        "Can I cancel after taking admission?",
        "Admission withdrawal process?"
    ],
    "faq_37": [
        "Documents for Freedom Fighter quota?",
        "How to claim FF reservation?"
    ],
    "faq_38": [
        "Documents required for orphan students?",
        "How to get orphan certificate?"
    ],
    "faq_39": [
        "Admission process for foreign students?",
        "Documents for NRI/OCI students?"
    ],
    "faq_40": [
        "How to fill marks for other state boards?",
        "Best 5 subjects calculation for non-Maharashtra?"
    ],
    "faq_41": [
        "Science stream showing wrong medium?",
        "How to select English medium for Science?"
    ],
    "faq_42": [
        "Are sports marks added to merit?",
        "Extra-curricular marks consideration?"
    ],
    "faq_43": [
        "Mother name not on marksheet, registration?",
        "How to register without mother's name?"
    ],
    "faq_44": [
        "Wrong contact details submitted, change?",
        "How to update mobile number and email?"
    ],
    "faq_45": [
        "When is 6th subject considered in CBSE?",
        "Additional subject marks policy?"
    ],
    "faq_46": [
        "ICSE mark entry guidelines?",
        "Which ICSE subjects to consider?"
    ],
    "faq_47": [
        "Missed deadline, can I still apply?",
        "Late registration possibility?"
    ],
    "faq_48": [
        "Failed in 11th, can I reapply?",
        "Repeat year admission process?"
    ]
}

# Additional Marathi questions
ADDITIONAL_MR_QUESTIONS = {
    "faq_1": [
        "FYJC प्रवेशासाठी अर्ज कसा करावा?",
        "अकरावी प्रवेश प्रक्रिया स्पष्ट करा"
    ],
    "faq_2": [
        "११ वी प्रवेशासाठी पात्रता काय आहे?",
        "कोण विद्यार्थी FYJC साठी अर्ज करू शकतात?"
    ],
    "faq_3": [
        "ऑफलाईन फॉर्म उपलब्ध आहे का?",
        "कागदावर अर्ज करता येतो का?"
    ],
    "faq_4": [
        "विद्यार्थी नोंदणीची पायरी काय आहे?",
        "FYJC पोर्टलवर अकाउंट कसे बनवावे?"
    ],
    "faq_5": [
        "फॉर्म एडिट करण्यासाठी कसे अनलॉक करावे?",
        "सबमिशन नंतर बदल करता येतात का?"
    ],
    "faq_6": [
        "किती कॉलेजचे पर्याय भरता येतात?",
        "कमाल आणि किमान कॉलेज निवड काय आहे?"
    ],
    "faq_7": [
        "प्रवेशासाठी कोणती प्रमाणपत्रे लागतात?",
        "FYJC साठी आवश्यक कागदपत्रे यादी"
    ],
    "faq_8": [
        "मी CBSE बोर्डामधून आहे, कसे अर्ज करावे?",
        "राज्य मंडळा व्यतिरिक्त विद्यार्थी प्रक्रिया"
    ],
    "faq_9": [
        "ATKT विद्यार्थ्यांसाठी तात्पुरता प्रवेश?",
        "ATKT विद्यार्थ्यांनी कधी अर्ज करावा?"
    ],
    "faq_10": [
        "वेगवेगळे कोटा प्रकार कोणते?",
        "आरक्षणाचे प्रकार स्पष्ट करा"
    ],
    "faq_11": [
        "कोटा जागांसाठी ऑनलाईन फॉर्म आवश्यक?",
        "आरक्षणासाठी ऑनलाईन अर्ज करावा लागतो?"
    ],
    "faq_12": [
        "किती प्रवेश फेऱ्या आहेत?",
        "फेरीनुसार प्रवेश प्रक्रिया स्पष्ट करा"
    ],
    "faq_13": [
        "पहिल्या आलेल्या सीटला सोडले तर काय होईल?",
        "मिळालेला प्रवेश न घेतल्यास परिणाम?"
    ],
    "faq_14": [
        "पुढील फेरीत चांगले कॉलेज मिळू शकते का?",
        "एकापेक्षा जास्त फेऱ्यांमध्ये सहभाग नियम?"
    ],
    "faq_15": [
        "अर्ज फी किती आहे?",
        "नोंदणी शुल्क कसे भरावे?"
    ],
    "faq_16": [
        "केंद्रावर फी भरता येते का?",
        "रोख payment स्वीकारले जाते का?"
    ],
    "faq_17": [
        "लॉगिन विसरलो, मदत हवी?",
        "माझे अकाउंट कसे पुनर्प्राप्त करावे?"
    ],
    "faq_18": [
        "अर्जासाठी कुठे मदत मिळेल?",
        "FYJC प्रवेशासाठी हेल्पलाइन नंबर?"
    ],
    "faq_19": [
        "कॉलेज प्राधान्यक्रम कसा बदलावा?",
        "कॉलेज निवड पुन्हा मांडता येते का?"
    ],
    "faq_20": [
        "सीट मिळाल्यानंतर काय करावे?",
        "प्रवेश निश्चित करण्याच्या पायऱ्या?"
    ],
    "faq_21": [
        "प्रवेश प्रक्रियेतून माघार कशी घ्यावी?",
        "अर्ज रद्द करण्याची प्रक्रिया?"
    ],
    "faq_22": [
        "मूळ कागदपत्रे कोण तपासतो?",
        "कॉलेजमध्ये कागदपत्र पडताळणी प्रक्रिया?"
    ],
    "faq_23": [
        "कला ते विज्ञान शाखा बदलता येते का?",
        "फॉर्म सबमिट केल्यानंतर स्ट्रीम कसे बदलावे?"
    ],
    "faq_24": [
        "कागदपत्रे आणि अर्जामध्ये फरक आढळल्यास?",
        "सबमिट केलेल्या माहितीमध्ये विसंगती?"
    ],
    "faq_25": [
        "मार्कशीट बनावट आढळल्यास काय होईल?",
        "खोट्या कागदपत्रांसाठी शिक्षा?"
    ],
    "faq_26": [
        "FYJC मध्ये शून्य फेरी म्हणजे काय?",
        "शून्य फेरीचा उद्देश?"
    ],
    "faq_27": [
        "रात्र शाळांसाठी ऑनलाईन प्रवेश आहे का?",
        "संध्याकाळच्या शाळेची प्रवेश प्रक्रिया?"
    ],
    "faq_28": [
        "ओपन टू ऑल राउंड म्हणजे काय?",
        "विशेष फेरी कशी काम करते?"
    ],
    "faq_29": [
        "HSVC प्रवेश कसे होतात?",
        "व्होकेशनल स्ट्रीम प्रवेश प्रक्रिया?"
    ],
    "faq_30": [
        "मूळ प्रमाणपत्रे कधी जमा करावीत?",
        "कागदपत्र सबमिशनची वेळ?"
    ],
    "faq_31": [
        "क्रीडा कोटासाठी कागदपत्रे?",
        "खेळाडू आरक्षणाची आवश्यकता?"
    ],
    "faq_32": [
        "NC प्रमाणपत्र नसेल तर काय?",
        "OBC नॉन-क्रीमी लेअर प्रमाणपत्र समस्या?"
    ],
    "faq_33": [
        "TC वर कोणती तारीख असावी?",
        "शाळा सोडल्याचा दाखला तारीख फॉरमॅट?"
    ],
    "faq_34": [
        "कागदपत्र अपलोडसाठी कमाल फाइल साइज?",
        "फोटो आणि कागदपत्र साइज मर्यादा?"
    ],
    "faq_35": [
        "NIOS विद्यार्थी TC शिवाय, काय करावे?",
        "LC शिवाय ओपन स्कूल प्रवेश?"
    ],
    "faq_36": [
        "प्रवेश घेतल्यानंतर रद्द करता येते का?",
        "प्रवेश माघार प्रक्रिया?"
    ],
    "faq_37": [
        "स्वातंत्र्य सैनिक कोटासाठी कागदपत्रे?",
        "FF आरक्षण कसे मिळवावे?"
    ],
    "faq_38": [
        "अनाथ विद्यार्थ्यांसाठी आवश्यक कागदपत्रे?",
        "अनाथ प्रमाणपत्र कसे मिळवावे?"
    ],
    "faq_39": [
        "परदेशी विद्यार्थ्यांसाठी प्रवेश प्रक्रिया?",
        "NRI/OCI विद्यार्थ्यांसाठी कागदपत्रे?"
    ],
    "faq_40": [
        "इतर राज्य बोर्डांसाठी गुण कसे भरावे?",
        "महाराष्ट्रा व्यतिरिक्त विद्यार्थ्यांसाठी Best 5?"
    ],
    "faq_41": [
        "विज्ञान शाखेचे माध्यम चुकीचे दिसते?",
        "विज्ञानासाठी इंग्रजी माध्यम कसे निवडावे?"
    ],
    "faq_42": [
        "क्रीडा गुण मेरिटमध्ये जोडले जातात का?",
        "अतिरिक्त-पाठ्यक्रम गुण विचार?"
    ],
    "faq_43": [
        "मार्कशीटवर आईचे नाव नाही, नोंदणी?",
        "आईच्या नावाशिवाय नोंदणी कशी करावी?"
    ],
    "faq_44": [
        "चुकीचे संपर्क तपशील दिले, बदल कसे करावे?",
        "मोबाईल नंबर आणि ईमेल कसे अपडेट करावे?"
    ],
    "faq_45": [
        "CBSE मध्ये 6वा विषय कधी विचारात घेतला जातो?",
        "अतिरिक्त विषय गुण धोरण?"
    ],
    "faq_46": [
        "ICSE गुण नोंदणी मार्गदर्शक?",
        "कोणते ICSE विषय विचारात घ्यावेत?"
    ],
    "faq_47": [
        "मुदत संपली, तरीही अर्ज करता येतो का?",
        "उशिरा नोंदणी शक्यता?"
    ],
    "faq_48": [
        "११ वी मध्ये नापास, पुन्हा अर्ज करू शकतो?",
        "पुन्हा वर्ष प्रवेश प्रक्रिया?"
    ]
}


def bulk_import():
    """Add Hinglish and additional questions to all FAQs."""
    
    base_dir = Path(__file__).parent
    json_path = base_dir / "questions_answers.json"
    
    # Load data
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    stats = {"hinglish_added": 0, "en_added": 0, "mr_added": 0}
    
    for item in data:
        faq_id = item["id"]
        
        # Add Hinglish questions
        if faq_id in HINGLISH_QUESTIONS:
            hinglish_variant = None
            for v in item["variants"]:
                if v["lang"] == "hinglish":
                    hinglish_variant = v
                    break
            
            if not hinglish_variant:
                # Create hinglish variant with English answer
                en_answer = ""
                for v in item["variants"]:
                    if v["lang"] == "en":
                        en_answer = v["answer"]
                        break
                hinglish_variant = {"lang": "hinglish", "questions": [], "answer": en_answer}
                item["variants"].append(hinglish_variant)

            # Add new hinglish questions
            for q in HINGLISH_QUESTIONS[faq_id]:
                if q not in hinglish_variant["questions"]:
                    hinglish_variant["questions"].append(q)
                    stats["hinglish_added"] += 1

        # Add additional English questions
        if faq_id in ADDITIONAL_EN_QUESTIONS:
            en_variant = None
            for v in item["variants"]:
                if v["lang"] == "en":
                    en_variant = v
                    break

            if en_variant:
                for q in ADDITIONAL_EN_QUESTIONS[faq_id]:
                    if q not in en_variant["questions"]:
                        en_variant["questions"].append(q)
                        stats["en_added"] += 1

        # Add additional Marathi questions
        if faq_id in ADDITIONAL_MR_QUESTIONS:
            mr_variant = None
            for v in item["variants"]:
                if v["lang"] == "mr":
                    mr_variant = v
                    break

            if mr_variant:
                for q in ADDITIONAL_MR_QUESTIONS[faq_id]:
                    if q not in mr_variant["questions"]:
                        mr_variant["questions"].append(q)
                        stats["mr_added"] += 1
    
    # Save updated data
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print("=" * 50)
    print("Bulk Import Complete!")
    print("=" * 50)
    print(f"Hinglish questions added: {stats['hinglish_added']}")
    print(f"English questions added:  {stats['en_added']}")
    print(f"Marathi questions added:  {stats['mr_added']}")
    print(f"Total questions added:    {sum(stats.values())}")
    print(f"\nFile saved: {json_path}")


if __name__ == "__main__":
    bulk_import()
