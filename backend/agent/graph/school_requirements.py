school_requirements = {
  "nontechnical_requirements": {
    "total_points_required": 27,
    "lists": {
      "A_required_nontechnical": {
        "points_required": { "min": 16, "max": 18 },
        "rules": [
          "Must be taken at Columbia.",
          "All components are required for Engineering students.",
          "Neither List A nor List B may be modified by advisers."
        ],
        "components": {
          "university_writing": ["ENGL CC1010"],
          "literature_or_civilization_sequence": {
            "choose_one": [
              {
                "id": "literature_humanities",
                "courses": ["HUMA CC1001", "HUMA CC1002"],
                "points": 6
              },
              {
                "id": "contemporary_civilization",
                "courses": ["COCI CC1101", "COCI CC1102"],
                "points": 6
              },
              {
                "id": "global_core_substitution",
                "rule": "Two approved Global Core courses taken for a letter grade.",
                "points": { "min": 6, "max": 8 }
              }
            ]
          },
          "art_or_music_humanities": {
            "choose_one": ["HUMA UN1121", "HUMA UN1123"]
          },
          "principles_of_economics": {
            "course": "ECON UN1105",
            "notes": [
              "May be satisfied through AP credit.",
              "Barnard substitutes are not permitted."
            ]
          }
        }
      },
      "B_elective_nontechnical": {
        "points_required": { "min": 9, "max": 11 },
        "rules": [
          "Must be chosen from the approved List B departmental rules.",
          "Professional/workshop/lab/project/scientific/studio/music-instruction/master’s-level professional courses do not count.",
          "AP credit in appropriate subject areas may apply toward the elective nontechnical requirement."
        ],
        "departmental_rules_reference": "course_eligibility_rules"
      }
    }
  },

  "technical_requirements": {
    "required_course": ["ENGI E1102"],
    "technical_areas": [
      "engineering",
      "mathematics",
      "physics",
      "chemistry",
      "computer_science"
    ],
    "notes": [
      "ENGI E1102 (The Art of Engineering) is required of all first-year Engineering students.",
      "Departments may recommend or require certain technical courses earlier for efficiency."
    ]
  },

  "course_eligibility_rules": {
    "scope": "Eligibility of courses for List B nontechnical electives.",
    "global_rules": {
      "does_not_count_departments": [
        "Computer Science",
        "Mathematics",
        "Physics",
        "Chemistry",
        "Statistics",
        "Astronomy",
        "Business"
      ],
      "general_exclusions": [
        "Professional courses",
        "Workshop courses",
        "Lab courses",
        "Project courses",
        "Scientific courses",
        "Studio courses",
        "Music instruction courses",
        "Master’s-level professional courses"
      ],
      "special_exceptions": [
        {
          "department": "Creative Writing",
          "rule": "All courses count (exception to workshop rule)."
        },
        {
          "department": "Visual Arts",
          "rule": "At most one course, must be 3000-level or higher."
        }
      ]
    },
    "departmental_rules": {
      "counts_all_courses": [
        "African-American Studies",
        "American Studies",
        "Ancient Studies",
        "Classics",
        "Colloquia",
        "Comparative Ethnic Studies",
        "Comparative Literature and Society",
        "Education",
        "English and Comparative Literature",
        "French and Romance Philology",
        "Germanic Languages",
        "Greek",
        "History",
        "History and Philosophy of Science",
        "Human Rights",
        "Italian",
        "Latin",
        "Latino Studies",
        "Medieval and Renaissance Studies",
        "Middle Eastern and Asian Language and Cultures",
        "Religion",
        "Slavic Languages",
        "Spanish and Portuguese",
        "Urban Studies",
        "Women and Gender Studies",
        "Art History and Archeology",
        "Asian American Studies",
        "East Asian Languages and Culture"
      ],
      "counts_with_restrictions": {
        "Anthropology": {
          "counts": [
            "Sociocultural anthropology",
            "Archaeology (except fieldwork)"
          ],
          "does_not_count": ["Biological anthropology", "Physical anthropology"]
        },
        "Architecture": {
          "counts_only": [
            "ARCH BC2500",
            "ARCH UN2505",
            "ARCH UN2530",
            "ARCH UN3117",
            "ARCH UN3120",
            "ARCH UN3123",
            "ARCH UN3501",
            "ARCH UN3502"
          ]
        },
        "Economics": {
          "counts": "All courses except excluded quantitative, econometrics, finance, and advanced theory courses.",
          "does_not_count_examples": [
            "ECON UN3412",
            "ECON UN3211",
            "ECON UN3213",
            "ECON GU4412",
            "ECON GU4415"
          ]
        },
        "Engineering": {
          "counts_only": ["BMEN E4010", "CHEN E4020", "EEHS E3900"]
        },
        "Philosophy": {
          "counts": "All courses except logic and set-theory-related courses.",
          "does_not_count": [
            "PHIL UN1401",
            "PHIL UN3411",
            "PHIL GU4137",
            "PHIL GU4431",
            "PHIL GU4424",
            "PHIL GU4810"
          ]
        },
        "Political Science": {
          "counts": "All courses except quantitative methods, game theory, and research design exclusions."
        },
        "Psychology": {
          "counts_only": ["PSYC UN1001", "PSYC UN2280"],
          "additional_counts": [
            "Perception/attention/cognition courses (2200s/3200s/4200s) except PSYC UN2235 and PSYC UN4289",
            "Social/personality/abnormal courses (2600s/3600s/4600s)"
          ]
        },
        "Sociology": {
          "counts": "All courses except SOCI UN3020"
        },
        "Sustainable Development": {
          "counts_only": [
            "SDEV UN2050",
            "SDEV UN2100",
            "SDEV UN2300",
            "SDEV UN3310",
            "SDEV UN3400",
            "SDEV GU4050",
            "SDEV GU4501"
          ]
        }
      }
    }
  },

  "advanced_placement_and_external_credit": {
    "general_rules": {
      "max_ap_points": 16,
      "purpose": "Accelerates First-Year/Sophomore Program requirements.",
      "anti_double_counting": "AP credit may be reduced to 0 if overlapping Columbia courses are taken."
    },
    "ap_credit": {
      "economics": {
        "micro_macro": {
          "scores_required": { "micro": 5, "macro_min": 4 },
          "credit_points": 4,
          "satisfies": "ECON UN1105"
        }
      },
      "computer_science": {
        "cs_a": {
          "score_min": 4,
          "credit_points": 3,
          "exemption": "COMS W1004"
        },
        "cs_principles": {
          "score_min": 4,
          "credit_points": 3,
          "exemption": "COMS W1001"
        }
      },
      "mathematics": {
        "calculus_ab": {
          "score_min": 4,
          "credit_points": 3,
          "conditions": [
            "Requires completion of MATH UN1102 with grade C or better.",
            "Credit reduced to 0 if MATH UN1101 is taken."
          ]
        },
        "calculus_bc": {
          "score_4": {
            "credit_points": 3,
            "conditions": ["Requires completion of MATH UN1102 with grade C or better."]
          },
          "score_5": {
            "credit_points": 6,
            "conditions": ["Requires completion of APMA E2000 with grade C or better."]
          }
        }
      },
      "physics": {
        "mechanics_or_em": {
          "score_min": 4,
          "credit_points": 3,
          "notes": [
            "Maximum of 6 physics AP credits total.",
            "Credit reduced to 0 if certain Columbia physics courses are taken."
          ]
        }
      }
    },
    "ib_credit": {
      "rule": "6 points of credit for each score of 6 or 7 on IB Higher Level exams in disciplines offered at Columbia."
    },
    "a_level_credit": {
      "rule": "Grades of A*, A, or B on British A-level exams may yield 6 points of credit in eligible disciplines."
    },
    "other_systems": {
      "rule": "Other national systems (e.g., French Baccalauréat) evaluated individually by advising."
    }
  }
}
