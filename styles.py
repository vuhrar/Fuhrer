# styles.py - Custom CSS for Fuhrer Legal App (Saudi Labor Law)

def get_custom_styles():
    """Return custom CSS styles for the Streamlit app"""
    return """
    <style>
        /* ===== GLOBAL STYLES ===== */
        @import url('https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&family=Cairo:wght@400;700&display=swap');

        /* Arabic font support */
        html, body, [class*="css"] {
            font-family: 'Cairo', 'Amiri', sans-serif !important;
            direction: rtl !important;
            text-align: right !important;
        }

        /* Main container */
        .main > div {
            max-width: 1200px !important;
            padding: 1rem !important;
        }

        /* ===== HEADER STYLES ===== */
        .header {
            background: linear-gradient(135deg, #0066cc 0%, #004080 100%) !important;
            color: white !important;
            padding: 2rem 1rem !important;
            border-radius: 0 0 15px 15px !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
        }

        .header h1 {
            font-size: 2.5rem !important;
            font-weight: 700 !important;
            margin: 0 !important;
            text-align: center !important;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3) !important;
        }

        .header p {
            font-size: 1.2rem !important;
            margin: 0.5rem 0 0 0 !important;
            opacity: 0.9 !important;
        }

        /* ===== SIDEBAR STYLES ===== */
        .css-1d391kg {
            background: linear-gradient(180deg, #0066cc 0%, #004080 100%) !important;
            color: white !important;
        }

        .css-1d391kg a {
            color: white !important;
            font-weight: 500 !important;
        }

        .css-1d391kg a:hover {
            background-color: rgba(255,255,255,0.2) !important;
        }

        /* ===== BUTTON STYLES ===== */
        .stButton > button {
            background: linear-gradient(135deg, #0066cc 0%, #004080 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 0.75rem 2rem !important;
            font-size: 1.1rem !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
        }

        .stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 12px rgba(0,0,0,0.15) !important;
            background: linear-gradient(135deg, #0055aa 0%, #003366 100%) !important;
        }

        .stButton > button:active {
            transform: translateY(0) !important;
        }

        /* Primary button (for main actions) */
        .stButton > button:first-child {
            background: linear-gradient(135deg, #28a745 0%, #218838 100%) !important;
        }

        .stButton > button:first-child:hover {
            background: linear-gradient(135deg, #218838 0%, #1e7e34 100%) !important;
        }

        /* Danger button */
        .stButton > button:last-child {
            background: linear-gradient(135deg, #dc3545 0%, #c82333 100%) !important;
        }

        .stButton > button:last-child:hover {
            background: linear-gradient(135deg, #c82333 0%, #bd2130 100%) !important;
        }

        /* ===== INPUT & TEXTAREA STYLES ===== */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {
            border: 2px solid #e0e0e0 !important;
            border-radius: 8px !important;
            padding: 0.75rem !important;
            font-size: 1rem !important;
            transition: border-color 0.3s ease !important;
            background-color: #f8f9fa !important;
        }

        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {
            border-color: #0066cc !important;
            box-shadow: 0 0 0 3px rgba(0,102,204,0.1) !important;
            outline: none !important;
        }

        /* ===== FILE UPLOAD STYLES ===== */
        .stFileUploader > div {
            border: 2px dashed #0066cc !important;
            border-radius: 12px !important;
            padding: 2rem !important;
            background-color: #f8f9fa !important;
            transition: all 0.3s ease !important;
        }

        .stFileUploader > div:hover {
            border-color: #004080 !important;
            background-color: #e9ecef !important;
        }

        /* ===== CARD STYLES ===== */
        .stCard {
            background: white !important;
            border: 1px solid #e0e0e0 !important;
            border-radius: 12px !important;
            padding: 1.5rem !important;
            margin: 1rem 0 !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05) !important;
            transition: transform 0.2s ease, box-shadow 0.2s ease !important;
        }

        .stCard:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 16px rgba(0,0,0,0.1) !important;
        }

        /* ===== TAB STYLES ===== */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px !important;
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 8px 8px 0 0 !important;
            padding: 12px 24px !important;
            font-weight: 600 !important;
            background-color: #f8f9fa !important;
        }

        .stTabs [data-baseweb="tab"]:hover {
            background-color: #e9ecef !important;
        }

        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #0066cc 0%, #004080 100%) !important;
            color: white !important;
        }

        /* ===== PROGRESS BAR ===== */
        .stProgress > div > div > div > div {
            background: linear-gradient(90deg, #0066cc 0%, #004080 100%) !important;
        }

        /* ===== ALERT STYLES ===== */
        .stAlert {
            border-radius: 8px !important;
            padding: 1rem !important;
            margin: 1rem 0 !important;
        }

        /* Success alert */
        .stAlert [data-baseweb="notification"] {
            background-color: #d4edda !important;
            border-left: 4px solid #28a745 !important;
            color: #155724 !important;
        }

        /* Error alert */
        .stAlert-error [data-baseweb="notification"] {
            background-color: #f8d7da !important;
            border-left: 4px solid #dc3545 !important;
            color: #721c24 !important;
        }

        /* Warning alert */
        .stAlert-warning [data-baseweb="notification"] {
            background-color: #fff3cd !important;
            border-left: 4px solid #ffc107 !important;
            color: #856404 !important;
        }

        /* ===== DATA TABLE STYLES ===== */
        .dataframe {
            font-size: 0.9rem !important;
            border-collapse: collapse !important;
            width: 100% !important;
        }

        .dataframe th {
            background: linear-gradient(135deg, #0066cc 0%, #004080 100%) !important;
            color: white !important;
            padding: 12px !important;
            text-align: center !important;
            font-weight: 600 !important;
        }

        .dataframe td {
            padding: 10px !important;
            border: 1px solid #e0e0e0 !important;
            text-align: center !important;
        }

        .dataframe tr:nth-child(even) {
            background-color: #f8f9fa !important;
        }

        .dataframe tr:hover {
            background-color: #e9ecef !important;
        }

        /* ===== MARKDOWN STYLES ===== */
        .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
            color: #004080 !important;
            border-bottom: 2px solid #0066cc !important;
            padding-bottom: 0.5rem !important;
            margin-top: 1.5rem !important;
        }

        .stMarkdown h1 {
            font-size: 2rem !important;
        }

        .stMarkdown h2 {
            font-size: 1.75rem !important;
        }

        .stMarkdown h3 {
            font-size: 1.5rem !important;
        }

        .stMarkdown p {
            line-height: 1.8 !important;
            font-size: 1.05rem !important;
        }

        .stMarkdown a {
            color: #0066cc !important;
            text-decoration: none !important;
            font-weight: 600 !important;
        }

        .stMarkdown a:hover {
            text-decoration: underline !important;
            color: #004080 !important;
        }

        /* ===== CODE BLOCK STYLES ===== */
        .stMarkdown code {
            background-color: #f8f9fa !important;
            padding: 2px 6px !important;
            border-radius: 4px !important;
            font-family: 'Courier New', monospace !important;
            font-size: 0.95rem !important;
        }

        /* ===== FOOTER STYLES ===== */
        .footer {
            text-align: center !important;
            padding: 2rem 1rem !important;
            margin-top: 2rem !important;
            background: linear-gradient(135deg, #0066cc 0%, #004080 100%) !important;
            color: white !important;
            border-radius: 15px 15px 0 0 !important;
        }

        /* ===== RESPONSIVE DESIGN ===== */
        @media (max-width: 768px) {
            .header h1 {
                font-size: 1.8rem !important;
            }

            .stButton > button {
                padding: 0.5rem 1.5rem !important;
                font-size: 1rem !important;
            }

            .main > div {
                padding: 0.5rem !important;
            }
        }

        /* ===== SCROLLBAR STYLES ===== */
        ::-webkit-scrollbar {
            width: 10px !important;
            height: 10px !important;
        }

        ::-webkit-scrollbar-track {
            background: #f1f1f1 !important;
        }

        ::-webkit-scrollbar-thumb {
            background: #0066cc !important;
            border-radius: 5px !important;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: #004080 !important;
        }

        /* ===== SAUDI FLAG COLORS ===== */
        .saudi-theme {
            background: linear-gradient(135deg, #006633 0%, #004080 100%) !important;
        }

        /* Loading spinner */
        .stSpinner > div {
            border-top-color: #0066cc !important;
            border-right-color: #0066cc !important;
            border-bottom-color: #0066cc !important;
        }

        /* Expander styles */
        .streamlit-expanderHeader {
            background-color: #f8f9fa !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            color: #004080 !important;
        }

        /* Metric card styles */
        .stMetric {
            background: white !important;
            border: 1px solid #e0e0e0 !important;
            border-radius: 12px !important;
            padding: 1.5rem !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05) !important;
        }

        /* Download button */
        .stDownloadButton > button {
            background: linear-gradient(135deg, #28a745 0%, #218838 100%) !important;
            color: white !important;
        }
    </style>
    """