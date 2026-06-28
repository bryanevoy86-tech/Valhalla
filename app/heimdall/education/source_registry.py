HEIMDALL_SOURCE_REGISTRY = {
    "canada_market_data": [
        {
            "name": "CMHC Rental Market Data Tables",
            "url": "https://www.cmhc-schl.gc.ca/professionals/housing-markets-data-and-research/housing-data/data-tables/rental-market/rental-market-report-data-tables",
            "priority": 1,
            "use_for": ["vacancy_rates", "average_rents", "turnover_rates", "rental_supply"],
            "source_type": "official_government",
        },
        {
            "name": "Statistics Canada Housing Statistics",
            "url": "https://www.statcan.gc.ca/en/subjects-start/housing",
            "priority": 1,
            "use_for": ["population", "income", "housing", "demographics", "economic_context"],
            "source_type": "official_government",
        },
    ],
    "winnipeg_property_data": [
        {
            "name": "Winnipeg Property Assessment Search",
            "url": "https://www.winnipeg.ca/city-governance/taxes/property-assessment/property-assessment-search",
            "priority": 1,
            "use_for": ["assessed_value", "property_details", "valuation_checks"],
            "source_type": "official_municipal",
        },
        {
            "name": "Winnipeg Residential Sales Information",
            "url": "https://assessment.winnipeg.ca/AsmtTax/English/SelfService/SalesBooks.stm",
            "priority": 1,
            "use_for": ["comparable_sales", "time_adjusted_sale_price", "valuation_support"],
            "source_type": "official_municipal",
        },
        {
            "name": "Winnipeg Tax Sale Information",
            "url": "https://assessment.winnipeg.ca/Asmttax/English/property/tax_sale.stm",
            "priority": 1,
            "use_for": ["tax_arrears", "distress_signal", "legal_process_warning"],
            "source_type": "official_municipal",
        },
    ],
    "us_market_data": [
        {
            "name": "HUD Fair Market Rent API",
            "url": "https://www.huduser.gov/portal/dataset/fmr-api.html",
            "priority": 1,
            "use_for": ["fair_market_rents", "income_limits", "us_rental_underwriting"],
            "source_type": "official_government_api",
        },
        {
            "name": "FRED Mortgage Rate Data",
            "url": "https://fred.stlouisfed.org/series/MORTGAGE30US",
            "priority": 1,
            "use_for": ["mortgage_rates", "capital_cost", "macro_risk"],
            "source_type": "official_economic_data",
        },
        {
            "name": "FEMA National Risk Index",
            "url": "https://www.fema.gov/flood-maps/products-tools/national-risk-index",
            "priority": 1,
            "use_for": ["flood_risk", "natural_hazard_risk", "insurance_risk", "location_risk"],
            "source_type": "official_government",
        },
    ],
}
