using UnityEngine;
using UnityEditor;
using System;
using System.Collections.Generic;
using System.IO;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;

public class AIDailyReport : EditorWindow
{
    // 任务管理相关
    private List<TaskItem> tasks = new List<TaskItem>();
    private string newTaskContent = "";
    private DateTime newTaskDate = DateTime.Now;
    private TaskItem selectedTask;

    // 日期选择相关
    private string newTaskDateString = "";

    // 界面状态
    private bool showAllTasks = false;

    // AI相关
    private HttpClient httpClient;
    private string apiKey = "sk-b4468b3ac8354ede9b0e12ee67a528a3";
    private string apiUrl = "https://api.deepseek.com/v1/chat/completions";

    // 数据保存相关
    private string taskDataPath;
    private string prefabDataPath;

    // UI相关
    private Vector2 scrollPosition;
    private Vector2 taskScrollPosition;
    private Vector2 allTasksScrollPosition;

    private void OnEnable()
    {
        httpClient = new HttpClient();
        httpClient.DefaultRequestHeaders.Add("Authorization", $"Bearer {apiKey}");

        // 初始化数据保存路径
        string recordsDir = Path.Combine(Application.dataPath, "WorkRecords");
        taskDataPath = Path.Combine(recordsDir, "task_data.json");
        prefabDataPath = Path.Combine(recordsDir, "prefab_data.json");

        // 初始化日期字符串
        newTaskDateString = newTaskDate.ToString("yyyy-MM-dd");

        // 加载保存的数据
        LoadTaskData();
    }

    private void OnDisable()
    {
        httpClient?.Dispose();
    }

    private void OnGUI()
    {
        scrollPosition = EditorGUILayout.BeginScrollView(scrollPosition);

        DrawTaskManagementSection();
        DrawWorkLogSection();

        EditorGUILayout.EndScrollView();
    }

    public void CallOnGUI()
    {
        var originalScrollPosition = scrollPosition;
        OnGUI();
        scrollPosition = originalScrollPosition;
    }

    private void DrawTaskManagementSection()
    {
        EditorGUILayout.LabelField("任务管理", EditorStyles.boldLabel);

        // 添加新任务
        EditorGUILayout.BeginVertical("box");
        EditorGUILayout.LabelField("添加新任务", EditorStyles.miniBoldLabel);

        newTaskContent = EditorGUILayout.TextField("任务内容", newTaskContent);

        // 日期选择
        EditorGUILayout.BeginHorizontal();
        EditorGUILayout.LabelField("任务日期", GUILayout.Width(80));
        newTaskDateString = EditorGUILayout.TextField(newTaskDateString, GUILayout.Width(100));

        if (GUILayout.Button("今天", GUILayout.Width(40)))
        {
            newTaskDate = DateTime.Now;
            newTaskDateString = newTaskDate.ToString("yyyy-MM-dd");
        }

        if (GUILayout.Button("明天", GUILayout.Width(40)))
        {
            newTaskDate = DateTime.Now.AddDays(1);
            newTaskDateString = newTaskDate.ToString("yyyy-MM-dd");
        }
        EditorGUILayout.EndHorizontal();

        // 日期格式提示
        EditorGUILayout.LabelField("格式: yyyy-MM-dd (例如: " + DateTime.Now.ToString("yyyy-MM-dd") + ")", EditorStyles.miniLabel);

        EditorGUILayout.BeginHorizontal();
        if (GUILayout.Button(selectedTask != null ? "更新任务" : "添加任务"))
        {
            AddNewTask();
        }

        if (GUILayout.Button("清除"))
        {
            newTaskContent = "";
            newTaskDate = DateTime.Now;
            newTaskDateString = newTaskDate.ToString("yyyy-MM-dd");
            selectedTask = null;
        }
        EditorGUILayout.EndHorizontal();

        if (selectedTask != null)
        {
            EditorGUILayout.HelpBox("正在编辑任务: " + selectedTask.content, MessageType.Info);
        }
        EditorGUILayout.EndVertical();

        EditorGUILayout.Space();

        // 任务列表 - 只显示今天和明天的任务
        DrawTodayTasks();
        EditorGUILayout.Space();
        DrawTomorrowTasks();

        EditorGUILayout.Space();

        // 管理所有任务按钮
        EditorGUILayout.BeginHorizontal();
        if (GUILayout.Button("管理所有任务", GUILayout.Width(120)))
        {
            showAllTasks = !showAllTasks;
        }

        if (GUILayout.Button("手动保存任务", GUILayout.Width(120)))
        {
            SaveTaskData();
            EditorUtility.DisplayDialog("成功", "任务数据已保存", "确定");
        }
        EditorGUILayout.EndHorizontal();

        // 所有任务管理界面
        if (showAllTasks)
        {
            DrawAllTasksManagement();
        }
    }

    private void DrawTodayTasks()
    {
        string today = DateTime.Today.ToString("yyyy-MM-dd");
        List<TaskItem> todayTasks = tasks.FindAll(task => task.date == today);

        EditorGUILayout.BeginVertical("box");
        EditorGUILayout.LabelField($"今日任务 ({todayTasks.Count})", EditorStyles.miniBoldLabel);

        if (todayTasks.Count == 0)
        {
            EditorGUILayout.HelpBox("今日无任务", MessageType.Info);
        }
        else
        {
            foreach (var task in todayTasks)
            {
                DrawTaskItem(task);
            }
        }
        EditorGUILayout.EndVertical();
    }

    private void DrawTomorrowTasks()
    {
        string tomorrow = DateTime.Today.AddDays(1).ToString("yyyy-MM-dd");
        List<TaskItem> tomorrowTasks = tasks.FindAll(task => task.date == tomorrow);

        EditorGUILayout.BeginVertical("box");
        EditorGUILayout.LabelField($"明日任务 ({tomorrowTasks.Count})", EditorStyles.miniBoldLabel);

        if (tomorrowTasks.Count == 0)
        {
            EditorGUILayout.HelpBox("明日无任务", MessageType.Info);
        }
        else
        {
            foreach (var task in tomorrowTasks)
            {
                DrawTaskItem(task);
            }
        }
        EditorGUILayout.EndVertical();
    }

    private void DrawTaskItem(TaskItem task)
    {
        EditorGUILayout.BeginVertical("box");
        EditorGUILayout.BeginHorizontal();

        // 任务状态
        bool newCompleted = EditorGUILayout.Toggle(task.isCompleted, GUILayout.Width(20));
        if (newCompleted != task.isCompleted)
        {
            task.isCompleted = newCompleted;
            task.completionDate = newCompleted ? DateTime.Now.ToString("yyyy-MM-dd") : "";
            SaveTaskData();
        }

        // 任务内容
        EditorGUILayout.BeginVertical(GUILayout.ExpandWidth(true));

        // 任务内容显示
        string taskContent = task.content;
        EditorGUILayout.LabelField(taskContent, EditorStyles.wordWrappedLabel);

        // 任务详情
        EditorGUILayout.BeginHorizontal();

        // 状态显示
        if (task.isCompleted)
        {
            EditorGUILayout.LabelField($"✓ 完成于 {task.completionDate}", EditorStyles.miniLabel, GUILayout.Width(120));
        }
        else
        {
            DateTime taskDate = DateTime.Parse(task.date);
            string statusText = taskDate.Date == DateTime.Today ? "今天到期" : "明天到期";

            GUIStyle statusStyle = new GUIStyle(EditorStyles.miniLabel);
            if (taskDate.Date == DateTime.Today) statusStyle.normal.textColor = Color.yellow;

            EditorGUILayout.LabelField(statusText, statusStyle, GUILayout.Width(80));
        }

        EditorGUILayout.EndHorizontal();
        EditorGUILayout.EndVertical();

        // 操作按钮
        EditorGUILayout.BeginVertical(GUILayout.Width(60));
        if (GUILayout.Button("编辑", GUILayout.Width(50)))
        {
            selectedTask = task;
            newTaskContent = task.content;
            newTaskDate = DateTime.Parse(task.date);
            newTaskDateString = newTaskDate.ToString("yyyy-MM-dd");
        }

        if (GUILayout.Button("删除", GUILayout.Width(50)))
        {
            if (EditorUtility.DisplayDialog("确认", "确定要删除这个任务吗？", "确定", "取消"))
            {
                tasks.Remove(task);
                SaveTaskData();
            }
        }
        EditorGUILayout.EndVertical();

        EditorGUILayout.EndHorizontal();
        EditorGUILayout.EndVertical();
    }

    private void DrawAllTasksManagement()
    {
        EditorGUILayout.Space();
        EditorGUILayout.LabelField("所有任务管理", EditorStyles.boldLabel);

        EditorGUILayout.BeginVertical("box");

        // 统计信息
        int totalTasks = tasks.Count;
        int completedTasks = tasks.FindAll(task => task.isCompleted).Count;
        int pendingTasks = totalTasks - completedTasks;

        EditorGUILayout.LabelField($"总计: {totalTasks} 个任务 | 已完成: {completedTasks} | 待完成: {pendingTasks}", EditorStyles.miniBoldLabel);

        if (tasks.Count == 0)
        {
            EditorGUILayout.HelpBox("暂无任务", MessageType.Info);
        }
        else
        {
            allTasksScrollPosition = EditorGUILayout.BeginScrollView(allTasksScrollPosition, GUILayout.Height(300));

            // 按日期排序
            List<TaskItem> sortedTasks = new List<TaskItem>(tasks);
            sortedTasks.Sort((a, b) =>
            {
                DateTime dateA = DateTime.Parse(a.date);
                DateTime dateB = DateTime.Parse(b.date);
                int dateCompare = dateA.CompareTo(dateB);
                if (dateCompare != 0) return dateCompare;

                // 同一天的任务，未完成的排在前面
                if (a.isCompleted != b.isCompleted)
                    return a.isCompleted ? 1 : -1;

                return string.Compare(a.content, b.content);
            });

            string currentDateGroup = "";
            foreach (var task in sortedTasks)
            {
                // 显示日期分组标题
                if (task.date != currentDateGroup)
                {
                    currentDateGroup = task.date;
                    DateTime taskDate = DateTime.Parse(task.date);
                    string dateDisplay = GetDateDisplayName(taskDate);

                    EditorGUILayout.Space();
                    EditorGUILayout.LabelField(dateDisplay, EditorStyles.boldLabel);

                    // 显示日期操作按钮
                    EditorGUILayout.BeginHorizontal();
                    if (GUILayout.Button("批量删除该日任务", GUILayout.Width(120)))
                    {
                        if (EditorUtility.DisplayDialog("确认", $"确定要删除{dateDisplay}的所有任务吗？", "确定", "取消"))
                        {
                            tasks.RemoveAll(t => t.date == currentDateGroup);
                            SaveTaskData();
                            return; // 退出循环，避免修改集合后继续迭代
                        }
                    }
                    EditorGUILayout.EndHorizontal();
                }

                DrawAllTaskItem(task);
            }

            EditorGUILayout.EndScrollView();
        }

        EditorGUILayout.EndVertical();
    }

    private void DrawAllTaskItem(TaskItem task)
    {
        EditorGUILayout.BeginVertical("box", GUILayout.Height(60));
        EditorGUILayout.BeginHorizontal();

        // 任务状态
        bool newCompleted = EditorGUILayout.Toggle(task.isCompleted, GUILayout.Width(20));
        if (newCompleted != task.isCompleted)
        {
            task.isCompleted = newCompleted;
            task.completionDate = newCompleted ? DateTime.Now.ToString("yyyy-MM-dd") : "";
            SaveTaskData();
        }

        // 任务内容
        EditorGUILayout.BeginVertical(GUILayout.ExpandWidth(true));

        // 完整任务内容
        EditorGUILayout.LabelField(task.content, EditorStyles.wordWrappedLabel);

        // 任务详情
        EditorGUILayout.BeginHorizontal();

        // 创建日期
        EditorGUILayout.LabelField($"创建: {task.creationDate}", EditorStyles.miniLabel, GUILayout.Width(140));

        // 状态显示
        DateTime taskDate = DateTime.Parse(task.date);
        string statusText = task.isCompleted ? $"✓ 完成于 {task.completionDate}" : GetTaskStatusText(taskDate);

        GUIStyle statusStyle = new GUIStyle(EditorStyles.miniLabel);
        if (!task.isCompleted)
        {
            if (taskDate < DateTime.Today)
                statusStyle.normal.textColor = Color.red;
            else if (taskDate == DateTime.Today)
                statusStyle.normal.textColor = Color.yellow;
        }

        EditorGUILayout.LabelField(statusText, statusStyle, GUILayout.Width(120));
        EditorGUILayout.EndHorizontal();
        EditorGUILayout.EndVertical();

        // 操作按钮
        EditorGUILayout.BeginVertical(GUILayout.Width(80));
        if (GUILayout.Button("编辑", GUILayout.Width(70)))
        {
            selectedTask = task;
            newTaskContent = task.content;
            newTaskDate = DateTime.Parse(task.date);
            newTaskDateString = newTaskDate.ToString("yyyy-MM-dd");
            showAllTasks = false; // 关闭所有任务界面，回到主界面编辑
        }

        if (GUILayout.Button("删除", GUILayout.Width(70)))
        {
            if (EditorUtility.DisplayDialog("确认", "确定要删除这个任务吗？", "确定", "取消"))
            {
                tasks.Remove(task);
                SaveTaskData();
            }
        }
        EditorGUILayout.EndVertical();

        EditorGUILayout.EndHorizontal();
        EditorGUILayout.EndVertical();
    }

    private string GetDateDisplayName(DateTime date)
    {
        if (date.Date == DateTime.Today)
            return "今天 (" + date.ToString("yyyy-MM-dd") + ")";
        else if (date.Date == DateTime.Today.AddDays(1))
            return "明天 (" + date.ToString("yyyy-MM-dd") + ")";
        else if (date.Date == DateTime.Today.AddDays(-1))
            return "昨天 (" + date.ToString("yyyy-MM-dd") + ")";
        else
            return date.ToString("yyyy-MM-dd dddd");
    }

    private string GetTaskStatusText(DateTime taskDate)
    {
        TimeSpan timeLeft = taskDate.Date - DateTime.Today;

        if (timeLeft.Days == 0)
            return "今天到期";
        else if (timeLeft.Days == 1)
            return "明天到期";
        else if (timeLeft.Days == -1)
            return "已过期1天";
        else if (timeLeft.Days < 0)
            return $"已过期{Math.Abs(timeLeft.Days)}天";
        else
            return $"{timeLeft.Days}天后到期";
    }

    private void AddNewTask()
    {
        if (string.IsNullOrWhiteSpace(newTaskContent))
        {
            EditorUtility.DisplayDialog("错误", "任务内容不能为空", "确定");
            return;
        }

        // 验证日期格式
        DateTime parsedDate;
        if (!DateTime.TryParse(newTaskDateString, out parsedDate))
        {
            EditorUtility.DisplayDialog("错误", "日期格式不正确，请使用 yyyy-MM-dd 格式", "确定");
            return;
        }

        if (selectedTask != null)
        {
            // 编辑现有任务
            selectedTask.content = newTaskContent;
            selectedTask.date = parsedDate.ToString("yyyy-MM-dd");
            selectedTask = null;
        }
        else
        {
            // 添加新任务
            TaskItem newTask = new TaskItem
            {
                content = newTaskContent,
                date = parsedDate.ToString("yyyy-MM-dd"),
                isCompleted = false,
                creationDate = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss")
            };
            tasks.Add(newTask);
        }

        newTaskContent = "";
        newTaskDate = DateTime.Now;
        newTaskDateString = newTaskDate.ToString("yyyy-MM-dd");
        SaveTaskData();
    }

    private void DrawWorkLogSection()
    {
        EditorGUILayout.Space();
        EditorGUILayout.LabelField("工作日志生成", EditorStyles.boldLabel);

        EditorGUILayout.HelpBox("基于今日处理的预制体和任务信息，自动生成工作日报", MessageType.Info);

        if (GUILayout.Button("生成AI工作日志", GUILayout.Height(30)))
        {
            GenerateWorkLog();
        }
    }

    private async void GenerateWorkLog()
    {
        try
        {
            string todayPrefabsInfo = GetTodayPrefabsInfo();
            string todayTasksInfo = GetTodayTasksInfo();
            string tomorrowTasksInfo = GetTomorrowTasksInfo();

            string prompt = $@"请根据我今日处理的预制体和任务信息，生成一份简洁的工作日报，格式要求如下：

本日工作进度：
首先总结当天完成的任务内容，随后说明今日处理的预制体数量，接着评估任务整体完成情况：若已完成当天任务，则写进度百分比为100%；
若尚未全部完成，则写进度百分比为60%至80%之间的某一具体数值，同时填写ETA，(计算方式为当前任务日期顺延一天），格式是ETA：MM.DD，例如：ETA：06.15。无需其他说明。
整体表述需简洁清晰，总字数控制在150-200字。
请注意：因岗位职责为UI搭建（非功能逻辑实现），请勿描述具体代码实现；同时，也无需提及多分辨率适配等相关测试内容。避免罗列预制体文件名（如""UIMainStageResultView""），确保日志清晰、言之有物。

明日工作计划：
简要说明次日的工作安排，字数请控制在100字到150字之间。

今天处理的预制体信息：
{todayPrefabsInfo}

今天完成的任务：
{todayTasksInfo}

明日计划任务：
{tomorrowTasksInfo}
            ";

            string jsonRequest = $@"{{
    ""model"": ""deepseek-chat"",
    ""messages"": [
        {{
            ""role"": ""user"",
            ""content"": ""{EscapeJsonString(prompt)}""
        }}
    ],
    ""temperature"": 0.3,
    ""max_tokens"": 500
}}";

            UnityEngine.Debug.Log("正在生成AI工作日志...");
            var content = new StringContent(jsonRequest, Encoding.UTF8, "application/json");

            var response = await httpClient.PostAsync(apiUrl, content);
            var responseContent = await response.Content.ReadAsStringAsync();

            if (response.IsSuccessStatusCode)
            {
                var apiResponse = ParseDeepSeekResponse(responseContent);
                if (apiResponse != null && !string.IsNullOrEmpty(apiResponse.content))
                {
                    string workLog = apiResponse.content.Trim();

                    // 复制到剪贴板
                    EditorGUIUtility.systemCopyBuffer = workLog;

                    // 显示完整的工作日志
                    ShowWorkLogDialog(workLog);
                    UnityEngine.Debug.Log($"AI工作日志: {workLog}");
                }
                else
                {
                    throw new Exception("无法解析AI响应");
                }
            }
            else
            {
                throw new Exception($"API调用失败: {response.StatusCode}");
            }
        }
        catch (Exception e)
        {
            UnityEngine.Debug.LogError($"生成工作日志失败: {e.Message}");
            EditorUtility.DisplayDialog("错误", $"生成工作日志失败: {e.Message}", "确定");
        }
    }

    private string GetTodayPrefabsInfo()
    {
        List<string> prefabInfo = new List<string>();

        if (File.Exists(prefabDataPath))
        {
            try
            {
                string json = File.ReadAllText(prefabDataPath);
                PrefabDataWrapper wrapper = JsonUtility.FromJson<PrefabDataWrapper>(json);
                if (wrapper != null && wrapper.prefabData != null && wrapper.prefabData.Count > 0)
                {
                    Dictionary<string, List<PrefabData>> categorizedPrefabs = CategorizePrefabsByPath(wrapper.prefabData);

                    foreach (var category in categorizedPrefabs)
                    {
                        string categoryName = GetFolderNameFromPath(category.Key);
                        List<string> prefabNames = new List<string>();
                        foreach (var prefabData in category.Value)
                        {
                            prefabNames.Add(prefabData.name);
                        }
                        prefabInfo.Add($"{categoryName}: {string.Join(", ", prefabNames)}");
                    }
                }
            }
            catch (Exception e)
            {
                UnityEngine.Debug.LogError($"读取预制体数据失败: {e.Message}");
            }
        }

        return prefabInfo.Count > 0 ? string.Join("\n", prefabInfo) : "今日未处理预制体";
    }

    private string GetTodayTasksInfo()
    {
        List<string> todayTasks = new List<string>();
        string today = DateTime.Today.ToString("yyyy-MM-dd");

        foreach (var task in tasks)
        {
            if (task.date == today && task.isCompleted)
            {
                // 修改这里：添加任务日期信息
                todayTasks.Add($"✓ {task.content} (计划日期: {task.date})");
            }
        }

        return todayTasks.Count > 0 ? string.Join("\n", todayTasks) : "今日无完成任务";
    }

    private string GetTomorrowTasksInfo()
    {
        List<string> tomorrowTasks = new List<string>();
        string tomorrow = DateTime.Today.AddDays(1).ToString("yyyy-MM-dd");

        foreach (var task in tasks)
        {
            if (task.date == tomorrow && !task.isCompleted)
            {
                // 修改这里：添加任务日期信息
                tomorrowTasks.Add($"• {task.content} (计划日期: {task.date})");
            }
        }

        return tomorrowTasks.Count > 0 ? string.Join("\n", tomorrowTasks) : "明日无计划任务";
    }

    private void ShowWorkLogDialog(string workLog)
    {
        WorkLogDisplayWindow displayWindow = ScriptableObject.CreateInstance<WorkLogDisplayWindow>();
        displayWindow.workLog = workLog;
        displayWindow.ShowModalUtility();
    }

    // ========== 数据管理相关方法 ==========
    private void LoadTaskData()
    {
        try
        {
            string recordsDir = Path.GetDirectoryName(taskDataPath);
            if (!Directory.Exists(recordsDir))
            {
                Directory.CreateDirectory(recordsDir);
            }

            if (File.Exists(taskDataPath))
            {
                string json = File.ReadAllText(taskDataPath);
                TaskDataWrapper wrapper = JsonUtility.FromJson<TaskDataWrapper>(json);
                if (wrapper != null && wrapper.tasks != null)
                {
                    tasks = wrapper.tasks;
                    UnityEngine.Debug.Log($"任务数据加载成功，共{tasks.Count}个任务");
                }
            }
        }
        catch (Exception e)
        {
            UnityEngine.Debug.LogError($"加载任务数据失败: {e.Message}");
        }
    }

    private void SaveTaskData()
    {
        try
        {
            TaskDataWrapper wrapper = new TaskDataWrapper
            {
                tasks = tasks,
                lastUpdateTime = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss")
            };

            string json = JsonUtility.ToJson(wrapper, true);

            string recordsDir = Path.GetDirectoryName(taskDataPath);
            if (!Directory.Exists(recordsDir))
            {
                Directory.CreateDirectory(recordsDir);
            }

            File.WriteAllText(taskDataPath, json);
            UnityEngine.Debug.Log("任务数据已保存");
        }
        catch (Exception e)
        {
            UnityEngine.Debug.LogError($"保存任务数据失败: {e.Message}");
        }
    }

    // ========== 工具方法 ==========
    private string EscapeJsonString(string input)
    {
        if (string.IsNullOrEmpty(input))
            return input;

        return input.Replace("\\", "\\\\")
                   .Replace("\"", "\\\"")
                   .Replace("\n", "\\n")
                   .Replace("\r", "\\r")
                   .Replace("\t", "\\t");
    }

    private DeepSeekMessage ParseDeepSeekResponse(string jsonResponse)
    {
        try
        {
            if (jsonResponse.Contains("\"choices\"") && jsonResponse.Contains("\"message\""))
            {
                int contentStart = jsonResponse.IndexOf("\"content\"") + 10;
                int contentEnd = jsonResponse.IndexOf("\"", contentStart);
                if (contentStart >= 10 && contentEnd > contentStart)
                {
                    string content = jsonResponse.Substring(contentStart, contentEnd - contentStart);
                    content = content.Replace("\\n", "\n").Replace("\\\"", "\"");
                    return new DeepSeekMessage { content = content };
                }
            }

            var wrapper = JsonUtility.FromJson<DeepSeekResponseWrapper>(jsonResponse);
            if (wrapper != null && wrapper.choices != null && wrapper.choices.Length > 0)
            {
                return wrapper.choices[0].message;
            }
        }
        catch (Exception e)
        {
            UnityEngine.Debug.LogError($"解析DeepSeek响应失败: {e.Message}");
        }

        return null;
    }

    private Dictionary<string, List<PrefabData>> CategorizePrefabsByPath(List<PrefabData> prefabDataList)
    {
        Dictionary<string, List<PrefabData>> categorized = new Dictionary<string, List<PrefabData>>();

        foreach (var prefabData in prefabDataList)
        {
            if (string.IsNullOrEmpty(prefabData.path))
                continue;

            string directory = Path.GetDirectoryName(prefabData.path);
            if (string.IsNullOrEmpty(directory))
            {
                directory = "未分类";
            }

            if (!categorized.ContainsKey(directory))
            {
                categorized[directory] = new List<PrefabData>();
            }

            categorized[directory].Add(prefabData);
        }

        return categorized;
    }

    private string GetFolderNameFromPath(string path)
    {
        if (string.IsNullOrEmpty(path))
            return "未分类";

        string folderName = Path.GetFileName(path);
        if (string.IsNullOrEmpty(folderName))
        {
            path = path.TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
            folderName = Path.GetFileName(path);
        }

        return string.IsNullOrEmpty(folderName) ? "未分类" : folderName;
    }

    // ========== 数据类定义 ==========
    [System.Serializable]
    private class TaskItem
    {
        public string content;        // 任务内容
        public string date;          // 任务日期 (yyyy-MM-dd)
        public bool isCompleted;     // 是否完成
        public string completionDate; // 完成日期
        public string creationDate;  // 创建日期
    }

    [System.Serializable]
    private class TaskDataWrapper
    {
        public List<TaskItem> tasks;
        public string lastUpdateTime;
    }

    [System.Serializable]
    private class PrefabData
    {
        public string name;
        public string path;
    }

    [System.Serializable]
    private class PrefabDataWrapper
    {
        public List<PrefabData> prefabData;
        public string lastUpdateTime;
    }

    [System.Serializable]
    private class DeepSeekResponseWrapper
    {
        public DeepSeekChoice[] choices;
    }

    [System.Serializable]
    private class DeepSeekChoice
    {
        public DeepSeekMessage message;
    }

    [System.Serializable]
    private class DeepSeekMessage
    {
        public string content;
    }
}

// 工作日志显示窗口（保持不变）
public class WorkLogDisplayWindow : EditorWindow
{
    public string workLog;
    private Vector2 scrollPosition;

    void OnGUI()
    {
        GUILayout.BeginVertical(GUILayout.ExpandHeight(true));

        GUILayout.Label("AI工作日志生成成功", EditorStyles.boldLabel);
        GUILayout.Space(10);

        GUILayout.Label("日志已复制到剪贴板，完整内容如下：", EditorStyles.miniLabel);
        GUILayout.Space(5);

        scrollPosition = EditorGUILayout.BeginScrollView(scrollPosition, GUILayout.Height(200));
        EditorGUILayout.TextArea(workLog, GUILayout.ExpandHeight(true));
        EditorGUILayout.EndScrollView();

        GUILayout.Space(10);
        GUILayout.Label($"字数: {workLog.Length}", EditorStyles.miniLabel);
        GUILayout.Space(10);

        if (GUILayout.Button("确定"))
        {
            this.Close();
        }

        GUILayout.EndVertical();
    }
}