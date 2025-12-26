import { useState, useEffect } from 'react';
import { BookOpen, GraduationCap, Target, ArrowRight, Pencil } from 'lucide-react';
import { AddToPlannerButton } from './AddToPlannerButton';
import { academicService, Class, Subject, Chapter, Topic } from '../api/academicService';

export interface HomeworkTopic {
  class: string;
  subject: string;
  chapter: string;
  assignmentType: string;
}

interface Task {
  id: string;
  subject: string;
  title: string;
  description: string;
  dueDate: string;
  reminderDate: string;
  reminderTime: string;
  priority: 'low' | 'medium' | 'high';
  status: 'pending' | 'in-progress' | 'completed';
  createdAt: string;
}

interface HomeworkSetupProps {
  onStartHomework: (config: HomeworkTopic) => void;
  onAddTask?: (task: Omit<Task, 'id' | 'createdAt'>) => void;
  isDark?: boolean;
}

export function HomeworkSetup({ onStartHomework, onAddTask, isDark = false }: HomeworkSetupProps) {
  const [selectedClass, setSelectedClass] = useState('');
  const [selectedSubject, setSelectedSubject] = useState('');
  const [selectedChapter, setSelectedChapter] = useState('');
  const [selectedAssignmentType, setSelectedAssignmentType] = useState('');
  
  // Data from backend
  const [classes, setClasses] = useState<Class[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [topics, setTopics] = useState<Topic[]>([]);
  
  // Loading states
  const [loadingClasses, setLoadingClasses] = useState(true);
  const [loadingSubjects, setLoadingSubjects] = useState(false);
  const [loadingChapters, setLoadingChapters] = useState(false);
  const [loadingTopics, setLoadingTopics] = useState(false);

  // Fetch classes on component mount
  useEffect(() => {
    const fetchClasses = async () => {
      try {
        setLoadingClasses(true);
        const classesData = await academicService.getClasses();
        setClasses(classesData);
      } catch (error) {
        console.error('Error fetching classes:', error);
        // Fallback to default classes if API fails
        setClasses([
          { id: '1', name: '6th Grade' },
          { id: '2', name: '7th Grade' },
          { id: '3', name: '8th Grade' },
          { id: '4', name: '9th Grade' },
          { id: '5', name: '10th Grade' },
          { id: '6', name: '11th Grade' },
          { id: '7', name: '12th Grade' }
        ]);
      } finally {
        setLoadingClasses(false);
      }
    };

    fetchClasses();
  }, []);

  // Fetch subjects when a class is selected
  useEffect(() => {
    const fetchSubjects = async () => {
      if (!selectedClass) {
        setSubjects([]);
        return;
      }

      try {
        setLoadingSubjects(true);
        const subjectsData = await academicService.getSubjects(selectedClass);
        setSubjects(subjectsData);
      } catch (error) {
        console.error('Error fetching subjects:', error);
        // Fallback to default subjects if API fails
        const classSubjects: Record<string, Subject[]> = {
          '1': [
            { id: '1', name: 'Mathematics', class_id: '1' },
            { id: '2', name: 'Science', class_id: '1' },
            { id: '3', name: 'English', class_id: '1' },
            { id: '4', name: 'Social Studies', class_id: '1' },
            { id: '5', name: 'Geography', class_id: '1' },
            { id: '6', name: 'Art', class_id: '1' }
          ],
          '2': [
            { id: '7', name: 'Mathematics', class_id: '2' },
            { id: '8', name: 'Science', class_id: '2' },
            { id: '9', name: 'English', class_id: '2' },
            { id: '10', name: 'History', class_id: '2' },
            { id: '11', name: 'Geography', class_id: '2' },
            { id: '12', name: 'Computer', class_id: '2' }
          ],
          '3': [
            { id: '13', name: 'Algebra', class_id: '3' },
            { id: '14', name: 'Biology', class_id: '3' },
            { id: '15', name: 'English', class_id: '3' },
            { id: '16', name: 'History', class_id: '3' },
            { id: '17', name: 'Civics', class_id: '3' },
            { id: '18', name: 'Physics', class_id: '3' }
          ],
          '4': [
            { id: '19', name: 'Algebra', class_id: '4' },
            { id: '20', name: 'Biology', class_id: '4' },
            { id: '21', name: 'English', class_id: '4' },
            { id: '22', name: 'World History', class_id: '4' },
            { id: '23', name: 'Physics', class_id: '4' },
            { id: '24', name: 'Chemistry', class_id: '4' }
          ],
          '5': [
            { id: '25', name: 'Geometry', class_id: '5' },
            { id: '26', name: 'Chemistry', class_id: '5' },
            { id: '27', name: 'English', class_id: '5' },
            { id: '28', name: 'World History', class_id: '5' },
            { id: '29', name: 'Physics', class_id: '5' },
            { id: '30', name: 'Biology', class_id: '5' }
          ],
          '6': [
            { id: '31', name: 'Pre-Calculus', class_id: '6' },
            { id: '32', name: 'Chemistry', class_id: '6' },
            { id: '33', name: 'English Literature', class_id: '6' },
            { id: '34', name: 'US History', class_id: '6' },
            { id: '35', name: 'Physics', class_id: '6' },
            { id: '36', name: 'Economics', class_id: '6' }
          ],
          '7': [
            { id: '37', name: 'Calculus', class_id: '7' },
            { id: '38', name: 'Advanced Physics', class_id: '7' },
            { id: '39', name: 'English Literature', class_id: '7' },
            { id: '40', name: 'Economics', class_id: '7' },
            { id: '41', name: 'Computer Science', class_id: '7' },
            { id: '42', name: 'Statistics', class_id: '7' }
          ]
        };
        setSubjects(classSubjects[selectedClass] || []);
      } finally {
        setLoadingSubjects(false);
      }
    };

    fetchSubjects();
  }, [selectedClass]);

  // Fetch chapters when a subject is selected
  useEffect(() => {
    const fetchChapters = async () => {
      if (!selectedSubject) {
        setChapters([]);
        return;
      }

      try {
        setLoadingChapters(true);
        const chaptersData = await academicService.getChapters(selectedSubject);
        setChapters(chaptersData);
      } catch (error) {
        console.error('Error fetching chapters:', error);
        // Fallback to default chapters if API fails
        const subjectChapters: Record<string, Chapter[]> = {
          '1': [ // Mathematics
            { id: '1', name: 'Number System', subject_id: '1' },
            { id: '2', name: 'Algebra', subject_id: '1' },
            { id: '3', name: 'Geometry', subject_id: '1' },
            { id: '4', name: 'Mensuration', subject_id: '1' },
            { id: '5', name: 'Data Handling', subject_id: '1' }
          ],
          '2': [ // Science
            { id: '6', name: 'Matter in Our Surroundings', subject_id: '2' },
            { id: '7', name: 'Is Matter Around Us Pure', subject_id: '2' },
            { id: '8', name: 'Atoms and Molecules', subject_id: '2' },
            { id: '9', name: 'Structure of the Atom', subject_id: '2' },
            { id: '10', name: 'The Fundamental Unit of Life', subject_id: '2' }
          ]
          // Add more subjects as needed
        };
        setChapters(subjectChapters[selectedSubject] || []);
      } finally {
        setLoadingChapters(false);
      }
    };

    fetchChapters();
  }, [selectedSubject]);

  // Fetch topics when a chapter is selected
  useEffect(() => {
    const fetchTopics = async () => {
      if (!selectedChapter) {
        setTopics([]);
        return;
      }

      try {
        setLoadingTopics(true);
        const topicsData = await academicService.getTopics(undefined, selectedChapter);
        setTopics(topicsData);
      } catch (error) {
        console.error('Error fetching topics:', error);
        // Fallback to default topics if API fails
        const chapterTopics: Record<string, Topic[]> = {
          '1': [ // Number System
            { id: '1', name: 'Natural Numbers', chapter_id: '1' },
            { id: '2', name: 'Whole Numbers', chapter_id: '1' },
            { id: '3', name: 'Integers', chapter_id: '1' },
            { id: '4', name: 'Fractions', chapter_id: '1' },
            { id: '5', name: 'Decimals', chapter_id: '1' }
          ],
          '2': [ // Algebra
            { id: '6', name: 'Variables and Constants', chapter_id: '2' },
            { id: '7', name: 'Algebraic Expressions', chapter_id: '2' },
            { id: '8', name: 'Linear Equations', chapter_id: '2' },
            { id: '9', name: 'Word Problems', chapter_id: '2' },
            { id: '10', name: 'Applications', chapter_id: '2' }
          ]
          // Add more chapters as needed
        };
        setTopics(chapterTopics[selectedChapter] || []);
      } finally {
        setLoadingTopics(false);
      }
    };

    fetchTopics();
  }, [selectedChapter]);

  const assignmentTypes = [
    { id: 'problem-solving', name: 'Problem Solving', icon: '🧮', description: 'Math problems, equations, calculations' },
    { id: 'essay', name: 'Essay/Writing', icon: '✍️', description: 'Essays, compositions, creative writing' },
    { id: 'research', name: 'Research Project', icon: '🔬', description: 'Research assignments, projects' },
    { id: 'reading', name: 'Reading Assignment', icon: '📖', description: 'Book chapters, comprehension' },
    { id: 'worksheet', name: 'Worksheet', icon: '📝', description: 'Fill-in-the-blanks, exercises' },
    { id: 'lab', name: 'Lab Report', icon: '🧪', description: 'Science experiments, lab work' },
  ];

  // Get the selected class name
  const selectedClassName = classes.find(cls => cls.id === selectedClass)?.name || '';
  
  // Get the selected subject name
  const selectedSubjectName = subjects.find(subj => subj.id === selectedSubject)?.name || '';
  
  // Get the selected chapter name
  const selectedChapterName = chapters.find(chap => chap.id === selectedChapter)?.name || '';

  const handleStart = () => {
    if (selectedClass && selectedSubject && selectedChapter && selectedAssignmentType) {
      onStartHomework({
        class: selectedClassName,
        subject: selectedSubjectName,
        chapter: selectedChapterName,
        assignmentType: selectedAssignmentType,
      });
    }
  };

  return (
    <div className="h-full overflow-y-auto bg-gradient-to-br from-pink-50 via-rose-50 to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 px-6 py-12">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-12">
          <div className="w-20 h-20 bg-gradient-to-br from-pink-500 to-rose-500 rounded-2xl flex items-center justify-center mx-auto mb-6">
            <Pencil className="w-10 h-10 text-white" />
          </div>
          <h2 className="text-4xl mb-4 dark:text-white">Homework Help</h2>
          <p className="text-xl text-gray-600 dark:text-gray-300">
            Let's get your homework done together!
          </p>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-3xl shadow-xl p-8 space-y-8">
          {/* Step 1: Select Class */}
          <div>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-pink-100 dark:bg-pink-900/30 rounded-lg flex items-center justify-center">
                <GraduationCap className="w-6 h-6 text-pink-600 dark:text-pink-400" />
              </div>
              <div>
                <h3 className="text-xl dark:text-white">Step 1: Select Your Class</h3>
                <p className="text-sm text-gray-500 dark:text-gray-400">Choose your current grade level</p>
              </div>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {loadingClasses ? (
                <div className="col-span-full text-center py-4">Loading classes...</div>
              ) : (
                classes.map((cls) => (
                  <button
                    key={cls.id}
                    onClick={() => {
                      setSelectedClass(cls.id);
                      setSelectedSubject('');
                      setSelectedChapter('');
                      setSelectedAssignmentType('');
                    }}
                    className={`p-4 rounded-xl border-2 transition-all ${
                      selectedClass === cls.id
                        ? 'border-pink-500 bg-pink-50 dark:bg-pink-900/20'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700/50'
                    }`}
                  >
                    <div className="text-sm dark:text-white">{cls.name}</div>
                  </button>
                ))
              )}
            </div>
          </div>

          {/* Step 2: Select Subject */}
          {selectedClass && (
            <div className="animate-fadeIn">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-rose-100 dark:bg-rose-900/30 rounded-lg flex items-center justify-center">
                  <BookOpen className="w-6 h-6 text-rose-600 dark:text-rose-400" />
                </div>
                <div>
                  <h3 className="text-xl dark:text-white">Step 2: Select Subject</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Which subject is your homework in?</p>
                </div>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {loadingSubjects ? (
                  <div className="col-span-full text-center py-4">Loading subjects...</div>
                ) : (
                  subjects.map((subject) => (
                    <button
                      key={subject.id}
                      onClick={() => {
                        setSelectedSubject(subject.id);
                        setSelectedChapter('');
                        setSelectedAssignmentType('');
                      }}
                      className={`p-4 rounded-xl border-2 transition-all ${
                        selectedSubject === subject.id
                          ? 'border-rose-500 bg-rose-50 dark:bg-rose-900/20'
                          : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700/50'
                      }`}
                    >
                      <span className="dark:text-white">{subject.name}</span>
                    </button>
                  ))
                )}
              </div>
            </div>
          )}

          {/* Step 3: Select Chapter */}
          {selectedSubject && (
            <div className="animate-fadeIn">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-purple-100 dark:bg-purple-900/30 rounded-lg flex items-center justify-center">
                  <Target className="w-6 h-6 text-purple-600 dark:text-purple-400" />
                </div>
                <div>
                  <h3 className="text-xl dark:text-white">Step 3: Select Chapter</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">What chapter is your homework about?</p>
                </div>
              </div>
              <div className="grid md:grid-cols-2 gap-3">
                {loadingChapters ? (
                  <div className="col-span-full text-center py-4">Loading chapters...</div>
                ) : (
                  chapters.map((chapter) => (
                    <button
                      key={chapter.id}
                      onClick={() => {
                        setSelectedChapter(chapter.id);
                        setSelectedAssignmentType('');
                      }}
                      className={`p-3 rounded-xl border-2 transition-all text-left ${
                        selectedChapter === chapter.id
                          ? 'border-purple-500 bg-purple-50 dark:bg-purple-900/20'
                          : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700/50'
                      }`}
                    >
                      <div className="text-sm dark:text-white">{chapter.name}</div>
                    </button>
                  ))
                )}
              </div>
            </div>
          )}

          {/* Step 4: Select Assignment Type */}
          {selectedChapter && (
            <div className="animate-fadeIn">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-orange-100 dark:bg-orange-900/30 rounded-lg flex items-center justify-center">
                  <Pencil className="w-6 h-6 text-orange-600 dark:text-orange-400" />
                </div>
                <div>
                  <h3 className="text-xl dark:text-white">Step 4: Assignment Type</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">What kind of homework is it?</p>
                </div>
              </div>
              <div className="grid md:grid-cols-3 gap-4">
                {assignmentTypes.map((type) => (
                  <button
                    key={type.id}
                    onClick={() => setSelectedAssignmentType(type.id)}
                    className={`p-5 rounded-xl border-2 transition-all text-left ${
                      selectedAssignmentType === type.id
                        ? 'border-orange-500 bg-orange-50 dark:bg-orange-900/20'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700/50'
                    }`}
                  >
                    <div className="text-2xl mb-2">{type.icon}</div>
                    <h4 className="mb-1 dark:text-white">{type.name}</h4>
                    <p className="text-xs text-gray-600 dark:text-gray-400">{type.description}</p>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Start Button */}
          {selectedAssignmentType && (
            <div className="pt-6 border-t border-gray-200 dark:border-gray-700 animate-fadeIn">
              <div className="bg-gradient-to-r from-pink-50 to-purple-50 dark:from-pink-900/20 dark:to-purple-900/20 rounded-2xl p-6">
                <h4 className="mb-3 dark:text-white">Homework Details</h4>
                <div className="grid md:grid-cols-2 gap-3 mb-4 text-sm">
                  <div className="flex items-center gap-2">
                    <span className="text-gray-600 dark:text-gray-400">Class:</span>
                    <span className="dark:text-white">{selectedClassName}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-gray-600 dark:text-gray-400">Subject:</span>
                    <span className="dark:text-white">{selectedSubjectName}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-gray-600 dark:text-gray-400">Chapter:</span>
                    <span className="dark:text-white">{selectedChapterName}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-gray-600 dark:text-gray-400">Type:</span>
                    <span className="capitalize dark:text-white">{assignmentTypes.find(t => t.id === selectedAssignmentType)?.name}</span>
                  </div>
                </div>
                <button
                  onClick={handleStart}
                  className="w-full flex items-center justify-center gap-2 px-6 py-4 bg-gradient-to-r from-pink-500 to-rose-500 text-white rounded-xl hover:from-pink-600 hover:to-rose-600 transition-all shadow-lg hover:shadow-xl"
                >
                  <span className="text-lg">Start Homework Help</span>
                  <ArrowRight className="w-6 h-6" />
                </button>
                {onAddTask && (
                  <div className="mt-4">
                    <AddToPlannerButton
                      subject={selectedSubjectName}
                      topic={selectedChapterName}
                      onAddTask={(task) => {
                        onAddTask(task);
                        alert('Task added to your planner! View it by clicking the Planner button in the header.');
                      }}
                      isDark={isDark}
                    />
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}