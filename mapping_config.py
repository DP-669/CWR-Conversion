# mapping_config.py

# Submitter Info (from your Bible: ORN record prefix/Header)
SUBMITTER_INFO = {
    "name": "RED COLA",
    "id": "000000009",
    "standard_version": "02.10"
}

# Mapping US Original Publishers to Agreement Numbers and IPIs
# Logic: These keys now match the 'PUBLISHER 1: Name' column in your CSV
PUBLISHER_MAPPING = {
    "Pashalina Publishing": {"agreement": "4316161", "ipi": "00498578867"},
    "Lukacino Publishing": {"agreement": "3845006", "ipi": "01254514077"},
    "Redcola Publishing": {"agreement": "4165777", "ipi": "00420164014"},
    "Snoople Songs": {"agreement": "13990221", "ipi": "01079343442"},
    "Mina Publishing": {"agreement": "13995081", "ipi": "01079343442"},
    "Tarmac 1331 Publishing": {"agreement": "6781310", "ipi": "00000000000"},
    "Tarmac 1332": {"agreement": "13992037", "ipi": "00000000000"},
    "Holly Palmer Music": {"agreement": "13994635", "ipi": "00000000000"},
    "Dementia Publishing": {"agreement": "13994638", "ipi": "00000000000"},
    "Manny G Music": {"agreement": "13994649", "ipi": "00000000000"},
    "Culvertown Music": {"agreement": "13994260", "ipi": "00000000000"},
    "Vantablack": {"agreement": "13994073", "ipi": "00000000000"},
    "Toro Rosso Tracks": {"agreement": "13994607", "ipi": "00000000000"},
    "Mc Trouble Music": {"agreement": "13996234", "ipi": "00000000000"}
}

# Lumina UK Identity (The Sub-Publisher)
SUB_PUB = {
    "name": "LUMINA PUBLISHING UK",
    "ipi": "01254514077",
    "role": "SE",
    "territory": "0826"
}
