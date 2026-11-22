import streamlit as st


def inject_styles() -> None:
    """Inject rich, multi-accent custom CSS via st.html() overriding bland defaults."""
    st.html(
        """
        <style>
            /* Remove Streamlit's default sidebar and fixed top header bar so nothing overlaps .nav-bar */
            [data-testid="stSidebar"],
            [data-testid="collapsedControl"],
            header[data-testid="stHeader"],
            [data-testid="stToolbar"] {
                display: none !important;
            }
            .stMainBlockContainer,
            .block-container {
                padding-top: 1.5rem !important;
                padding-bottom: 4rem !important;
                max-width: 1180px !important;
            }

            /* Top Navigation Header */
            .nav-bar {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 0.9rem 1.4rem;
                background: #FFFFFF;
                border: 1px solid #E6DFD3;
                border-radius: 14px;
                box-shadow: 0 6px 24px rgba(16, 42, 42, 0.05);
                margin-bottom: 1.15rem;
                position: relative;
                z-index: 10;
            }
            .brand-group {
                display: flex;
                align-items: center;
                gap: 0.7rem;
            }
            .brand-pill {
                background: linear-gradient(135deg, #0D5C5C 0%, #147D7D 100%);
                color: #FFFFFF;
                font-weight: 800;
                font-size: 0.78rem;
                padding: 0.34rem 0.68rem;
                border-radius: 8px;
                letter-spacing: 0.06em;
            }
            .brand-title {
                font-weight: 800;
                font-size: 1.06rem;
                color: #102A2A;
                letter-spacing: -0.015em;
            }
            .nav-pills {
                display: flex;
                gap: 0.55rem;
                flex-wrap: wrap;
            }
            .nav-chip {
                font-size: 0.76rem;
                font-weight: 700;
                padding: 0.25rem 0.65rem;
                border-radius: 999px;
                background: #F3EFE6;
                color: #0D5C5C;
                border: 1px solid #E2D9C8;
            }

            /* Rich Multi-Stop Gradient Hero Banner */
            .hero-showcase {
                background: linear-gradient(135deg, #0B3B3C 0%, #115E59 55%, #1D7874 100%);
                color: #FFFFFF;
                border-radius: 18px;
                padding: 2rem 2.25rem;
                box-shadow: 0 14px 36px rgba(11, 59, 60, 0.18);
                margin-bottom: 1.35rem;
                position: relative;
                overflow: hidden;
            }
            .hero-badge {
                display: inline-block;
                background: rgba(245, 158, 11, 0.22);
                border: 1px solid rgba(251, 191, 36, 0.55);
                color: #FDE68A;
                font-size: 0.74rem;
                font-weight: 700;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                padding: 0.26rem 0.72rem;
                border-radius: 999px;
                margin-bottom: 0.65rem;
            }
            .hero-title {
                font-size: 2.1rem;
                font-weight: 800;
                letter-spacing: -0.025em;
                line-height: 1.18;
                color: #FFFFFF;
                margin: 0 0 0.55rem 0;
            }
            .hero-sub {
                font-size: 0.98rem;
                color: #D1FAE5;
                max-width: 780px;
                line-height: 1.55;
                margin: 0;
            }

            /* Styled Expander & Inputs */
            div[data-testid="stExpander"] {
                background: #FFFFFF !important;
                border: 1px solid #E6DFD3 !important;
                border-radius: 16px !important;
                box-shadow: 0 8px 26px rgba(16, 42, 42, 0.05) !important;
            }

            /* Primary Coral CTA & Emerald-Outlined Secondary CTA */
            div.stButton > button[kind="primary"] {
                background: linear-gradient(135deg, #E05A47 0%, #C94432 100%) !important;
                border: none !important;
                color: #FFFFFF !important;
                font-weight: 700 !important;
                border-radius: 10px !important;
                padding: 0.55rem 1.1rem !important;
                box-shadow: 0 6px 18px rgba(224, 90, 71, 0.30) !important;
                transition: transform 0.15s ease, box-shadow 0.15s ease !important;
            }
            div.stButton > button[kind="primary"]:hover {
                transform: translateY(-1px);
                box-shadow: 0 9px 22px rgba(224, 90, 71, 0.40) !important;
            }
            div.stButton > button[kind="secondary"] {
                background: #F4FBF9 !important;
                border: 1.5px solid #0D5C5C !important;
                color: #0D5C5C !important;
                font-weight: 700 !important;
                border-radius: 10px !important;
                padding: 0.55rem 1.1rem !important;
            }
            div.stButton > button[kind="secondary"]:hover {
                background: #E2F4F0 !important;
            }

            /* Colorful Accent-Bordered Feature Cards */
            .pillar-card {
                background: #FFFFFF;
                border: 1px solid #E6DFD3;
                border-top: 4px solid #0D5C5C;
                border-radius: 16px;
                padding: 1.4rem 1.5rem;
                box-shadow: 0 10px 28px rgba(16, 42, 42, 0.05);
                height: 100%;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
            }
            .pillar-coral {
                border-top-color: #E05A47;
            }
            .pillar-amber {
                border-top-color: #D97706;
            }
            .card-kicker {
                font-size: 0.73rem;
                font-weight: 800;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                color: #0D5C5C;
                margin-bottom: 0.35rem;
            }
            .card-kicker-coral {
                color: #E05A47;
            }
            .card-kicker-amber {
                color: #B45309;
            }
            .card-heading {
                font-size: 1.16rem;
                font-weight: 800;
                color: #102A2A;
                margin-bottom: 0.65rem;
                letter-spacing: -0.01em;
            }
            .bullet-list {
                list-style: none;
                padding: 0;
                margin: 0 0 1rem 0;
                font-size: 0.91rem;
                line-height: 1.6;
                color: #334E4E;
            }
            .bullet-list li {
                margin-bottom: 0.48rem;
                padding-left: 1.25rem;
                position: relative;
            }
            .bullet-list li::before {
                content: "✦";
                position: absolute;
                left: 0;
                color: #E05A47;
                font-size: 0.82rem;
            }
            .card-footer-strip {
                font-size: 0.76rem;
                font-weight: 800;
                letter-spacing: 0.06em;
                text-transform: uppercase;
                color: #0D5C5C;
                background: #F4FBF9;
                border-radius: 8px;
                padding: 0.45rem 0.65rem;
                text-align: center;
            }

            /* 3-Step Workflow Cards */
            .step-box {
                background: #FFFFFF;
                border: 1px solid #E6DFD3;
                border-radius: 14px;
                padding: 1.2rem 1.35rem;
                box-shadow: 0 6px 20px rgba(16, 42, 42, 0.04);
                height: 100%;
            }
            .step-circle {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                width: 30px;
                height: 30px;
                border-radius: 50%;
                background: linear-gradient(135deg, #E05A47 0%, #D97706 100%);
                color: #FFFFFF;
                font-weight: 800;
                font-size: 0.85rem;
                margin-bottom: 0.55rem;
            }
            .step-title {
                font-weight: 800;
                font-size: 1.02rem;
                color: #102A2A;
                margin-bottom: 0.3rem;
            }
            .step-text {
                font-size: 0.88rem;
                color: #486565;
                line-height: 1.5;
            }

            /* Colorful Tags */
            .pill-teal {
                display: inline-block;
                padding: 0.22rem 0.62rem;
                border-radius: 6px;
                font-size: 0.77rem;
                font-weight: 700;
                background: #E6F4F1;
                color: #0B4F4F;
                border: 1px solid #BCE0D9;
                margin-right: 0.36rem;
                margin-bottom: 0.35rem;
            }
            .pill-amber {
                display: inline-block;
                padding: 0.22rem 0.62rem;
                border-radius: 6px;
                font-size: 0.77rem;
                font-weight: 700;
                background: #FEF3C7;
                color: #92400E;
                border: 1px solid #FDE68A;
                margin-right: 0.36rem;
                margin-bottom: 0.35rem;
            }
            .pill-coral {
                display: inline-block;
                padding: 0.22rem 0.62rem;
                border-radius: 6px;
                font-size: 0.77rem;
                font-weight: 700;
                background: #FEE2E2;
                color: #991B1B;
                border: 1px solid #FECACA;
                margin-right: 0.36rem;
                margin-bottom: 0.35rem;
            }

            /* Daily Schedule Time-Block Cards */
            .slot-box {
                background: #FFFFFF;
                border: 1px solid #E6DFD3;
                border-radius: 14px;
                padding: 1.1rem 1.2rem;
                box-shadow: 0 6px 18px rgba(16, 42, 42, 0.04);
                min-height: 165px;
            }
            .slot-morning { border-top: 3px solid #D97706; }
            .slot-afternoon { border-top: 3px solid #0D5C5C; }
            .slot-evening { border-top: 3px solid #E05A47; }
            .slot-label {
                font-size: 0.82rem;
                font-weight: 800;
                letter-spacing: 0.06em;
                text-transform: uppercase;
                margin-bottom: 0.6rem;
                padding-bottom: 0.4rem;
                border-bottom: 1px solid #F0EAE0;
            }
            .slot-morning .slot-label { color: #B45309; }
            .slot-afternoon .slot-label { color: #0D5C5C; }
            .slot-evening .slot-label { color: #C94432; }
            .slot-box ul {
                margin: 0;
                padding-left: 1.1rem;
                font-size: 0.91rem;
                color: #243B3B;
                line-height: 1.55;
            }
        </style>
        """
    )