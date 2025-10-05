import pandas as pd


def sample_members():
    data = [
        {
            "id": "M001",
            "company": "CU1",
            "name": "Alice",
            "joined_year": 2018,
            "credit_score": 720,
            "amount_transaction": 25000,
        },
        {
            "id": "M002",
            "company": "CU1",
            "name": "Bob",
            "joined_year": 2020,
            "credit_score": 650,
            "amount_transaction": 12000,
        },
        {
            "id": "M003",
            "company": "CU2",
            "name": "Charlie",
            "joined_year": 2015,
            "credit_score": 780,
            "amount_transaction": 40000,
        },
    ]
    return pd.DataFrame(data)


def sample_missions():
    data = [
        {
            "mission_id": "MSN001",
            "company": "CU1",
            "title": "Auto Loan",
            "description": "Car financing mission",
            "type": "auto loan",
            "stages": [
                "IDENTIFIED",
                "INTENT DETECTED",
                "ACTIVATED",
                "ENGAGED",
                "CONVERTED",
            ],
        },
        {
            "mission_id": "MSN002",
            "company": "CU1",
            "title": "Personal Loan",
            "description": "Personal financing mission",
            "type": "personal loan",
            "stages": [
                "IDENTIFIED",
                "INTENT DETECTED",
                "ACTIVATED",
                "ENGAGED",
                "CONVERTED",
            ],
        },
    ]
    return pd.DataFrame(data)
