// Client-side translation dictionary
const translations = {
    'en': {
        'hero-title': 'NEXT-GEN IPO ANALYTICS',
        'hero-subtitle': 'AI-Powered Deep Dive into Financial Prospectus',
        'start-btn': 'START ANALYSIS',
        'nav-dash': 'Dashboard',
        'term-header': 'LIVE TERMINAL LOGS',
        'report-header': 'AI INVESTMENT MEMO',
        'charts-header': 'FINANCIAL VISUALIZATION',
        'chat-header': 'RAG CHATBOT',
        'chat-placeholder': 'Ask a question about the IPO...',
        'send-btn': 'Send',
        'ticker-label': 'LIVE MARKET DATA'
    },
    'hi': {
        'hero-title': 'नेक्स्ट-जेन आईपीओ एनालिटिक्स',
        'hero-subtitle': 'वित्तीय विवरणिका का एआई-संचालित विश्लेषण',
        'start-btn': 'विश्लेषण शुरू करें',
        'nav-dash': 'डैशबोर्ड',
        'term-header': 'लाइव टर्मिनल लॉग',
        'report-header': 'एआई निवेश मेमो',
        'charts-header': 'वित्तीय विज़ुअलाइज़ेशन',
        'chat-header': 'RAG चैटबॉट',
        'chat-placeholder': 'आईपीओ के बारे में कोई प्रश्न पूछें...',
        'send-btn': 'भेजें',
        'ticker-label': 'लाइव मार्केट डेटा'
    },
    'mr': {
        'hero-title': 'नेक्स्ट-जेन आयपीओ अ‍ॅनालिटिक्स',
        'hero-subtitle': 'आर्थिक माहितीचे एआय-आधारित विश्लेषण',
        'start-btn': 'विश्लेषण सुरू करा',
        'nav-dash': 'डॅशबोर्ड',
        'term-header': 'लाइव्ह टर्मिनल लॉग्स',
        'report-header': 'एआय इन्व्हेस्टमेंट मेमो',
        'charts-header': 'आर्थिक आलेख',
        'chat-header': 'RAG चॅटबॉट',
        'chat-placeholder': 'आयपीओ बद्दल प्रश्न विचारा...',
        'send-btn': 'पाठवा',
        'ticker-label': 'लाइव्ह मार्केट डेटा'
    },
    'gu': {
        'hero-title': 'નેક્સ્ટ-જેન આઈપીઓ એનાલિટિક્સ',
        'hero-subtitle': 'આર્થિક માહિતીનું એઆઈ-સંચાલિત વિશ્લેષણ',
        'start-btn': 'વિશ્લેષણ શરૂ કરો',
        'nav-dash': 'ડેશબોર્ડ',
        'term-header': 'લાઈવ ટર્મિનલ લોગ્સ',
        'report-header': 'એઆઈ ઇન્વેસ્ટમેન્ટ મેમો',
        'charts-header': 'આર્થિક ચાર્ટ્સ',
        'chat-header': 'RAG ચેટબોટ',
        'chat-placeholder': 'આઈપીઓ વિશે પ્રશ્ન પૂછો...',
        'send-btn': 'મોકલો',
        'ticker-label': 'લાઈવ માર્કેટ ડેટા'
    },
    'ta': {
        'hero-title': 'அடுத்த தலைமுறை IPO பகுப்பாய்வு',
        'hero-subtitle': 'நிதி அறிக்கையின் AI-ஆற்றல் பகுப்பாய்வு',
        'start-btn': 'பகுப்பாய்வைத் தொடங்கவும்',
        'nav-dash': 'டாஷ்போர்டு',
        'term-header': 'நேரடி முனைய பதிவுகள்',
        'report-header': 'AI முதலீட்டு குறிப்பு',
        'charts-header': 'நிதி வரைபடங்கள்',
        'chat-header': 'RAG சாட்போட்',
        'chat-placeholder': 'IPO பற்றி கேள்வி கேட்கவும்...',
        'send-btn': 'அனுப்பு',
        'ticker-label': 'நேரடி சந்தை தரவு'
    },
    'te': {
        'hero-title': 'నెక్స్ట్-జన్ IPO అనలిటిక్స్',
        'hero-subtitle': 'ఆర్థిక సమాచారం యొక్క AI-ఆధారిత విశ్లేషణ',
        'start-btn': 'విశ్లేషణ ప్రారంభించండి',
        'nav-dash': 'డాష్‌బోర్డ్',
        'term-header': 'లైవ్ టెర్మినల్ లాగ్స్',
        'report-header': 'AI ఇన్వెస్ట్‌మెంట్ మెమో',
        'charts-header': 'ఆర్థిక పటాలు',
        'chat-header': 'RAG చాట్‌బాట్',
        'chat-placeholder': 'IPO గురించి ప్రశ్న అడగండి...',
        'send-btn': 'పంపండి',
        'ticker-label': 'లైవ్ మార్కెట్ డేటా'
    }
};

function changeLanguage() {
    const lang = document.getElementById('lang-select').value;
    const data = translations[lang];

    if (!data) return;

    for (const [id, text] of Object.entries(data)) {
        const el = document.getElementById(id);
        if (el) {
            if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
                el.placeholder = text;
            } else {
                el.innerText = text;
            }
        }
    }

    // Save preference
    localStorage.setItem('fincore_lang', lang);
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    const saved = localStorage.getItem('fincore_lang');
    if (saved) {
        const sel = document.getElementById('lang-select');
        if (sel) {
            sel.value = saved;
            changeLanguage();
        }
    }
});
