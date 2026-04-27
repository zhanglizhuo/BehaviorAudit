from .mm_tba import MMTBAAdapter
from .oulad import OULADAdapter
from .uci_student import UCIStudentAdapter
from .xapi_edu import XAPIEduAdapter
from .student_dropout import StudentDropoutAdapter
from .entrance_exam import EntranceExamAdapter
from .higher_ed import HigherEdAdapter

__all__ = [
    "MMTBAAdapter", "OULADAdapter", "UCIStudentAdapter",
    "XAPIEduAdapter", "StudentDropoutAdapter", "EntranceExamAdapter", "HigherEdAdapter",
]