from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Field:
    start: int
    width: int

    def extract(self, record: str) -> str:
        return record[self.start - 1 : self.start - 1 + self.width].strip()


# Official positions from CDC ed22inp.txt. Positions are one-based.
FIELDS = {
    "visit_month": Field(1, 2),
    "visit_weekday": Field(3, 1),
    "arrival_time": Field(4, 4),
    "waiting_time_minutes": Field(8, 4),
    "length_of_stay_minutes": Field(12, 4),
    "age": Field(16, 3),
    "sex": Field(25, 1),
    "arrival_by_ambulance": Field(33, 2),
    "temperature_f": Field(48, 4),
    "heart_rate": Field(52, 3),
    "respiratory_rate": Field(55, 3),
    "systolic_bp": Field(58, 3),
    "diastolic_bp": Field(61, 3),
    "spo2": Field(64, 3),
    "triage_level": Field(67, 2),
    "pain_score": Field(69, 2),
    "reason_for_visit_code": Field(73, 5),
    "diagnosis_code": Field(122, 4),
    "no_followup": Field(488, 1),
    "return_ed": Field(489, 1),
    "return_refer": Field(490, 1),
    "left_without_seen": Field(491, 1),
    "left_before_complete": Field(492, 1),
    "left_ama": Field(493, 1),
    "dead_on_arrival": Field(494, 1),
    "died_in_ed": Field(495, 1),
    "transfer_nursing": Field(496, 1),
    "transfer_psych": Field(497, 1),
    "transfer_other": Field(498, 1),
    "admit_hospital": Field(499, 1),
    "observation_hospitalized": Field(500, 1),
    "observation_discharged": Field(501, 1),
    "other_disposition": Field(502, 1),
    "hospital_code": Field(544, 3),
    "patient_code": Field(547, 3),
    "survey_year": Field(2341, 4),
    "patient_weight": Field(2359, 11),
}

SEX = {"1": "F", "2": "M"}
WEEKDAY = {
    "1": "Sunday",
    "2": "Monday",
    "3": "Tuesday",
    "4": "Wednesday",
    "5": "Thursday",
    "6": "Friday",
    "7": "Saturday",
}
TRIAGE = {"1": 1, "2": 2, "3": 3, "4": 4, "5": 5}
