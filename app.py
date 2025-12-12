"""
Virtual Course Selection Application

Expected columns in courses.xlsx:
- 课程号 (Course ID)
- 班号 (Class ID)
- 院系 (Department)
- 课程名 (Course Name)
- 参考学分 (Credits)
- 授课教师 (Instructor)
- 上课时间 (Time)
- 修读对象 (Target Audience)

Additional columns that may exist:
- 学年学期 (Academic Year/Term)
- 表格类型 (Table Type)
- 内部学期 (Internal Term)
- 课程英文名 (English Course Name)
- 课程类别 (Course Category)
- 周学时 (Weekly Hours)
- 总学时 (Total Hours)
- 起止周 (Start-End Weeks)
- 备注 (Notes)
"""

import streamlit as st
import pandas as pd
import numpy as np
from collections import defaultdict
import io
import base64

# Language dictionary for internationalization
LANGUAGES = {
    "en": {
        "app_title": "Virtual Course Selection Application",
        "department": "Department",
        "course_name": "Course Name",
        "class_id": "Class ID",
        "credits": "Credits",
        "instructor": "Instructor",
        "time": "Time",
        "select": "Select",
        "cancel": "Cancel",
        "user_department": "User Department",
        "degree_type": "Degree Type",
        "single_degree": "Single Degree (Max 25 Credits)",
        "double_degree": "Double Degree (Max 30 Credits)",
        "filter_by_department": "Filter by Course Department",
        "search_course": "Search by Course Name",
        "timetable": "Timetable",
        "current_credits": "Current Credits",
        "max_credits": "Max Credits",
        "warning": "Warning",
        "credit_exceeded": "Credit limit exceeded!",
        "conflict_detected": "Time conflict detected with",
        "no_conflict": "No conflicts. Course added successfully.",
        "page": "Page",
        "of": "of",
        "courses_per_page": "courses per page",
        "week_mon": "Mon",
        "week_tue": "Tue",
        "week_wed": "Wed",
        "week_thu": "Thu",
        "week_fri": "Fri",
        "week_sat": "Sat",
        "week_sun": "Sun",
        "periods": "Periods",
        "language": "Language",
        "chinese": "Chinese",
        "english": "English",
        "file_not_found": "courses.xlsx file not found. Please upload a file or generate sample data.",
        "upload_file": "Upload Excel File",
        "generate_sample": "Generate Sample Data",
        "all_departments": "All Departments",
        "all_courses": "All Courses",
        "selected_courses": "Selected Courses",
        "export_timetable": "Export Timetable",
        "export_success": "Timetable exported successfully!"
    },
    "zh": {
        "app_title": "虚拟选课系统",
        "department": "院系",
        "course_name": "课程名",
        "class_id": "班号",
        "credits": "学分",
        "instructor": "授课教师",
        "time": "上课时间",
        "select": "选课",
        "cancel": "取消",
        "user_department": "用户所在院系",
        "degree_type": "学位类型",
        "single_degree": "单学位（最多25学分）",
        "double_degree": "双学位（最多30学分）",
        "filter_by_department": "按院系筛选",
        "search_course": "搜索课程名",
        "timetable": "课程表",
        "current_credits": "当前学分",
        "max_credits": "最大学分",
        "warning": "警告",
        "credit_exceeded": "超过学分限制！",
        "conflict_detected": "检测到时间冲突，与以下课程冲突：",
        "no_conflict": "无冲突。成功添加课程。",
        "page": "第",
        "of": "页，共",
        "courses_per_page": "门课程每页",
        "week_mon": "周一",
        "week_tue": "周二",
        "week_wed": "周三",
        "week_thu": "周四",
        "week_fri": "周五",
        "week_sat": "周六",
        "week_sun": "周日",
        "periods": "节次",
        "language": "语言",
        "chinese": "中文",
        "english": "英文",
        "file_not_found": "未找到 courses.xlsx 文件。请上传文件或生成示例数据。",
        "upload_file": "上传Excel文件",
        "generate_sample": "生成示例数据",
        "all_departments": "所有院系",
        "all_courses": "所有课程",
        "selected_courses": "已选课程",
        "export_timetable": "导出课程表",
        "export_success": "课程表导出成功！"
    }
}

def load_data():
    """Load course data from Excel file or generate sample data"""
    try:
        # Try to load the Excel file
        df = pd.read_excel("courses.xlsx")
    except FileNotFoundError:
        try:
            # Try the Chinese-named file
            df = pd.read_excel("课表信息汇总.xlsx")
        except FileNotFoundError:
            # Return None if no file found
            return None
    
    # Process the data according to requirements
    # Merge rows with same Course ID + Class ID
    grouped = df.groupby(['课程号', '班号'], as_index=False)
    
    processed_data = []
    for _, group in grouped:
        # Get the first row as base
        row = group.iloc[0].copy()
        
        # Concatenate Target Audience (修读对象)
        if len(group) > 1:
            row['修读对象'] = '，'.join(group['修读对象'].astype(str).unique())
        
        processed_data.append(row)
    
    return pd.DataFrame(processed_data)

def generate_sample_data():
    """Generate sample course data for demonstration"""
    sample_data = {
        '课程号': ['CS101', 'CS102', 'CS201', 'CS202', 'CS301', 'CS302', 'CS401', 'CS402'],
        '班号': ['01', '01', '01', '01', '01', '01', '01', '01'],
        '院系': ['计算机学院', '计算机学院', '计算机学院', '计算机学院', '计算机学院', '计算机学院', '计算机学院', '计算机学院'],
        '课程名': ['计算机基础', 'Python编程', '数据结构', '算法分析', '数据库原理', '操作系统', '计算机网络', '软件工程'],
        '参考学分': [3, 3, 4, 4, 3, 3, 3, 3],
        '授课教师': ['张老师', '李老师', '王老师', '赵老师', '孙老师', '周老师', '吴老师', '郑老师'],
        '上课时间': [
            '周一1-2，周三3-4',
            '周二1-2单，周四3-4单',
            '周一3-4双，周五1-2双',
            '周二5-6，周四5-6',
            '周三7-8，周五3-4',
            '周一7-8单，周三7-8单',
            '周二7-8双，周四7-8双',
            '周五5-6'
        ],
        '修读对象': [
            '计算机学院学生',
            '全校学生在籍',
            '计算机学院学生',
            '计算机学院学生',
            '计算机学院学生',
            '计算机学院学生',
            '计算机学院学生',
            '计算机学院学生'
        ]
    }
    return pd.DataFrame(sample_data)

def parse_time(time_str):
    """
    Parse time string into structured data
    Format examples:
    - "周一1-2" (Every week)
    - "周二1-2单" (Odd weeks only)
    - "周三1-2双" (Even weeks only)
    - "周一1-2，周三3-4" (Multiple time slots)
    """
    if pd.isna(time_str):
        return []
    
    slots = str(time_str).split('，')
    parsed_slots = []
    
    for slot in slots:
        # Extract day, periods, and week type
        if '单' in slot:
            week_type = 'odd'
            slot = slot.replace('单', '')
        elif '双' in slot:
            week_type = 'even'
            slot = slot.replace('双', '')
        else:
            week_type = 'all'
        
        # Extract day and periods
        day_map = {
            '周一': 'mon', '周二': 'tue', '周三': 'wed',
            '周四': 'thu', '周五': 'fri', '周六': 'sat', '周日': 'sun'
        }
        
        day = None
        for chinese_day, english_day in day_map.items():
            if slot.startswith(chinese_day):
                day = english_day
                slot = slot[len(chinese_day):]
                break
        
        if day and '-' in slot:
            try:
                start_period, end_period = map(int, slot.split('-'))
                parsed_slots.append({
                    'day': day,
                    'start_period': start_period,
                    'end_period': end_period,
                    'week_type': week_type
                })
            except ValueError:
                continue  # Skip malformed entries
    
    return parsed_slots

def check_conflict(new_course_time, selected_courses):
    """
    Check if there's a time conflict between new course and selected courses
    Conflict occurs when:
    - Same day
    - Overlapping periods
    - Overlapping weeks (all vs all, odd vs even = no conflict)
    """
    new_time_slots = parse_time(new_course_time)
    
    for course in selected_courses:
        existing_time_slots = parse_time(course['上课时间'])
        
        for new_slot in new_time_slots:
            for existing_slot in existing_time_slots:
                # Check if same day
                if new_slot['day'] == existing_slot['day']:
                    # Check if periods overlap
                    if (new_slot['start_period'] <= existing_slot['end_period'] and 
                        new_slot['end_period'] >= existing_slot['start_period']):
                        # Check if weeks overlap
                        # No conflict if one is odd and the other is even
                        if not ((new_slot['week_type'] == 'odd' and existing_slot['week_type'] == 'even') or
                                (new_slot['week_type'] == 'even' and existing_slot['week_type'] == 'odd')):
                            return course['课程名']  # Return conflicting course name
    
    return None  # No conflict

def create_timetable(selected_courses, lang):
    """Create timetable visualization"""
    # Initialize timetable matrix (7 days x 12 periods) - Mon-Sun as requested
    days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']  # Added sat and sun as requested
    day_names = {
        'mon': lang["week_mon"], 'tue': lang["week_tue"], 'wed': lang["week_wed"],
        'thu': lang["week_thu"], 'fri': lang["week_fri"], 'sat': lang["week_sat"], 
        'sun': lang["week_sun"]
    }
    
    timetable = {}
    for day in days:
        timetable[day] = {period: [] for period in range(1, 13)}
    
    # Fill timetable with selected courses
    for course in selected_courses:
        time_slots = parse_time(course['上课时间'])
        for slot in time_slots:
            day = slot['day']
            week_type = slot['week_type']
            course_display = f"{course['课程名']} ({course['班号']})"
            
            for period in range(slot['start_period'], slot['end_period'] + 1):
                if week_type == 'odd':
                    timetable[day][period].append({'course': course_display, 'week': 'odd'})
                elif week_type == 'even':
                    timetable[day][period].append({'course': course_display, 'week': 'even'})
                else:  # all weeks
                    timetable[day][period].append({'course': course_display, 'week': 'all'})
    
    return timetable, day_names

def export_timetable_to_excel(selected_courses, lang):
    """Export timetable to Excel file"""
    if not selected_courses:
        return None
    
    # Create timetable data
    timetable, day_names = create_timetable(selected_courses, lang)
    
    # Always show periods 1-12
    periods = list(range(1, 13))
    
    # Create timetable DataFrame for export
    timetable_df = pd.DataFrame(index=periods, columns=list(day_names.values()))
    
    for day_key, day_name in day_names.items():
        for period in periods:
            courses_in_slot = timetable[day_key][period]
            if courses_in_slot:
                # Format display based on week type
                course_texts = []
                for c in courses_in_slot:
                    if c['week'] == 'odd':
                        course_texts.append(f"{c['course']} [单]")
                    elif c['week'] == 'even':
                        course_texts.append(f"{c['course']} [双]")
                    else:
                        course_texts.append(c['course'])
                timetable_df.loc[period, day_name] = '\n'.join(course_texts)
            else:
                timetable_df.loc[period, day_name] = ""
    
    # Convert to Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        timetable_df.to_excel(writer, sheet_name='课程表' if lang.get('language') == 'zh' else 'Timetable')
        
        # Also export selected courses as a separate sheet with all necessary information for import
        selected_df = pd.DataFrame(selected_courses)
        selected_df.to_excel(writer, sheet_name='已选课程' if lang.get('language') == 'zh' else 'Selected Courses', index=False)
    
    output.seek(0)
    return output

def main():
    st.set_page_config(page_title="Virtual Course Selection", layout="wide")
    
    # Language selection - Changed default to Chinese
    language = st.sidebar.selectbox(
        "Language / 语言",
        options=["zh", "en"],  # Changed order to make Chinese the default
        format_func=lambda x: "中文" if x == "zh" else "English"
    )
    lang = LANGUAGES[language]
    
    st.title(lang["app_title"])
    
    # Load data
    df = load_data()
    
    if df is None:
        st.warning(lang["file_not_found"])
        
        col1, col2 = st.columns(2)
        with col1:
            uploaded_file = st.file_uploader(lang["upload_file"], type=['xlsx'])
            if uploaded_file is not None:
                df = pd.read_excel(uploaded_file)
        
        with col2:
            if st.button(lang["generate_sample"]):
                df = generate_sample_data()
                # Save to file for future use
                df.to_excel("courses.xlsx", index=False)
        
        if df is None:
            st.stop()
    
    # Initialize session state
    if 'selected_courses' not in st.session_state:
        st.session_state.selected_courses = []
    
    if 'user_department' not in st.session_state:
        st.session_state.user_department = ""
    
    if 'degree_type' not in st.session_state:
        st.session_state.degree_type = "single"  # single or double
    
    # Sidebar controls
    st.sidebar.header(lang["user_department"])
    
    # Get unique departments
    departments = sorted(df['院系'].unique())
    
    # User department selection
    user_dept = st.sidebar.selectbox(
        lang["user_department"],
        options=departments,
        key="user_dept_select"
    )
    
    # Degree type selection
    degree_type = st.sidebar.radio(
        lang["degree_type"],
        options=["single", "double"],
        format_func=lambda x: lang["single_degree"] if x == "single" else lang["double_degree"]
    )
    
    max_credits = 25 if degree_type == "single" else 30
    
    # Calculate current credits
    current_credits = sum(float(course.get('参考学分', 0)) for course in st.session_state.selected_courses)
    
    # Filter courses based on user department and target audience
    filtered_df = df.copy()
    
    # Apply visibility logic: 
    # If Course Department ≠ User Department AND Target Audience does NOT contain "全校学生在籍", hide course
    def should_show_course(row):
        course_dept = row['院系']
        target_audience = str(row.get('修读对象', ''))
        return course_dept == user_dept or '全校学生在籍' in target_audience
    
    filtered_df = filtered_df[filtered_df.apply(should_show_course, axis=1)]
    
    # Additional filters
    st.sidebar.header("Filters")
    
    # Department filter
    all_depts = [lang["all_departments"]] + sorted(filtered_df['院系'].unique())
    dept_filter = st.sidebar.selectbox(
        lang["filter_by_department"],
        options=all_depts
    )
    
    if dept_filter != lang["all_departments"]:
        filtered_df = filtered_df[filtered_df['院系'] == dept_filter]
    
    # Course name search
    course_search = st.sidebar.text_input(lang["search_course"])
    if course_search:
        filtered_df = filtered_df[filtered_df['课程名'].str.contains(course_search, case=False, na=False)]
    
    # Pagination
    courses_per_page = 10
    total_courses = len(filtered_df)
    total_pages = (total_courses - 1) // courses_per_page + 1 if total_courses > 0 else 1
    
    page_number = st.number_input(
        "Page",  # Added a label for accessibility
        min_value=1,
        max_value=total_pages,
        value=1,
        label_visibility="collapsed"  # Hide the label visually but keep it for accessibility
    )
    
    start_idx = (page_number - 1) * courses_per_page
    end_idx = start_idx + courses_per_page
    page_courses = filtered_df.iloc[start_idx:end_idx]
    
    # Display courses table with select buttons properly aligned
    if not page_courses.empty:
        # Removed the "X courses per page" text
        
        # Create a container for each course with properly aligned select button
        for idx, (_, row) in enumerate(page_courses.iterrows()):
            with st.container():
                col1, col2, col3, col4, col5, col6, col7 = st.columns([1, 2, 1, 1, 1, 2, 1])
                
                col1.write(row['院系'])
                col2.write(row['课程名'])
                col3.write(row['班号'])
                col4.write(str(row['参考学分']))
                col5.write(row['授课教师'])
                col6.write(row['上课时间'])
                
                button_key = f"select_{idx}_{page_number}"
                if col7.button(lang["select"], key=button_key, use_container_width=True):
                    # Check for conflicts
                    conflict_course = check_conflict(row['上课时间'], st.session_state.selected_courses)
                    
                    if conflict_course:
                        st.toast(f"❌ {lang['conflict_detected']} {conflict_course}", icon='⚠️')
                    else:
                        # Add course to selected courses
                        st.session_state.selected_courses.append(row.to_dict())
                        st.toast(f"✅ {lang['no_conflict']}", icon='🎉')
                        st.rerun()
                
                # Add a separator line
                st.divider()
    else:
        st.info(lang["all_courses"])
    
    # Display timetable before selected courses table
    st.subheader(lang["timetable"])
    
    # Create and display timetable
    if st.session_state.selected_courses:
        timetable, day_names = create_timetable(st.session_state.selected_courses, lang)
        
        # Always show periods 1-12
        periods = list(range(1, 13))
        
        # Create timetable DataFrame for display with all 12 periods
        timetable_df = pd.DataFrame(index=periods, columns=list(day_names.values()))
        
        for day_key, day_name in day_names.items():
            for period in periods:
                courses_in_slot = timetable[day_key][period]
                if courses_in_slot:
                    # Format display based on week type
                    course_texts = []
                    for c in courses_in_slot:
                        if c['week'] == 'odd':
                            course_texts.append(f"{c['course']} [单]")
                        elif c['week'] == 'even':
                            course_texts.append(f"{c['course']} [双]")
                        else:
                            course_texts.append(c['course'])
                    timetable_df.loc[period, day_name] = '\n'.join(course_texts)
                else:
                    timetable_df.loc[period, day_name] = ""
        
        # Set height for 12 rows
        timetable_height = 480  # 12 rows * 40px per row
        st.dataframe(timetable_df, height=timetable_height, width='stretch')
        
        # Export timetable button - Fixed to work with one click
        excel_data = export_timetable_to_excel(st.session_state.selected_courses, lang)
        if excel_data:
            st.download_button(
                label=lang["export_timetable"],
                data=excel_data,
                file_name="课程表.xlsx" if language == "zh" else "timetable.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        # Display credit counter immediately after timetable
        st.subheader(f"{lang['current_credits']}: {current_credits} / {lang['max_credits']}: {max_credits}")
        if current_credits > max_credits:
            st.error(f"⚠️ {lang['warning']}: {lang['credit_exceeded']}")
        
        # Option to clear selections
        if st.button("Clear Selections" if language == "en" else "清空选课"):
            st.session_state.selected_courses = []
            st.rerun()
    else:
        # Show empty timetable with all 12 periods when no courses are selected
        day_names = {
            'mon': lang["week_mon"], 'tue': lang["week_tue"], 'wed': lang["week_wed"],
            'thu': lang["week_thu"], 'fri': lang["week_fri"], 'sat': lang["week_sat"], 
            'sun': lang["week_sun"]
        }
        
        periods = list(range(1, 13))
        empty_timetable_df = pd.DataFrame(index=periods, columns=list(day_names.values()))
        for day_name in day_names.values():
            empty_timetable_df[day_name] = ""
        
        timetable_height = 480  # 12 rows * 40px per row
        st.dataframe(empty_timetable_df, height=timetable_height, width='stretch')
        st.info("No courses selected yet." if language == "en" else "尚未选择任何课程。")
        
        # Display credit counter immediately after timetable even when empty
        st.subheader(f"{lang['current_credits']}: {current_credits} / {lang['max_credits']}: {max_credits}")
        if current_credits > max_credits:
            st.error(f"⚠️ {lang['warning']}: {lang['credit_exceeded']}")
    
    # Display selected courses table after timetable and credit counter
    if st.session_state.selected_courses:
        st.subheader(lang["selected_courses"])
        
        # Create a container for each selected course with cancel button
        for idx, course in enumerate(st.session_state.selected_courses):
            with st.container():
                col1, col2, col3, col4, col5, col6, col7 = st.columns([1, 2, 1, 1, 1, 2, 1])
                
                col1.write(course['院系'])
                col2.write(course['课程名'])
                col3.write(course['班号'])
                col4.write(str(course['参考学分']))
                col5.write(course['授课教师'])
                col6.write(course['上课时间'])
                
                button_key = f"cancel_{idx}"
                if col7.button(lang["cancel"], key=button_key, use_container_width=True):
                    # Remove course from selected courses
                    st.session_state.selected_courses.pop(idx)
                    st.rerun()
                
                # Add a separator line
                st.divider()

if __name__ == "__main__":
    main()
