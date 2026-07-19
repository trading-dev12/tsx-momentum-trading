"""
Northstar Quant
Sector mapping for the complete production TSX universe.

The mapping is intentionally maintained internally so sector
classification remains deterministic and historically consistent.

Each symbol maps to:

    (
        sector_name,
        sector_benchmark,
    )
"""

SECTOR_MAP = {
    # Banks
    "RY.TO": ("Banks", "XFN.TO"),
    "TD.TO": ("Banks", "XFN.TO"),
    "BMO.TO": ("Banks", "XFN.TO"),
    "CM.TO": ("Banks", "XFN.TO"),
    "BNS.TO": ("Banks", "XFN.TO"),
    "NA.TO": ("Banks", "XFN.TO"),
    "EQB.TO": ("Banks", "XFN.TO"),

    # Consumer Staples
    "ATD.TO": ("Consumer", "XST.TO"),
    "DOL.TO": ("Consumer", "XST.TO"),
    "MRU.TO": ("Consumer", "XST.TO"),
    "EMP-A.TO": ("Consumer", "XST.TO"),

    # Energy
    "CNQ.TO": ("Energy", "XEG.TO"),
    "SU.TO": ("Energy", "XEG.TO"),
    "CVE.TO": ("Energy", "XEG.TO"),
    "BTE.TO": ("Energy", "XEG.TO"),
    "TOU.TO": ("Energy", "XEG.TO"),
    "IMO.TO": ("Energy", "XEG.TO"),
    "ARX.TO": ("Energy", "XEG.TO"),
    "PEY.TO": ("Energy", "XEG.TO"),
    "ATH.TO": ("Energy", "XEG.TO"),

    # Industrials
    "CNR.TO": ("Industrials", "ZIN.TO"),
    "CP.TO": ("Industrials", "ZIN.TO"),
    "WCN.TO": ("Industrials", "ZIN.TO"),
    "TFII.TO": ("Industrials", "ZIN.TO"),
    "CAE.TO": ("Industrials", "ZIN.TO"),
    "STN.TO": ("Industrials", "ZIN.TO"),
    "CCL-B.TO": ("Industrials", "ZIN.TO"),
    "AC.TO": ("Industrials", "ZIN.TO"),

    # Insurance
    "MFC.TO": ("Insurance", "XFN.TO"),
    "SLF.TO": ("Insurance", "XFN.TO"),
    "IFC.TO": ("Insurance", "XFN.TO"),

    # Gold and Precious Metals
    "AEM.TO": ("Gold", "XGD.TO"),
    "AGI.TO": ("Gold", "XGD.TO"),
    "WPM.TO": ("Gold", "XGD.TO"),
    "PAAS.TO": ("Gold", "XGD.TO"),
    "K.TO": ("Gold", "XGD.TO"),

    # Diversified Materials and Mining
    "TECK-B.TO": ("Materials", "XMA.TO"),
    "FM.TO": ("Materials", "XMA.TO"),
    "LUN.TO": ("Materials", "XMA.TO"),
    "NTR.TO": ("Materials", "XMA.TO"),

    # Pipelines
    "ENB.TO": ("Pipelines", "XEG.TO"),
    "TRP.TO": ("Pipelines", "XEG.TO"),
    "PPL.TO": ("Pipelines", "XEG.TO"),

    # Technology
    "SHOP.TO": ("Technology", "XIT.TO"),
    "CSU.TO": ("Technology", "XIT.TO"),
    "GIB-A.TO": ("Technology", "XIT.TO"),
    "DSG.TO": ("Technology", "XIT.TO"),
    "HIVE.TO": ("Technology", "XIT.TO"),
    "BB.TO": ("Technology", "XIT.TO"),
    "CLS.TO": ("Technology", "XIT.TO"),

    # Utilities
    "FTS.TO": ("Utilities", "ZUT.TO"),
    "EMA.TO": ("Utilities", "ZUT.TO"),
    "AQN.TO": ("Utilities", "ZUT.TO"),
}


def get_sector_mapping(symbol):
    """
    Return the configured sector and benchmark for a symbol.

    Returns:
        tuple[str, str] | None
    """
    if not isinstance(symbol, str):
        return None

    return SECTOR_MAP.get(symbol.strip().upper())