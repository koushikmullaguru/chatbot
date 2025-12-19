from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from ...core.database import get_db
from ...api.deps import get_current_user
from ...models.user_management import User, StudentProfile, ParentStudentRelation
from ...models.planner_performance import (
    ReportCard, SubjectGrade, StudySession, Task
)
from ...schemas.planner_performance import (
    StudentPerformanceReport, TeacherInsights, ParentDashboard,
    ReportCardWithSubjectGrades, WeeklyPerformanceMetrics
)

router = APIRouter()


@router.get("/student", response_model=StudentPerformanceReport)
def get_student_performance(
    student_profile_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Full performance report for a student.
    """
    # Get student profile
    student_profile = db.query(StudentProfile).filter(
        StudentProfile.id == student_profile_id
    ).first()
    
    if not student_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    # Check if user has access to this student profile
    if current_user.user_type == "parent":
        is_linked = db.query(ParentStudentRelation).filter(
            ParentStudentRelation.parent_id == current_user.id,
            ParentStudentRelation.student_profile_id == student_profile_id
        ).first()
        
        if not is_linked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not linked to this student"
            )
    elif current_user.user_type == "student":
        if student_profile.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own performance report"
            )
    
    # Get report cards with subject grades
    report_cards_with_grades = []
    report_cards = db.query(ReportCard).filter(
        ReportCard.student_profile_id == student_profile_id
    ).all()
    
    for report_card in report_cards:
        subject_grades = db.query(SubjectGrade).filter(
            SubjectGrade.report_card_id == report_card.id
        ).all()
        
        report_card_with_grades = ReportCardWithSubjectGrades(
            id=str(report_card.id),
            student_profile_id=str(report_card.student_profile_id),
            term=report_card.term,
            year=report_card.year,
            percentage=report_card.percentage,
            rank=report_card.rank,
            subject_grades=subject_grades
        )
        report_cards_with_grades.append(report_card_with_grades)
    
    # Get study sessions
    study_sessions = db.query(StudySession).filter(
        StudySession.student_profile_id == student_profile_id
    ).all()
    
    # Get tasks
    tasks = db.query(Task).filter(
        Task.student_profile_id == student_profile_id
    ).all()
    
    # TODO: Calculate weekly metrics
    # For now, return placeholder data
    weekly_metrics = WeeklyPerformanceMetrics(
        total_study_time=120,  # 2 hours
        average_performance_score=75.5,
        completed_tasks=5,
        pending_tasks=3
    )
    
    return StudentPerformanceReport(
        student_profile_id=student_profile_id,
        report_cards=report_cards_with_grades,
        study_sessions=study_sessions,
        tasks=tasks,
        weekly_metrics=weekly_metrics
    )


@router.get("/teacher/insights", response_model=TeacherInsights)
def get_teacher_insights(
    class_id: str,
    subject_id: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Class-wide analytics for teachers.
    """
    # Only teachers can view insights
    if current_user.user_type != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can view class insights"
        )
    
    # TODO: Calculate actual insights from the database
    # For now, return placeholder data
    return TeacherInsights(
        class_id=class_id,
        subject_id=subject_id,
        student_count=25,
        average_performance=78.5,
        top_performers=[
            {"name": "Student A", "percentage": 95},
            {"name": "Student B", "percentage": 92},
            {"name": "Student C", "percentage": 90}
        ],
        struggling_students=[
            {"name": "Student X", "percentage": 45},
            {"name": "Student Y", "percentage": 50},
            {"name": "Student Z", "percentage": 55}
        ]
    )


@router.get("/parent/dashboard", response_model=ParentDashboard)
def get_parent_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Dashboard for multiple linked children.
    """
    # Only parents can view this dashboard
    if current_user.user_type != "parent":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can view this dashboard"
        )
    
    # Get all student profiles linked to this parent
    student_profiles = (
        db.query(StudentProfile)
        .join(ParentStudentRelation)
        .filter(ParentStudentRelation.parent_id == current_user.id)
        .all()
    )
    
    if not student_profiles:
        return ParentDashboard(
            parent_id=str(current_user.id),
            students=[],
            weekly_metrics=[]
        )
    
    # TODO: Get actual student data and metrics
    # For now, return placeholder data
    students_data = []
    for student in student_profiles:
        # Get latest report card for this student
        latest_report_card = db.query(ReportCard).filter(
            ReportCard.student_profile_id == student.id
        ).order_by(ReportCard.year.desc(), ReportCard.term.desc()).first()
        
        student_data = {
            "id": str(student.id),
            "name": student.name,
            "grade": student.grade,
            "latest_percentage": latest_report_card.percentage if latest_report_card else None,
            "latest_rank": latest_report_card.rank if latest_report_card else None
        }
        students_data.append(student_data)
    
    # TODO: Get actual weekly metrics
    # For now, return placeholder data
    weekly_metrics = [
        {"student_name": "Student A", "study_time": 120, "completed_tasks": 5, "avg_performance": 85},
        {"student_name": "Student B", "study_time": 90, "completed_tasks": 3, "avg_performance": 75}
    ]
    
    return ParentDashboard(
        parent_id=str(current_user.id),
        students=students_data,
        weekly_metrics=weekly_metrics
    )


@router.get("/teacher/students")
def get_teacher_students(
    class_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    List students in a teacher's class.
    """
    # Only teachers can view students in their class
    if current_user.user_type != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can view class students"
        )
    
    # TODO: Get actual students for this class
    # For now, return placeholder data
    return [
        {
            "id": "student-1-id",
            "name": "Student A",
            "grade": "10",
            "roll_number": "101"
        },
        {
            "id": "student-2-id",
            "name": "Student B",
            "grade": "10",
            "roll_number": "102"
        }
    ]


@router.get("/content/{id}/download")
def download_content(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Generate downloadable file for content.
    """
    # TODO: Get content and generate downloadable file
    # For now, return a placeholder response
    return {
        "message": "Content download request received",
        "content_id": id,
        "download_url": "https://example.com/download/file.pdf",
        "status": "ready"
    }