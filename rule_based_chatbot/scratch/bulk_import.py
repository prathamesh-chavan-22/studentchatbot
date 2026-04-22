import requests
import time

BASE_URL = "http://103.150.187.129:8005"
LOGIN_URL = f"{BASE_URL}/api/admin/login"
QNA_URL = f"{BASE_URL}/api/admin/qna"

# Default credentials
USER = "admin"
PASS = "admin123"

# Data to import
DATA = [
    {
        "question": "माझा अर्ज भरण्याची प्रक्रिया पूर्ण झाली असताना देखील, अर्ज पूर्ण झालेला नाही असे दर्शविले जाते किंवा लॉक करताना त्रुटी येते, याचे कारण काय आहे आणि मी यावर काय उपाय करू शकतो?",
        "answer": "अर्ज भरण्याच्या प्रक्रियेतील सर्व आवश्यक फील्ड्स भरले आहेत किंवा नाही याची खात्री करा. जर तुम्ही सर्व आवश्यक माहिती भरली असेल आणि तुमचा अर्ज पूर्ण झाला असेल, तर तुम्ही तुमचा अर्ज लॉक करू शकता. जर तुम्हाला अजूनही त्रुटी येत असेल, तर कृपया थोड्या वेळाने पुन्हा प्रयत्न करा किंवा तुमच्या अर्जाची स्थिती तपासा. तुम्ही तुमचा अर्ज लॉक करण्यापूर्वी तुमच्या अर्जाची पुनर्तपासणी करून घ्या आणि आवश्यक असल्यास तुमचा अर्ज अनलॉक करून त्यातील त्रुटी दूर करा."
    },
    {
        "question": "मी अनेक कॉलेजे निवडण्याचा प्रयत्न करतो आहे, पण वेबसाइट मला परवानगी देत नाही. मी पहिले कॉलेज निवडले आणि \"Add\" वर क्लिक केले तर ते यादीत जोडले जाते, पण दुसरे कॉलेज निवडण्याचा प्रयत्न केला असता दोन समस्या येतात: 1. पहिले निवडलेले कॉलेज दोनदा यादीत जोडले जाते 2. दुसरे कॉलेज जोडल्यानंतर, पहिले निवडलेले कॉलेज यादीतून विलोपते.",
        "answer": "कृपया सर्व आवश्यक फील्ड्स भरून, दस्तऐवज अपलोड करून, आणि शाखा आणि माध्यम निवडून पुन्हा प्रयत्न करा. तुम्ही कॉलेज शोधत असताना तुमच्या पसंतींनुसार शाखा आणि माध्यम निवडणे आवश्यक आहे. तुमच्या आवडत्या कॉलेजचे पूर्ण नाव वापरून शोध करण्याचा प्रयत्न करा. जर समस्या सोडली नाही तर, काही वेळाने पुन्हा तपासणे."
    },
    {
        "question": "After locking Part 1 of the application form, I am unable to view or access Part 2. What should I do to resolve this issue and proceed with completing Part 2?",
        "answer": "To access Part 2, please ensure that Part 1 of the form has been locked. After locking Part 1, refresh the page or log in again to proceed to Part 2. Then, select the stream and medium to continue. If the issue persists, kindly try again after some time or re-login to your account."
    },
    {
        "question": "विद्यार्थ्यांना महाविद्यालय निवड फॉर्ममध्ये समस्या येत आहे, जसे की वेगवेगळी महाविद्यालये निवडली तरीही सेव्ह केलेल्या निवडीच्या टॅबमध्ये तीच महाविद्यालये दोनदा दिसतात, वेगवेगळी महाविद्यालये निवडली तरीही एकच महाविद्यालय दिसते, किंवा महाविद्यालयांची निवड योग्यरित्या सेव्ह होत नाही. या समस्येचे निराकरण कसे करावे?",
        "answer": "कृपया थोड्या वेळाने पुन्हा तपासून पहा. संभवत: ही समस्या तात्पुरती असेल आणि थोड्या वेळाने सुधारली असेल. जर समस्या सोडली नाही तर, कृपया अधिक माहिती देऊन पुन्हा संपर्क साधा."
    },
    {
        "question": "I am facing issues during the 11th admission registration process, such as problems with uploading documents, filling out the option form, or checking my fee status. What should I do to resolve these issues?",
        "answer": "If you experience any issues during registration, please inform us and mention your issue in detail. Attach necessary supporting documents, such as screenshots, and provide a brief description of the problem. Our team will work on resolving the issue, and you can also try checking again after some time to see if the issue has been resolved. Additionally, ensure you have filled out the application form on the official website (https://mahafyjcadmissions.in) and followed all the necessary steps for the admission process."
    },
    {
        "question": "While selecting multiple college preferences, the first selected college is being duplicated in the list, and subsequent selections are either not being saved or are being replaced by the first college. Despite trying various solutions, such as clearing the cache, restarting the system, and logging out and back in, the issue persists. What should I do to resolve this problem?",
        "answer": "Kindly check again after some time. If the problem persists, please contact support for further assistance. Please contact support@mahafyjcadmissions.in or call the helpline at 8530955564."
    },
    {
        "question": "What should I do if I encounter any issues during the registration process?",
        "answer": "For more details, please contact support@mahafyjcadmissions.in or call the helpline at 8530955564."
    },
    {
        "question": "ICSE विद्यार्थी म्हणून मी माझा सीट नंबर कसा भरावा आणि माझ्या शाळेचा UDISE नंबर आणि इंडेक्स नंबर भरल्यानंतरही मला इनहाउस कोटा विकल्प मिळत नाही, तर मी काय करावे?",
        "answer": "तुम्ही तुमचा हॉल तिकिटावरील सीट नंबर (Roll Number) वापरून नोंदणी करावी. UDISE नंबर आणि इंडेक्स नंबर यांची माहिती भरल्यानंतर, तुमचे डॅशबोर्ड रिफ्रेश करा आणि इनहाउस कोटा विकल्प उपलब्ध असल्याची खात्री करा. या समस्येचा सामना करत असाल तर, तुम्ही तुमच्या समस्येचे वर्णन करून, तुमच्या स्वाक्षरीसह 10 वी उत्तीर्ण प्रमाणपत्र संलग्न करून तक्रार नोंदवावी."
    },
    {
        "question": "I am facing issues while filling the FYJC registration form, what should I do?",
        "answer": "If you are experiencing any issues during registration, please try again after some time. \nFor more details, please contact support@mahafyjcadmissions.in or call the helpline at 8530955564."
    },
    {
        "question": "माझ्या 10 वी च्या प्रमाणपत्राची आणि लीविंग सर्टिफिकेटची माहिती अद्यतनित करणे किंवा बदलणे कसे करावे?",
        "answer": "तुमच्या 10 वी च्या प्रमाणपत्राची आणि लीविंग सर्टिफिकेटची माहिती अद्यतनित करण्यासाठी किंवा बदलण्यासाठी, कृपया तुमचा फॉर्म अनलॉक करा आणि योग्य दस्तऐवज जोडा.\nअधिक तपशीलांसाठी, कृपया support@mahafyjcadmissions.in वर संपर्क साधा किंवा 8530955564 या हेल्पलाइन क्रमांकावर कॉल करा."
    },
    {
        "question": "माझ्या ११वी प्रवेश अर्जात काही तपशील चुकीचे भरले आहेत, जसे की महिना चुकीचा भरला आहे, माध्यम चुकीचे भरले आहे किंवा इतर कोणतेही तपशील चुकीचे भरले आहेत, तर मी ते कसे बदलू शकतो?",
        "answer": "कृपया तुमचा फॉर्म अनलॉक करा, सर्व आवश्यक माहिती भरा आणि तुमचा अर्ज पूर्ण झाला असेल, तर तुम्ही तुमचा अर्ज लॉक करू शकता.\nअधिक तपशीलांसाठी, कृपया support@mahafyjcadmissions.in वर संपर्क साधा किंवा 8530955564 या हेल्पलाइन क्रमांकावर कॉल करा."
    },
    {
        "question": "माझ्या FYJC अर्जाच्या प्रक्रियेत मी विविध तांत्रिक समस्या आणि त्रुटी अनुभवत आहे, जसे की अर्जाचे भाग II पूर्ण करण्यात अडचणी, विविध तपशील भरताना त्रुटी, पेमेंट पेंडिंग, लॉगिन समस्या, आणि इतर तांत्रिक क्लेश. मी या समस्यांचे निराकरण कसे करू शकतो?",
        "answer": "तुमच्या अर्जाच्या प्रक्रियेतील तांत्रिक समस्या आणि त्रुटींसाठी, कृपया प्रथम तुमचे लॉगिन आयडी आणि पासवर्ड यांची पुनःतपासणी करा. तुमच्या अर्जाच्या प्रत्येक भागातील तपशील पुन्हा तपासून घ्या. जर तुम्हाला पेमेंट पेंडिंगची समस्या असेल, तर काही वेळाने पुन्हा प्रयत्न करा. तुमच्या लॉगिन आयडीमध्ये भाग II पूर्ण करण्यासाठी, तुम्ही लॉगिन करून पुन्हा प्रयत्न करू शकता. जर तुम्हाला अजूनही समस्या असेल, तर तुम्ही स्क्रीनशॉटसह तुमची समस्या आमच्याशी संपर्क साधून सांगू शकता. आम्ही तुमच्या समस्येचे निराकरण करण्यासाठी मदत करू.\nअधिक तपशीलांसाठी, कृपया support@mahafyjcadmissions.in वर संपर्क साधा किंवा 8530955564 या हेल्पलाइन क्रमांकावर कॉल करा."
    },
    {
        "question": "I am facing technical issues such as errors, missing selections, or data not found while trying to access or fill out the FYJC form. What should I do to resolve these issues?",
        "answer": "If you are facing any technical issues, please try the following steps: refresh the page (press ctrl+shift+R), check your internet connection, and try again after some time. For more details, please contact support@mahafyjcadmissions.in or call the helpline at 8530955564."
    },
    {
        "question": "कॉलेजची यादी मध्ये काही कॉलेज दिसत नाहीत, त्यामुळे कॉलेज निवड करताना अडचण येत आहे, त्यासाठी काय करावे?",
        "answer": "कॉलेज शोधण्यासाठी प्रवाह (Stream) आणि माध्यम (Medium) योग्यरित्या निवडावे. कॉलेजचे पूर्ण नाव किंवा UDISE नंबर वापरून शोध घ्यावा. जर काही कॉलेज दिसत नसेल तर काही वेळाने पुन्हा तपासावे. \nअधिक तपशीलांसाठी, कृपया support@mahafyjcadmissions.in वर संपर्क साधा किंवा 8530955564 या हेल्पलाइन क्रमांकावर कॉल करा."
    },
    {
        "question": "I'm facing issues with paying my application fee or it's not being reflected in my account. What should I do to resolve this problem and proceed with my application?",
        "answer": "If you're experiencing difficulties with online payment processing, please try the following steps: \n1. Wait for 30 minutes and then click on the 'validate' button.\n2. If the issue persists, check your account after 4 hours or 24 hours for bank reconciliation.\n3. Ensure you have a stable internet connection and try refreshing the dashboard or re-logging into your account.\n4. If you've already made the payment, please be patient and check after some time as it may take a while to update.\n5. In case of multiple payments, you will receive a refund within 7 working days.\nPlease note that the system may take some time to update, and we appreciate your patience and cooperation in this matter."
    },
    {
        "question": "माझ्या अर्जातील तपशीलांमध्ये बदल करणे किंवा आवश्यक दस्तऐवज जोडणे आवश्यक आहे, परंतु माझा अर्ज लॉक झाला आहे. मी आता काय करू शकतो?",
        "answer": "आपण आपला अर्ज पुन्हा लॉगिन करून उघडा (unlock) करून त्यातील तपशील बदलू शकता किंवा आवश्यक दस्तऐवज जोडू शकता. जर तुम्हाला अर्जातील कोणताही तपशील बदलायचा असेल, तर तुम्ही तो बदलू शकता और नंतर तुमचा अर्ज पुन्हा लॉक करू शकता. जर तुम्ही दस्तऐवज जोडण्यासाठी विलंब झाला असेल, तर तुम्ही ते प्रवेश प्रक्रियेतील दस्तऐवज तपासणी दरम्यान सादर करू शकता."
    },
    {
        "question": "माझ्या 11वी आणि 12वी च्या प्रवेशाबाबत माहिती आणि मदत मिळावी",
        "answer": "प्रवेश प्रक्रियेत कोणत्याही समस्येचा अनुभव आल्यास, कृपया आम्हाला माहिती द्या. तुमच्या समस्येचे विस्तृत वर्णन करा आणि आवश्यक असलेले समर्थन दस्तळे जोडा. आम्ही तुमची मदत करण्यासाठी येथे आहोत.\nअधिक तपशीलांसाठी, कृपया support@mahafyjcadmissions.in वर संपर्क साधा किंवा 8530955564 या हेल्पलाइन क्रमांकावर कॉल करा."
    },
    {
        "question": "When will Part 2 of the form be available, and how can I access it?",
        "answer": "You will receive a notification and announcement on the portal once the registration starts. Please also check the Admission Schedule for the timetable. Stay tuned.\nFor more details, please contact support@mahafyjcadmissions.in or call the helpline at 8530955564."
    },
    {
        "question": "माझा अर्ज स्थिती अद्ययावत झालेली नाहीये, कृपया मार्गदर्शन करा",
        "answer": "कृपया अर्ज भरण्यासाठी प्रत्येक आवश्यक फील्ड भरून, अर्ज लॉक करा. अर्ज लॉक झाल्यानंतर, अर्ज स्थिती 'पूर्ण' असे अद्ययावत होईल. जर तुम्हाला अद्यापही समस्या असेल तर कृपया एक तासानंतर पुन्हा तपासा आणि अर्ज भरण्याची प्रक्रिया पूर्ण करा."
    },
    {
        "question": "I'm facing issues with payment validation while trying to fill out my form. Despite successful transactions, the system shows a \"validate payment\" option, and I'm unable to proceed. What should I do?",
        "answer": "Please wait for 1 to 3 hours and then try again to check if the issue has been resolved. If the problem persists, you may try logging in again to see if your payment status has been updated."
    },
    {
        "question": "I have made a payment, but it is not reflecting on the website. What should I do?",
        "answer": "Please check after some time, it may take up to 1-4 hours or even 24 hours for bank reconciliation. If you have made an excess payment, you will receive a refund for all except one payment within 7 working days. Try logging in again after some time to see if the payment has been updated."
    },
    {
        "question": "I do not have any grievances or issues with the FYJC registration process, what should I do?",
        "answer": "Thank you for confirming that you do not have any grievances. If you experience any issues during registration in the future, please inform us and provide detailed information about the issue, along with any necessary supporting documents."
    },
    {
        "question": "माझ्या दाखल्यासंबंधी काही समस्या आहे, ती मी कशी सोडवू शकतो?",
        "answer": "कृपया तुमच्या समस्येचे संक्षिप्त वर्णन करा जेणेकरून आम्ही तुमची समस्या समजून घेऊ शकू आणि ती सोडवू शकू."
    },
    {
        "question": "My application form status shows \"incomplete\" with a missing section of \"Registration Details\", but I have filled all the required fields. What should I do to resolve this issue?",
        "answer": "To resolve the issue of the missing ‘Registration Details’ section, please ensure that all mandatory fields are filled in and all required documents are uploaded. Lock the first form; you will then be able to view the second form and proceed by clicking ‘Save & Next."
    },
    {
        "question": "I am facing issues while selecting and saving college preferences, such as being unable to select more than one college, error messages like \"requested choice code did not match\", and my preferences not being saved. What should I do to resolve this issue?",
        "answer": "Please try again after some time, If the issue persists, try logging in from a different tab, refreshing the screen, or checking back after sometime.\nFor more details, please contact support@mahafyjcadmissions.in or call the helpline at 8530955564."
    },
    {
        "question": "I am unable to access/find Part 2 of the application form, what should I do?",
        "answer": "Please ensure that you have locked your Part 1 form. Then, log in to your account and refresh the page. Part 2 should now be available for you to complete. If you still face any issues, kindly check again after some time and try again."
    },
    {
        "question": "मी फॉर्म भरताना कॉलेजची निवड करू शकत नाही आणि माझा अर्ज लॉक करू शकत नाही, यामध्ये काय प्रक्रिया आहे आणि मला काय करावे लागेल?",
        "answer": "तुमचा अर्ज लॉक करण्यासाठी आणि कॉलेज निवडण्यासाठी, खालील पायऱ्या अनुसरण करा:\nपार्ट-१ पूर्ण करा: सर्व आवश्यक फील्ड्स (*) भरा.\nपार्ट-१ लॉक करा: 'लॉक & प्रोसीड' वर क्लिक करा – हे पार्ट-२ च्या आधी अनिवार्य आहे.\nपुन्हा लॉगिन करा: जर पार्ट-२ (कॉलेज निवड) दिसली नाही, तर पेज रिफ्रेश करा किंवा लॉगआउट करून पुन्हा लॉगिन करा.\nअधिक तपशीलांसाठी, कृपया support@mahafyjcadmissions.in वर संपर्क साधा किंवा 8530955564 या हेल्पलाइन क्रमांकावर कॉल करा."
    },
    {
        "question": "Part 2 CAP round is not visible despite trying from different devices and refreshing, what should I do?",
        "answer": "Please log in again, ensure that your Part 1 form is locked, and then refresh the page to proceed to Part 2. If the problem persists, kindly check again after some time and try again."
    },
    {
        "question": "I am facing issues with selecting or locking my college preferences, such as the option not being available, college names not showing, or login problems. What should I do to resolve this issue?",
        "answer": "Please try logging in again after some time and ensure that you are filling out the form correctly. Make sure that Part 1 is locked, then refresh the page and check again."
    }
]

def main():
    session = requests.Session()
    
    # 1. Login
    print(f"Logging in to {LOGIN_URL}...")
    try:
        resp = session.post(LOGIN_URL, json={"username": USER, "password": PASS})
        if resp.status_code != 200:
            print(f"Login failed: {resp.status_code} {resp.text}")
            return
        
        # Get the cookie manually
        cookie = resp.cookies.get("admin_session")
        if not cookie:
            print("No admin_session cookie received!")
            return
            
        print("Login successful.")
        
        # Manually set the cookie in headers for subsequent requests
        # This bypasses the 'Secure' flag restriction in requests when using HTTP
        headers = {"Cookie": f"admin_session={cookie}"}
        
    except Exception as e:
        print(f"Connection error: {e}")
        return

    # 2. Bulk Insert
    success_count = 0
    fail_count = 0
    
    for i, item in enumerate(DATA):
        print(f"[{i+1}/{len(DATA)}] Adding: {item['question'][:50]}...")
        try:
            resp = session.post(QNA_URL, json=item, headers=headers)
            if resp.status_code in [200, 201]:
                print("  Success.")
                success_count += 1
            else:
                print(f"  Failed ({resp.status_code}): {resp.text}")
                fail_count += 1
        except Exception as e:
            print(f"  Error: {e}")
            fail_count += 1
        
        # throttle slightly to be safe
        time.sleep(0.5)

    print("\n--- Summary ---")
    print(f"Total: {len(DATA)}")
    print(f"Successfully added: {success_count}")
    print(f"Failed: {fail_count}")

if __name__ == "__main__":
    main()
