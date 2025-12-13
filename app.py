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
        "app_title": "Mock Course Selection Application",
        "department": "Department",
        "course_name": "Course Name",
        "class_id": "Class ID",
        "credits": "Credits",
        "instructor": "Instructor",
        "time": "Time",
        "select": "Select",
        "cancel": "Cancel",
        "user_department": "User Department",
        "second_department": "Second Department",
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
        "app_title": "模拟选课系统",
        "department": "院系",
        "course_name": "课程名",
        "class_id": "班号",
        "credits": "学分",
        "instructor": "授课教师",
        "time": "上课时间",
        "select": "选课",
        "cancel": "取消",
        "user_department": "用户所在院系",
        "second_department": "第二学位院系",
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
        "page": "页码",
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

@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_data():
    """Load course data from Parquet/Excel file with caching"""
    # Try Parquet first (10x faster)
    try:
        df = pd.read_parquet("courses.parquet")
        return df
    except FileNotFoundError:
        pass
    
    # Fallback to Excel
    try:
        df = pd.read_excel("courses.xlsx")
    except FileNotFoundError:
        try:
            df = pd.read_excel("课表信息汇总.xlsx")
        except FileNotFoundError:
            return None
    
    # Process the data according to requirements
    # Merge rows with same Course ID + Class ID
    grouped = df.groupby(['课程号', '班号'], as_index=False)
    
    processed_data = []
    for _, group in grouped:
        row = group.iloc[0].copy()
        
        # Concatenate Target Audience (修读对象)
        if len(group) > 1:
            row['修读对象'] = '，'.join(group['修读对象'].astype(str).unique())
        
        processed_data.append(row)
    
    processed_df = pd.DataFrame(processed_data)
    
    # Auto-save as Parquet for next time
    try:
        processed_df.to_parquet("courses.parquet", compression='snappy', index=False)
    except Exception:
        pass  # Silently fail if can't save
    
    return processed_df

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

@st.cache_data
def preprocess_course_times(df):
    """预处理所有课程的时间信息，避免重复解析"""
    if df is None or df.empty:
        return df
    
    # 为DataFrame添加解析后的时间列
    df_copy = df.copy()
    df_copy['_parsed_time'] = df_copy['上课时间'].apply(lambda x: parse_time(x) if pd.notna(x) else [])
    return df_copy

@st.cache_data
def parse_time(time_str):
    """
    Parse time string into structured data (cached version)
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
    Optimized with early exit strategy
    """
    new_time_slots = parse_time(new_course_time)
    
    # Early exit if no time slots
    if not new_time_slots:
        return None
    
    for course in selected_courses:
        existing_time_slots = parse_time(course['上课时间'])
        
        # Early exit if no existing time slots
        if not existing_time_slots:
            continue
        
        for new_slot in new_time_slots:
            for existing_slot in existing_time_slots:
                # Check if same day (early exit if not)
                if new_slot['day'] != existing_slot['day']:
                    continue
                
                # Check if periods overlap (early exit if not)
                if not (new_slot['start_period'] <= existing_slot['end_period'] and 
                        new_slot['end_period'] >= existing_slot['start_period']):
                    continue
                
                # Check if weeks overlap
                # No conflict if one is odd and the other is even
                if (new_slot['week_type'] == 'odd' and existing_slot['week_type'] == 'even') or \
                   (new_slot['week_type'] == 'even' and existing_slot['week_type'] == 'odd'):
                    continue
                
                # Conflict detected - return immediately
                return course['课程名']
    
    return None  # No conflict

def create_timetable(selected_courses, lang):
    """Create timetable visualization (optimized with cached time parsing)"""
    # Initialize timetable matrix (7 days x 12 periods) - Mon-Sun as requested
    days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
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
        # Use cached parsed time if available
        if isinstance(course, dict) and '_parsed_time' in course:
            time_slots = course['_parsed_time']
        else:
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
    st.set_page_config(page_title="模拟选课", layout="wide")
    
    # Custom CSS to reduce row height and spacing for a more compact view
    st.markdown("""
        <style>
        /* Commented out to fix inconsistent button sizes */
        /*
        div.stButton > button {
            min-height: 30px !important;
            height: 30px !important;
            padding-top: 2px !important;
            padding-bottom: 2px !important;
            font-size: 14px !important;
        }
        */
        
        /* Target BOTH standard buttons and download buttons to ensure equal sizing */
        div.stButton > button, div.stDownloadButton > button {
            padding-top: 0.4rem !important;
            padding-bottom: 0.4rem !important;
            padding-left: 0.6rem !important;
            padding-right: 0.6rem !important;
            min-height: auto !important;
            height: auto !important;
            line-height: 1.2 !important;
            margin-top: 0px !important; /* Reset to 0 */
            margin-bottom: 0px !important; /* Reset to 0 */
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
        }
        
        /* Make text input fields compact to match button height */
        div[data-baseweb="input"] > div, div[data-baseweb="input"] input {
            min-height: 30px !important;
            height: 30px !important;
            padding: 0px 8px !important;
            font-size: 14px !important;
        }
        
        /* Reduce padding in markdown text elements */
        div[data-testid="stMarkdownContainer"] p {
            margin-bottom: 0px !important;
        }
        
        /* Reduce margin around horizontal rules (dividers) */
        hr {
            margin-top: 0.25rem !important;
            margin-bottom: 0.25rem !important;
        }
        
        /* Reduce padding inside columns */
        div[data-testid="column"] {
            padding-top: 0rem !important;
            padding-bottom: 0rem !important;
        }
        
        /* Fine-tune text vertical alignment in columns */
        div[data-testid="column"] {
            display: flex !important;
            flex-direction: column !important;
            justify-content: center !important;
        }
        
        /* CRITICAL: Remove bottom margin from text inside columns */
        /* This ensures the text's visual center matches the row's center */
        div[data-testid="column"] p {
            margin-bottom: 0px !important;
            line-height: 1.5 !important; /* Standardize line height */
            padding-top: 2px !important; /* Micro-adjustment for visual weight */
        }
        
        /* Ensure timetable takes full height and shows all rows */
        div[data-testid="stDataFrame"] {
            height: auto !important;
        }
        
        /* Style for timetable cells to ensure proper display */
        td {
            padding: 2px 4px !important;
            font-size: 13px !important;
        }
        
        th {
            padding: 4px !important;
            font-size: 13px !important;
        }
        
        /* Force toast to auto-expand for long text */
        div[data-baseweb="toast"] {
            height: auto !important;
            min-height: 60px !important;
            white-space: pre-wrap !important; /* Allow text wrapping */
            word-break: break-word !important;
            width: auto !important;
            max-width: 40vw !important; /* Make it wider if needed */
        }
        div[data-baseweb="toast"] > div {
            height: auto !important;
        }

        /* Adjust blue info box height */
        .info-box {
            padding: 10px !important;
            line-height: 1.5 !important;
        }
        
        /* Fix Toast Notification Truncation */
        div[data-baseweb="toast"] {
            width: auto !important;
            min-height: auto !important;
            height: auto !important;
            max-width: 80vw !important;
        }
        
        /* Target the inner text body of the toast */
        div[data-baseweb="toast"] div {
            white-space: pre-wrap !important;
            word-wrap: break-word !important;
            line-height: 1.5 !important;
            height: auto !important;
        }
        
        /* Ensure the close button doesn't overlap text */
        div[data-baseweb="toast"] > div:last-child {
            align-items: flex-start !important;
            padding-top: 8px !important;
        }

        /* Adjust blue info box height */
        .info-box {
            padding: 10px !important;
            line-height: 1.5 !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Initialize page state at the very beginning
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 1
    
    # Language selection - Changed default to Chinese
    language = st.sidebar.selectbox(
        "Language / 语言",
        options=["zh", "en"],  # Changed order to make Chinese the default
        format_func=lambda x: "中文" if x == "zh" else "English"
    )
    lang = LANGUAGES[language]
    
    st.title(lang["app_title"])
    
    # Add cache clear button in sidebar
    with st.sidebar:
        if st.button("🔄 " + ("清除缓存" if language == "zh" else "Clear Cache")):
            st.cache_data.clear()
            st.session_state.current_page = 1 # Reset page on cache clear
            st.success("✓ " + ("缓存已清除" if language == "zh" else "Cache cleared"))
            st.rerun()
    
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
    
    # Preprocess time data once (cached)
    df = preprocess_course_times(df)
    
    # Initialize session state for courses
    if 'selected_courses' not in st.session_state:
        st.session_state.selected_courses = []
    
    if 'user_department' not in st.session_state:
        st.session_state.user_department = ""
    
    if 'degree_type' not in st.session_state:
        st.session_state.degree_type = "single"  # single or double
    
    # Cache for timetable
    if 'timetable_cache' not in st.session_state:
        st.session_state.timetable_cache = None
    if 'timetable_courses_hash' not in st.session_state:
        st.session_state.timetable_courses_hash = None
    
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
    
    # Second department selection for double degree students
    second_dept = None
    if degree_type == "double":
        # Filter out the user's primary department from the options
        second_dept_options = [dept for dept in departments if dept != user_dept]
        second_dept = st.sidebar.selectbox(
            lang["second_department"],
            options=second_dept_options,
            key="second_dept_select"
        )
    
    max_credits = 25 if degree_type == "single" else 30
    
    # Calculate current credits
    current_credits = sum(float(course.get('参考学分', 0)) for course in st.session_state.selected_courses)
    
    # Filter courses based on user department and target audience
    # For double degree students, also include courses from their second department
    if degree_type == "double" and second_dept:
        mask = (df['院系'] == user_dept) | (df['院系'] == second_dept) | df['修读对象'].fillna('').str.contains('全校学生在籍', na=False)
    else:
        mask = (df['院系'] == user_dept) | df['修读对象'].fillna('').str.contains('全校学生在籍', na=False)
    filtered_df = df[mask].copy()
    
    # Additional filters
    st.sidebar.header("Filters")
    
    # Department filter
    all_depts = [lang["all_departments"]] + sorted(filtered_df['院系'].unique())
    
    # Reset page when filters change
    def reset_page_callback():
        st.session_state.current_page = 1
        
    dept_filter = st.sidebar.selectbox(
        lang["filter_by_department"],
        options=all_depts,
        on_change=reset_page_callback
    )
    
    if dept_filter != lang["all_departments"]:
        filtered_df = filtered_df[filtered_df['院系'] == dept_filter]
    
    # Course name search (Moved to main page)
    course_search = st.text_input(lang["search_course"], on_change=reset_page_callback)
    if course_search:
        filtered_df = filtered_df[filtered_df['课程名'].str.contains(course_search, case=False, na=False, regex=False)]

 # --- Pagination Logic ---
    courses_per_page = 10
    total_courses = len(filtered_df)
    total_pages = (total_courses - 1) // courses_per_page + 1 if total_courses > 0 else 1
    
    # Ensure current page is valid
    if st.session_state.current_page > total_pages:
        st.session_state.current_page = total_pages
    if st.session_state.current_page < 1:
        st.session_state.current_page = 1
    # Initialize page input state if not present
    if "page_input" not in st.session_state:
        st.session_state.page_input = str(st.session_state.current_page)
    
    # --- Pagination UI ---
    if total_pages > 1:
        # update page input
        def prev_page_callback():
            st.session_state.current_page -= 1
            st.session_state.page_input = str(st.session_state.current_page)
        
        def next_page_callback():
            st.session_state.current_page += 1
            st.session_state.page_input = str(st.session_state.current_page)
            
        def set_page_callback():
            try:
                val = int(st.session_state.page_input)
                if 1 <= val <= total_pages:
                    st.session_state.current_page = val
                else:
                    st.session_state.page_input = str(st.session_state.current_page)
            except ValueError:
                st.session_state.page_input = str(st.session_state.current_page)
        
        # Create 5 columns: Spacer, Prev, Display, Next, Spacer
        # vertical_alignment="center" is a safeguard, but the button trick does the heavy lifting
        c1, c2, c3, c4, c5 = st.columns([6, 1, 2, 1, 6], vertical_alignment="center")
        
        with c2:
            # Previous Button
            st.button("←", on_click=prev_page_callback, disabled=(st.session_state.current_page <= 1), key="prev_top", use_container_width=True)

        with c3:
            # The "Display" Button (Disabled, acting as a label)
            # It sits perfectly flush with the arrow buttons
            st.button(f"{st.session_state.current_page} / {total_pages}", disabled=True, key="page_display_top", use_container_width=True)

        with c4:
            # Next Button
            st.button("→", on_click=next_page_callback, disabled=(st.session_state.current_page >= total_pages), key="next_top", use_container_width=True)
        
        st.write("")
    
    start_idx = (st.session_state.current_page - 1) * courses_per_page
    end_idx = start_idx + courses_per_page
    page_courses = filtered_df.iloc[start_idx:end_idx]
    
    # Display courses table
    if not page_courses.empty:
        # Display each course as a card
        for idx, (_, row) in enumerate(page_courses.iterrows()):
            # Create a bordered container for each course item
            with st.container(border=True):
                # Split into two main sections: Information (Left) and Action (Right)
                # Ratio 4:1 ensures the button has its own dedicated space
                c_info, c_action = st.columns([4, 1], vertical_alignment="center")
                
                with c_info:
                    # Top Row: Course Name (Bold/Large) and ID
                    st.markdown(f"**{row['课程名']}** <span style='color:grey; font-size:0.9em'>({row['课程号']})</span>", unsafe_allow_html=True)
                    
                    # Bottom Row: Meta data (Dept, Credit, Teacher, Time) using distinct styling or captions
                    # Using a single line with separators looks clean
                    meta_text = f"教师：{row['授课教师']} &nbsp;|&nbsp; 院系：{row['院系']} &nbsp;|&nbsp; 学分：{row['参考学分']} &nbsp;|&nbsp; 时间：{row['上课时间']}"
                    st.caption(meta_text)
                    
                with c_action:
                    # The button lives here, vertically centered by the column setting
                    # use_container_width=True makes it fill the right side neatly
                    if st.button(lang["select"], key=f"sel_{idx}_{row['课程号']}", use_container_width=True):
                        conflict_course = check_conflict(row['上课时间'], st.session_state.selected_courses)
                        
                        if conflict_course:
                            st.toast(f"❌ {lang['conflict_detected']} {conflict_course}", icon='⚠️')
                        else:
                            course_dict = row.to_dict()
                            if '_parsed_time' in row:
                                course_dict['_parsed_time'] = row['_parsed_time']
                            st.session_state.selected_courses.append(course_dict)
                            st.toast(f"✅ {lang['no_conflict']}", icon='🎉')
                            st.rerun()
    else:
        # Custom styled message for no matching courses
        message_text = "No matching courses found" if language == "en" else "无符合条件的课程"
        st.markdown(f'''
        <div style="
            background-color: rgba(28, 131, 225, 0.1);
            color: rgb(0, 66, 128);
            padding: 20px;
            border-radius: 0.5rem;
            border: 1px solid rgba(28, 131, 225, 0.1);
            text-align: center;
            margin-top: 10px;
            margin-bottom: 10px;">
            {message_text}
        </div>
        ''', unsafe_allow_html=True)
    
    # Define a helper to generate the HTML timetable
    def get_timetable_html(timetable, day_names):
        html = """
        <style>
            .tt-table { width: 100%; border-collapse: collapse; font-family: sans-serif; }
            .tt-header { background-color: #262730; color: white; padding: 12px; text-align: center; font-weight: bold; width: 12.5%; border: 1px solid #444; }
            .tt-cell { border: 1px solid #ddd; padding: 5px; height: 65px; vertical-align: top; width: 12.5%; }
            .tt-period { background-color: #f0f2f6; font-weight: bold; text-align: center; vertical-align: middle; width: 5%; color: #31333F; }
            
            /* Style for a course block inside the cell */
            .course-block {
                background-color: #e8f0fe; 
                color: #1967d2;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 0.85em;
                margin-bottom: 4px;
                border-left: 3px solid #1967d2;
                box-shadow: 0 1px 2px rgba(0,0,0,0.1);
            }
        </style>
        <table class="tt-table">
            <thead>
                <tr>
                    <th class="tt-header">#</th>
        """
        # Add Headers
        for day_code in day_names:
            html += f'<th class="tt-header">{day_names[day_code]}</th>'
        html += "</tr></thead><tbody>"

        # Add Rows (Periods 1-12)
        for period in range(1, 13):
            html += f'<tr><td class="tt-cell tt-period">{period}</td>'
            for day_code in day_names:
                courses = timetable[day_code][period]
                cell_content = ""
                if courses:
                    for c in courses:
                        # Format course info
                        info = c['course']
                        if c['week'] == 'odd': info += " (单)"
                        elif c['week'] == 'even': info += " (双)"
                        
                        cell_content += f'<div class="course-block">{info}</div>'
                
                html += f'<td class="tt-cell">{cell_content}</td>'
            html += "</tr>"
        
        html += "</tbody></table>"
        return html

    # Display timetable before selected courses table
    st.subheader(lang["timetable"])
    
    # Create and display timetable
    if st.session_state.selected_courses:
        # Check if we can use cached timetable
        courses_hash = hash(str([(c['课程号'], c['班号']) for c in st.session_state.selected_courses]))
        
        if (st.session_state.timetable_courses_hash == courses_hash and 
            st.session_state.timetable_cache is not None):
            # Use cached timetable
            timetable, day_names = st.session_state.timetable_cache
        else:
            # Generate new timetable and cache it
            timetable, day_names = create_timetable(st.session_state.selected_courses, lang)
            st.session_state.timetable_cache = (timetable, day_names)
            st.session_state.timetable_courses_hash = courses_hash
        
        # 1. Create the DataFrame for the view
        # (Assuming you already have 'timetable' dict from previous logic)
        timetable_data_for_df = {}
        days_list = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
        
        for day in days_list:
            day_col = []
            for period in range(1, 13):
                # Extract course info string
                courses = timetable[day][period]
                if courses:
                    # Combine multiple courses with newlines
                    text_parts = []
                    for c in courses:
                        info = c['course']
                        if c['week'] == 'odd': info += " (单)"
                        elif c['week'] == 'even': info += " (双)"
                        text_parts.append(info)
                    day_col.append("\n".join(text_parts))
                else:
                    day_col.append("")
            
            # Add to dict with translated header
            timetable_data_for_df[lang['week_' + day]] = day_col

        # Create DF with 1-12 index
        df_tt = pd.DataFrame(timetable_data_for_df, index=range(1, 13))

        # Define the styling function (Blue background for courses)
        def color_courses(val):
            if val and str(val).strip() != "":
                return 'background-color: rgba(28, 131, 225, 0.2); border-radius: 4px; font-weight: bold; color: inherit;'
            return ''

        # Get translated day names for styling subset
        translated_days_list = [lang['week_' + day] for day in days_list]

        # Apply Styler with FIXED Layout Logic
        styled_df = df_tt.style.map(color_courses) \
            .set_properties(**{
                'height': '65px',              # Fixed row height
                'vertical-align': 'middle',    # Center vertically
                'text-align': 'center',        # Center horizontally
                'white-space': 'pre-wrap',     # Wrap text inside the fixed width
                'border': '1px solid #444' if language == 'zh' else '1px solid #ddd'
            }) \
            .set_table_styles([
                # 1. CRITICAL: Force the table to stop shrinking based on content
                {'selector': 'table', 'props': [
                    ('width', '100%'),          # Fill container
                    ('table-layout', 'fixed'),  # Ignore content length
                    ('border-collapse', 'collapse'),
                    ('margin', '0'),            # Remove margins
                    ('padding', '0')            # Remove padding
                ]},
                # 2. Header Styling
                {'selector': 'th', 'props': [
                    ('background-color', '#262730'),
                    ('color', 'white'),
                    ('text-align', 'center'),
                    ('vertical-align', 'middle')
                ]},
                # 3. Cell styling
                {'selector': 'td, th', 'props': [
                    ('box-sizing', 'border-box')  # Include padding and border in width calculation
                ]}
            ]) \
            .set_properties(
                subset=translated_days_list,  # <--- ONLY apply width to Mon-Sun (using translated names)
                **{'width': '13.5%'} # 13.5% * 7 = 94.5%, leaving 5.5% for the index
            )

        # 4. Render with container that ensures full width
        # to_html() generates the HTML, st.markdown renders it
        st.markdown(f"""
<style>
    .timetable-wrapper table {{
        width: 100% !important;
        table-layout: fixed !important;
        border-collapse: collapse !important;
    }}
    /* First Column: Narrow (Index) */
    .timetable-wrapper th:first-child,
    .timetable-wrapper td:first-child {{
        width: 6% !important;
    }}
    /* Other Columns: Evenly distributed */
    .timetable-wrapper th:not(:first-child),
    .timetable-wrapper td:not(:first-child) {{
        width: 13.4% !important;
    }}
    .timetable-wrapper td, .timetable-wrapper th {{
        text-align: center !important;
        vertical-align: middle !important;
    }}
</style>
<div class="timetable-wrapper">
    {styled_df.to_html()}
</div>
""", unsafe_allow_html=True)
        
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
            # Replacing st.error with custom styled markdown div
            st.markdown(
                f"""
                <div style="
                    background-color: rgba(255, 75, 75, 0.1);
                    color: rgb(163, 6, 6);
                    padding: 20px;
                    border-radius: 0.5rem;
                    border: 1px solid rgba(255, 75, 75, 0.2);
                    text-align: center;
                    margin-top: 10px;
                    margin-bottom: 10px;">
                    ⚠️ {lang['warning']}: {lang['credit_exceeded']}
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        # Show empty timetable with all 12 periods when no courses are selected
        day_names = {
            'mon': lang["week_mon"], 'tue': lang["week_tue"], 'wed': lang["week_wed"],
            'thu': lang["week_thu"], 'fri': lang["week_fri"], 'sat': lang["week_sat"], 
            'sun': lang["week_sun"]
        }
        
        # 1. Create the DataFrame for the view (empty)
        timetable_data_for_df = {}
        days_list = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
        
        for day in days_list:
            # Add to dict with translated header
            timetable_data_for_df[lang['week_' + day]] = [""] * 12

        # Create DF with 1-12 index
        df_tt = pd.DataFrame(timetable_data_for_df, index=range(1, 13))

        # Define the styling function (Blue background for courses)
        def color_courses(val):
            if val and str(val).strip() != "":
                return 'background-color: rgba(28, 131, 225, 0.2); border-radius: 4px; font-weight: bold; color: inherit;'
            return ''

        # Get translated day names for styling subset
        translated_days_list = [lang['week_' + day] for day in days_list]

        # Apply Styler with FIXED Layout Logic - Reuse the same logic as non-empty case
        # The styling logic is identical, only the data source (df_tt) is different
        styled_df = df_tt.style.map(color_courses) \
            .set_properties(**{
                'height': '65px',              # Fixed row height
                'vertical-align': 'middle',    # Center vertically
                'text-align': 'center',        # Center horizontally
                'white-space': 'pre-wrap',     # Wrap text inside the fixed width
                'border': '1px solid #444' if language == 'zh' else '1px solid #ddd'
            }) \
            .set_table_styles([
                # 1. CRITICAL: Force the table to stop shrinking based on content
                {'selector': 'table', 'props': [
                    ('width', '100%'),          # Fill container
                    ('table-layout', 'fixed'),  # Ignore content length
                    ('border-collapse', 'collapse')
                ]},
                # 2. Header Styling
                {'selector': 'th', 'props': [
                    ('background-color', '#262730'),
                    ('color', 'white'),
                    ('text-align', 'center'),
                    ('vertical-align', 'middle')
                ]}
            ]) \
            .set_properties(
                subset=translated_days_list,  # <--- ONLY apply width to Mon-Sun (using translated names)
                **{'width': '13.5%'} # 13.5% * 7 = 94.5%, leaving 5.5% for the index
            )

        # 4. Render with container that ensures full width
        # to_html() generates the HTML, st.markdown renders it
        st.markdown(f"""
<style>
    .timetable-wrapper table {{
        width: 100% !important;
        table-layout: fixed !important;
        border-collapse: collapse !important;
    }}
    /* First Column: Narrow (Index) */
    .timetable-wrapper th:first-child,
    .timetable-wrapper td:first-child {{
        width: 6% !important;
    }}
    /* Other Columns: Evenly distributed */
    .timetable-wrapper th:not(:first-child),
    .timetable-wrapper td:not(:first-child) {{
        width: 13.4% !important;
    }}
    .timetable-wrapper td, .timetable-wrapper th {{
        text-align: center !important;
        vertical-align: middle !important;
    }}
</style>
<div class="timetable-wrapper">
    {styled_df.to_html()}
</div>
""", unsafe_allow_html=True)
        
        # Replacing st.info with custom styled markdown div
        message_text = "No courses selected yet." if language == "en" else "尚未选择任何课程。"
        st.markdown(f'''
        <div style="
            background-color: rgba(28, 131, 225, 0.1);
            color: rgb(0, 66, 128);
            padding: 20px;
            border-radius: 0.5rem;
            border: 1px solid rgba(28, 131, 225, 0.1);
            text-align: center;
            margin-top: 10px;
            margin-bottom: 10px;">
            {message_text}
        </div>
        ''', unsafe_allow_html=True)
        
        # Display credit counter immediately after timetable even when empty
        st.subheader(f"{lang['current_credits']}: {current_credits} / {lang['max_credits']}: {max_credits}")
        if current_credits > max_credits:
            # Replacing st.error with custom styled markdown div (consistent with the first warning)
            st.markdown(
                f"""
                <div style="
                    background-color: rgba(255, 75, 75, 0.1);
                    color: rgb(163, 6, 6);
                    padding: 20px;
                    border-radius: 0.5rem;
                    border: 1px solid rgba(255, 75, 75, 0.2);
                    text-align: center;
                    margin-top: 10px;
                    margin-bottom: 10px;">
                    ⚠️ {lang['warning']}: {lang['credit_exceeded']}
                </div>
                """,
                unsafe_allow_html=True
            )
    
    # Display selected courses table after timetable and credit counter
    if st.session_state.selected_courses:
        st.subheader(lang["selected_courses"])
        
        # Display each selected course as a card with cancel option
        for idx, course in enumerate(st.session_state.selected_courses):
            # Create a bordered container for each selected course item
            with st.container(border=True):
                # Split into two main sections: Information (Left) and Action (Right)
                # Ratio 4:1 ensures the button has its own dedicated space
                c_info, c_action = st.columns([4, 1], vertical_alignment="center")
                
                with c_info:
                    # Top Row: Course Name (Bold/Large) and ID
                    st.markdown(f"**{course['课程名']}** <span style='color:grey; font-size:0.9em'>({course['课程号']})</span>", unsafe_allow_html=True)
                    
                    # Bottom Row: Meta data (Dept, Credit, Teacher, Time) using distinct styling or captions
                    # Using a single line with separators looks clean
                    meta_text = f"教师：{course['授课教师']} &nbsp;|&nbsp; 院系：{course['院系']} &nbsp;|&nbsp; 学分：{course['参考学分']} &nbsp;|&nbsp; 时间：{course['上课时间']}"
                    st.caption(meta_text)
                    
                with c_action:
                    # The cancel button lives here, vertically centered by the column setting
                    # use_container_width=True makes it fill the right side neatly
                    # type="primary" distinguishes it from the select button
                    if st.button(lang["cancel"], key=f"cancel_{idx}_{course['课程号']}", use_container_width=True, type="primary"):
                        # Remove course from selected courses
                        st.session_state.selected_courses.pop(idx)
                        st.rerun()

if __name__ == "__main__":
    main()