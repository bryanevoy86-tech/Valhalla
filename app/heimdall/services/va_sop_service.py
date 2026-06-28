from typing import Dict


TASK_SOPS = {
    "Check municipal assessment details": {
        "steps": [
            "Open municipal assessment search.",
            "Search property address.",
            "Record assessed value.",
            "Record property class.",
            "Record lot/building details.",
        ],
    },

    "Verify ownership/title information": {
        "steps": [
            "Check official ownership/title source.",
            "Confirm owner matches outreach target.",
            "Check for obvious title issues.",
            "Flag legal review if uncertain.",
        ],
    },

    "Check tax arrears / tax-sale indicators": {
        "steps": [
            "Search municipal tax sale lists.",
            "Check arrears indicators.",
            "Record tax distress findings.",
        ],
    },

    "Research nearby comparable sales": {
        "steps": [
            "Find nearby sold properties.",
            "Compare size/condition.",
            "Estimate realistic ARV.",
        ],
    },
}


def get_task_sop(task_title: str) -> Dict:
    return TASK_SOPS.get(task_title, {
        "steps": [
            "Manual review required.",
        ]
    })
