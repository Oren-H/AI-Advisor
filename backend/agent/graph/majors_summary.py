requirements = {
    "applied mathematics": {
        "total_points": 128,
        "degree_type": "BS",

        "core_courses": {
            "calculus": ["MATH UN1101", "MATH UN1102"],
            "multivariable": ["APMA E2000", "APMA E2001"],

            "linear_algebra": {
                "default": ["APMA E3101"],
                "substitutions": [
                    "MATH UN2010",
                    "COMS W3251"
                ]
            },

            "ordinary_differential_equations": {
                "default": ["MATH UN2030"],
                "alternative": ["APMA E2101"],
                "notes": "APMA E2101 allowed only with adviser permission if taken before declaring APMA"
            },

            "partial_differential_equations": {
                "default": ["APMA E3102"],
                "substitutions": ["MATH UN3028", "APMA E4200"]
            },

            "complex_analysis": {
                "default": ["APMA E4204"],
                "substitution": ["MATH UN3007"]
            },

            "analysis": {
                "default": ["MATH GU4061"],
                "substitution": ["MATH UN2500"]
            },

            "numerical_methods": ["APMA E4300"],

            "seminar": {
                "junior_year": ["APMA E4901"],  # 0 points
                "senior_year": ["APMA E4903"]   # 3–4 points
            },

            "research": {
                "default": ["APMA E3900"],
                "substitution": "Approved technical elective with adviser permission"
            }
        },

        "probability_statistics": {
            "group_A_probability": {
                "choose_one": [
                    "IEOR E3658",
                    "IEOR E4150",
                    "STAT GU4203",
                    "MATH GU4155"
                ]
            },
            "group_B_applied_probability_statistics": {
                "choose_one": [
                    "IEOR E3106",
                    "IEOR E4106",
                    "STAT GU4204",
                    "STAT GU4207",
                    "COMS W4771"
                ]
            }
        },

        "science_requirement": {
            "physics_sequence_choose_one": {
                "sequence_1": ["PHYS UN1401", "PHYS UN1402", "PHYS UN1403"],
                "sequence_2": ["PHYS UN1601", "PHYS UN1602", "PHYS UN2601"],
                "sequence_3": ["PHYS UN2801", "PHYS UN2802", "PHYS UN3081"]
            },
            "lab": {
                "choose_one": [
                    "PHYS UN1494",
                    "PHYS UN3081",
                    "CHEM UN1500",
                    "CHEM UN1507",
                    "CHEM UN3085",
                    "Approved astronomy/biology lab"
                ]
            }
        },

        "technical_electives": {
            "total_points": 27,
            "constraints": {
                "minimum_approved_technical": 15,
                "level": "3000+",
                "advisor_approval_required": True
            },
            "allowed_departments": [
                "APMA", "MATH", "STAT", "COMS",
                "PHYS", "IEOR", "ECON",
                "Engineering departments"
            ]
        },

        "nontechnical": {
            "total_points": 27,

            "required": {
                "university_writing": ["ENGL CC1010"],
                "core_sequence_choose_one": {
                    "literature_humanities": ["HUMA CC1001", "HUMA CC1002"],
                    "contemporary_civilization": ["COCI CC1101", "COCI CC1102"],
                    "global_core": "Two approved Global Core courses"
                },
                "art_humanities": ["HUMA UN1121", "HUMA UN1123"],
                "economics": ["ECON UN1105"]
            }
        },

        "other_requirements": {
            "intro_computing": ["ENGI E1006"],
            "art_of_engineering": ["ENGI E1102"],
            "physical_education": ["PHED UN1001", "PHED UN1002"]
        },

        "notes": {
            "seminar_required": "Must be taken in both junior and senior years",
            "transfer_policy": "GPA >= 3.0 and APMA committee approval required",
            "program_flexibility": "Course sequencing depends on specialization; adviser consultation required"
        }
    },

    "computer science": {
        "total_points": 62,
        "degree_type": "BS",

        "prerequisite": {
            "intro_programming": ["ENGI E1006"]
        },

        "math_requirements": {
            "calculus": ["MATH UN1101", "MATH UN1102", "APMA E2000"],

            "linear_algebra": {
                "choose_one": [
                    "COMS W3251",
                    "MATH UN2010",
                    "MATH UN2015",
                    "MATH UN2020",
                    "APMA E2101",
                    "APMA E3101"
                ]
            },

            "probability_statistics": {
                "choose_one": [
                    "IEOR E3658",
                    "STAT UN1201",
                    "STAT GU4001",
                    "MATH UN2015"
                ],
                "note": "MATH UN2015 may satisfy both linear algebra and probability"
            }
        },

        "core_courses": {
            "intro_programming": ["COMS W1004", "COMS W1007"],
            "data_structures": ["COMS W3134", "COMS W3137"],
            "advanced_programming": ["COMS W3157"],
            "discrete_math": ["COMS W3203"],
            "theory": ["COMS W3261"],
            "computer_systems": ["CSEE W3827"]
        },

        "area_foundations": {
            "total_courses": 4,
            "choose_from": [
                "COMS W4111",
                "COMS W4113",
                "COMS W4115",
                "COMS W4118",
                "CSEE W4119",
                "COMS W4152",
                "COMS W4156",
                "COMS W4160",
                "COMS W4167",
                "COMS W4170",
                "COMS W4181",
                "CSOR W4231",
                "COMS W4236",
                "COMS W4701",
                "COMS W4705",
                "COMS W4731",
                "COMS W4733",
                "CBMF W4761",
                "COMS W4771",
                "CSEE W4824",
                "CSEE W4868"
            ]
        },

        "computer_science_electives": {
            "total_courses": 4,
            "constraints": {
                "level": "3000+",
                "department": "COMS / joint CS",
                "minimum_points_per_course": 3
            }
        },

        "general_technical_electives": {
            "total_courses": 4,
            "constraints": {
                "level": "3000+",
                "approved_departments_only": True
            },
            "allowed_departments": [
                "SEAS departments",
                "Astronomy",
                "Biological Sciences",
                "Chemistry",
                "Earth & Environmental Sciences",
                "Mathematics",
                "Physics",
                "Psychology",
                "Statistics",
                "Economics"
            ]
        },

        "thesis_option": {
            "optional": True,
            "course": ["COMS W3902"],
            "replaces": "Up to 6 points of CS electives",
            "restrictions": "Cannot replace Area Foundation courses"
        },

        "restrictions": {
            "grading": "All courses must be taken for a letter grade",
            "D_limit": "At most one course (<=4 points) with grade D",
            "research_limit": "Max 6 points of research/project courses",
            "transfer_limit": {
                "major": 4,
                "math_exempt": True
            }
        },

        "notes": {
            "AP_credit": "AP CS score 4–5 gives exemption from COMS W1004",
            "adviser_required": "Program planning strongly advised"
        }
    },
    "electrical engineering": {
        "total_points": 128,
        "degree_type": "BS",

        "core_courses": {
            "intro": ["ELEN E1201"],
            "circuits": ["ELEN E3201", "ELEN E3331"],
            "signals_systems": ["ELEN E3801"],
            "electromagnetics": ["ELEN E3401"],
            "communications_or_networking": ["ELEN E3701", "CSEE W4119"],
            "computer_systems": ["CSEE W3827"],
            "professional_practice": ["ELEN E3399"],
            "senior_design": ["ELEN E3390"]
        },

        "labs": {
            "required": [
                "ELEN E3081",  # Circuit Analysis Lab
                "ELEN E3084",  # Signals & Systems Lab
                "ELEN E3083",  # Electronic Circuits Lab
                "ELEN E3082",  # Digital Systems Lab
                "ELEN E3043"   # Solid-State/Microwave/Fiber Optics Lab
            ],
            "notes": "Take labs with corresponding lecture courses when possible"
        },

        "math_science": {
            "calculus": ["MATH UN1101", "MATH UN1102"],
            "multivariable": ["APMA E2000", "APMA E2001"],

            "differential_equations": {
                "default": ["APMA E2101"],
                "alternative": ["MATH UN2030", "APMA E3101 or MATH UN2010"]
            },

            "probability": {
                "choose_one": ["IEOR E3658", "STAT GU4203"],
                "notes": "STAT GU4001 / SIEO W3600 generally not accepted as substitutes"
            },

            "physics": {
                "choose_one_sequence": {
                    "sequence_1": ["PHYS UN1401", "PHYS UN1402", "PHYS UN1403"],
                    "sequence_2": ["PHYS UN1601", "PHYS UN1602", "PHYS UN2601"],
                    "sequence_3": ["PHYS UN2801", "PHYS UN2802", "PHYS UN3081"]
                },
                "lab": {
                    "default": ["PHYS UN1494"],
                    "substitution_note": "CHEM UN1500 may substitute for physics lab (not generally recommended)",
                    "substitute": ["CHEM UN1500"]
                }
            },

            "chemistry": {
                "lecture_choose_one": ["CHEM UN1403", "CHEM UN1404", "CHEM UN2045", "CHEM UN1604"]
            },

            "computer_science": {
                "data_structures_choose_one": ["COMS W3134", "COMS W3136", "COMS W3137"],
                "notes": "If planning a CS minor, prefer COMS W3134 or COMS W3137"
            }
        },

        "technical_electives": {
            "total_points": 18,
            "constraints": {
                "ee_courses_must_be_3000_level_or_above": True,
                "no_significant_overlap": True,
                "advisor_approval_if_not_clearly_listed": True
            },
            "depth": {
                "points": 6,
                "requirement": ">=6 points of EE courses in ONE chosen depth area",
                "areas": [
                    "photonics, solid-state devices, and electromagnetics",
                    "circuits and electronics",
                    "signals and systems",
                    "communications and networking"
                ]
            },
            "breadth": {
                "points": 6,
                "requirement": ">=6 points OUTSIDE chosen depth area with significant engineering content"
            },
            "other": {
                "points": 6,
                "requirement": "Any additional technical courses to reach 18 total (engineering not required unless missing ELEN E1201)"
            }
        },

        "nontechnical": {
            "total_points": 27,

            "required": {
                "university_writing": ["ENGL CC1010"],  # must be taken at Columbia
                "core_humanities_sequence_choose_one": {
                    "literature_humanities": ["HUMA CC1001", "HUMA CC1002"],
                    "contemporary_civilization": ["COCI CC1101", "COCI CC1102"],
                    "global_core": "Two approved Global Core courses (letter grade)"
                },
                "art_or_music_choose_one": ["HUMA UN1121", "HUMA UN1123"],
                "economics": ["ECON UN1105"]
            },

            "electives": {
                "points": "9–11",
                "rule": "Choose from SEAS-approved nontechnical elective list (List B); cannot be modified by advisors"
            },

            "notes": "Required nontechnical courses are 16–18 points (List A) + 9–11 elective points (List B) = at least 27 total"
        },

        "other_requirements": {
            "art_of_engineering": ["ENGI E1102"],
            "physical_education": ["PHED UN1001", "PHED UN1002"]
        },

        "notes": {
            "early_start": "ELEN E1201 can be taken as early as first year (typically spring)",
            "transfer_students": {
                "plan_1": "No ELEN E1201 equivalent — cannot choose circuits & electronics as depth area",
                "plan_2": "Has ELEN E1201 equivalent — can choose circuits & electronics as depth area"
            },
            "technical_elective_waiver": {
                "condition": "If APMA E2101 replaced by MATH UN2030 + Linear Algebra",
                "effect": "Technical electives reduced from 18 to 15 points"
            }
        }
    }
}
