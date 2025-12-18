from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user_management import User, StudentProfile, ParentStudentRelation
from ..models.planner_performance import Task
from ..schemas.planner_performance import (
    TaskCreate, TaskResponse, TaskUpdate,
    WeeklyPerformanceMetrics
)

router = APIRouter()


@router.get("/tasks", response_model=List[TaskResponse])
def get_tasks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get student tasks for the planner.
    """
    if current_user.user_type == "student":
        # Get student profile
        student_profile = db.query(StudentProfile).filter(
            StudentProfile.user_id == current_user.id
        ).first()
        
        if not student_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student profile not found"
            )
        
        # Get all tasks for this student
        tasks = db.query(Task).filter(
            Task.student_profile_id == student_profile.id
        ).all()
        
        return tasks
    elif current_user.user_type == "parent":
        # Get all student profiles linked to this parent
        student_profiles = (
            db.query(StudentProfile)
            .join(ParentStudentRelation)
            .filter(ParentStudentRelation.parent_id == current_user.id)
            .all()
        )
        
        if not student_profiles:
            return []
        
        # Get all tasks for these students
        student_profile_ids = [sp.id for sp in student_profiles]
        tasks = db.query(Task).filter(
            Task.student_profile_id.in_(student_profile_ids)
        ).all()
        
        return tasks
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students and parents can view tasks"
        )


@router.post("/tasks", response_model=TaskResponse)
def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Add new task to the planner.
    """
    # Verify student profile exists and user has access
    student_profile = db.query(StudentProfile).filter(
        StudentProfile.id == task_data.student_profile_id
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
            ParentStudentRelation.student_profile_id == task_data.student_profile_id
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
                detail="You can only create tasks for your own profile"
            )
    
    # Create task
    task = Task(
        student_profile_id=task_data.student_profile_id,
        subject_id=task_data.subject_id,
        title=task_data.title,
        due_date=task_data.due_date,
        priority=task_data.priority,
        status=task_data.status
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    
    return task


@router.put("/tasks/{id}", response_model=TaskResponse)
def update_task(
    id: str,
    task_data: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update task status (Pending/Completed).
    """
    # Get task
    task = db.query(Task).filter(Task.id == id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Check if user has access to this task
    student_profile = db.query(StudentProfile).filter(
        StudentProfile.id == task.student_profile_id
    ).first()
    
    if current_user.user_type == "parent":
        is_linked = db.query(ParentStudentRelation).filter(
            ParentStudentRelation.parent_id == current_user.id,
            ParentStudentRelation.student_profile_id == task.student_profile_id
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
                detail="You can only update your own tasks"
            )
    
    # Update task
    for field, value in task_data.dict(exclude_unset=True).items():
        setattr(task, field, value)
    
    db.commit()
    db.refresh(task)
    
    return task


@router.delete("/tasks/{id}")
def delete_task(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Remove task from planner.
    """
    # Get task
    task = db.query(Task).filter(Task.id == id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Check if user has access to this task
    student_profile = db.query(StudentProfile).filter(
        StudentProfile.id == task.student_profile_id
    ).first()
    
    if current_user.user_type == "parent":
        is_linked = db.query(ParentStudentRelation).filter(
            ParentStudentRelation.parent_id == current_user.id,
            ParentStudentRelation.student_profile_id == task.student_profile_id
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
                detail="You can only delete your own tasks"
            )
    
    # Delete task
    db.delete(task)
    db.commit()
    
    return {"message": "Task deleted successfully"}


@router.get("/progress/weekly", response_model=WeeklyPerformanceMetrics)
def get_weekly_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get weekly performance metrics.
    """
    if current_user.user_type == "student":
        # Get student profile
        student_profile = db.query(StudentProfile).filter(
            StudentProfile.user_id == current_user.id
        ).first()
        
        if not student_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student profile not found"
            )
        
        student_profile_id = student_profile.id
    elif current_user.user_type == "parent":
        # For parents, we'll aggregate metrics for all their students
        # For now, just return placeholder data
        return WeeklyPerformanceMetrics(
            total_study_time=0,
            average_performance_score=0,
            completed_tasks=0,
            pending_tasks=0
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students and parents can view progress metrics"
        )
    
    # TODO: Calculate actual metrics from the database
    # For now, return placeholder data
    return WeeklyPerformanceMetrics(
        total_study_time=120,  # 2 hours
        average_performance_score=75.5,
        completed_tasks=5,
        pending_tasks=3
    )