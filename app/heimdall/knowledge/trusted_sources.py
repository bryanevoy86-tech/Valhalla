TRUSTED_KNOWLEDGE_SOURCES = {
    "canada_housing": [
        {
            "name": "CMHC Housing Market Reports",
            "url": "https://www.cmhc-schl.gc.ca/professionals/housing-markets-data-and-research/market-reports",
            "use_for": [
                "housing market trends",
                "rental market reports",
                "vacancy rates",
                "average rents",
                "market conditions",
            ],
            "trust_level": "primary_official",
        },
        {
            "name": "CMHC Rental Market Data Tables",
            "url": "https://www.cmhc-schl.gc.ca/professionals/housing-markets-data-and-research/housing-data/data-tables/rental-market/rental-market-report-data-tables",
            "use_for": [
                "vacancy rate estimates",
                "average rents",
                "turnover rates",
                "rental universe counts",
            ],
            "trust_level": "primary_official",
        },
        {
            "name": "CMHC Housing Market Information Portal",
            "url": "https://www.cmhc-schl.gc.ca/hmiportal",
            "use_for": [
                "local housing data",
                "market comparisons",
                "historical housing trends",
            ],
            "trust_level": "primary_official",
        },
    ],
    "canada_demographics": [
        {
            "name": "Statistics Canada Housing Statistics",
            "url": "https://www.statcan.gc.ca/en/subjects-start/housing",
            "use_for": [
                "housing statistics",
                "ownership patterns",
                "property data",
                "demographic trends",
            ],
            "trust_level": "primary_official",
        },
        {
            "name": "Statistics Canada Web Data Service",
            "url": "https://open.canada.ca/data/en/dataset/05c7f8e7-9885-434a-99a2-68d253cb6401",
            "use_for": [
                "official datasets",
                "economic indicators",
                "population data",
                "income data",
            ],
            "trust_level": "primary_official_api",
        },
    ],
    "winnipeg_property": [
        {
            "name": "City of Winnipeg Open Data",
            "url": "https://data.winnipeg.ca/",
            "use_for": [
                "open civic datasets",
                "assessment parcels",
                "property-related public data",
            ],
            "trust_level": "primary_municipal",
        },
        {
            "name": "Winnipeg Assessment Parcels",
            "url": "https://data.winnipeg.ca/Assessment-Taxation-Corporate/Assessment-Parcels/d4mq-wa44",
            "use_for": [
                "parcel data",
                "assessment geography",
                "property matching",
            ],
            "trust_level": "primary_municipal_dataset",
        },
        {
            "name": "Winnipeg Property Assessment Search",
            "url": "https://assessment.winnipeg.ca/asmtpub/english/propertydetails/RealtySearch.htm",
            "use_for": [
                "property assessment values",
                "property detail checks",
                "assessed value comparison",
            ],
            "trust_level": "primary_municipal",
        },
    ],
}
